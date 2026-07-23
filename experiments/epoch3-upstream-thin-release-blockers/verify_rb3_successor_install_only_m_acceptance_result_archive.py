#!/usr/bin/env python3
"""Verify the exact successful install-only acceptance-r1 result archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
from typing import Any

EXPECTED_RESULT = {
    "filename": "cpython-android-cli-e3-rb3-successor-install-only-m-acceptance-r1-results.tar.zst",
    "sha256": "0712ccde2ea5db376242098b3503aa27d53e281f2906b0990600f0e7b58151a7",
    "size_bytes": 9973,
    "self_index_file_count": 21,
}
EXPECTED_POST = {
    "head": "1760149bb6cea14e9726dae3f268830d740f29fc",
    "tree": "0cd6900c20178e840cdb254d4f0ae92ca1d86cd3",
}
EXPECTED_ACTION = "applied-rb3-profile-M-successor-install-only-r5-accepted-stripped-derivation-authorized-pushed"


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
    return {
        "pass": not missing and not extra and not mismatched,
        "indexed_file_count": len(expected),
        "actual_file_count": len(actual),
        "missing": missing,
        "extra": extra,
        "mismatched": mismatched,
    }


def verify_extracted(result_root: Path) -> dict[str, Any]:
    index = verify_index(result_root)
    summary = load(result_root / "summary.json")
    result_verify = load(result_root / "receipts/install-only-r2-result-archive-verification.json")
    acceptance = load(result_root / "receipts/successor-install-only-acceptance-verification.json")
    contract = load(result_root / "receipts/successor-install-only-transition-contract-verification.json")
    boundary = summary.get("claim_boundary", {})
    checks = {
        "self_index_exact": index["pass"] is True and index["indexed_file_count"] == EXPECTED_RESULT["self_index_file_count"],
        "transaction_pass": summary.get("claim_transaction_rc") == 0
        and summary.get("action") == EXPECTED_ACTION
        and summary.get("failure_reason") == "none"
        and summary.get("first_failure") == "none"
        and bool(summary.get("return_codes"))
        and all(value == 0 for value in summary["return_codes"].values()),
        "repository_identity": summary.get("post") == {"head": EXPECTED_POST["head"], "tree": EXPECTED_POST["tree"], "remote_head": EXPECTED_POST["head"]},
        "install_only_result_verified": result_verify.get("pass") is True and not result_verify.get("failed_checks"),
        "acceptance_authority_verified": acceptance.get("pass") is True and not acceptance.get("failed_checks"),
        "transition_contract_verified": contract.get("pass") is True and not contract.get("failed_checks"),
        "claim_boundary": boundary.get("successor_full_accepted") is True
        and boundary.get("successor_install_only_accepted") is True
        and boundary.get("successor_stripped_authorized") is True
        and boundary.get("successor_stripped_started") is False
        and boundary.get("artifact_family_superseded") is False
        and boundary.get("rb3_closed") is False
        and boundary.get("selectable") is False
        and boundary.get("publication") is False,
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-rb3-profile-M-successor-install-only-acceptance-r1-result-archive",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "index": index,
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
            "verifier_kind": "epoch3-rb3-profile-M-successor-install-only-acceptance-r1-result-archive",
            "pass": False,
            "checks": checks,
            "failed_checks": sorted(name for name, passed in checks.items() if passed is not True),
            "identity": identity,
            "member_count": len(members),
            "member_errors": member_errors,
        }
    with tempfile.TemporaryDirectory(prefix="rb3-install-accept-r1-result-") as td:
        proc = subprocess.run(["tar", "--zstd", "-xf", os.fspath(archive), "-C", td], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if proc.returncode != 0:
            return {
                "schema_version": 1,
                "verifier_kind": "epoch3-rb3-profile-M-successor-install-only-acceptance-r1-result-archive",
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
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
