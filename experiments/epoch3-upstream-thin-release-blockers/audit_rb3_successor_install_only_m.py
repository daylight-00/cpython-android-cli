#!/usr/bin/env python3
"""Independent audit of the successor install-only owner result."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED = {
    "filename": "cpython-3.14.6+e3-full-r5-aarch64-linux-android-install_only.tar.gz",
    "sha256": "c904a4d1da527e512c715a3227c62da99728ec62747487795292320cee71ab56",
    "size_bytes": 23843355,
    "member_count": 3699,
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def audit(result_dir: Path) -> dict[str, Any]:
    result = load(result_dir / "rb3-successor-install-only-m-result.json")
    verification = load(result_dir / "receipts/install-only-verification.json")
    qualification = load(result_dir / "receipts/install-only-android-qualification.json")
    direct = load(result_dir / "receipts/native-wheel-elf-boundary.json")
    managed = load(result_dir / "receipts/native-managed-wheel-elf-boundary.json")
    protected = load(result_dir / "protected-state.json")
    artifact = result_dir / "artifacts" / EXPECTED["filename"]

    checks = {
        "result_pass": result.get("pass") is True and result.get("failed_checks") == [],
        "all_result_checks_true": bool(result.get("checks")) and all(value is True for value in result.get("checks", {}).values()),
        "artifact_identity": result.get("artifact") == EXPECTED,
        "artifact_exists": artifact.is_file(),
        "artifact_bytes_exact": artifact.is_file() and hashlib.sha256(artifact.read_bytes()).hexdigest() == EXPECTED["sha256"] and artifact.stat().st_size == EXPECTED["size_bytes"],
        "projection_verification": verification.get("pass") is True and verification.get("failed_checks") == [],
        "android_qualification": qualification.get("pass") is True and qualification.get("failed_checks") == [],
        "direct_native_build_import": direct.get("pass") is True and direct.get("wheel_import_returncode") == 0,
        "direct_native_16k": direct.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "managed_native_build_import": managed.get("pass") is True and managed.get("wheel_import_returncode") == 0,
        "managed_native_16k": managed.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "raw_policy_diagnostic_only": direct.get("raw_policy_clean") is False
        and managed.get("raw_policy_clean") is False
        and direct.get("postprocessing_boundary") == "out-of-scope-external-tool-responsibility"
        and managed.get("postprocessing_boundary") == "out-of-scope-external-tool-responsibility"
        and result.get("claim_boundary", {}).get("portable_raw_wheel_claim") is False
        and result.get("claim_boundary", {}).get("user_built_wheel_postprocessing") == "out-of-scope-external-tool-responsibility",
        "accepted_full_unchanged": protected.get("accepted_full_unchanged") is True,
        "predecessor_install_only_unchanged": protected.get("predecessor_install_only_unchanged") is True,
        "real_managed_root_unchanged": protected.get("real_managed_root_unchanged") is True,
        "candidate_only_boundary": result.get("claim_boundary", {}).get("successor_install_only_candidate") is True and result.get("claim_boundary", {}).get("successor_install_only_accepted") is False,
        "stripped_not_started": result.get("claim_boundary", {}).get("successor_stripped_started") is False,
        "predecessor_not_superseded": result.get("claim_boundary", {}).get("predecessor_family_superseded") is False,
        "rb3_open": result.get("claim_boundary", {}).get("rb3_closed") is False,
        "not_selectable_or_published": result.get("claim_boundary", {}).get("selectable") is False and result.get("claim_boundary", {}).get("publication") is False,
    }
    failed = sorted(name for name, value in checks.items() if value is not True)
    return {"schema_version": 1, "audit_kind": "epoch3-rb3-profile-M-successor-install-only-independent-audit", "pass": not failed, "checks": dict(sorted(checks.items())), "failed_checks": failed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(args.result_dir.resolve())
    except Exception as exc:  # noqa: BLE001
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
