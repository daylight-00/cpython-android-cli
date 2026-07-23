#!/usr/bin/env python3
"""Independent audit of the profile-M successor technical-family candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))

from archive import canonical_json_bytes, sha256_file, write_json  # noqa: E402
from successor_release_family import RELEASE_ID, expected_family, verify_successor_release_family  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def inventory(directory: Path) -> list[dict[str, Any]]:
    return [
        {"path": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        for path in sorted(directory.iterdir(), key=lambda item: item.name)
        if path.is_file()
    ]


def audit(result_dir: Path, zstd: str = "zstd") -> dict[str, Any]:
    result = load(result_dir / "rb3-successor-technical-family-m-result.json")
    reproduction = load(result_dir / "receipts/technical-family-reproducibility.json")
    primary = load(result_dir / "receipts/technical-family-verification.json")
    protected = load(result_dir / "receipts/protected-state.json")
    inputs = load(result_dir / "receipts/input-identities.json")
    family = result_dir / "artifacts" / RELEASE_ID
    expected = expected_family(ROOT)
    rerun = verify_successor_release_family(family, root=ROOT, expected=expected, zstd=zstd) if family.is_dir() else {"pass": False}
    rows = inventory(family) if family.is_dir() else []
    fingerprint = hashlib.sha256(canonical_json_bytes(rows)).hexdigest() if rows else None
    checks = {
        "result_pass": result.get("pass") is True and result.get("failed_checks") == [],
        "all_result_checks_true": bool(result.get("checks")) and all(value is True for value in result.get("checks", {}).values()),
        "family_directory": family.is_dir(),
        "exact_file_count": len(rows) == 23,
        "result_fingerprint": fingerprint == result.get("release_family", {}).get("fingerprint_sha256"),
        "two_assemblies_reproducible": reproduction.get("pass") is True
        and reproduction.get("inventory_byte_identical") is True
        and reproduction.get("all_files_byte_identical") is True
        and reproduction.get("first", {}).get("inventory") == reproduction.get("second", {}).get("inventory"),
        "primary_verification": primary.get("pass") is True and primary.get("failed_checks") == [],
        "independent_verification": rerun.get("pass") is True
        and rerun.get("release_sha256") == primary.get("release_sha256")
        and rerun.get("fingerprint_sha256") == primary.get("fingerprint_sha256"),
        "exact_input_identities": inputs.get("pass") is True
        and all(inputs.get("checks", {}).get(flavor) is True for flavor in expected),
        "accepted_artifacts_present": all(
            any(row["path"] == item["filename"] and row["sha256"] == item["sha256"] and row["size_bytes"] == item["size_bytes"] for row in rows)
            for item in expected.values()
        ),
        "protected_state": protected.get("pass") is True
        and protected.get("predecessor_family_unchanged") is True
        and protected.get("successor_authorities_unchanged") is True
        and protected.get("contracts_unchanged") is True,
        "candidate_only": result.get("claim_boundary", {}).get("successor_technical_family_candidate") is True
        and result.get("claim_boundary", {}).get("successor_technical_family_accepted") is False,
        "legal_integration_not_started": result.get("claim_boundary", {}).get("legal_family_integration_started") is False,
        "predecessor_not_superseded": result.get("claim_boundary", {}).get("predecessor_family_superseded") is False,
        "rb1_rb2_not_rebound": result.get("claim_boundary", {}).get("rb1_rebound") is False
        and result.get("claim_boundary", {}).get("rb2_rebound") is False,
        "rb3_open": result.get("claim_boundary", {}).get("rb3_closed") is False,
        "not_selectable_or_published": result.get("claim_boundary", {}).get("selectable") is False
        and result.get("claim_boundary", {}).get("publication") is False,
        "user_wheel_boundary": result.get("claim_boundary", {}).get("portable_user_built_wheel_claim") is False
        and result.get("claim_boundary", {}).get("user_built_wheel_postprocessing") == "out-of-scope-external-tool-responsibility",
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1,
        "audit_kind": "epoch3-rb3-profile-M-successor-technical-family-independent-audit",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "independent_verification": rerun,
        "release_family": {
            "release_id": RELEASE_ID,
            "file_count": len(rows),
            "fingerprint_sha256": fingerprint,
            "release_sha256": rerun.get("release_sha256"),
        },
        "claim_boundary": result.get("claim_boundary"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--zstd", default="zstd")
    args = parser.parse_args()
    try:
        result = audit(args.result_dir.resolve(), args.zstd)
    except Exception as exc:  # noqa: BLE001
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
    if args.output:
        write_json(args.output.resolve(), result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
