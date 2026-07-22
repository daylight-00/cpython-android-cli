#!/usr/bin/env python3
"""Verify the exact accepted RB-3 profile-M successor-full r4 result archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/epoch3-upstream-thin-release-blockers"
EVIDENCE = BASE / "rb3-successor-full-m-authority-evidence"
EXPECTED_RESULT = {
    "filename": "cpython-android-cli-e3-rb3-successor-full-m-r4-results.tar.zst",
    "sha256": "0bf2f2ff4e180206f0b6b59f4e6ff2368fea326d1d64efb5ddd23e5d0db7cc0d",
    "size_bytes": 63029723,
    "self_index_file_count": 77,
}
EXPECTED_CANDIDATE = {
    "filename": "cpython-3.14.6+e3-full-r5-aarch64-linux-android-full.tar.zst",
    "sha256": "b13206f67d900c1954ee6720c1b3d9337c467c9008b93a0384c16fb6127260d2",
    "size_bytes": 39414556,
}
EVIDENCE_MAP = {
    "artifacts/assembly-receipt.json": "assembly-receipt.json",
    "artifacts/reproducibility.json": "reproducibility.json",
    "result-index.json": "result-index.json",
    "summary.json": "owner-summary.json",
    "target/rb3-successor-full-m-result.json": "owner-result.json",
    "target/independent-audit.json": "owner-independent-audit.json",
    "target/full-structural-verification.json": "full-structural-verification.json",
    "target/full-android-qualification.json": "full-android-qualification.json",
    "target/native-wheel-elf-boundary.json": "native-wheel-elf-boundary.json",
    "target/native-managed-wheel-elf-boundary.json": "native-managed-wheel-elf-boundary.json",
    "target/protected-state.json": "protected-state.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_member_root(archive: Path) -> tuple[str | None, list[str], list[str]]:
    proc = subprocess.run(
        ["tar", "--zstd", "-tf", os.fspath(archive)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return None, [], [f"tar-list-returncode:{proc.returncode}", proc.stderr.strip()]
    members = [line.rstrip("/") for line in proc.stdout.splitlines() if line.strip()]
    errors: list[str] = []
    roots: set[str] = set()
    seen: set[str] = set()
    for raw in members:
        if raw in seen:
            errors.append(f"duplicate-member:{raw}")
        seen.add(raw)
        p = PurePosixPath(raw)
        if p.is_absolute() or not p.parts or any(part in {"", ".", ".."} for part in p.parts):
            errors.append(f"unsafe-member:{raw}")
            continue
        roots.add(p.parts[0])
    if len(roots) != 1:
        errors.append(f"root-count:{len(roots)}")
    return next(iter(roots), None), members, errors


def verify_index(result_root: Path) -> dict[str, Any]:
    index = load(result_root / "result-index.json")
    expected = {
        row["path"]: (row["sha256"], row["size_bytes"])
        for row in index.get("files", [])
    }
    excluded = set(index.get("excluded_paths", []))
    actual: dict[str, tuple[str, int]] = {}
    for path in result_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(result_root).as_posix()
        if rel in excluded:
            continue
        actual[rel] = (sha256_file(path), path.stat().st_size)
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    mismatched = sorted(
        rel for rel in set(expected) & set(actual) if expected[rel] != actual[rel]
    )
    return {
        "pass": not missing and not extra and not mismatched,
        "indexed_file_count": len(expected),
        "actual_file_count": len(actual),
        "missing": missing,
        "extra": extra,
        "mismatched": mismatched,
    }


def verify_extracted(result_root: Path) -> dict[str, Any]:
    index_result = verify_index(result_root)
    candidate = result_root / "artifacts" / EXPECTED_CANDIDATE["filename"]
    evidence_exact = {
        rel: (result_root / rel).is_file()
        and (EVIDENCE / name).is_file()
        and (result_root / rel).read_bytes() == (EVIDENCE / name).read_bytes()
        for rel, name in EVIDENCE_MAP.items()
    }
    owner = load(result_root / "target/rb3-successor-full-m-result.json")
    owner_audit = load(result_root / "target/independent-audit.json")
    repro = load(result_root / "artifacts/reproducibility.json")
    structural = load(result_root / "target/full-structural-verification.json")
    android = load(result_root / "target/full-android-qualification.json")
    direct = load(result_root / "target/native-wheel-elf-boundary.json")
    managed = load(result_root / "target/native-managed-wheel-elf-boundary.json")
    protected = load(result_root / "target/protected-state.json")
    checks = {
        "self_index_exact": index_result["pass"] is True
        and index_result["indexed_file_count"] == EXPECTED_RESULT["self_index_file_count"],
        "committed_evidence_exact": all(evidence_exact.values()),
        "candidate_present": candidate.is_file(),
        "candidate_identity": candidate.is_file()
        and sha256_file(candidate) == EXPECTED_CANDIDATE["sha256"]
        and candidate.stat().st_size == EXPECTED_CANDIDATE["size_bytes"],
        "reproducibility": repro.get("pass") is True
        and repro.get("byte_identical") is True
        and repro.get("assembly_a", {}).get("sha256") == EXPECTED_CANDIDATE["sha256"]
        and repro.get("assembly_b", {}).get("sha256") == EXPECTED_CANDIDATE["sha256"],
        "owner_result": owner.get("pass") is True
        and not owner.get("failed_checks")
        and bool(owner.get("checks"))
        and all(value is True for value in owner["checks"].values()),
        "owner_independent_audit": owner_audit.get("pass") is True
        and not owner_audit.get("failed_checks"),
        "structural": structural.get("pass") is True and not structural.get("failed_checks"),
        "android": android.get("pass") is True and not android.get("failed_checks"),
        "direct_native_sdk": direct.get("pass") is True
        and direct.get("wheel_import_returncode") == 0
        and direct.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "managed_native_sdk": managed.get("pass") is True
        and managed.get("wheel_import_returncode") == 0
        and managed.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "raw_wheel_repair_out_of_scope": direct.get("raw_policy_clean") is False
        and managed.get("raw_policy_clean") is False
        and direct.get("postprocessing_boundary") == "out-of-scope-external-tool-responsibility"
        and managed.get("postprocessing_boundary") == "out-of-scope-external-tool-responsibility",
        "protected_state": all(
            protected.get(key) is True
            for key in (
                "candidate_full_unchanged",
                "predecessor_full_unchanged",
                "real_managed_root_unchanged",
            )
        ),
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-rb3-profile-M-successor-full-r4-result-archive",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "index": index_result,
        "evidence_exact": dict(sorted(evidence_exact.items())),
        "candidate_full": EXPECTED_CANDIDATE,
    }


def verify_archive(archive: Path) -> dict[str, Any]:
    archive = archive.resolve()
    identity = {
        "filename": archive.name,
        "sha256": sha256_file(archive) if archive.is_file() else None,
        "size_bytes": archive.stat().st_size if archive.is_file() else None,
    }
    root_name, members, member_errors = safe_member_root(archive) if archive.is_file() else (None, [], ["archive-missing"])
    identity_ok = (
        archive.is_file()
        and identity["sha256"] == EXPECTED_RESULT["sha256"]
        and identity["size_bytes"] == EXPECTED_RESULT["size_bytes"]
    )
    if not identity_ok or member_errors or root_name is None:
        return {
            "schema_version": 1,
            "verifier_kind": "epoch3-rb3-profile-M-successor-full-r4-result-archive",
            "pass": False,
            "checks": {"result_archive_identity": identity_ok, "safe_archive_members": not member_errors},
            "failed_checks": [
                name
                for name, passed in {
                    "result_archive_identity": identity_ok,
                    "safe_archive_members": not member_errors,
                }.items()
                if not passed
            ],
            "identity": identity,
            "member_count": len(members),
            "member_errors": member_errors,
        }
    with tempfile.TemporaryDirectory(prefix="rb3-r4-result-") as td:
        proc = subprocess.run(
            ["tar", "--zstd", "-xf", os.fspath(archive), "-C", td],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            return {
                "schema_version": 1,
                "verifier_kind": "epoch3-rb3-profile-M-successor-full-r4-result-archive",
                "pass": False,
                "checks": {"result_archive_identity": True, "safe_archive_members": True, "extract": False},
                "failed_checks": ["extract"],
                "identity": identity,
                "extract_stderr": proc.stderr,
            }
        result = verify_extracted(Path(td) / root_name)
    result["identity"] = identity
    result["member_count"] = len(members)
    result["checks"]["result_archive_identity"] = True
    result["checks"]["safe_archive_members"] = True
    result["checks"] = dict(sorted(result["checks"].items()))
    result["failed_checks"] = sorted(name for name, passed in result["checks"].items() if passed is not True)
    result["pass"] = not result["failed_checks"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = verify_archive(args.archive)
    except Exception as exc:  # noqa: BLE001
        result = {
            "schema_version": 1,
            "verifier_kind": "epoch3-rb3-profile-M-successor-full-r4-result-archive",
            "pass": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
