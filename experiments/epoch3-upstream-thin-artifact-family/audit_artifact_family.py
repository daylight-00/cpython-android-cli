#!/usr/bin/env python3
"""Independently audit an Epoch 3 artifact-family candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))

from archive import sha256_file, write_json  # noqa: E402
from release_family import verify_release_family  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def inventory(directory: Path) -> list[dict[str, Any]]:
    return [{"path": p.name, "sha256": sha256_file(p), "size_bytes": p.stat().st_size} for p in sorted(directory.iterdir(), key=lambda p: p.name) if p.is_file()]


def fingerprint(rows: list[dict[str, Any]]) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--zstd", default="zstd")
    args = parser.parse_args()

    result = Path(args.result_dir).resolve()
    receipts = result / "receipts"
    family_dirs = sorted((result / "artifacts").iterdir()) if (result / "artifacts").is_dir() else []
    summary = load(receipts / "gate-diagnostics.json")
    reproduction = load(receipts / "artifact-family-reproducibility.json")
    verification = load(receipts / "artifact-family-verification.json")
    authority_rows = {flavor: load(receipts / f"{flavor}-authority-verification.json") for flavor in ("full", "install_only", "install_only_stripped")}

    checks: dict[str, bool] = {
        "one_release_family_directory": len(family_dirs) == 1 and family_dirs[0].is_dir(),
        "summary_pass": summary.get("pass") is True,
        "all_authorities_pass": all(row.get("pass") is True for row in authority_rows.values()),
        "two_assembly_reproducibility": reproduction.get("pass") is True and reproduction.get("first") == reproduction.get("second"),
        "primary_verification_pass": verification.get("pass") is True,
        "claims_withheld": all(summary.get("claim_boundary", {}).get(key) is False for key in ("artifact_family_authority_frozen", "selectable", "publication", "component_license_mapping_complete", "api24_runtime_claim", "actual_16k_runtime_claim", "non_termux_context_claim")),
    }
    rerun: dict[str, Any] = {"pass": False}
    if checks["one_release_family_directory"]:
        family = family_dirs[0]
        rows = inventory(family)
        checks["exact_file_count"] = len(rows) == 23
        checks["fingerprint_matches_summary"] = fingerprint(rows) == summary.get("release_family", {}).get("fingerprint_sha256")
        rerun = verify_release_family(family, root=ROOT, zstd=args.zstd)
        checks["independent_family_verification"] = rerun.get("pass") is True and rerun.get("release_sha256") == verification.get("release_sha256")
        checks["frozen_artifact_bytes_present"] = all(any(row["path"] == item["filename"] and row["sha256"] == item["sha256"] and row["size_bytes"] == item["size_bytes"] for row in rows) for item in summary.get("inputs", {}).values())
    else:
        checks.update(exact_file_count=False, fingerprint_matches_summary=False, independent_family_verification=False, frozen_artifact_bytes_present=False)

    failed = sorted(key for key, value in checks.items() if value is not True)
    audit = {
        "schema_version": 1,
        "audit_kind": "epoch3-upstream-thin-artifact-family-independent-audit",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "independent_verification": rerun,
        "claim_boundary": {
            "artifact_family_authority_frozen": False,
            "selectable": False,
            "publication": False,
            "component_license_mapping_complete": False,
        },
    }
    write_json(receipts / "independent-audit.json", audit)
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
