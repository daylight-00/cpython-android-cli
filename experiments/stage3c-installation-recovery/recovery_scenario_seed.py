from __future__ import annotations

from pathlib import Path

from recovery_scenario_context import ScenarioContext
from recovery_scenario_support import (
    EXPECTED_GATE1_CONTRACT_INDEX,
    EXPECTED_GATE2_RESULT_INDEX,
    clone_installation,
    fingerprint,
    newest_journal,
    read_json,
    sha256_file,
)


def run_seed_and_early_recovery(ctx: ScenarioContext) -> dict[str, Path]:
    gate2 = ctx.gate2
    contract = ctx.contract
    work = ctx.work

    gate2_scenario = read_json(gate2 / "scenario.json")
    gate2_verification = read_json(gate2 / "verification.json")
    gate2_workflow = read_json(gate2 / "workflow-status.json")
    ctx.check(
        "gate2_scenario_pass_61",
        gate2_scenario.get("pass") is True
        and gate2_scenario.get("check_count") == 61
        and gate2_scenario.get("failed_checks") == [],
    )
    ctx.check(
        "gate2_verification_pass_58",
        gate2_verification.get("pass") is True
        and gate2_verification.get("check_count") == 58
        and gate2_verification.get("failed_checks") == [],
    )
    ctx.check(
        "gate2_workflow_pass",
        gate2_workflow.get("pass") is True
        and all(value == 0 for value in gate2_workflow.get("returncodes", {}).values()),
    )
    ctx.check(
        "gate2_result_index_hash_exact",
        sha256_file(gate2 / "result-index.json") == EXPECTED_GATE2_RESULT_INDEX,
    )
    ctx.check(
        "gate1_contract_index_hash_exact",
        sha256_file(contract / "contract-index.json") == EXPECTED_GATE1_CONTRACT_INDEX,
    )

    runtime_seed = work / "runtime-seed"
    seed, _ = ctx.run_engine(
        "runtime-seed-install",
        runtime_seed,
        "install",
        artifact="runtime-base",
    )
    seed_verify, _ = ctx.run_engine("runtime-seed-verify", runtime_seed, "verify")
    ctx.check(
        "runtime_seed_create_714",
        seed.get("pass") is True and seed.get("action_counts") == {"create": 714},
    )
    ctx.check(
        "runtime_seed_registry_714",
        seed_verify.get("pass") is True and seed_verify.get("owned_path_count") == 714,
    )

    runtime_development_seed = work / "runtime-development-seed"
    clone_installation(runtime_seed, runtime_development_seed)
    dev_seed, _ = ctx.run_engine(
        "runtime-development-seed-install",
        runtime_development_seed,
        "install",
        artifact="development-addon",
    )
    dev_seed_verify, _ = ctx.run_engine(
        "runtime-development-seed-verify",
        runtime_development_seed,
        "verify",
    )
    ctx.check(
        "runtime_development_seed_create_454",
        dev_seed.get("pass") is True and dev_seed.get("action_counts") == {"create": 454},
    )
    ctx.check(
        "runtime_development_seed_registry_1168",
        dev_seed_verify.get("pass") is True
        and dev_seed_verify.get("owned_path_count") == 1168,
    )

    prepared = work / "prepared"
    clone_installation(runtime_seed, prepared)
    before = fingerprint(prepared)
    crashed, process = ctx.run_engine(
        "prepared-crash",
        prepared,
        "install",
        artifact="development-addon",
        extra=["--crash-after-prepared"],
        expect_rc=90,
    )
    _, journal = newest_journal(prepared)
    ctx.save("prepared-journal-before-recovery", journal)
    recovery, _ = ctx.run_engine("prepared-recovery", prepared, "recover")
    _, recovered_journal = newest_journal(prepared)
    ctx.save("prepared-journal-after-recovery", recovered_journal)
    verified, _ = ctx.run_engine("prepared-verify", prepared, "verify")
    ctx.check(
        "prepared_crash_exit_90",
        process.returncode == 90 and crashed.get("output_absent") is True,
    )
    ctx.check(
        "prepared_journal_state_exact",
        journal.get("state") == "PREPARED" and journal.get("mutations") == [],
    )
    ctx.check(
        "prepared_recovery_action",
        recovery.get("pass") is True
        and recovery.get("actions", [{}])[0].get("action") == "ROLLED_BACK",
    )
    ctx.check("prepared_recovered_state", recovered_journal.get("state") == "ROLLED_BACK")
    ctx.check("prepared_fingerprint_restored", fingerprint(prepared) == before)
    ctx.check(
        "prepared_registry_runtime_only",
        verified.get("pass") is True
        and verified.get("artifact_count") == 1
        and verified.get("owned_path_count") == 714,
    )

    intent = work / "intent"
    clone_installation(runtime_seed, intent)
    before = fingerprint(intent)
    crashed, process = ctx.run_engine(
        "intent-crash",
        intent,
        "install",
        artifact="development-addon",
        extra=["--crash-after-intents", "1"],
        expect_rc=93,
    )
    _, journal = newest_journal(intent)
    ctx.save("intent-journal-before-recovery", journal)
    recovery, _ = ctx.run_engine("intent-recovery", intent, "recover")
    _, recovered_journal = newest_journal(intent)
    ctx.save("intent-journal-after-recovery", recovered_journal)
    verified, _ = ctx.run_engine("intent-verify", intent, "verify")
    ctx.check(
        "intent_crash_exit_93",
        process.returncode == 93 and crashed.get("output_absent") is True,
    )
    ctx.check(
        "intent_journal_has_one_intent",
        journal.get("state") == "APPLYING"
        and len(journal.get("mutations", [])) == 1
        and journal["mutations"][0].get("status") == "INTENT",
    )
    ctx.check(
        "intent_recovery_action",
        recovery.get("actions", [{}])[0].get("action") == "ROLLED_BACK",
    )
    ctx.check("intent_recovered_state", recovered_journal.get("state") == "ROLLED_BACK")
    ctx.check("intent_fingerprint_restored", fingerprint(intent) == before)
    ctx.check(
        "intent_registry_runtime_only",
        verified.get("pass") is True and verified.get("owned_path_count") == 714,
    )

    return {
        "runtime_seed": runtime_seed,
        "runtime_development_seed": runtime_development_seed,
        "prepared": prepared,
        "intent": intent,
    }
