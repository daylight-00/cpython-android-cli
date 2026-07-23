#!/usr/bin/env python3
"""Verify the exact accepted RB-3 profile-M successor install-only r2 result archive."""
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
EVIDENCE = BASE / "rb3-successor-install-only-m-authority-evidence"
EXPECTED_RESULT = {
    "filename": "cpython-android-cli-e3-rb3-successor-install-only-m-r2-results.tar.zst",
    "sha256": "d8f4d13c34d1ce3eae3ba5ca8002fbc9a357941aa2b46c16fedc032d82b975be",
    "size_bytes": 47232364,
    "self_index_file_count": 72,
}
EXPECTED_CANDIDATE = {
    "filename": "cpython-3.14.6+e3-full-r5-aarch64-linux-android-install_only.tar.gz",
    "sha256": "c904a4d1da527e512c715a3227c62da99728ec62747487795292320cee71ab56",
    "size_bytes": 23843355,
    "member_count": 3699,
}
EVIDENCE_MAP = {
    "summary.json": "owner-summary.json",
    "receipts/independent-audit.json": "owner-independent-audit.json",
    "receipts/rb3-successor-install-only-m.json": "owner-result.json",
    "receipts/full-result-verification.json": "accepted-full-result-verification.json",
    "result-index.json": "result-index.json",
    "target/protected-state.json": "protected-state.json",
    "target/receipts/install-only-reproducibility.json": "reproducibility.json",
    "target/receipts/install-only-verification.json": "install-only-verification.json",
    "target/receipts/install-only-android-qualification.json": "install-only-android-qualification.json",
    "target/receipts/native-wheel-elf-boundary.json": "native-wheel-elf-boundary.json",
    "target/receipts/native-managed-wheel-elf-boundary.json": "native-managed-wheel-elf-boundary.json",
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
        part = PurePosixPath(raw)
        if part.is_absolute() or not part.parts or any(piece in {"", ".", ".."} for piece in part.parts):
            errors.append(f"unsafe-member:{raw}")
            continue
        roots.add(part.parts[0])
    if len(roots) != 1:
        errors.append(f"root-count:{len(roots)}")
    return next(iter(roots), None), members, errors


def verify_index(result_root: Path) -> dict[str, Any]:
    index = load(result_root / "result-index.json")
    expected = {row["path"]: (row["sha256"], row["size_bytes"]) for row in index.get("files", [])}
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
    mismatched = sorted(rel for rel in set(expected) & set(actual) if expected[rel] != actual[rel])
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
    final_candidate = result_root / "artifacts" / EXPECTED_CANDIDATE["filename"]
    target_candidate = result_root / "target/artifacts" / EXPECTED_CANDIDATE["filename"]
    evidence_exact = {
        rel: (result_root / rel).is_file()
        and (EVIDENCE / name).is_file()
        and (result_root / rel).read_bytes() == (EVIDENCE / name).read_bytes()
        for rel, name in EVIDENCE_MAP.items()
    }
    summary = load(result_root / "summary.json")
    owner = load(result_root / "receipts/rb3-successor-install-only-m.json")
    owner_audit = load(result_root / "receipts/independent-audit.json")
    repro = load(result_root / "target/receipts/install-only-reproducibility.json")
    projection = load(result_root / "target/receipts/install-only-verification.json")
    android = load(result_root / "target/receipts/install-only-android-qualification.json")
    direct = load(result_root / "target/receipts/native-wheel-elf-boundary.json")
    managed = load(result_root / "target/receipts/native-managed-wheel-elf-boundary.json")
    protected = load(result_root / "target/protected-state.json")
    candidate_paths = (final_candidate, target_candidate)
    checks = {
        "self_index_exact": index_result["pass"] is True
        and index_result["indexed_file_count"] == EXPECTED_RESULT["self_index_file_count"],
        "committed_evidence_exact": bool(evidence_exact) and all(evidence_exact.values()),
        "candidate_copies_present": all(path.is_file() for path in candidate_paths),
        "candidate_copies_exact": all(
            path.is_file()
            and sha256_file(path) == EXPECTED_CANDIDATE["sha256"]
            and path.stat().st_size == EXPECTED_CANDIDATE["size_bytes"]
            for path in candidate_paths
        ),
        "summary_pass": summary.get("claim_transaction_rc") == 0
        and summary.get("failure_reason") == "none"
        and bool(summary.get("return_codes"))
        and all(value == 0 for value in summary["return_codes"].values()),
        "reproducibility": repro.get("pass") is True
        and repro.get("byte_identical") is True
        and repro.get("first", {}).get("sha256") == EXPECTED_CANDIDATE["sha256"]
        and repro.get("second", {}).get("sha256") == EXPECTED_CANDIDATE["sha256"],
        "projection": projection.get("pass") is True
        and not projection.get("failed_checks")
        and projection.get("artifact", {}).get("sha256") == EXPECTED_CANDIDATE["sha256"]
        and projection.get("artifact", {}).get("member_count") == EXPECTED_CANDIDATE["member_count"],
        "android": android.get("pass") is True
        and not android.get("failed_checks")
        and bool(android.get("checks"))
        and all(value is True for value in android["checks"].values()),
        "owner_result": owner.get("pass") is True
        and not owner.get("failed_checks")
        and bool(owner.get("checks"))
        and all(value is True for value in owner["checks"].values()),
        "owner_independent_audit": owner_audit.get("pass") is True
        and not owner_audit.get("failed_checks")
        and bool(owner_audit.get("checks"))
        and all(value is True for value in owner_audit["checks"].values()),
        "direct_native_sdk": direct.get("pass") is True
        and direct.get("wheel_import_returncode") == 0
        and direct.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "managed_native_sdk": managed.get("pass") is True
        and managed.get("wheel_import_returncode") == 0
        and managed.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "raw_wheel_repair_out_of_scope": direct.get("raw_policy_clean") is False
        and managed.get("raw_policy_clean") is False
        and direct.get("postprocessing_boundary")
        == managed.get("postprocessing_boundary")
        == "out-of-scope-external-tool-responsibility",
        "protected_state": all(
            protected.get(key) is True
            for key in (
                "accepted_full_unchanged",
                "predecessor_install_only_unchanged",
                "real_managed_root_unchanged",
            )
        ),
        "candidate_boundary": summary.get("claim_boundary", {}).get("successor_install_only_candidate") is True
        and summary.get("claim_boundary", {}).get("successor_install_only_accepted") is False
        and summary.get("claim_boundary", {}).get("successor_stripped_started") is False
        and summary.get("claim_boundary", {}).get("artifact_family_superseded") is False
        and summary.get("claim_boundary", {}).get("rb3_closed") is False
        and summary.get("claim_boundary", {}).get("selectable") is False
        and summary.get("claim_boundary", {}).get("publication") is False,
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-rb3-profile-M-successor-install-only-r2-result-archive",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "index": index_result,
        "evidence_exact": dict(sorted(evidence_exact.items())),
        "candidate_install_only": EXPECTED_CANDIDATE,
    }


def verify_archive(archive: Path) -> dict[str, Any]:
    archive = archive.resolve()
    identity = {
        "filename": archive.name,
        "sha256": sha256_file(archive) if archive.is_file() else None,
        "size_bytes": archive.stat().st_size if archive.is_file() else None,
    }
    root_name, members, member_errors = safe_member_root(archive) if archive.is_file() else (None, [], ["archive-missing"])
    identity_ok = archive.is_file() and identity["sha256"] == EXPECTED_RESULT["sha256"] and identity["size_bytes"] == EXPECTED_RESULT["size_bytes"]
    if not identity_ok or member_errors or root_name is None:
        checks = {"result_archive_identity": identity_ok, "safe_archive_members": not member_errors}
        return {
            "schema_version": 1,
            "verifier_kind": "epoch3-rb3-profile-M-successor-install-only-r2-result-archive",
            "pass": False,
            "checks": checks,
            "failed_checks": sorted(name for name, passed in checks.items() if not passed),
            "identity": identity,
            "member_count": len(members),
            "member_errors": member_errors,
        }
    with tempfile.TemporaryDirectory(prefix="rb3-install-r2-result-") as td:
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
                "verifier_kind": "epoch3-rb3-profile-M-successor-install-only-r2-result-archive",
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
            "verifier_kind": "epoch3-rb3-profile-M-successor-install-only-r2-result-archive",
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
