#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ARCHIVE_SHA = "579b880495098e9a46b40e2d96c9555178d0ad8c725d40768e6b854227d66143"
INDEX_SHA = "5f9aa64cb4e0679a4784c9c3b8ebd6d8d91829704984672186dc9f9c0d96ed60"
SAFETY_SHA = "47b571d79990cf6c5f1157f7784a5acfa47478b04a7c6f55185d3c4f38ab8a00"
TREE_SHA = "5d54f8e0ab69ab5923949b9a5a34d71e2ab3da36"
MATRIX_SHA = "a36f86d82ad04b71dfa0afb4ab4fd2da764354402cb8db3fdd73d1903606797f"
AUDIT_SHA = "55f1411cb6ef88f8641d6b3ef74324d07e1be20080070dfe0cf8ead1aae25c63"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(path: Path) -> bool:
    obj = json.loads(path.read_text())
    return path.read_bytes() == (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()

    acceptance_path = repo / "experiments/stage3c-installed-runtime-lifecycle/gate3d-final-uninstall-acceptance.json"
    audit_path = repo / "docs/evidence/STAGE3C_PHASE5_GATE3D_EXTERNAL_AUDIT.json"
    result_doc = repo / "docs/evidence/STAGE3C_PHASE5_GATE3D_FINAL_UNINSTALL_ACCEPTANCE_RESULT.md"
    gate3d_handoff = repo / "docs/handoff/PHASE5_GATE3D_FINAL_UNINSTALL_HANDOFF_20260713.md"
    gate4_handoff = repo / "docs/handoff/PHASE5_GATE4_UPGRADE_DOWNGRADE_HANDOFF_20260713.md"
    readme = repo / "docs/handoff/README.md"
    ledger = repo / "docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md"
    scope = repo / "docs/stages/STAGE3C_PHASE5_SCOPE.md"
    experiment_readme = repo / "experiments/stage3c-installed-runtime-lifecycle/README.md"
    matrix_path = repo / "experiments/stage3c-installed-runtime-lifecycle/gate3d-final-uninstall-matrix.json"

    files = [acceptance_path, audit_path, result_doc, gate3d_handoff, gate4_handoff, readme, ledger, scope, experiment_readme, matrix_path]
    texts = {p: p.read_text() if p.is_file() else "" for p in files}
    acceptance = json.loads(texts[acceptance_path]) if acceptance_path.is_file() else {}
    audit = json.loads(texts[audit_path]) if audit_path.is_file() else {}

    checks: dict[str, bool] = {}
    checks["all_authority_files_exist"] = all(p.is_file() for p in files)
    checks["acceptance_json_canonical"] = canonical_json(acceptance_path)
    checks["external_audit_json_canonical"] = canonical_json(audit_path)
    checks["external_audit_sha_exact"] = sha256(audit_path) == AUDIT_SHA
    checks["matrix_sha_exact"] = sha256(matrix_path) == MATRIX_SHA
    checks["acceptance_kind"] = acceptance.get("authority_kind") == "stage3c-phase5-gate3d-final-uninstall-acceptance"
    checks["acceptance_status_frozen"] = acceptance.get("status") == "FROZEN_PASS"
    checks["acceptance_target_exact"] = acceptance.get("target") == "Termux on Android arm64"
    checks["accepted_tree_exact"] = acceptance.get("accepted_repository", {}).get("semantic_tree") == TREE_SHA
    checks["accepted_head_recorded"] = acceptance.get("accepted_repository", {}).get("observed_head") == "d147a577fce60005890c04d8a0fec34a8a37190b"
    checks["archive_sha_exact"] = acceptance.get("archive", {}).get("sha256") == ARCHIVE_SHA
    checks["archive_name_exact"] = acceptance.get("archive", {}).get("name") == "stage3c-phase5-gate3d-final-uninstall-results-20260713T053801Z.tar.zst"
    checks["archive_size_exact"] = acceptance.get("archive", {}).get("size_bytes") == 23270627
    checks["archive_member_count_exact"] = acceptance.get("archive", {}).get("member_count") == 909
    checks["archive_regular_directory_counts"] = acceptance.get("archive", {}).get("regular_members") == 846 and acceptance.get("archive", {}).get("directory_members") == 63
    checks["archive_unsafe_zero"] = all(acceptance.get("archive", {}).get(k) == 0 for k in ("unsafe_paths", "symlinks", "hardlinks", "special_entries"))
    checks["root_index_sha_exact"] = acceptance.get("root_result_index", {}).get("sha256") == INDEX_SHA
    checks["root_index_count_exact"] = acceptance.get("root_result_index", {}).get("indexed_files") == 845
    checks["root_index_membership_identity_exact"] = acceptance.get("root_result_index", {}).get("membership_exact") is True and acceptance.get("root_result_index", {}).get("identities_exact") is True
    checks["safety_sha_exact"] = acceptance.get("result_tree_safety", {}).get("sha256") == SAFETY_SHA
    checks["safety_counts_exact"] = acceptance.get("result_tree_safety", {}).get("directory_count") == 62 and acceptance.get("result_tree_safety", {}).get("regular_count_before_self") == 844
    checks["target_scenarios_44"] = acceptance.get("checks", {}).get("target_scenarios") == "44/44 PASS"
    checks["target_verifier_138"] = acceptance.get("checks", {}).get("independent_verifier") == "138/138 PASS"
    checks["external_audit_37"] = acceptance.get("checks", {}).get("external_archive_audit") == "37/37 PASS"
    checks["authority_22"] = acceptance.get("checks", {}).get("accepted_authorities") == "22/22 PASS"
    checks["canonical_json_442"] = acceptance.get("checks", {}).get("generated_canonical_json") == "442/442 PASS"
    checks["group_counts_exact"] = acceptance.get("scenario_group_counts") == {"audit": 6, "locking": 2, "preflight": 6, "recovery": 12, "residual": 10, "teardown": 8}
    checks["ordinals_exact"] = acceptance.get("registry_intent_ordinals") == {"exact-owned": 715, "modified-owned-regular": 714, "modified-owned-symlink": 714, "unowned-file": 715}
    raw = acceptance.get("raw_process_evidence", {})
    checks["raw_process_counts"] = raw.get("process_records") == 177 and raw.get("output_records") == 164 and raw.get("stdout_output_byte_exact") == 164
    checks["raw_returncodes_exact"] = raw.get("returncode_counts") == {"0": 144, "44": 20, "90": 5, "92": 4, "93": 4}
    recovery = acceptance.get("recovery_contract", {})
    checks["recovery_rc_exact"] = [recovery.get("prepared_returncode"), recovery.get("late_applying_returncode"), recovery.get("committed_returncode")] == [90, 93, 92]
    checks["rollback_topology_exact"] = recovery.get("precommit_first_recovery") == "ROLLED_BACK" and recovery.get("precommit_second_recovery") == "NOOP_ROLLED_BACK"
    checks["committed_topology_exact"] = recovery.get("committed_first_recovery") == "FINALIZED_COMMIT" and recovery.get("committed_second_recovery") == "ZERO_TRANSACTIONS"
    checks["audit_object_pass_37"] = audit.get("pass") is True and audit.get("check_count") == 37 and audit.get("pass_count") == 37 and not audit.get("failed_checks")
    checks["audit_archive_sha_exact"] = audit.get("archive_sha256") == ARCHIVE_SHA
    checks["audit_root_index_exact"] = audit.get("checks", {}).get("root_index_membership_exact") is True and audit.get("checks", {}).get("root_index_identities_exact") is True
    checks["audit_process_exact"] = audit.get("checks", {}).get("raw_process_records_consistent") is True
    checks["audit_recovery_exact"] = audit.get("checks", {}).get("recovery_rc_actions_exact") is True
    checks["audit_no_fast_success"] = audit.get("checks", {}).get("target_did_not_enable_fast_success") is True
    checks["result_doc_frozen"] = "**Status:** FROZEN PASS" in texts[result_doc] and ARCHIVE_SHA in texts[result_doc] and INDEX_SHA in texts[result_doc]
    checks["gate3d_handoff_frozen"] = "**Status:** FROZEN PASS" in texts[gate3d_handoff] and "37/37 external archive audit" in texts[gate3d_handoff]
    checks["gate4_handoff_active"] = "**Status:** ACTIVE — second product authority and design pending" in texts[gate4_handoff]
    gate4_text = texts[gate4_handoff].lower()
    checks["gate4_requires_complete_second_product"] = "second complete frozen product" in gate4_text and "synthetic version label" in gate4_text
    checks["gate4_no_policy_frozen"] = "No scenario count, operation ordering, or acceptance policy is frozen yet." in texts[gate4_handoff]
    checks["handoff_readme_state"] = "Gate 3D final uninstall target                       FROZEN 44/44 + 138/138 + 37/37" in texts[readme] and "Gate 4 upgrade/downgrade                             ACTIVE" in texts[readme]
    checks["ledger_gate3d_once"] = texts[ledger].count("## Gate 3D — final uninstall and ownership boundary") == 1
    checks["ledger_gate4_once"] = texts[ledger].count("## Gate 4 — upgrade and downgrade") == 1
    checks["scope_gate3d_frozen_gate4_active"] = "Gate 3D   runtime uninstall and final ownership boundary          FROZEN" in texts[scope] and "Gate 4    upgrade and downgrade with second frozen product        ACTIVE" in texts[scope]
    checks["experiment_readme_boundary"] = "Gate 3D frozen; Gate 4 second-product authority and design pending" in texts[experiment_readme]
    checks["claim_boundary_no_gate4_target"] = "no Gate 4 claim is made" in acceptance.get("claim_boundary", "") and "No upgrade/downgrade policy or target claim is frozen" in texts[experiment_readme]

    failed = sorted(k for k, v in checks.items() if not v)
    result = {
        "schema_version": 1,
        "verification_kind": "stage3c-phase5-gate3d-acceptance-freeze-validation",
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "checks": checks,
        "failed_checks": failed,
        "claim_boundary": "Gate 3D is frozen PASS. Gate 4 is open only for second-product authority acquisition and design; no upgrade/downgrade target claim is made.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
