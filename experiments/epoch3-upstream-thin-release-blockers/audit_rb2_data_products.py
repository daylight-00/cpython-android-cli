#!/usr/bin/env python3
"""Independent audit for an RB-2 owner result directory."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))

from archive import sha256_file  # noqa: E402
from data_products import verify_data_product  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def audit(directory: Path) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    try:
        result = load(directory / "rb2-data-product-result.json")
        reproducibility = load(directory / "reproducibility.json")
        lifecycle = load(directory / "lifecycle.json")
        qualification = load(directory / "runtime-qualification.json")
        invariance = load(directory / "frozen-family-invariance.json")
        artifacts = sorted((directory / "artifacts").glob("*.tar.zst"))
        checks["two_artifacts"] = len(artifacts) == 2
        product_verifications = [verify_data_product(path) for path in artifacts]
        checks["products_verify_independently"] = len(product_verifications) == 2 and all(row["pass"] for row in product_verifications)
        checks["reproducibility"] = reproducibility.get("pass") is True and reproducibility.get("rollback", {}).get("two_run_byte_identity") is True and reproducibility.get("current", {}).get("two_run_byte_identity") is True
        checks["update_rollback"] = lifecycle.get("pass") is True and [row.get("event") for row in lifecycle.get("events", [])] == ["install-rollback", "install-current", "rollback", "reactivate-current"]
        checks["runtime"] = qualification.get("pass") is True and qualification.get("claim_boundary", {}).get("exact_runtime_context_only") is True
        checks["frozen_family"] = invariance.get("pass") is True and invariance.get("file_count") == 128 and invariance.get("before_fingerprint_sha256") == invariance.get("after_fingerprint_sha256")
        checks["result_consistency"] = result.get("pass") is True and not result.get("failed_checks") and all(result.get("checks", {}).values())
        checks["claims_bounded"] = result.get("claim_boundary") == {"publication": False, "rb2_closed": False, "selectable": False}
        subject = [{"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size} for path in artifacts]
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{type(exc).__name__}: {exc}")
        subject = []
    failed = sorted(key for key, value in checks.items() if value is not True)
    return {
        "schema_version": 1,
        "audit_kind": "epoch3-rb2-ca-timezone-data-product-independent-audit",
        "pass": not failed and not errors,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "subjects": subject,
        "claim_boundary": {"rb2_closed": False, "selectable": False, "publication": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = audit(args.directory)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
