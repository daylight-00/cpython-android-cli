#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

EXPECTED_DEPS = {
    "bzip2": ("1.0.8", "3"),
    "libffi": ("3.4.4", "3"),
    "openssl": ("3.5.7", "0"),
    "sqlite": ("3.50.4", "0"),
    "xz": ("5.4.6", "1"),
    "zstd": ("1.5.7", "2"),
}

EXPECTED_CONFIG_TOKENS = [
    "--host=aarch64-linux-android",
    "--without-ensurepip",
    "--enable-shared",
    "--without-static-libpython",
    "--with-openssl=",
]

EXPECTED_CFLAGS_TOKENS = [
    "-D__BIONIC_NO_PAGE_SIZE_MACRO",
    "/prefix/include",
]

EXPECTED_LDFLAGS_TOKENS = [
    "-Wl,--build-id=sha1",
    "-Wl,--no-rosegment",
    "-Wl,-z,max-page-size=16384",
    "-Wl,--no-undefined",
    "-lm",
    "/prefix/lib",
]


def load_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def read_deps(path: Path) -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            out[row["name"]] = (row["version"], row["recipe_revision"])
    return out


def contains_all(value: str, tokens: list[str]) -> tuple[bool, list[str]]:
    missing = [token for token in tokens if token not in value]
    return not missing, missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True, type=Path)
    args = ap.parse_args()

    root = args.input_dir.resolve()
    inputs = load_json(root / "current-build-inputs.json")
    toolchain = load_json(root / "current-toolchain-identity.json")
    deps = read_deps(root / "current-dependency-provenance.tsv")

    sysconfigs = inputs.get("sysconfigdata", [])
    selected = sysconfigs[0].get("selected_build_time_vars", {}) if sysconfigs else {}

    config_args = str(selected.get("CONFIG_ARGS", ""))
    cflags = str(selected.get("CONFIGURE_CFLAGS") or selected.get("CFLAGS") or "")
    ldflags = str(selected.get("CONFIGURE_LDFLAGS") or selected.get("LDFLAGS") or "")
    cc = str(selected.get("CC", ""))
    build_type = str(selected.get("BUILD_GNU_TYPE", ""))

    dep_checks = {
        name: {
            "expected_version": version,
            "expected_recipe_revision": revision,
            "observed": deps.get(name),
            "match": deps.get(name) == (version, revision),
        }
        for name, (version, revision) in EXPECTED_DEPS.items()
    }

    config_ok, config_missing = contains_all(config_args, EXPECTED_CONFIG_TOKENS)
    cflags_ok, cflags_missing = contains_all(cflags, EXPECTED_CFLAGS_TOKENS)
    ldflags_ok, ldflags_missing = contains_all(ldflags, EXPECTED_LDFLAGS_TOKENS)

    snapshot_ndk = toolchain.get("ndk_version_from_android_env")
    active_ndk = toolchain.get("ndk_version_derived")
    embedded_ndk_match = re.search(r"/ndk/([^/]+)/", cc)
    embedded_ndk = embedded_ndk_match.group(1) if embedded_ndk_match else None

    producer_os = "UNKNOWN"
    if "apple-darwin" in build_type or cc.startswith("/Users/"):
        producer_os = "MACOS"
    elif "linux" in build_type and not cc.startswith("/Users/"):
        producer_os = "LINUX_OR_OTHER_UNIX"

    release_workspace_style = "/Users/runner/work/release-tools/" in config_args or "/Users/runner/work/release-tools/" in str(selected)

    source_git = inputs.get("cpython_source_git", {})
    exact_source_identity = bool(source_git.get("is_git_worktree") and source_git.get("head"))

    findings = {
        "dependency_release_tag_model_match": all(item["match"] for item in dep_checks.values()),
        "dependency_count_observed": len(deps),
        "producer_config_structure_match": config_ok and cflags_ok and ldflags_ok,
        "embedded_producer_os_classification": producer_os,
        "release_workspace_style_path_observed": release_workspace_style,
        "snapshot_ndk_version": snapshot_ndk,
        "active_compiler_ndk_version": active_ndk,
        "embedded_prefix_ndk_version": embedded_ndk,
        "snapshot_vs_embedded_ndk_match": snapshot_ndk is not None and snapshot_ndk == embedded_ndk,
        "snapshot_vs_active_ndk_match": snapshot_ndk is not None and active_ndk is not None and snapshot_ndk == active_ndk,
        "exact_cpython_source_git_identity_available": exact_source_identity,
        "historical_build_evidence_file_count": inputs.get("historical_build_evidence_file_count", 0),
        "phase2_ready": bool(
            exact_source_identity
            and all(item["match"] for item in dep_checks.values())
            and config_ok
            and cflags_ok
            and ldflags_ok
            and snapshot_ndk is not None
            and active_ndk is not None
            and snapshot_ndk == active_ndk
        ),
    }

    report = {
        "findings": findings,
        "dependency_checks": dep_checks,
        "config_structure_checks": {
            "CONFIG_ARGS": {"pass": config_ok, "missing_tokens": config_missing},
            "CFLAGS": {"pass": cflags_ok, "missing_tokens": cflags_missing},
            "LDFLAGS": {"pass": ldflags_ok, "missing_tokens": ldflags_missing},
        },
        "selected_embedded_metadata": {
            "BUILD_GNU_TYPE": build_type,
            "CC": cc,
            "HOST_GNU_TYPE": selected.get("HOST_GNU_TYPE"),
            "CONFIG_ARGS": config_args,
        },
        "remaining_gates": [
            gate
            for gate, passed in [
                ("exact CPython source Git identity", exact_source_identity),
                ("dependency release-tag model match", all(item["match"] for item in dep_checks.values())),
                ("producer config structure match", config_ok and cflags_ok and ldflags_ok),
                ("active compiler NDK matches preserved snapshot", snapshot_ndk is not None and active_ndk is not None and snapshot_ndk == active_ndk),
            ]
            if not passed
        ],
    }

    out = root / "current-lineage-analysis.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))

    print()
    print(f"Result: {out}")
    print()
    print("STAGE3B_LINEAGE_ANALYSIS=COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
