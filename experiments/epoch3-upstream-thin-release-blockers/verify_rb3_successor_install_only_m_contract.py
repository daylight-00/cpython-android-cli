#!/usr/bin/env python3
"""Verify the completed successor install-only transition and stripped routing."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_FULL = {
    "filename": "cpython-3.14.6+e3-full-r5-aarch64-linux-android-full.tar.zst",
    "sha256": "b13206f67d900c1954ee6720c1b3d9337c467c9008b93a0384c16fb6127260d2",
    "size_bytes": 39414556,
    "member_count": 3752,
}
EXPECTED_INSTALL = {
    "filename": "cpython-3.14.6+e3-full-r5-aarch64-linux-android_install_only.tar.gz".replace("android_", "android-"),
    "sha256": "c904a4d1da527e512c715a3227c62da99728ec62747487795292320cee71ab56",
    "size_bytes": 23843355,
    "member_count": 3699,
}
EXPECTED_R2_RESULT = {
    "filename": "cpython-android-cli-e3-rb3-successor-install-only-m-r2-results.tar.zst",
    "sha256": "d8f4d13c34d1ce3eae3ba5ca8002fbc9a357941aa2b46c16fedc032d82b975be",
    "size_bytes": 47232364,
    "self_index_file_count": 72,
}
CONTRACT = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-contract.json"
CORRECTION = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-r2-correction-contract.json"
R1_INSPECTION = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-r1-return-inspection.json"
R2_INSPECTION = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-r2-return-inspection.json"
FULL_INSPECTION = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-acceptance-r2-return-inspection.json"
LOCK = "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-full-r5.lock.json"
FULL_AUTHORITY = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-authority.json"
INSTALL_AUTHORITY = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-authority.json"
STRIPPED_CONTRACT = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-stripped-m-contract.json"


def load(root: Path, path: str) -> dict[str, Any]:
    value = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha(root: Path, path: str) -> str:
    return hashlib.sha256((root / path).read_bytes()).hexdigest()


def verify(root: Path) -> dict[str, Any]:
    contract = load(root, CONTRACT)
    correction = load(root, CORRECTION)
    r1 = load(root, R1_INSPECTION)
    r2 = load(root, R2_INSPECTION)
    full_inspection = load(root, FULL_INSPECTION)
    lock = load(root, LOCK)
    full_authority = load(root, FULL_AUTHORITY)
    install_authority = load(root, INSTALL_AUTHORITY)
    stripped = load(root, STRIPPED_CONTRACT)
    state = load(root, "docs/current/STATE.json")
    catalog = load(root, "docs/agent/TASK_CATALOG.json")
    task = next(row for row in catalog["tasks"] if row["task_id"] == "E3-RELEASE-BLOCKERS")
    registry = load(root, "docs/documentation/document-registry.json")
    registered = {row["path"] for row in registry["documents"]}
    expected_r1_archive = {
        "filename": "cpython-android-cli-e3-rb3-successor-install-only-m-r1-results.tar.zst",
        "sha256": "ecd0b73bd3e9f6339ab8119000959cec721104b5d1c5a260998f9054ca2c8bf3",
        "size_bytes": 23629446,
        "self_index_exact": True,
        "self_index_file_count": 68,
    }
    checks = {
        "predecessor_contract_completed": contract.get("status") == "owner-r2-qualified-candidate-accepted-by-successor-install-only-authority"
        and contract.get("accepted_by") == INSTALL_AUTHORITY,
        "correction_completed": correction.get("status") == "completed-owner-r2-pass-candidate-accepted-by-successor-install-only-authority"
        and correction.get("predecessor_contract") == CONTRACT
        and correction.get("result_archive") == EXPECTED_R2_RESULT
        and correction.get("accepted_by") == INSTALL_AUTHORITY,
        "accepted_full_exact": {key: contract.get("accepted_input", {}).get(key) for key in EXPECTED_FULL} == EXPECTED_FULL,
        "candidate_exact": {key: contract.get("expected_candidate", {}).get(key) for key in EXPECTED_INSTALL} == EXPECTED_INSTALL,
        "correction_candidate_exact": correction.get("accepted_input", {}).get("expected_install_only") == EXPECTED_INSTALL,
        "full_lock_exact": lock.get("artifact") == EXPECTED_FULL,
        "full_authority_exact": full_authority.get("accepted_full") == EXPECTED_FULL,
        "lock_authority_hash": lock.get("authority", {}).get("sha256") == sha(root, FULL_AUTHORITY),
        "full_acceptance_receipt_success": full_inspection.get("receipt", {}).get("claim_transaction_rc") == 0
        and full_inspection.get("verification", {}).get("all_return_codes_zero") is True,
        "r1_result_exact": r1.get("result_archive") == expected_r1_archive,
        "r1_target_pass_audit_only_failure": r1.get("candidate", {}).get("target_result_pass") is True
        and r1.get("candidate", {}).get("all_target_checks_true") is True
        and r1.get("audit_observation", {}).get("only_failed_check") is True,
        "r2_result_exact": r2.get("result_archive") == {
            **EXPECTED_R2_RESULT,
            "self_index_exact": True,
        },
        "r2_result_registered": any(row.get("path") == R2_INSPECTION and row.get("sha256") == sha(root, R2_INSPECTION) for row in state.get("accepted_authorities", [])),
        "install_authority_exact": install_authority.get("accepted_install_only") == EXPECTED_INSTALL
        and install_authority.get("status") == "successor-install-only-r5-accepted-stripped-derivation-authorized",
        "install_authority_registered": any(row.get("path") == INSTALL_AUTHORITY and row.get("sha256") == sha(root, INSTALL_AUTHORITY) for row in state.get("accepted_authorities", [])),
        "audit_only_scope": correction.get("correction_scope", {}).get("audit_predicate_changed") is True
        and correction.get("correction_scope", {}).get("product_bytes_changed") is False
        and correction.get("correction_scope", {}).get("projection_changed") is False,
        "state_active_work": state.get("active_work_package") == STRIPPED_CONTRACT,
        "state_install_only_accepted": state.get("claim_boundaries", {}).get("successor_install_only_accepted") is True,
        "state_stripped_not_started": state.get("claim_boundaries", {}).get("successor_stripped_started") is False,
        "state_no_premature_completion": state.get("claim_boundaries", {}).get("selectable") is False
        and state.get("claim_boundaries", {}).get("successor_technical_family_accepted") is False,
        "task_transition": task.get("deliverable", {}).get("current_bounded_transition") == "rb3-profile-M-successor-install-only-r5-accepted-and-successor-stripped-owner-derivation",
        "task_reads_transition": all(any(row.get("path") == path for row in task.get("required_reads", [])) for path in (CONTRACT, CORRECTION, R1_INSPECTION, R2_INSPECTION, INSTALL_AUTHORITY, STRIPPED_CONTRACT)),
        "task_binds_acceptance": all(any(row.get("path") == path and row.get("sha256") == sha(root, path) for row in task.get("required_authorities", [])) for path in (R2_INSPECTION, INSTALL_AUTHORITY)),
        "registry_complete": {CONTRACT, CORRECTION, R1_INSPECTION, R2_INSPECTION, INSTALL_AUTHORITY, STRIPPED_CONTRACT, LOCK}.issubset(registered),
        "correction_success_candidate_only": correction.get("success_boundary", {}).get("successor_install_only_candidate") is True
        and correction.get("success_boundary", {}).get("successor_install_only_accepted") is False,
        "stripped_contract_exact": stripped.get("accepted_input", {}).get("sha256") == EXPECTED_INSTALL["sha256"]
        and stripped.get("success_boundary", {}).get("successor_stripped_candidate") is True
        and stripped.get("success_boundary", {}).get("successor_stripped_accepted") is False,
        "predecessor_not_superseded": install_authority.get("claim_boundary", {}).get("artifact_family_superseded") is False
        and stripped.get("success_boundary", {}).get("predecessor_family_superseded") is False,
        "rb3_open_unpublished": install_authority.get("claim_boundary", {}).get("rb3_closed") is False
        and install_authority.get("claim_boundary", {}).get("selectable") is False
        and install_authority.get("claim_boundary", {}).get("publication") is False,
    }
    failed = sorted(name for name, value in checks.items() if value is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-rb3-successor-install-only-accepted-stripped-routing",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    try:
        result = verify(args.root.resolve())
    except Exception as exc:  # noqa: BLE001
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
