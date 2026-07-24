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
STRIPPED_EXECUTION = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-stripped-m-r1-execution-contract.json"
ACCEPTANCE_INSPECTION = "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-acceptance-r1-return-inspection.json"
SUCCESSOR_INSTALL_LOCK = "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-successor-install-only-r5.lock.json"


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
    stripped_execution = load(root, STRIPPED_EXECUTION)
    acceptance_inspection = load(root, ACCEPTANCE_INSPECTION)
    successor_install_lock = load(root, SUCCESSOR_INSTALL_LOCK)
    state = load(root, "docs/current/STATE.json")
    catalog = load(root, "docs/agent/TASK_CATALOG.json")
    task = next(row for row in catalog["tasks"] if row["task_id"] == "E3-RELEASE-BLOCKERS")
    registry = load(root, "docs/documentation/document-registry.json")
    registered = {row["path"] for row in registry["documents"]}
    rb5_contract = "experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-contract.json"
    rb4_authority = "experiments/epoch3-upstream-thin-release-blockers/rb4-release-operations-authority.json"
    rb4_temporal_amendment = "experiments/epoch3-upstream-thin-release-blockers/rb4-release-operations-temporal-verifier-amendment.json"
    rb5_scope_authority = "experiments/epoch3-upstream-thin-release-blockers/rb5-api24-support-scope-authority.json"
    rb5_scope_temporal = "experiments/epoch3-upstream-thin-release-blockers/rb5-api24-support-scope-temporal-verifier-amendment.json"
    rb6_contract = "experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-disposition-contract.json"
    rb6_scope_authority = "experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-authority.json"
    rb6_scope_temporal = "experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-temporal-verifier-amendment.json"
    rb7_contract = "experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-disposition-contract.json"
    rb7_scope_authority = "experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-authority.json"
    rb7_scope_temporal = "experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-temporal-verifier-amendment.json"
    rb1_owner_contract = "experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-contract.json"
    task_reads = {row.get("path") for row in task.get("required_reads", [])}
    task_authorities = {row.get("path"): row.get("sha256") for row in task.get("required_authorities", [])}
    rb5_progression = (
        state.get("state_revision", 0) >= 54
        and state.get("active_work_package") == rb5_contract
        and state.get("claim_boundaries", {}).get("rb4_closed") is True
        and state.get("claim_boundaries", {}).get("release_operations_complete") is True
        and task.get("deliverable", {}).get("current_bounded_transition") == "rb5-api24-runtime-owner-qualification"
        and {rb5_contract, rb4_authority, rb4_temporal_amendment}.issubset(task_reads)
        and (root / rb4_authority).is_file()
        and (root / rb4_temporal_amendment).is_file()
        and task_authorities.get(rb4_authority) == sha(root, rb4_authority)
        and task_authorities.get(rb4_temporal_amendment) == sha(root, rb4_temporal_amendment)
    )
    scope_progression = (
        state.get("state_revision") == 56
        and state.get("active_work_package") == rb6_contract
        and state.get("claim_boundaries", {}).get("rb5_closed") is True
        and state.get("claim_boundaries", {}).get("api24_runtime_supported") is False
        and state.get("claim_boundaries", {}).get("api24_runtime_scope_excluded") is True
        and task.get("deliverable", {}).get("current_bounded_transition") == "rb6-real-16k-runtime-support-disposition"
        and {rb6_contract, rb5_scope_authority, rb5_scope_temporal}.issubset(task_reads)
        and all((root / path).is_file() for path in (rb5_scope_authority, rb5_scope_temporal, rb6_contract))
        and task_authorities.get(rb5_scope_authority) == sha(root, rb5_scope_authority)
        and task_authorities.get(rb5_scope_temporal) == sha(root, rb5_scope_temporal)
    )
    rb6_scope_progression = (
        state.get("state_revision") == 57
        and state.get("active_work_package") == rb7_contract
        and state.get("claim_boundaries", {}).get("rb6_closed") is True
        and state.get("claim_boundaries", {}).get("actual_16k_runtime_supported") is False
        and state.get("claim_boundaries", {}).get("actual_16k_runtime_scope_excluded") is True
        and task.get("deliverable", {}).get("current_bounded_transition") == "rb7-non-termux-runtime-support-disposition"
        and {rb7_contract, rb6_scope_authority, rb6_scope_temporal}.issubset(task_reads)
        and all((root / path).is_file() for path in (rb7_contract, rb6_scope_authority, rb6_scope_temporal))
        and task_authorities.get(rb6_scope_authority) == sha(root, rb6_scope_authority)
        and task_authorities.get(rb6_scope_temporal) == sha(root, rb6_scope_temporal)
    )
    rb7_scope_progression = (
        state.get("state_revision") == 58
        and state.get("active_work_package") == rb1_owner_contract
        and state.get("claim_boundaries", {}).get("rb7_closed") is True
        and state.get("claim_boundaries", {}).get("non_termux_android_context_supported") is False
        and state.get("claim_boundaries", {}).get("non_termux_android_context_scope_excluded") is True
        and task.get("deliverable", {}).get("current_bounded_transition") == "rb1-successor-r3-explicit-owner-approval"
        and {rb7_scope_authority, rb7_scope_temporal, rb1_owner_contract}.issubset(task_reads)
        and all((root / path).is_file() for path in (rb7_scope_authority, rb7_scope_temporal, rb1_owner_contract))
        and task_authorities.get(rb7_scope_authority) == sha(root, rb7_scope_authority)
        and task_authorities.get(rb7_scope_temporal) == sha(root, rb7_scope_temporal)
    )
    policy_correction_authority = "experiments/epoch3-upstream-thin-release-blockers/rb5-rb7-runtime-support-policy-correction-authority.json"
    policy_correction_temporal = "experiments/epoch3-upstream-thin-release-blockers/rb5-rb7-runtime-support-policy-correction-temporal-verifier-amendment.json"
    policy_correction_progression = (
        state.get("state_revision") == 59
        and state.get("active_work_package") == rb1_owner_contract
        and state.get("claim_boundaries", {}).get("api24_runtime_supported") is True
        and state.get("claim_boundaries", {}).get("api24_runtime_scope_excluded") is False
        and state.get("claim_boundaries", {}).get("app_uid_non_termux_runtime_qualified") is True
        and state.get("claim_boundaries", {}).get("non_termux_android_context_scope_excluded") is False
        and task.get("deliverable", {}).get("current_bounded_transition") == "rb1-successor-r3-explicit-owner-approval"
        and {policy_correction_authority, policy_correction_temporal, rb1_owner_contract}.issubset(task_reads)
        and all((root / path).is_file() for path in (policy_correction_authority, policy_correction_temporal, rb1_owner_contract))
        and task_authorities.get(policy_correction_authority) == sha(root, policy_correction_authority)
        and task_authorities.get(policy_correction_temporal) == sha(root, policy_correction_temporal)
    )
    later_progression = rb5_progression or scope_progression or rb6_scope_progression or rb7_scope_progression or policy_correction_progression
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
        "state_active_work": state.get("active_work_package") in {STRIPPED_EXECUTION, "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-technical-family-m-contract.json", "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-family-m-contract.json", "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-data-rebinding-m-contract.json", "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-data-rebinding-m-r1-execution-contract.json", "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-predecessor-supersession-m-contract.json"} or later_progression,
        "state_install_only_accepted": state.get("claim_boundaries", {}).get("successor_install_only_accepted") is True,
        "state_stripped_started": state.get("claim_boundaries", {}).get("successor_stripped_started") is True,
        "state_no_premature_completion": state.get("claim_boundaries", {}).get("selectable") is False
        and isinstance(state.get("claim_boundaries", {}).get("successor_technical_family_accepted"), bool),
        "task_transition": task.get("deliverable", {}).get("current_bounded_transition") in {"rb3-profile-M-successor-stripped-r1-owner-derivation-and-qualification", "rb3-profile-M-successor-technical-family-owner-assembly-and-audit", "rb3-profile-M-successor-legal-family-owner-integration-and-audit", "rb3-profile-M-successor-legal-data-rebinding-owner-qualification", "rb3-profile-M-successor-predecessor-supersession-and-rb3-closure-owner-transition"} or later_progression,
        "task_reads_transition": all(any(row.get("path") == path for row in task.get("required_reads", [])) for path in (CONTRACT, CORRECTION, R1_INSPECTION, R2_INSPECTION, INSTALL_AUTHORITY, STRIPPED_CONTRACT, ACCEPTANCE_INSPECTION, STRIPPED_EXECUTION, SUCCESSOR_INSTALL_LOCK)) or later_progression,
        "task_binds_acceptance": all(any(row.get("path") == path and row.get("sha256") == sha(root, path) for row in task.get("required_authorities", [])) for path in (R2_INSPECTION, INSTALL_AUTHORITY, ACCEPTANCE_INSPECTION)) or later_progression,
        "registry_complete": {CONTRACT, CORRECTION, R1_INSPECTION, R2_INSPECTION, INSTALL_AUTHORITY, STRIPPED_CONTRACT, STRIPPED_EXECUTION, ACCEPTANCE_INSPECTION, LOCK, SUCCESSOR_INSTALL_LOCK}.issubset(registered),
        "correction_success_candidate_only": correction.get("success_boundary", {}).get("successor_install_only_candidate") is True
        and correction.get("success_boundary", {}).get("successor_install_only_accepted") is False,
        "stripped_contract_exact": stripped.get("accepted_input", {}).get("sha256") == EXPECTED_INSTALL["sha256"]
        and stripped.get("success_boundary", {}).get("successor_stripped_candidate") is True
        and stripped.get("success_boundary", {}).get("successor_stripped_accepted") is False,
        "stripped_execution_prepared": stripped_execution.get("status") == "prepared-owner-derivation-pending"
        and stripped_execution.get("accepted_input", {}).get("install_only") == EXPECTED_INSTALL
        and stripped_execution.get("success_boundary", {}).get("successor_stripped_started") is True
        and stripped_execution.get("success_boundary", {}).get("successor_stripped_candidate") is True
        and stripped_execution.get("success_boundary", {}).get("successor_stripped_accepted") is False,
        "acceptance_result_exact": acceptance_inspection.get("result_archive", {}).get("sha256") == "0712ccde2ea5db376242098b3503aa27d53e281f2906b0990600f0e7b58151a7"
        and acceptance_inspection.get("result_archive", {}).get("size_bytes") == 9973
        and acceptance_inspection.get("result_archive", {}).get("self_index_file_count") == 21,
        "successor_install_lock_exact": successor_install_lock.get("artifact") == EXPECTED_INSTALL
        and successor_install_lock.get("authority_path") == INSTALL_AUTHORITY,
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
