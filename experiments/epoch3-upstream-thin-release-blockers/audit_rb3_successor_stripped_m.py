#!/usr/bin/env python3
"""Independent audit of the profile-M successor stripped owner result."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_SOURCE = {
    "filename": "cpython-3.14.6+e3-full-r5-aarch64-linux-android-install_only.tar.gz",
    "sha256": "c904a4d1da527e512c715a3227c62da99728ec62747487795292320cee71ab56",
    "size_bytes": 23843355,
}
EXPECTED_FILENAME = "cpython-3.14.6+e3-full-r5-aarch64-linux-android-install_only_stripped.tar.gz"
EXPECTED_CHANGED_PATHS = ["bin/python3.14"]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def audit(result_dir: Path) -> dict[str, Any]:
    result = load(result_dir / "rb3-successor-stripped-m-result.json")
    reproducibility = load(result_dir / "receipts/stripped-reproducibility.json")
    mutation = load(result_dir / "receipts/stripped-mutation-receipt.json")
    verification = load(result_dir / "receipts/stripped-verification.json")
    qualification = load(result_dir / "receipts/stripped-android-qualification.json")
    direct = load(result_dir / "receipts/native-wheel-elf-boundary.json")
    managed = load(result_dir / "receipts/native-managed-wheel-elf-boundary.json")
    protected = load(result_dir / "protected-state.json")
    artifact = result_dir / "artifacts" / EXPECTED_FILENAME
    artifact_identity = result.get("artifact", {})
    actual_sha = hashlib.sha256(artifact.read_bytes()).hexdigest() if artifact.is_file() else None
    actual_size = artifact.stat().st_size if artifact.is_file() else None

    checks = {
        "result_pass": result.get("pass") is True and result.get("failed_checks") == [],
        "all_result_checks_true": bool(result.get("checks")) and all(value is True for value in result.get("checks", {}).values()),
        "source_install_only_exact": result.get("source_install_only") == EXPECTED_SOURCE,
        "artifact_exists": artifact.is_file(),
        "artifact_filename": artifact_identity.get("filename") == EXPECTED_FILENAME,
        "artifact_identity_self_consistent": artifact.is_file()
        and artifact_identity.get("sha256") == actual_sha
        and artifact_identity.get("size_bytes") == actual_size
        and artifact_identity.get("member_count") == 3699,
        "artifact_distinct_from_install_only": artifact_identity.get("sha256") not in {None, EXPECTED_SOURCE["sha256"]},
        "reproducibility": reproducibility.get("pass") is True
        and reproducibility.get("byte_identical") is True
        and reproducibility.get("first") == reproducibility.get("second")
        and reproducibility.get("first", {}).get("sha256") == artifact_identity.get("sha256"),
        "bounded_mutation": mutation.get("decision") == "distinct-archive"
        and mutation.get("regular_elf_count") == 81
        and mutation.get("eligible_elf_count") == 1
        and mutation.get("changed_elf_count") == 1
        and mutation.get("eligible_paths") == EXPECTED_CHANGED_PATHS
        and mutation.get("changed_paths") == EXPECTED_CHANGED_PATHS,
        "stripped_verification": verification.get("pass") is True
        and verification.get("failed_checks") == []
        and verification.get("eligible_paths") == EXPECTED_CHANGED_PATHS
        and verification.get("changed_paths") == EXPECTED_CHANGED_PATHS,
        "non_elf_and_dynamic_surface": verification.get("checks", {}).get("non_elf_bytes_unchanged") is True
        and verification.get("checks", {}).get("elf_dynamic_alignment_preserved") is True
        and verification.get("checks", {}).get("removable_sections_absent_after") is True,
        "android_qualification": qualification.get("pass") is True and qualification.get("failed_checks") == [],
        "direct_native_build_import": direct.get("pass") is True and direct.get("wheel_import_returncode") == 0,
        "direct_native_16k": direct.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "managed_native_build_import": managed.get("pass") is True and managed.get("wheel_import_returncode") == 0,
        "managed_native_16k": managed.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "raw_policy_diagnostic_only": direct.get("raw_policy_clean") is False
        and managed.get("raw_policy_clean") is False
        and direct.get("postprocessing_boundary") == "out-of-scope-external-tool-responsibility"
        and managed.get("postprocessing_boundary") == "out-of-scope-external-tool-responsibility"
        and result.get("claim_boundary", {}).get("portable_raw_wheel_claim") is False,
        "accepted_install_only_unchanged": protected.get("accepted_install_only_unchanged") is True,
        "accepted_full_unchanged": protected.get("accepted_full_unchanged") is True,
        "predecessor_stripped_unchanged": protected.get("predecessor_stripped_unchanged") is True,
        "frozen_authorities_unchanged": protected.get("frozen_authorities_unchanged") is True,
        "real_managed_root_unchanged": protected.get("real_managed_root_unchanged") is True,
        "candidate_only_boundary": result.get("claim_boundary", {}).get("successor_stripped_candidate") is True
        and result.get("claim_boundary", {}).get("successor_stripped_accepted") is False,
        "technical_family_not_started": result.get("claim_boundary", {}).get("successor_technical_family_started") is False
        and result.get("claim_boundary", {}).get("successor_technical_family_accepted") is False,
        "predecessor_not_superseded": result.get("claim_boundary", {}).get("predecessor_family_superseded") is False,
        "rb3_open": result.get("claim_boundary", {}).get("rb3_closed") is False,
        "not_selectable_or_published": result.get("claim_boundary", {}).get("selectable") is False
        and result.get("claim_boundary", {}).get("publication") is False,
    }
    failed = sorted(name for name, value in checks.items() if value is not True)
    return {
        "schema_version": 1,
        "audit_kind": "epoch3-rb3-profile-M-successor-stripped-independent-audit",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "artifact": {
            "filename": artifact_identity.get("filename"),
            "sha256": actual_sha,
            "size_bytes": actual_size,
            "member_count": artifact_identity.get("member_count"),
        },
    }


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
