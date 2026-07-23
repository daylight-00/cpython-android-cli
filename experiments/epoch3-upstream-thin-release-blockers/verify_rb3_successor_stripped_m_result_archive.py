#!/usr/bin/env python3
"""Verify a successful profile-M successor stripped owner result archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
from typing import Any

EXPECTED_SOURCE = {
    "filename": "cpython-3.14.6+e3-full-r5-aarch64-linux-android-install_only.tar.gz",
    "sha256": "c904a4d1da527e512c715a3227c62da99728ec62747487795292320cee71ab56",
    "size_bytes": 23843355,
}
EXPECTED_CANDIDATE_FILENAME = "cpython-3.14.6+e3-full-r5-aarch64-linux-android-install_only_stripped.tar.gz"
EXPECTED_ACTION = "applied-rb3-profile-M-successor-stripped-derived-qualified-audited-pushed"
EXPECTED_CHANGED_PATHS = ["bin/python3.14"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_member_root(archive: Path) -> tuple[str | None, list[str], list[str]]:
    proc = subprocess.run(["tar", "--zstd", "-tf", os.fspath(archive)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        return None, [], [f"tar-list-returncode:{proc.returncode}", proc.stderr.strip()]
    members = [line.rstrip("/") for line in proc.stdout.splitlines() if line.strip()]
    roots: set[str] = set()
    seen: set[str] = set()
    errors: list[str] = []
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
    return {"pass": not missing and not extra and not mismatched, "indexed_file_count": len(expected), "actual_file_count": len(actual), "missing": missing, "extra": extra, "mismatched": mismatched}


def verify_extracted(result_root: Path) -> dict[str, Any]:
    index = verify_index(result_root)
    summary = load(result_root / "summary.json")
    owner = load(result_root / "receipts/rb3-successor-stripped-m.json")
    independent = load(result_root / "receipts/independent-audit.json")
    target = result_root / "target"
    target_result = load(target / "rb3-successor-stripped-m-result.json")
    repro = load(target / "receipts/stripped-reproducibility.json")
    mutation = load(target / "receipts/stripped-mutation-receipt.json")
    verification = load(target / "receipts/stripped-verification.json")
    qualification = load(target / "receipts/stripped-android-qualification.json")
    direct = load(target / "receipts/native-wheel-elf-boundary.json")
    managed = load(target / "receipts/native-managed-wheel-elf-boundary.json")
    protected = load(target / "protected-state.json")
    artifact_paths = [result_root / "artifacts" / EXPECTED_CANDIDATE_FILENAME, target / "artifacts" / EXPECTED_CANDIDATE_FILENAME]
    target_identity = target_result.get("artifact", {})
    copies_exact = all(path.is_file() and sha256_file(path) == target_identity.get("sha256") and path.stat().st_size == target_identity.get("size_bytes") for path in artifact_paths)
    boundary = summary.get("claim_boundary", {})
    checks = {
        "self_index_exact": index["pass"] is True and index["indexed_file_count"] > 0,
        "transaction_pass": summary.get("claim_transaction_rc") == 0
        and summary.get("action") == EXPECTED_ACTION
        and summary.get("failure_reason") == "none"
        and summary.get("first_failure") == "none"
        and bool(summary.get("return_codes"))
        and all(value == 0 for value in summary["return_codes"].values()),
        "source_install_only_exact": target_result.get("source_install_only") == EXPECTED_SOURCE,
        "candidate_identity_consistent": target_identity.get("filename") == EXPECTED_CANDIDATE_FILENAME
        and target_identity.get("member_count") == 3699
        and target_identity.get("sha256") not in {None, EXPECTED_SOURCE["sha256"]}
        and copies_exact,
        "reproducibility": repro.get("pass") is True and repro.get("byte_identical") is True and repro.get("first") == repro.get("second") and repro.get("first", {}).get("sha256") == target_identity.get("sha256"),
        "bounded_mutation": mutation.get("decision") == "distinct-archive"
        and mutation.get("regular_elf_count") == 81
        and mutation.get("eligible_elf_count") == 1
        and mutation.get("changed_elf_count") == 1
        and mutation.get("eligible_paths") == EXPECTED_CHANGED_PATHS
        and mutation.get("changed_paths") == EXPECTED_CHANGED_PATHS,
        "stripped_verification": verification.get("pass") is True and not verification.get("failed_checks") and verification.get("changed_paths") == EXPECTED_CHANGED_PATHS,
        "android_qualification": qualification.get("pass") is True and not qualification.get("failed_checks"),
        "owner_result": owner.get("pass") is True and not owner.get("failed_checks") and bool(owner.get("checks")) and all(value is True for value in owner["checks"].values()),
        "target_result": target_result.get("pass") is True and not target_result.get("failed_checks") and bool(target_result.get("checks")) and all(value is True for value in target_result["checks"].values()),
        "independent_audit": independent.get("pass") is True and not independent.get("failed_checks") and bool(independent.get("checks")) and all(value is True for value in independent["checks"].values()),
        "direct_native_sdk": direct.get("pass") is True and direct.get("wheel_import_returncode") == 0 and direct.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "managed_native_sdk": managed.get("pass") is True and managed.get("wheel_import_returncode") == 0 and managed.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "raw_wheel_diagnostic_only": direct.get("raw_policy_clean") is False
        and managed.get("raw_policy_clean") is False
        and direct.get("postprocessing_boundary") == managed.get("postprocessing_boundary") == "out-of-scope-external-tool-responsibility",
        "protected_state": all(protected.get(key) is True for key in ("accepted_install_only_unchanged", "accepted_full_unchanged", "predecessor_stripped_unchanged", "frozen_authorities_unchanged", "real_managed_root_unchanged")),
        "candidate_boundary": boundary.get("successor_stripped_started") is True
        and boundary.get("successor_stripped_candidate") is True
        and boundary.get("successor_stripped_accepted") is False
        and boundary.get("successor_technical_family_started") is False
        and boundary.get("artifact_family_superseded") is False
        and boundary.get("rb3_closed") is False
        and boundary.get("selectable") is False
        and boundary.get("publication") is False,
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {"schema_version": 1, "verifier_kind": "epoch3-rb3-profile-M-successor-stripped-owner-result-archive", "pass": not failed, "checks": dict(sorted(checks.items())), "failed_checks": failed, "index": index, "candidate": target_identity}


def verify_archive(archive: Path) -> dict[str, Any]:
    archive = archive.resolve()
    identity = {"filename": archive.name, "sha256": sha256_file(archive) if archive.is_file() else None, "size_bytes": archive.stat().st_size if archive.is_file() else None}
    root_name, members, member_errors = safe_member_root(archive) if archive.is_file() else (None, [], ["archive-missing"])
    name_ok = archive.name == "cpython-android-cli-e3-rb3-successor-stripped-m-r1-results.tar.zst"
    if not archive.is_file() or not name_ok or member_errors or root_name is None:
        checks = {"archive_present": archive.is_file(), "archive_name": name_ok, "safe_archive_members": not member_errors}
        return {"schema_version": 1, "verifier_kind": "epoch3-rb3-profile-M-successor-stripped-owner-result-archive", "pass": False, "checks": checks, "failed_checks": sorted(name for name, passed in checks.items() if passed is not True), "identity": identity, "member_count": len(members), "member_errors": member_errors}
    with tempfile.TemporaryDirectory(prefix="rb3-stripped-r1-result-") as td:
        proc = subprocess.run(["tar", "--zstd", "-xf", os.fspath(archive), "-C", td], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if proc.returncode != 0:
            return {"schema_version": 1, "verifier_kind": "epoch3-rb3-profile-M-successor-stripped-owner-result-archive", "pass": False, "checks": {"extract": False}, "failed_checks": ["extract"], "identity": identity, "extract_stderr": proc.stderr}
        result = verify_extracted(Path(td) / root_name)
    result["identity"] = identity
    result["member_count"] = len(members)
    result["checks"]["archive_present"] = True
    result["checks"]["archive_name"] = True
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
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
