#!/usr/bin/env python3
"""Observe an exact Astral full archive as a golden structural reference."""
from __future__ import annotations

import argparse
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from archive import normalize_member_name, sha256_file


def _member_kind(member: tarfile.TarInfo) -> str:
    if member.isdir(): return "directory"
    if member.isfile(): return "file"
    if member.issym(): return "symlink"
    if member.islnk(): return "hardlink"
    return "other"


def observe(archive: Path, *, expected_sha256: str, zstd: str = "zstd") -> dict[str, Any]:
    observed_sha = sha256_file(archive)
    checks: dict[str, bool] = {"exact_sha256": observed_sha == expected_sha256}
    errors: list[str] = []
    members: list[dict[str, Any]] = []
    python_json: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="astral-golden-") as tmp:
        tar_path = Path(tmp) / "golden.tar"
        proc = subprocess.run([zstd, "-q", "-d", "-f", str(archive), "-o", str(tar_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        checks["decompress"] = proc.returncode == 0
        if proc.returncode:
            errors.append(proc.stderr)
        else:
            names: set[str] = set()
            with tarfile.open(tar_path, "r:") as tf:
                for member in tf.getmembers():
                    name = normalize_member_name(member.name)
                    if name in names:
                        errors.append(f"duplicate member: {name}")
                    names.add(name)
                    members.append({"path": name, "type": _member_kind(member), "mode": f"{member.mode & 0o7777:04o}", "size_bytes": member.size, "linkname": member.linkname or None})
                try:
                    py_member = tf.getmember("python/PYTHON.json")
                    stream = tf.extractfile(py_member)
                    if stream is None:
                        raise RuntimeError("PYTHON.json body missing")
                    python_json = json.loads(stream.read().decode("utf-8"))
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"PYTHON.json: {type(exc).__name__}: {exc}")
            paths = {row["path"] for row in members}
            checks["one_python_root"] = bool(paths) and all(path == "python" or path.startswith("python/") for path in paths)
            # Real Astral release tarballs do not necessarily emit explicit
            # directory entries. The canonical roots are therefore structural
            # path prefixes, not mandatory zero-length directory members.
            checks["canonical_full_roots"] = (
                "python/PYTHON.json" in paths
                and any(path.startswith("python/build/") for path in paths)
                and any(path.startswith("python/install/") for path in paths)
            )
            # Astral format 8 archives in the observed 20260610 release encode
            # the schema version as the JSON string "8". Accept the published
            # representation as well as the integer form used by our candidate.
            checks["python_json_format_8"] = str(python_json.get("version")) == "8"
            checks["no_duplicate_members"] = len(paths) == len(members)
    bin_rows = [row for row in members if row["path"].startswith("python/install/bin/") and len(PurePosixPath(row["path"]).parts) == 4]
    build_info = python_json.get("build_info", {}) if isinstance(python_json, dict) else {}
    result = {
        "schema_version": 1,
        "observation_kind": "astral-python-build-standalone-golden-full",
        "pass": all(checks.values()) and not errors,
        "checks": dict(sorted(checks.items())),
        "errors": errors,
        "asset": {"filename": archive.name, "sha256": observed_sha, "expected_sha256": expected_sha256, "size_bytes": archive.stat().st_size},
        "member_count": len(members),
        "members": members,
        "immediate_python_children": sorted({PurePosixPath(row["path"]).parts[1] for row in members if len(PurePosixPath(row["path"]).parts) >= 2}),
        "install_bin_entries": bin_rows,
        "python_json": {
            "top_level_keys": sorted(python_json),
            "value": python_json,
            "build_info_core_keys": sorted(build_info.get("core", {})) if isinstance(build_info, dict) and isinstance(build_info.get("core"), dict) else [],
            "extension_count": len(build_info.get("extensions", {})) if isinstance(build_info, dict) and isinstance(build_info.get("extensions"), dict) else 0,
        },
        "decision_boundary": {
            "archive_structure_is_primary_reference": True,
            "producer_object_tree_is_not_required_from_upstream_thin": True,
            "android_adaptations_may_differ_when_recorded": True,
        },
    }
    return result


def compare(golden: dict[str, Any], candidate_json: dict[str, Any]) -> dict[str, Any]:
    golden_keys = set(golden.get("python_json", {}).get("top_level_keys", []))
    candidate_keys = set(candidate_json)
    required_structure = {"PYTHON.json", "build", "install"}.issubset(set(golden.get("immediate_python_children", [])))
    return {
        "schema_version": 1,
        "comparison_kind": "astral-golden-to-android-upstream-thin-full",
        "pass": golden.get("pass") is True and required_structure and candidate_json.get("version") == 8,
        "shared_python_json_keys": sorted(golden_keys & candidate_keys),
        "golden_only_python_json_keys": sorted(golden_keys - candidate_keys),
        "candidate_only_python_json_keys": sorted(candidate_keys - golden_keys),
        "canonical_roots_match": required_structure,
        "intentional_non_equivalence": [
            "Astral producer object/static build_info is unavailable from the official Android embedding package.",
            "The Android launcher and per-object relative RUNPATH are bounded project adaptations.",
            "Dependency versions and native module topology are inherited from Python.org/BeeWare, not rebuilt by this project.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--candidate-python-json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--comparison-output")
    parser.add_argument("--zstd", default="zstd")
    args = parser.parse_args()
    result = observe(Path(args.archive).resolve(), expected_sha256=args.expected_sha256, zstd=args.zstd)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.candidate_python_json and args.comparison_output:
        candidate = json.loads(Path(args.candidate_python_json).read_text(encoding="utf-8"))
        comparison = compare(result, candidate)
        Path(args.comparison_output).write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result["comparison_pass"] = comparison["pass"]
    print(json.dumps({"pass": result["pass"], "member_count": result["member_count"], "asset": result["asset"], "comparison_pass": result.get("comparison_pass")}, indent=2, sort_keys=True))
    return 0 if result["pass"] and result.get("comparison_pass", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
