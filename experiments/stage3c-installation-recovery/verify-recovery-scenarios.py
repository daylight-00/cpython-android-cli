#!/usr/bin/env python3
from __future__ import annotations

import argparse
import stat
from pathlib import Path
from typing import Any

import recovery_engine as engine
from recovery_verify_support import (
    EXPECTED_GATE1_CONTRACT_INDEX,
    EXPECTED_GATE2_RESULT_INDEX,
    EXPECTED_LOGS,
    EXPECTED_SNAPSHOTS,
    canonical_json_bytes,
    fingerprint,
    journals,
    read_json,
    sha256_file,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate2-results", required=True, type=Path)
    parser.add_argument("--scenario-results", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--input-before", required=True, type=Path)
    parser.add_argument("--input-after", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    gate2 = args.gate2_results.resolve()
    contract = gate2 / "input/contract"
    results = args.scenario_results.resolve()
    work = args.work_root.resolve()
    before = read_json(args.input_before.resolve())
    after = read_json(args.input_after.resolve())
    scenario = read_json(results / "scenario.json")
    logs = {name: read_json(results / name) for name in EXPECTED_LOGS}
    gate2_scenario = read_json(gate2 / "scenario.json")
    gate2_verification = read_json(gate2 / "verification.json")
    gate2_workflow = read_json(gate2 / "workflow-status.json")

    prepared = work / "prepared"
    intent = work / "intent"
    applying_install = work / "applying-install"
    applying_uninstall = work / "applying-uninstall"
    registry_crash = work / "registry-crash"
    prepared_journals = journals(prepared)
    intent_journals = journals(intent)
    applying_install_journals = journals(applying_install)
    applying_uninstall_journals = journals(applying_uninstall)
    registry_journals = journals(registry_crash)

    checks: dict[str, bool] = {
        "gate2_scenario_pass_61": gate2_scenario.get("pass") is True
        and gate2_scenario.get("check_count") == 61
        and gate2_scenario.get("failed_checks") == [],
        "gate2_verification_pass_58": gate2_verification.get("pass") is True
        and gate2_verification.get("check_count") == 58
        and gate2_verification.get("failed_checks") == [],
        "gate2_workflow_pass": gate2_workflow.get("pass") is True
        and all(value == 0 for value in gate2_workflow.get("returncodes", {}).values()),
        "gate2_result_index_hash_exact": sha256_file(gate2 / "result-index.json")
        == EXPECTED_GATE2_RESULT_INDEX,
        "gate1_contract_index_hash_exact": sha256_file(contract / "contract-index.json")
        == EXPECTED_GATE1_CONTRACT_INDEX,
        "input_tree_unchanged": before.get("pass") is True
        and after.get("pass") is True
        and before.get("entry_count") == after.get("entry_count")
        and before.get("fingerprint") == after.get("fingerprint"),
        "scenario_pass_55": scenario.get("pass") is True
        and scenario.get("check_count") == 55
        and scenario.get("failed_checks") == [],
        "scenario_all_checks_true": len(scenario.get("checks", {})) == 55
        and all(scenario["checks"].values()),
        "scenario_log_set_exact": sorted(path.name for path in results.glob("[0-9][0-9]-*.json"))
        == EXPECTED_LOGS,
        "scenario_log_count_40": scenario.get("observed", {}).get("scenario_log_count") == 40,
        "scenario_logs_canonical": all(
            (results / name).read_bytes() == canonical_json_bytes(logs[name])
            for name in EXPECTED_LOGS
        ),
        "scenario_json_canonical": (results / "scenario.json").read_bytes()
        == canonical_json_bytes(scenario),
        "runtime_seed_exact": logs["01-runtime-seed-install.json"].get("pass") is True
        and logs["01-runtime-seed-install.json"].get("action_counts") == {"create": 714}
        and logs["02-runtime-seed-verify.json"].get("owned_path_count") == 714,
        "development_seed_exact": logs["03-runtime-development-seed-install.json"].get("pass") is True
        and logs["03-runtime-development-seed-install.json"].get("action_counts") == {"create": 454}
        and logs["04-runtime-development-seed-verify.json"].get("owned_path_count") == 1168,
        "prepared_crash_exit_90": logs["05-prepared-crash.json"].get("process_exit") == 90
        and logs["05-prepared-crash.json"].get("output_absent") is True,
        "prepared_journal_before_exact": logs["06-prepared-journal-before-recovery.json"].get("state") == "PREPARED"
        and logs["06-prepared-journal-before-recovery.json"].get("mutations") == [],
        "prepared_recovery_exact": logs["07-prepared-recovery.json"].get("pass") is True
        and logs["07-prepared-recovery.json"].get("actions", [{}])[0].get("action") == "ROLLED_BACK",
        "prepared_journal_after_exact": logs["08-prepared-journal-after-recovery.json"].get("state") == "ROLLED_BACK",
        "prepared_verify_714": logs["09-prepared-verify.json"].get("pass") is True
        and logs["09-prepared-verify.json"].get("owned_path_count") == 714,
        "intent_crash_exit_93": logs["10-intent-crash.json"].get("process_exit") == 93
        and logs["10-intent-crash.json"].get("output_absent") is True,
        "intent_journal_before_exact": logs["11-intent-journal-before-recovery.json"].get("state") == "APPLYING"
        and len(logs["11-intent-journal-before-recovery.json"].get("mutations", [])) == 1
        and logs["11-intent-journal-before-recovery.json"]["mutations"][0].get("status") == "INTENT",
        "intent_recovery_exact": logs["12-intent-recovery.json"].get("actions", [{}])[0].get("action") == "ROLLED_BACK",
        "intent_journal_after_exact": logs["13-intent-journal-after-recovery.json"].get("state") == "ROLLED_BACK",
        "intent_verify_714": logs["14-intent-verify.json"].get("pass") is True
        and logs["14-intent-verify.json"].get("owned_path_count") == 714,
        "applying_install_crash_exit_91": logs["15-applying-install-crash.json"].get("process_exit") == 91,
        "applying_install_five_applied": logs["16-applying-install-journal-before-recovery.json"].get("state") == "APPLYING"
        and len(logs["16-applying-install-journal-before-recovery.json"].get("mutations", [])) == 5
        and all(item.get("status") == "APPLIED" for item in logs["16-applying-install-journal-before-recovery.json"]["mutations"]),
        "applying_install_recovery_restored_5": logs["17-applying-install-recovery.json"].get("actions", [{}])[0].get("restored_count") == 5,
        "applying_install_after_rolled_back": logs["18-applying-install-journal-after-recovery.json"].get("state") == "ROLLED_BACK",
        "applying_install_verify_714_before_lock": logs["19-applying-install-verify.json"].get("pass") is True
        and logs["19-applying-install-verify.json"].get("owned_path_count") == 714,
        "applying_uninstall_crash_exit_91": logs["20-applying-uninstall-crash.json"].get("process_exit") == 91,
        "applying_uninstall_five_applied": logs["21-applying-uninstall-journal-before-recovery.json"].get("state") == "APPLYING"
        and len(logs["21-applying-uninstall-journal-before-recovery.json"].get("mutations", [])) == 5
        and all(item.get("kind") == "removed" and item.get("status") == "APPLIED" for item in logs["21-applying-uninstall-journal-before-recovery.json"]["mutations"]),
        "applying_uninstall_recovery_restored_5": logs["22-applying-uninstall-recovery.json"].get("actions", [{}])[0].get("restored_count") == 5,
        "applying_uninstall_after_rolled_back": logs["23-applying-uninstall-journal-after-recovery.json"].get("state") == "ROLLED_BACK",
        "applying_uninstall_verify_1168": logs["24-applying-uninstall-verify.json"].get("pass") is True
        and logs["24-applying-uninstall-verify.json"].get("owned_path_count") == 1168,
        "registry_crash_exit_91": logs["25-registry-crash-repair.json"].get("process_exit") == 91,
        "registry_crash_mutations_exact": [
            item.get("kind")
            for item in logs["26-registry-crash-journal-before-recovery.json"].get("mutations", [])
        ]
        == ["replaced", "registry"]
        and all(item.get("status") == "APPLIED" for item in logs["26-registry-crash-journal-before-recovery.json"]["mutations"]),
        "registry_crash_recovery_restored_2": any(
            item.get("action") == "ROLLED_BACK" and item.get("restored_count") == 2
            for item in logs["27-registry-crash-recovery.json"].get("actions", [])
        ),
        "registry_crash_after_rolled_back": logs["28-registry-crash-journal-after-recovery.json"].get("state") == "ROLLED_BACK",
        "registry_crash_prior_corruption_restored": logs["29-registry-crash-verify-restored-corruption.json"].get("pass") is False
        and len(logs["29-registry-crash-verify-restored-corruption.json"].get("bad_paths", [])) == 1,
        "registry_crash_normal_repair_exact": logs["30-registry-crash-normal-repair.json"].get("pass") is True
        and logs["30-registry-crash-normal-repair.json"].get("action_counts") == {"noop": 453, "repair": 1},
        "registry_crash_final_verify_1168": logs["31-registry-crash-repaired-verify.json"].get("pass") is True
        and logs["31-registry-crash-repaired-verify.json"].get("owned_path_count") == 1168,
        "committed_crash_exit_92": logs["32-committed-repair-crash.json"].get("process_exit") == 92,
        "committed_journal_exact": logs["33-committed-journal-before-recovery.json"].get("state") == "COMMITTED"
        and [item.get("kind") for item in logs["33-committed-journal-before-recovery.json"].get("mutations", [])]
        == ["replaced", "registry"],
        "committed_recovery_finalized": any(
            item.get("action") == "FINALIZED_COMMIT"
            for item in logs["34-committed-recovery.json"].get("actions", [])
        ),
        "committed_verify_1168": logs["35-committed-verify.json"].get("pass") is True
        and logs["35-committed-verify.json"].get("owned_path_count") == 1168,
        "lock_contender_rejected": logs["36-lock-contender.json"].get("pass") is False
        and "installation lock busy" in logs["36-lock-contender.json"].get("error", ""),
        "lock_holder_completed": logs["37-lock-holder.json"].get("pass") is True
        and logs["37-lock-holder.json"].get("ready_observed") is True,
        "lock_post_release_install_exact": logs["38-lock-post-release-install.json"].get("pass") is True
        and logs["38-lock-post-release-install.json"].get("action_counts") == {"create": 454},
        "lock_post_release_verify_1168": logs["39-lock-post-release-verify.json"].get("pass") is True
        and logs["39-lock-post-release-verify.json"].get("owned_path_count") == 1168,
        "rolled_back_recovery_idempotent": logs["40-idempotent-second-recovery.json"].get("pass") is True
        and any(item.get("action") == "NOOP_ROLLED_BACK" for item in logs["40-idempotent-second-recovery.json"].get("actions", [])),
        "prepared_work_verify": engine.verify(prepared).get("pass") is True
        and engine.verify(prepared).get("owned_path_count") == 714,
        "intent_work_verify": engine.verify(intent).get("pass") is True
        and engine.verify(intent).get("owned_path_count") == 714,
        "applying_install_work_verify": engine.verify(applying_install).get("pass") is True
        and engine.verify(applying_install).get("owned_path_count") == 1168,
        "applying_uninstall_work_verify": engine.verify(applying_uninstall).get("pass") is True
        and engine.verify(applying_uninstall).get("owned_path_count") == 1168,
        "registry_crash_work_verify": engine.verify(registry_crash).get("pass") is True
        and engine.verify(registry_crash).get("owned_path_count") == 1168,
        "prepared_retained_journal_exact": len(prepared_journals) == 1
        and prepared_journals[0].get("state") == "ROLLED_BACK",
        "intent_retained_journal_exact": len(intent_journals) == 1
        and intent_journals[0].get("state") == "ROLLED_BACK",
        "applying_install_retained_journal_exact": len(applying_install_journals) == 1
        and applying_install_journals[0].get("state") == "ROLLED_BACK",
        "applying_uninstall_retained_journal_exact": len(applying_uninstall_journals) == 1
        and applying_uninstall_journals[0].get("state") == "ROLLED_BACK",
        "registry_only_rolled_back_journal_retained": len(registry_journals) == 1
        and registry_journals[0].get("state") == "ROLLED_BACK",
        "prepared_fingerprint_exact": fingerprint(prepared) == scenario["observed"]["prepared_final_fingerprint"],
        "intent_fingerprint_exact": fingerprint(intent) == scenario["observed"]["intent_final_fingerprint"],
        "applying_install_fingerprint_exact": fingerprint(applying_install) == scenario["observed"]["applying_install_final_fingerprint"],
        "applying_uninstall_fingerprint_exact": fingerprint(applying_uninstall) == scenario["observed"]["applying_uninstall_final_fingerprint"],
        "registry_crash_fingerprint_exact": fingerprint(registry_crash) == scenario["observed"]["registry_crash_final_fingerprint"],
        "work_root_set_exact": {path.name for path in work.iterdir()}
        == {
            "runtime-seed",
            "runtime-development-seed",
            "prepared",
            "intent",
            "applying-install",
            "applying-uninstall",
            "registry-crash",
            "lock-ready.txt",
        },
        "claim_boundary_exact": scenario.get("claim_boundary", {}).get("not_proved")
        == "Kernel or power-loss durability, parent-directory fsync, crashes inside an individual non-atomic filesystem primitive, multi-user adversarial mutation, fairness, upgrade or downgrade, or installed runtime behavior.",
    }

    for name, expected_count in EXPECTED_SNAPSHOTS.items():
        registry_snapshot = read_json(results / "snapshots" / f"{name}-registry.json")
        observed_snapshot = read_json(results / "snapshots" / f"{name}-observed-owned-paths.json")
        checks[f"snapshot_{name}_registry_count"] = len(registry_snapshot.get("owned_paths", [])) == expected_count
        checks[f"snapshot_{name}_observed_exact"] = observed_snapshot.get("owned_path_count") == expected_count and observed_snapshot.get("all_match") is True
        checks[f"snapshot_{name}_canonical"] = (
            (results / "snapshots" / f"{name}-registry.json").read_bytes() == canonical_json_bytes(registry_snapshot)
            and (results / "snapshots" / f"{name}-observed-owned-paths.json").read_bytes() == canonical_json_bytes(observed_snapshot)
        )

    if len(checks) != 82:
        raise RuntimeError(f"unexpected check count: {len(checks)}")
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "observed": {
            "scenario_check_count": scenario["check_count"],
            "scenario_log_count": len(EXPECTED_LOGS),
            "snapshot_set": sorted(EXPECTED_SNAPSHOTS),
            "prepared_journal_count": len(prepared_journals),
            "intent_journal_count": len(intent_journals),
            "applying_install_journal_count": len(applying_install_journals),
            "applying_uninstall_journal_count": len(applying_uninstall_journals),
            "registry_crash_journal_count": len(registry_journals),
        },
        "claim_boundary": scenario["claim_boundary"],
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 46


if __name__ == "__main__":
    raise SystemExit(main())
