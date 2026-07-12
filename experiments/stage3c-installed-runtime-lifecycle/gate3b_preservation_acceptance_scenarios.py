#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from gate3b0_preservation_scenarios import run_reinstall, run_uninstall
from gate3b0_preservation_support import clone_seed, read_json, registry, transactions, write_json
from gate3b_preservation_acceptance_support import (
    BOUNDARIES,
    SUBJECTS,
    expected_preserved_paths,
    expected_remaining_leaves,
    expected_verify_bad_paths,
    invoke_engine_process,
    one_transaction,
    prepare_subject,
    recovery_action,
    recovery_state,
    registry_intent_ordinal,
    remaining_registered_paths,
    snapshot_identity,
)


def run_happy_reinstall(
    *,
    subject: str,
    seed: Path,
    rows: list[dict[str, Any]],
    regular: dict[str, Any],
    symlink: dict[str, Any],
    runner: Path,
    engine: Path,
    contract: Path,
    root: Path,
    output: Path,
) -> tuple[dict[str, Any], dict[str, bool]]:
    clone = clone_seed(seed, root, [regular["path"], symlink["path"]])
    candidate = regular if subject == "owned-regular" else symlink if subject == "owned-symlink" else None
    name = "reinstall-" + subject
    row = run_reinstall(
        name=name,
        root=root,
        rows=rows,
        candidate=candidate,
        runner=runner,
        engine=engine,
        contract=contract,
        out=output,
    )
    row["subject_kind"] = subject
    row["clone_separation"] = clone
    row["pass"] = row.get("pass") is True and all(clone.values())
    write_json(output / "scenario.json", row)
    return row, clone


def run_happy_uninstall(
    *,
    subject: str,
    seed: Path,
    rows: list[dict[str, Any]],
    regular: dict[str, Any],
    symlink: dict[str, Any],
    runner: Path,
    engine: Path,
    contract: Path,
    root: Path,
    output: Path,
) -> tuple[dict[str, Any], dict[str, bool]]:
    clone = clone_seed(seed, root, [regular["path"], symlink["path"]])
    candidate = regular if subject == "owned-regular" else symlink if subject == "owned-symlink" else None
    name = "uninstall-" + subject
    row = run_uninstall(
        name=name,
        root=root,
        rows=rows,
        candidate=candidate,
        runner=runner,
        engine=engine,
        contract=contract,
        out=output,
    )
    expected_preserved = expected_preserved_paths(row["subject"], candidate, rows)
    remaining_paths = remaining_registered_paths(root, rows)
    ordinal = registry_intent_ordinal(row, rows)
    row.update(
        subject_kind=subject,
        clone_separation=clone,
        expected_preserved_rows=expected_preserved,
        remaining_registered_paths=remaining_paths,
        registry_intent_ordinal=ordinal,
    )
    row["pass"] = (
        row.get("pass") is True
        and all(clone.values())
        and row.get("preserved_rows") == expected_preserved
        and remaining_paths == expected_preserved
        and ordinal > row.get("uninstall", {}).get("result", {}).get("mutation_count", 0)
    )
    write_json(output / "scenario.json", row)
    return row, clone


def run_crash_scenario(
    *,
    subject: str,
    boundary: str,
    seed: Path,
    rows: list[dict[str, Any]],
    regular: dict[str, Any],
    symlink: dict[str, Any],
    all_registered_leaves: list[str],
    happy_uninstall: dict[str, Any],
    runner: Path,
    engine: Path,
    contract: Path,
    root: Path,
    output: Path,
) -> tuple[dict[str, Any], dict[str, bool]]:
    if boundary not in BOUNDARIES:
        raise ValueError(boundary)
    clone = clone_seed(seed, root, [regular["path"], symlink["path"]])
    subject_path, subject_before, candidate = prepare_subject(root, subject, regular, symlink)
    registry_before = registry(root)
    pre_state = recovery_state(root=root, rows=rows, subject_path=subject_path)
    expected_preserved = expected_preserved_paths(subject_path, candidate, rows)
    expected_ordinal = happy_uninstall["registry_intent_ordinal"]

    if boundary == "prepared":
        crash_flag, crash_value, expected_rc, expected_journal = "--crash-after-prepared", None, 90, "PREPARED"
    elif boundary == "applying-late":
        crash_flag, crash_value, expected_rc, expected_journal = "--crash-after-intents", expected_ordinal, 93, "APPLYING"
    else:
        crash_flag, crash_value, expected_rc, expected_journal = "--crash-after-commit", None, 92, "COMMITTED"

    crash = invoke_engine_process(
        runner=runner,
        engine=engine,
        contract=contract,
        root=root,
        operation="uninstall",
        artifact="runtime-base",
        output=output / "crash-uninstall.json",
        crash_flag=crash_flag,
        crash_value=crash_value,
    )
    transaction, journal_before = one_transaction(root)
    state_before_recovery = recovery_state(root=root, rows=rows, subject_path=subject_path)

    recover1 = invoke_engine_process(
        runner=runner,
        engine=engine,
        contract=contract,
        root=root,
        operation="recover",
        output=output / "recover-1.json",
    )
    state_after_recovery = recovery_state(root=root, rows=rows, subject_path=subject_path)
    verify1 = invoke_engine_process(
        runner=runner,
        engine=engine,
        contract=contract,
        root=root,
        operation="verify",
        output=output / "verify-1.json",
    )
    journal_after_recovery = None
    journal_path = transaction / "journal.json"
    if journal_path.is_file():
        journal_after_recovery = read_json(journal_path)

    recover2 = invoke_engine_process(
        runner=runner,
        engine=engine,
        contract=contract,
        root=root,
        operation="recover",
        output=output / "recover-2.json",
    )
    state_after_second = recovery_state(root=root, rows=rows, subject_path=subject_path)
    verify2 = invoke_engine_process(
        runner=runner,
        engine=engine,
        contract=contract,
        root=root,
        operation="verify",
        output=output / "verify-2.json",
    )

    committed = boundary == "committed"
    expected_bad = expected_verify_bad_paths(subject, subject_path, committed)
    expected_verify_rc = 44 if expected_bad else 0
    expected_leaves = expected_remaining_leaves(subject, subject_path, all_registered_leaves, committed)
    action1_count, action1 = recovery_action(recover1.get("result"))
    action2_count, action2 = recovery_action(recover2.get("result"))
    expected_remaining_paths = expected_preserved if committed else sorted(row["path"] for row in rows)

    journal_mutations = journal_before.get("mutations", [])
    applying_shape = (
        boundary != "applying-late"
        or (
            sorted(set(journal_before.get("preserved", []))) == expected_preserved
            and len(journal_mutations) == happy_uninstall["uninstall"]["result"]["mutation_count"]
            and journal_mutations[-1].get("kind") == "registry"
            and journal_mutations[-1].get("status") == "INTENT"
            and all(item.get("status") == "APPLIED" for item in journal_mutations[:-1])
        )
    )
    prepared_shape = boundary != "prepared" or (
        journal_before.get("mutations") == [] and journal_before.get("preserved") == []
    )
    committed_shape = boundary != "committed" or (
        sorted(set(journal_before.get("preserved", []))) == expected_preserved
        and state_before_recovery["registry"]["artifact_count"] == 0
        and state_before_recovery["registry"]["owned_path_count"] == 0
        and state_before_recovery["remaining_registered_paths"] == expected_preserved
        and snapshot_identity(state_before_recovery["subject"]) == snapshot_identity(subject_before)
    )

    if committed:
        recovery_pass = (
            action1_count == 1
            and action1 == "FINALIZED_COMMIT"
            and state_after_recovery["registry"]["artifact_count"] == 0
            and state_after_recovery["registry"]["owned_path_count"] == 0
            and state_after_recovery["remaining_registered_paths"] == expected_preserved
            and state_after_recovery["remaining_registered_leaves"] == expected_leaves
            and snapshot_identity(state_after_recovery["subject"]) == snapshot_identity(subject_before)
            and state_after_recovery["transactions"] == []
            and recover2.get("result", {}).get("transaction_count") == 0
            and state_after_second == state_after_recovery
        )
    else:
        recovery_pass = (
            action1_count == 1
            and action1 == "ROLLED_BACK"
            and state_after_recovery["registry"]["sha256"] == registry_before["sha256"]
            and state_after_recovery["registry"]["artifact_count"] == 1
            and state_after_recovery["registry"]["owned_path_count"] == 714
            and state_after_recovery["owned_digest"] == pre_state["owned_digest"]
            and state_after_recovery["remaining_registered_leaves"] == all_registered_leaves
            and state_after_recovery["remaining_registered_paths"] == sorted(row["path"] for row in rows)
            and snapshot_identity(state_after_recovery["subject"]) == snapshot_identity(subject_before)
            and len(state_after_recovery["transactions"]) == 1
            and state_after_recovery["transactions"][0]["journal"].get("state") == "ROLLED_BACK"
            and journal_after_recovery is not None
            and journal_after_recovery.get("state") == "ROLLED_BACK"
            and action2_count == 1
            and action2 == "NOOP_ROLLED_BACK"
            and state_after_second == state_after_recovery
        )

    verify_pass = (
        verify1.get("returncode") == expected_verify_rc
        and verify1.get("result", {}).get("bad_paths") == expected_bad
        and verify2.get("returncode") == expected_verify_rc
        and verify2.get("result", {}).get("bad_paths") == expected_bad
    )
    result = {
        "schema_version": 1,
        "scenario": f"{subject}-{boundary}",
        "subject_kind": subject,
        "boundary": boundary,
        "subject": subject_path,
        "candidate": candidate,
        "subject_before_crash": subject_before,
        "expected_preserved_rows": expected_preserved,
        "expected_registry_intent_ordinal": expected_ordinal,
        "clone_separation": clone,
        "registry_before": registry_before,
        "pre_crash_state": pre_state,
        "crash": crash,
        "journal_before_recovery": journal_before,
        "state_before_recovery": state_before_recovery,
        "recover_1": recover1,
        "journal_after_recovery": journal_after_recovery,
        "state_after_recovery": state_after_recovery,
        "verify_1": verify1,
        "recover_2": recover2,
        "state_after_second_recovery": state_after_second,
        "verify_2": verify2,
        "expected": {
            "crash_returncode": expected_rc,
            "journal_state": expected_journal,
            "verify_bad_paths": expected_bad,
            "verify_returncode": expected_verify_rc,
            "remaining_registered_leaves": expected_leaves,
            "remaining_registered_paths": expected_remaining_paths,
        },
        "checks": {
            "clone_separation": all(clone.values()),
            "crash_returncode": crash.get("returncode") == expected_rc,
            "crash_output_absent": crash.get("output_exists") is False,
            "journal_state": journal_before.get("state") == expected_journal,
            "prepared_shape": prepared_shape,
            "applying_shape": applying_shape,
            "committed_shape": committed_shape,
            "recovery": recovery_pass,
            "verify": verify_pass,
        },
    }
    result["pass"] = all(result["checks"].values())
    write_json(output / "scenario.json", result)
    return result, clone
