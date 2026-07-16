#!/usr/bin/env python3
"""Negative-fixture tests for the Epoch 2 Phase 1 contract verifier."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
VERIFY_PATH = HERE / "verify-e2p1-standalone-artifact-contract.py"
SPEC = importlib.util.spec_from_file_location("e2p1_verify", VERIFY_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load verifier")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

ARTIFACT_ID = MODULE.ARTIFACT_ID
ARCHIVE_NAME = MODULE.ARCHIVE_NAME


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(MODULE.canonical_json_bytes(value))


def mutate_json(fixture: Path, suffix: str, fn: Callable[[dict[str, Any]], None]) -> None:
    path = fixture / f"{ARTIFACT_ID}.{suffix}.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    fn(value)
    write_json(path, value)


def mutate_release(fixture: Path, fn: Callable[[dict[str, Any]], None], recompute: bool = False) -> None:
    path = fixture / "release-index.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    fn(value)
    if recompute:
        value["release_sha256"] = MODULE.sha256_bytes(MODULE.canonical_body_bytes(value["release"]))
    write_json(path, value)


def run(root: Path) -> dict[str, Any]:
    return MODULE.verify(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=HERE.parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    source_fixture = root / "experiments/epoch2-standalone-artifact-contract/fixtures/valid"

    baseline = MODULE.verify(root)
    cases: list[tuple[str, str, Callable[[Path], None]]] = [
        ("target-triple", "target_identity", lambda f: mutate_json(f, "artifact", lambda v: v["target"].__setitem__("target_triple", "aarch64-termux"))),
        ("wheel-tag", "wheel_api_consistency", lambda f: mutate_json(f, "artifact", lambda v: v["target"].__setitem__("wheel_platform_tag", "linux_aarch64"))),
        ("termux-bound", "termux_profile_not_binary_identity", lambda f: mutate_json(f, "artifact", lambda v: v["profiles"].__setitem__("binary_identity_requires_termux", True))),
        ("termux-absolute", "no_termux_absolute_identity", lambda f: mutate_json(f, "artifact", lambda v: v["extensions"].__setitem__("bad_path", "/data/data/com.termux/files/usr"))),
        ("payload-class", "artifact_payload_split", lambda f: mutate_json(f, "artifact", lambda v: v["artifact"].__setitem__("payload_classes", ["runtime"]))),
        ("uv-alias-canonical", "uv_mapping_noncanonical", lambda f: mutate_json(f, "artifact", lambda v: v["compatibility"]["consumer_mappings"].__setitem__("uv_catalog_key_is_canonical_identity", True))),
        ("manifest-escape", "manifest_paths_safe_rooted", lambda f: mutate_json(f, "manifest", lambda v: v["entries"][0].__setitem__("path", "../escape"))),
        ("manifest-order", "manifest_paths_sorted_unique", lambda f: mutate_json(f, "manifest", lambda v: v["entries"].reverse())),
        ("manifest-type", "manifest_entry_types", lambda f: mutate_json(f, "manifest", lambda v: v["entries"][0].__setitem__("type", "hardlink"))),
        ("qualification-selectable", "release_selectability_consistent", lambda f: mutate_json(f, "qualification", lambda v: (v.__setitem__("status", "passed"), v.__setitem__("selectable", True)))),
        ("release-digest", "release_index_digest", lambda f: mutate_release(f, lambda v: v["release"].__setitem__("channel", "prerelease"), recompute=False)),
        ("release-sidecar", "release_sidecar_refs", lambda f: mutate_release(f, lambda v: v["release"]["products"][0]["metadata"]["artifact"].__setitem__("sha256", "0" * 64), recompute=True)),
        ("checksums", "checksums_exact", lambda f: (f / "SHA256SUMS").write_text("0" * 64 + "  bad\n", encoding="utf-8")),
        ("archive-truncate", "archive_decompress_parse", lambda f: (f / ARCHIVE_NAME).write_bytes((f / ARCHIVE_NAME).read_bytes()[:24])),
        ("license-hash", "licenses_match_manifest", lambda f: mutate_json(f, "licenses", lambda v: v["entries"][0].__setitem__("sha256", "f" * 64))),
    ]

    outcomes: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="e2p1-contract-tests-") as td:
        temp = Path(td)
        for name, expected_failure, mutator in cases:
            fixture = temp / name
            shutil.copytree(source_fixture, fixture)
            mutator(fixture)
            result = MODULE.verify(root, fixture)
            passed = (not result["pass"]) and expected_failure in result["failed_checks"]
            outcomes.append({
                "name": name,
                "expected_failure": expected_failure,
                "observed_failed_checks": result["failed_checks"],
                "pass": passed,
            })

    failed = [item["name"] for item in outcomes if not item["pass"]]
    result = {
        "schema_version": 1,
        "test_kind": "epoch2-p1-contract-negative-fixtures",
        "pass": baseline["pass"] and not failed,
        "baseline_pass": baseline["pass"],
        "case_count": len(outcomes),
        "pass_count": sum(item["pass"] for item in outcomes),
        "failed_cases": failed,
        "cases": outcomes,
        "claim_boundary": "Verifier regression tests only; no runtime or target execution.",
    }
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
