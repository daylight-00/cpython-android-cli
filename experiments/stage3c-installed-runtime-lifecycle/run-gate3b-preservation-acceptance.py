#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from gate3b0_preservation_support import (  # noqa: E402
    REGULAR_CANDIDATE,
    SYMLINK_CANDIDATE,
    read_json,
    registry,
    sha256_file,
    transactions,
    write_json,
)
from gate3b_preservation_acceptance_scenarios import (  # noqa: E402
    run_crash_scenario,
    run_happy_reinstall,
    run_happy_uninstall,
)
from gate3b_preservation_acceptance_support import (  # noqa: E402
    BOUNDARIES,
    EXPECTED_CONTRACT_INDEX,
    EXPECTED_ENGINE_SHA,
    EXPECTED_GATE3B0_INDEX,
    EXPECTED_OPS_SHA,
    SUBJECTS,
    invoke_engine_process,
    remaining_registered_paths,
)

EXPECTED_GATE3B0_CLASSIFICATIONS = {
    "reinstall-owned-regular": "ENFORCED_REPAIR",
    "reinstall-owned-symlink": "ENFORCED_REPAIR",
    "reinstall-unowned-file": "PRESERVED_NOOP",
    "reinstall-unowned-directory": "PRESERVED_NOOP",
    "uninstall-owned-regular": "PRESERVED_AND_DEREGISTERED",
    "uninstall-owned-symlink": "PRESERVED_AND_DEREGISTERED",
    "uninstall-unowned-file": "UNOWNED_PRESERVED",
    "uninstall-unowned-directory": "UNOWNED_PRESERVED",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in (
        "gate3b0-results",
        "contract-results",
        "manifest",
        "engine",
        "operations",
        "local-script-runner",
        "work-root",
        "output-dir",
    ):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    gate3b0 = args.gate3b0_results.resolve()
    contract = args.contract_results.resolve()
    manifest_path = args.manifest.resolve()
    engine = args.engine.resolve()
    operations = args.operations.resolve()
    local_runner = args.local_script_runner.resolve()
    work = args.work_root.resolve()
    output = args.output_dir.resolve()
    shutil.rmtree(work, ignore_errors=True)
    shutil.rmtree(output, ignore_errors=True)
    work.mkdir(parents=True)
    output.mkdir(parents=True)
    input_dir = output / "input"
    input_dir.mkdir()

    copied = (
        (gate3b0 / "result-index.json", "gate3b0-result-index.json"),
        (gate3b0 / "verification.json", "gate3b0-verification.json"),
        (gate3b0 / "scenario-summary.json", "gate3b0-scenario-summary.json"),
        (gate3b0 / "workflow-status.json", "gate3b0-workflow-status.json"),
        (gate3b0 / "termux-wrapper-status.json", "gate3b0-wrapper-status.json"),
        (gate3b0 / "accepted-authority.json", "gate3b0-accepted-authority.json"),
    )
    for source, name in copied:
        shutil.copy2(source, input_dir / name)
    shutil.copytree(contract, input_dir / "contract", symlinks=True, copy_function=shutil.copy2)

    gate3b0_verification = read_json(gate3b0 / "verification.json")
    gate3b0_summary = read_json(gate3b0 / "scenario-summary.json")
    gate3b0_workflow = read_json(gate3b0 / "workflow-status.json")
    gate3b0_wrapper = read_json(gate3b0 / "termux-wrapper-status.json")
    authority = {
        "schema_version": 1,
        "gate3b0_result_index_sha256": sha256_file(gate3b0 / "result-index.json"),
        "expected_gate3b0_result_index_sha256": EXPECTED_GATE3B0_INDEX,
        "gate3b0_verification_pass": gate3b0_verification.get("pass") is True,
        "gate3b0_verification_check_count": gate3b0_verification.get("check_count"),
        "gate3b0_scenario_pass": gate3b0_summary.get("pass") is True,
        "gate3b0_scenario_check_count": gate3b0_summary.get("check_count"),
        "gate3b0_classifications": gate3b0_summary.get("classifications"),
        "gate3b0_workflow_pass": gate3b0_workflow.get("pass") is True,
        "gate3b0_wrapper_pass": gate3b0_wrapper.get("pass") is True,
        "contract_index_sha256": sha256_file(contract / "contract-index.json"),
        "copied_contract_index_sha256": sha256_file(input_dir / "contract/contract-index.json"),
        "expected_contract_index_sha256": EXPECTED_CONTRACT_INDEX,
        "engine_sha256": sha256_file(engine),
        "expected_engine_sha256": EXPECTED_ENGINE_SHA,
        "operations_sha256": sha256_file(operations),
        "expected_operations_sha256": EXPECTED_OPS_SHA,
    }
    authority["pass"] = (
        authority["gate3b0_result_index_sha256"] == EXPECTED_GATE3B0_INDEX
        and authority["gate3b0_verification_pass"]
        and authority["gate3b0_verification_check_count"] == 40
        and authority["gate3b0_scenario_pass"]
        and authority["gate3b0_scenario_check_count"] == 16
        and authority["gate3b0_classifications"] == EXPECTED_GATE3B0_CLASSIFICATIONS
        and authority["gate3b0_workflow_pass"]
        and authority["gate3b0_wrapper_pass"]
        and authority["contract_index_sha256"] == EXPECTED_CONTRACT_INDEX
        and authority["copied_contract_index_sha256"] == EXPECTED_CONTRACT_INDEX
        and authority["engine_sha256"] == EXPECTED_ENGINE_SHA
        and authority["operations_sha256"] == EXPECTED_OPS_SHA
    )
    write_json(output / "accepted-authority.json", authority)

    manifest = read_json(manifest_path)
    rows = [
        {
            "path": entry["payload_path"],
            "type": entry["type"],
            "mode": entry["mode"],
            "size": entry.get("size"),
            "sha256": entry.get("sha256"),
            "target": entry.get("symlink_target"),
        }
        for entry in manifest["entries"]
        if entry["entry_class"] == "OWNED_PAYLOAD"
    ]
    row_map = {row["path"]: row for row in rows}
    regular = row_map[REGULAR_CANDIDATE]
    symlink = row_map[SYMLINK_CANDIDATE]
    all_registered_leaves = sorted(row["path"] for row in rows if row["type"] != "directory")

    seed = work / "seed"
    seed_output = output / "seed"
    install = invoke_engine_process(
        runner=local_runner,
        engine=engine,
        contract=contract,
        root=seed,
        operation="install",
        artifact="runtime-base",
        output=seed_output / "install.json",
    )
    verify = invoke_engine_process(
        runner=local_runner,
        engine=engine,
        contract=contract,
        root=seed,
        operation="verify",
        output=seed_output / "verify.json",
    )
    seed_registry = registry(seed)
    seed_summary = {
        "schema_version": 1,
        "install": install,
        "verify": verify,
        "registry": seed_registry,
        "remaining_registered_paths": remaining_registered_paths(seed, rows),
        "transactions": transactions(seed),
    }
    seed_summary["pass"] = (
        install.get("returncode") == 0
        and install.get("result", {}).get("action_counts") == {"create": 714}
        and install.get("result", {}).get("mutation_count") == 715
        and verify.get("returncode") == 0
        and verify.get("result", {}).get("bad_paths") == []
        and seed_registry["artifact_count"] == 1
        and seed_registry["owned_path_count"] == 714
        and len(seed_summary["remaining_registered_paths"]) == 714
        and seed_summary["transactions"] == []
    )
    write_json(seed_output / "summary.json", seed_summary)

    happy_reinstall: dict[str, dict[str, Any]] = {}
    happy_uninstall: dict[str, dict[str, Any]] = {}
    crash_rows: dict[str, dict[str, Any]] = {}
    clone_records: dict[str, dict[str, bool]] = {}

    for subject in SUBJECTS:
        name = "reinstall-" + subject
        row, clone = run_happy_reinstall(
            subject=subject,
            seed=seed,
            rows=rows,
            regular=regular,
            symlink=symlink,
            runner=local_runner,
            engine=engine,
            contract=contract,
            root=work / "happy" / name,
            output=output / "happy" / name,
        )
        happy_reinstall[subject] = row
        clone_records[name] = clone

    for subject in SUBJECTS:
        name = "uninstall-" + subject
        row, clone = run_happy_uninstall(
            subject=subject,
            seed=seed,
            rows=rows,
            regular=regular,
            symlink=symlink,
            runner=local_runner,
            engine=engine,
            contract=contract,
            root=work / "happy" / name,
            output=output / "happy" / name,
        )
        happy_uninstall[subject] = row
        clone_records[name] = clone

    for subject in SUBJECTS:
        for boundary in BOUNDARIES:
            name = subject + "-" + boundary
            row, clone = run_crash_scenario(
                subject=subject,
                boundary=boundary,
                seed=seed,
                rows=rows,
                regular=regular,
                symlink=symlink,
                all_registered_leaves=all_registered_leaves,
                happy_uninstall=happy_uninstall[subject],
                runner=local_runner,
                engine=engine,
                contract=contract,
                root=work / "crash" / name,
                output=output / "crash" / name,
            )
            crash_rows[name] = row
            clone_records[name] = clone

    clone_summary = {
        "schema_version": 1,
        "roots": clone_records,
        "pass": len(clone_records) == 20 and all(all(values.values()) for values in clone_records.values()),
    }
    write_json(output / "clone-separation.json", clone_summary)

    happy_rows = list(happy_reinstall.values()) + list(happy_uninstall.values())
    crash_values = list(crash_rows.values())
    prepared = [row for row in crash_values if row["boundary"] == "prepared"]
    applying = [row for row in crash_values if row["boundary"] == "applying-late"]
    committed = [row for row in crash_values if row["boundary"] == "committed"]
    precommit = prepared + applying

    checks = {
        "accepted_authority_exact": authority["pass"],
        "seed_pass": seed_summary["pass"],
        "clone_roots_20": clone_summary["pass"],
        "happy_scenario_count_8": len(happy_rows) == 8,
        "happy_all_pass": all(row.get("pass") is True for row in happy_rows),
        "reinstall_count_4": len(happy_reinstall) == 4,
        "uninstall_count_4": len(happy_uninstall) == 4,
        "reinstall_owned_repair_2": all(happy_reinstall[name].get("classification") == "ENFORCED_REPAIR" for name in SUBJECTS[:2]),
        "reinstall_unowned_noop_2": all(happy_reinstall[name].get("classification") == "PRESERVED_NOOP" for name in SUBJECTS[2:]),
        "uninstall_owned_preserved_2": all(happy_uninstall[name].get("classification") == "PRESERVED_AND_DEREGISTERED" for name in SUBJECTS[:2]),
        "uninstall_unowned_preserved_2": all(happy_uninstall[name].get("classification") == "UNOWNED_PRESERVED" for name in SUBJECTS[2:]),
        "happy_registry_transitions": all(row.get("registry_after", {}).get("artifact_count") == 0 and row.get("registry_after", {}).get("owned_path_count") == 0 for row in happy_uninstall.values()),
        "happy_preserved_exact": all(row.get("preserved_rows") == row.get("expected_preserved_rows") for row in happy_uninstall.values()),
        "happy_remaining_exact": all(row.get("remaining_registered_paths") == row.get("expected_preserved_rows") for row in happy_uninstall.values()),
        "happy_transactions_empty": all(row.get("transactions_after") == [] for row in happy_rows),
        "crash_scenario_count_12": len(crash_values) == 12,
        "crash_all_pass": all(row.get("pass") is True for row in crash_values),
        "prepared_count_4": len(prepared) == 4,
        "applying_count_4": len(applying) == 4,
        "committed_count_4": len(committed) == 4,
        "prepared_rc_90": all(row.get("crash", {}).get("returncode") == 90 for row in prepared),
        "applying_rc_93": all(row.get("crash", {}).get("returncode") == 93 for row in applying),
        "committed_rc_92": all(row.get("crash", {}).get("returncode") == 92 for row in committed),
        "precommit_rollback_8": all(row.get("recover_1", {}).get("result", {}).get("actions", [{}])[0].get("action") == "ROLLED_BACK" for row in precommit),
        "committed_finalize_4": all(row.get("recover_1", {}).get("result", {}).get("actions", [{}])[0].get("action") == "FINALIZED_COMMIT" for row in committed),
        "second_recovery_idempotent_12": all(row.get("checks", {}).get("recovery") is True for row in crash_values),
        "verify_expectations_12": all(row.get("checks", {}).get("verify") is True for row in crash_values),
        "late_registry_intent_exact_4": all(row.get("checks", {}).get("applying_shape") is True for row in applying),
        "claim_boundary_product_acceptance": True,
    }
    if len(checks) != 29:
        raise RuntimeError(f"unexpected scenario check count: {len(checks)}")
    failed = sorted(name for name, passed in checks.items() if not passed)
    summary = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": 29,
        "checks": checks,
        "failed_checks": failed,
        "happy_reinstall": {name: row["classification"] for name, row in happy_reinstall.items()},
        "happy_uninstall": {name: row["classification"] for name, row in happy_uninstall.items()},
        "crash_scenarios": sorted(crash_rows),
        "claim_boundary": {
            "proved": "The frozen preserve-and-report contract passed happy reinstall/uninstall and twelve crash-recovery scenarios for runtime-base.",
            "not_proved": "Addon lifecycle, final multi-artifact uninstall, upgrade, and downgrade remain separate gates.",
        },
    }
    write_json(output / "scenario-summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("GATE3B_PRESERVATION_ACCEPTANCE=" + ("PASS" if summary["pass"] else "FAIL"))
    return 103 if args.require_pass and not summary["pass"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
