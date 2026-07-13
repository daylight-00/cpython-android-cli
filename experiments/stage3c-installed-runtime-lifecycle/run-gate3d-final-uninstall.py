#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from gate3c_addon_lifecycle_support import (  # noqa: E402
    EXPECTED_ARTIFACTS,
    cjson,
    clone_seed,
    invoke_engine,
    product_snapshot,
    read_json,
    rows_from_manifest,
    start_lock_holder,
    state_check,
    stop_lock_holder,
    transaction_inventory,
    write_json,
)
from gate3d_final_uninstall_support import (  # noqa: E402
    RUNTIME_REGULAR,
    RUNTIME_SYMLINK,
    expected_residual_paths,
    final_state_audit,
    kind,
    path_snapshot,
    prepare_subject,
    registry_intent_ordinal,
    snapshot_identity,
    verify_authorities,
)

STATE_INSTALL_ORDER = {
    "runtime": ("runtime-base",),
    "runtime-development": ("runtime-base", "development-addon"),
    "runtime-test": ("runtime-base", "test-addon"),
    "composed": ("runtime-base", "development-addon", "test-addon"),
}
EXPECTED_GROUPS = {"preflight": 6, "teardown": 8, "residual": 10, "recovery": 12, "locking": 2, "audit": 6}
CRASH_NAME = {"prepared": "PREPARED", "applying-late": "LATE_APPLYING", "committed": "COMMITTED"}
CRASH_RC = {"prepared": 90, "applying-late": 93, "committed": 92}


def result_pass(process: dict[str, Any]) -> bool:
    return process.get("returncode") == 0 and process.get("result", {}).get("pass") is True


def error_contains(process: dict[str, Any], text: str) -> bool:
    return text in str(process.get("result", {}).get("error", ""))


def canonical(path: Path) -> bool:
    try:
        return path.read_bytes() == cjson(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return False


def install_seed(
    *,
    name: str,
    order: tuple[str, ...],
    root: Path,
    output: Path,
    runner: Path,
    engine: Path,
    contract: Path,
) -> dict[str, Any]:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    operations = []
    for artifact in order:
        operations.append(
            invoke_engine(
                runner=runner,
                engine=engine,
                contract=contract,
                root=root,
                operation="install",
                artifact=artifact,
                output=output / f"install-{artifact}.json",
            )
        )
    verify = invoke_engine(runner=runner, engine=engine, contract=contract, root=root, operation="verify", output=output / "verify.json")
    shape = state_check(root, name)
    value = {
        "schema_version": 1,
        "seed": name,
        "order": list(order),
        "operations": operations,
        "verify": verify,
        "shape": shape,
        "transactions": transaction_inventory(root),
    }
    value["pass"] = all(result_pass(item) for item in operations) and result_pass(verify) and shape["pass"] and value["transactions"] == []
    write_json(output / "summary.json", value)
    return value


def finish(output: Path, value: dict[str, Any]) -> dict[str, Any]:
    value.setdefault("schema_version", 1)
    value["pass"] = all(value.get("checks", {}).values())
    write_json(output / "scenario.json", value)
    return value


def uninstall(
    *, root: Path, output: Path, runner: Path, engine: Path, contract: Path, artifact: str, name: str
) -> dict[str, Any]:
    return invoke_engine(
        runner=runner,
        engine=engine,
        contract=contract,
        root=root,
        operation="uninstall",
        artifact=artifact,
        output=output / f"{name}.json",
    )


def verify_state(
    *, root: Path, output: Path, runner: Path, engine: Path, contract: Path, state: str, name: str = "verify"
) -> tuple[dict[str, Any], dict[str, Any]]:
    process = invoke_engine(runner=runner, engine=engine, contract=contract, root=root, operation="verify", output=output / f"{name}.json")
    return process, state_check(root, state)


def run_rejection(
    *, scenario: dict[str, Any], root: Path, output: Path, runner: Path, engine: Path, contract: Path, expected_error: str
) -> dict[str, Any]:
    before = product_snapshot(root)
    process = uninstall(root=root, output=output, runner=runner, engine=engine, contract=contract, artifact="runtime-base", name="reject-runtime")
    after = product_snapshot(root)
    return finish(
        output,
        {
            "id": scenario["id"],
            "group": scenario["group"],
            "matrix": scenario,
            "before": before,
            "operation": process,
            "after": after,
            "checks": {
                "returncode_44": process["returncode"] == 44,
                "error": error_contains(process, expected_error),
                "product_unchanged": before["identity_sha256"] == after["identity_sha256"],
                "zero_transactions": after["transactions"] == [],
            },
        },
    )


def run_success_sequence(
    *,
    scenario: dict[str, Any],
    root: Path,
    output: Path,
    runner: Path,
    engine: Path,
    contract: Path,
    artifacts: list[str],
    runtime_rows: list[dict[str, Any]],
    final_class: str = "exact-owned-teardown",
    subject_paths: list[str] | None = None,
    subject_snapshots: list[dict[str, Any]] | None = None,
    guard_after: int | None = None,
    repeat_runtime: bool = False,
) -> dict[str, Any]:
    before = product_snapshot(root)
    operations: list[dict[str, Any]] = []
    guard = None
    guard_before = guard_after_state = None
    for index, artifact in enumerate(artifacts):
        operations.append(uninstall(root=root, output=output, runner=runner, engine=engine, contract=contract, artifact=artifact, name=f"step-{index + 1}-{artifact}"))
        if guard_after is not None and index + 1 == guard_after:
            guard_before = product_snapshot(root)
            guard = uninstall(root=root, output=output, runner=runner, engine=engine, contract=contract, artifact="runtime-base", name="guard-runtime")
            guard_after_state = product_snapshot(root)
    repeated = None
    if repeat_runtime:
        repeated = uninstall(root=root, output=output, runner=runner, engine=engine, contract=contract, artifact="runtime-base", name="repeat-runtime")
    verify, shape = verify_state(root=root, output=output, runner=runner, engine=engine, contract=contract, state="empty", name="verify-final")
    audit = final_state_audit(
        root=root,
        runtime_rows=runtime_rows,
        final_class=final_class,
        subject_paths=subject_paths or [],
        subject_snapshots=subject_snapshots or [],
    )
    after = product_snapshot(root)
    checks = {
        "operations_pass": all(result_pass(item) for item in operations),
        "final_runtime_operation_present": bool(operations) and operations[-1].get("result", {}).get("artifact") == "runtime-base",
        "verify_empty": result_pass(verify) and shape["pass"],
        "final_state": audit["pass"],
        "zero_transactions": after["transactions"] == [],
    }
    if guard is not None:
        checks.update(
            guard_rc44=guard["returncode"] == 44,
            guard_error=error_contains(guard, "dependent addons installed"),
            guard_zero_mutation=guard_before is not None and guard_after_state is not None and guard_before["identity_sha256"] == guard_after_state["identity_sha256"],
        )
    if repeated is not None:
        checks.update(repeat_rc44=repeated["returncode"] == 44, repeat_error=error_contains(repeated, "artifact not installed"))
    value = {
        "id": scenario["id"],
        "group": scenario["group"],
        "matrix": scenario,
        "before": before,
        "operations": operations,
        "guard": guard,
        "guard_before": guard_before,
        "guard_after": guard_after_state,
        "repeat": repeated,
        "verify": verify,
        "shape": shape,
        "final_audit": audit,
        "after": after,
        "checks": checks,
    }
    return finish(output, value)


def run_recovery(
    *,
    scenario: dict[str, Any],
    root: Path,
    output: Path,
    runner: Path,
    engine: Path,
    contract: Path,
    runtime_rows: list[dict[str, Any]],
    subject_paths: list[str],
    subject_snapshots: list[dict[str, Any]],
    intent_ordinal: int,
) -> dict[str, Any]:
    boundary = scenario["crash_boundary"]
    before = product_snapshot(root)
    crash = invoke_engine(
        runner=runner,
        engine=engine,
        contract=contract,
        root=root,
        operation="uninstall",
        artifact="runtime-base",
        output=output / "crash-runtime.json",
        crash_boundary=CRASH_NAME[boundary],
        intent_ordinal=intent_ordinal,
    )
    transactions_after_crash = transaction_inventory(root)
    recover1 = invoke_engine(runner=runner, engine=engine, contract=contract, root=root, operation="recover", output=output / "recover-1.json")
    after_recover1 = product_snapshot(root)
    verify1 = invoke_engine(runner=runner, engine=engine, contract=contract, root=root, operation="verify", output=output / "verify-1.json")
    recover2 = invoke_engine(runner=runner, engine=engine, contract=contract, root=root, operation="recover", output=output / "recover-2.json")
    after_recover2 = product_snapshot(root)
    verify2 = invoke_engine(runner=runner, engine=engine, contract=contract, root=root, operation="verify", output=output / "verify-2.json")
    actions1 = recover1.get("result", {}).get("actions", [])
    actions2 = recover2.get("result", {}).get("actions", [])
    committed = boundary == "committed"
    expected_action = "FINALIZED_COMMIT" if committed else "ROLLED_BACK"
    expected_bad = [path for path in subject_paths if path in {RUNTIME_REGULAR, RUNTIME_SYMLINK}] if not committed else []
    if committed:
        final_audit = final_state_audit(
            root=root,
            runtime_rows=runtime_rows,
            final_class=scenario["committed_final_state_class"],
            subject_paths=subject_paths,
            subject_snapshots=subject_snapshots,
        )
        topology = (
            after_recover1["transactions"] == []
            and after_recover2 == after_recover1
            and actions2 == []
            and result_pass(verify1)
            and result_pass(verify2)
            and final_audit["pass"]
        )
    else:
        final_audit = None
        topology = (
            before["prefix_digest"] == after_recover1["prefix_digest"]
            and before["registry"]["sha256"] == after_recover1["registry"]["sha256"]
            and len(after_recover1["transactions"]) == 1
            and after_recover1["transactions"][0].get("journal", {}).get("state") == "ROLLED_BACK"
            and after_recover2 == after_recover1
            and len(actions2) == 1
            and actions2[0].get("action") == "NOOP_ROLLED_BACK"
            and verify1["returncode"] == (44 if expected_bad else 0)
            and verify1.get("result", {}).get("bad_paths") == expected_bad
            and verify2["returncode"] == (44 if expected_bad else 0)
            and verify2.get("result", {}).get("bad_paths") == expected_bad
        )
    checks = {
        "crash_returncode": crash["returncode"] == CRASH_RC[boundary],
        "one_transaction_after_crash": len(transactions_after_crash) == 1,
        "recover_1": result_pass(recover1),
        "recover_1_action": len(actions1) == 1 and actions1[0].get("action") == expected_action,
        "recover_2": result_pass(recover2),
        "topology": topology,
    }
    return finish(
        output,
        {
            "id": scenario["id"],
            "group": scenario["group"],
            "matrix": scenario,
            "subject_paths": subject_paths,
            "subject_snapshots": subject_snapshots,
            "registry_intent_ordinal": intent_ordinal,
            "before": before,
            "crash": crash,
            "transactions_after_crash": transactions_after_crash,
            "recover_1": recover1,
            "after_recover_1": after_recover1,
            "verify_1": verify1,
            "recover_2": recover2,
            "after_recover_2": after_recover2,
            "verify_2": verify2,
            "final_audit": final_audit,
            "checks": checks,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in (
        "gate3b-archive",
        "gate3b-results",
        "gate3c-archive",
        "gate3c-results",
        "contract-results",
        "matrix",
        "engine",
        "operations",
        "local-script-runner",
        "work-root",
        "output-dir",
    ):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--resume", action="store_true", help="development-only resume of an interrupted local run")
    args = parser.parse_args()

    gate3b_archive = args.gate3b_archive.resolve()
    gate3b = args.gate3b_results.resolve()
    gate3c_archive = args.gate3c_archive.resolve()
    gate3c = args.gate3c_results.resolve()
    contract = args.contract_results.resolve()
    matrix_path = args.matrix.resolve()
    engine = args.engine.resolve()
    operations = args.operations.resolve()
    local_runner = args.local_script_runner.resolve()
    work = args.work_root.resolve()
    output = args.output_dir.resolve()
    if not args.resume:
        shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(output, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    (output / "input").mkdir(exist_ok=True)

    authority = verify_authorities(
        gate3b_archive=gate3b_archive,
        gate3b_results=gate3b,
        gate3c_archive=gate3c_archive,
        gate3c_results=gate3c,
        contract=contract,
        matrix=matrix_path,
        engine=engine,
        operations=operations,
        output=output / "accepted-authority.json",
    )
    shutil.copy2(matrix_path, output / "input/gate3d-final-uninstall-matrix.json")
    for source, name in (
        (gate3b / "result-index.json", "gate3b-result-index.json"),
        (gate3b / "verification.json", "gate3b-verification.json"),
        (gate3b / "scenario-summary.json", "gate3b-scenario-summary.json"),
        (gate3c / "result-index.json", "gate3c-result-index.json"),
        (gate3c / "result-tree-safety.json", "gate3c-result-tree-safety.json"),
        (gate3c / "verification.json", "gate3c-verification.json"),
        (gate3c / "scenario-summary.json", "gate3c-scenario-summary.json"),
        (gate3c / "workflow-status.json", "gate3c-workflow-status.json"),
        (gate3c / "termux-wrapper-status.json", "gate3c-wrapper-status.json"),
    ):
        shutil.copy2(source, output / "input" / name)
    shutil.copytree(contract, output / "input/contract", symlinks=True, copy_function=shutil.copy2, dirs_exist_ok=True)

    matrix = read_json(matrix_path)
    scenario_by_id = {row["id"]: row for row in matrix["scenarios"]}
    manifest_dir = contract / "input/phase3/input/manifest-schema/manifests"
    artifact_rows = {
        artifact: rows_from_manifest(read_json(manifest_dir / f"{artifact}.manifest.json"))
        for artifact in EXPECTED_ARTIFACTS
    }
    runtime_rows = artifact_rows["runtime-base"]
    probes = [RUNTIME_REGULAR, RUNTIME_SYMLINK, "include/python3.14/Python.h", "lib/python3.14/test/support/__init__.py"]

    seed_root = work / "seeds"
    seed_output = output / "seeds"
    seeds: dict[str, Path] = {"empty": seed_root / "empty"}
    seeds["empty"].mkdir(parents=True, exist_ok=True)
    seed_summaries: dict[str, dict[str, Any]] = {}
    for name, order in STATE_INSTALL_ORDER.items():
        seeds[name] = seed_root / name
        existing_seed = seed_output / name / "summary.json"
        if args.resume and existing_seed.is_file() and read_json(existing_seed).get("pass") is True and seeds[name].is_dir():
            seed_summaries[name] = read_json(existing_seed)
            continue
        seed_summaries[name] = install_seed(
            name=name,
            order=order,
            root=seeds[name],
            output=seed_output / name,
            runner=local_runner,
            engine=engine,
            contract=contract,
        )

    scenario_results: dict[str, dict[str, Any]] = {}
    clone_results: dict[str, dict[str, bool]] = {}

    def resume_existing(sid: str) -> bool:
        path = output / "scenarios" / sid / "scenario.json"
        clone_path = output / "scenarios" / sid / "clone-separation.json"
        if args.resume and path.is_file() and read_json(path).get("pass") is True:
            scenario_results[sid] = read_json(path)
            clone_results[sid] = read_json(clone_path) if clone_path.is_file() else {"resumed": True}
            return True
        return False

    def prepare(sid: str, seed_name: str) -> tuple[dict[str, Any], Path, Path]:
        scenario = scenario_by_id[sid]
        root = work / "scenarios" / sid
        out = output / "scenarios" / sid
        out.mkdir(parents=True, exist_ok=True)
        if seed_name == "empty":
            root.mkdir(parents=True, exist_ok=True)
            clone = {"root_inode_separate": True, "empty_seed": True}
        else:
            clone = clone_seed(seeds[seed_name], root, probes)
        write_json(out / "clone-separation.json", clone)
        clone_results[sid] = clone
        return scenario, root, out

    # Preflight rejection boundaries.
    for sid, seed in (("P01", "composed"), ("P02", "runtime-development"), ("P03", "runtime-test")):
        if resume_existing(sid):
            continue
        scenario, root, out = prepare(sid, seed)
        scenario_results[sid] = run_rejection(scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract, expected_error="dependent addons installed")

    for sid, first, state in (("P04", "test-addon", "runtime-development"), ("P05", "development-addon", "runtime-test")):
        if resume_existing(sid):
            continue
        scenario, root, out = prepare(sid, "composed")
        first_process = uninstall(root=root, output=out, runner=local_runner, engine=engine, contract=contract, artifact=first, name=f"first-{first}")
        before_reject = product_snapshot(root)
        reject = uninstall(root=root, output=out, runner=local_runner, engine=engine, contract=contract, artifact="runtime-base", name="reject-runtime")
        after_reject = product_snapshot(root)
        verify, shape = verify_state(root=root, output=out, runner=local_runner, engine=engine, contract=contract, state=state, name="verify-after-reject")
        scenario_results[sid] = finish(out, {
            "id": sid, "group": "preflight", "matrix": scenario, "first_uninstall": first_process,
            "before_reject": before_reject, "operation": reject, "after_reject": after_reject, "verify": verify, "shape": shape,
            "checks": {
                "first_uninstall": result_pass(first_process), "reject_rc44": reject["returncode"] == 44,
                "reject_error": error_contains(reject, "dependent addons installed"),
                "zero_reject_mutation": before_reject["identity_sha256"] == after_reject["identity_sha256"],
                "state": result_pass(verify) and shape["pass"], "zero_transactions": after_reject["transactions"] == [],
            },
        })

    if not resume_existing("P06"):
        scenario, root, out = prepare("P06", "empty")
        scenario_results["P06"] = run_rejection(scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract, expected_error="artifact not installed")

    # Valid/guarded exact teardown.
    teardown_specs = {
        "T01": ("composed", ["test-addon", "development-addon", "runtime-base"], None, False),
        "T02": ("composed", ["development-addon", "test-addon", "runtime-base"], None, False),
        "T03": ("runtime-development", ["development-addon", "runtime-base"], None, False),
        "T04": ("runtime-test", ["test-addon", "runtime-base"], None, False),
        "T05": ("runtime", ["runtime-base"], None, False),
        "T06": ("composed", ["test-addon", "development-addon", "runtime-base"], 1, False),
        "T07": ("composed", ["development-addon", "test-addon", "runtime-base"], 1, False),
        "T08": ("runtime", ["runtime-base"], None, True),
    }
    for sid, (seed, artifacts, guard_after, repeat) in teardown_specs.items():
        if resume_existing(sid):
            continue
        scenario, root, out = prepare(sid, seed)
        scenario_results[sid] = run_success_sequence(
            scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract,
            artifacts=artifacts, runtime_rows=runtime_rows, guard_after=guard_after, repeat_runtime=repeat,
        )

    # Residual ownership scenarios.
    residual_specs = {
        "S01": ("runtime", [], "modified-owned-regular", "modified-owned-residual"),
        "S02": ("runtime", [], "modified-owned-symlink", "modified-owned-residual"),
        "S03": ("composed", ["test-addon", "development-addon"], "modified-owned-regular", "modified-owned-residual"),
        "S04": ("composed", ["development-addon", "test-addon"], "modified-owned-symlink", "modified-owned-residual"),
        "S05": ("runtime", [], "unowned-file", "unowned-sentinel-residual"),
        "S06": ("runtime", [], "unowned-directory", "unowned-sentinel-residual"),
        "S07": ("runtime", [], "unowned-descendant-under-owned-directory", "unowned-sentinel-residual"),
        "S08": ("composed", ["test-addon", "development-addon"], "unowned-file-under-shared-namespace", "unowned-sentinel-residual"),
        "S09": ("runtime", [], "mixed", "mixed-approved-residual"),
    }
    for sid, (seed, addon_order, subject, final_class) in residual_specs.items():
        if resume_existing(sid):
            continue
        scenario, root, out = prepare(sid, seed)
        subject_paths, mutations, subject_snapshots = prepare_subject(root, subject, runtime_rows)
        scenario_results[sid] = run_success_sequence(
            scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract,
            artifacts=[*addon_order, "runtime-base"], runtime_rows=runtime_rows, final_class=final_class,
            subject_paths=subject_paths, subject_snapshots=subject_snapshots,
        )
        scenario_results[sid]["subject_kind"] = subject
        scenario_results[sid]["mutations"] = mutations
        write_json(out / "scenario.json", scenario_results[sid])

    if not resume_existing("S10"):
        scenario, root, out = prepare("S10", "runtime")
        subject_paths, mutations, subject_snapshots = prepare_subject(root, "modified-owned-regular", runtime_rows)
        final_uninstall = uninstall(root=root, output=out, runner=local_runner, engine=engine, contract=contract, artifact="runtime-base", name="uninstall-runtime")
        audit = final_state_audit(root=root, runtime_rows=runtime_rows, final_class="modified-owned-residual", subject_paths=subject_paths, subject_snapshots=subject_snapshots)
        before_reinstall = product_snapshot(root)
        reinstall = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="install", artifact="runtime-base", output=out / "reinstall-runtime.json")
        after_reinstall = product_snapshot(root)
        scenario_results["S10"] = finish(out, {
        "id": "S10", "group": "residual", "matrix": scenario, "subject_kind": "modified-owned-regular",
        "mutations": mutations, "final_uninstall": final_uninstall, "final_audit": audit,
        "before_reinstall": before_reinstall, "reinstall": reinstall, "after_reinstall": after_reinstall,
        "checks": {
            "uninstall": result_pass(final_uninstall), "final_state": audit["pass"],
            "reinstall_rc44": reinstall["returncode"] == 44, "collision": error_contains(reinstall, "unowned collision"),
            "zero_reinstall_mutation": before_reinstall["identity_sha256"] == after_reinstall["identity_sha256"],
        },
        })

    # Derive late-applying registry intent ordinals from successful target operations.
    calibrations = {
        "exact-owned": registry_intent_ordinal(scenario_results["T05"]["operations"][-1]["result"], runtime_rows),
        "modified-owned-regular": registry_intent_ordinal(scenario_results["S01"]["operations"][-1]["result"], runtime_rows),
        "modified-owned-symlink": registry_intent_ordinal(scenario_results["S02"]["operations"][-1]["result"], runtime_rows),
        "unowned-file": registry_intent_ordinal(scenario_results["S05"]["operations"][-1]["result"], runtime_rows),
    }
    write_json(output / "registry-intent-ordinals.json", calibrations)

    # Crash recovery over exact, modified and unowned final teardown.
    recovery_subjects = {
        "R01": "exact-owned", "R02": "exact-owned", "R03": "exact-owned",
        "R04": "modified-owned-regular", "R05": "modified-owned-regular", "R06": "modified-owned-regular",
        "R07": "modified-owned-symlink", "R08": "modified-owned-symlink", "R09": "modified-owned-symlink",
        "R10": "unowned-file", "R11": "unowned-file", "R12": "unowned-file",
    }
    for sid, subject in recovery_subjects.items():
        if resume_existing(sid):
            continue
        scenario, root, out = prepare(sid, "composed")
        setup = [
            uninstall(root=root, output=out, runner=local_runner, engine=engine, contract=contract, artifact="test-addon", name="setup-test-addon"),
            uninstall(root=root, output=out, runner=local_runner, engine=engine, contract=contract, artifact="development-addon", name="setup-development-addon"),
        ]
        subject_paths, mutations, subject_snapshots = prepare_subject(root, subject, runtime_rows)
        value = run_recovery(
            scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract,
            runtime_rows=runtime_rows, subject_paths=subject_paths, subject_snapshots=subject_snapshots,
            intent_ordinal=calibrations[subject],
        )
        value["setup"] = setup
        value["mutations"] = mutations
        value["checks"]["setup"] = all(result_pass(item) for item in setup) and state_check(root, "empty" if scenario["crash_boundary"] == "committed" else "runtime")["pass"]
        value["pass"] = all(value["checks"].values())
        write_json(out / "scenario.json", value)
        scenario_results[sid] = value

    # Lock exclusion.
    if not resume_existing("L01"):
        scenario, root, out = prepare("L01", "runtime")
        before = product_snapshot(root)
        ready = out / "holder.ready"
        holder = start_lock_holder(runner=local_runner, engine=engine, root=root, output=out / "holder.json", ready=ready)
        contender = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="uninstall", artifact="runtime-base", output=out / "contender.json", nonblocking=True)
        holder_rc = stop_lock_holder(holder)
        after = product_snapshot(root)
        scenario_results["L01"] = finish(out, {
            "id": "L01", "group": "locking", "matrix": scenario, "before": before, "contender": contender, "holder_returncode": holder_rc, "after": after,
            "checks": {"returncode_44": contender["returncode"] == 44, "lock_error": error_contains(contender, "installation lock busy"), "zero_mutation": before["identity_sha256"] == after["identity_sha256"], "state_runtime": state_check(root, "runtime")["pass"]},
        })

    if not resume_existing("L02"):
        scenario, root, out = prepare("L02", "runtime")
        before = product_snapshot(root)
        crash = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="uninstall", artifact="runtime-base", output=out / "crash-prepared.json", crash_boundary="PREPARED", intent_ordinal=calibrations["exact-owned"])
        before_contender = product_snapshot(root)
        ready = out / "holder.ready"
        holder = start_lock_holder(runner=local_runner, engine=engine, root=root, output=out / "holder.json", ready=ready)
        contender = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="recover", output=out / "contender-recover.json", nonblocking=True)
        holder_rc = stop_lock_holder(holder)
        after_contender = product_snapshot(root)
        cleanup = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="recover", output=out / "cleanup-recover.json")
        scenario_results["L02"] = finish(out, {
            "id": "L02", "group": "locking", "matrix": scenario, "before": before, "crash": crash,
            "before_contender": before_contender, "contender": contender, "holder_returncode": holder_rc,
            "after_contender": after_contender, "cleanup": cleanup,
            "checks": {
                "prepared_rc90": crash["returncode"] == 90, "one_transaction": len(before_contender["transactions"]) == 1,
                "returncode_44": contender["returncode"] == 44, "lock_error": error_contains(contender, "installation lock busy"),
                "zero_contender_mutation": before_contender["identity_sha256"] == after_contender["identity_sha256"],
                "cleanup": result_pass(cleanup), "state_runtime": state_check(root, "runtime")["pass"],
            },
        })

    # Final audit scenarios, deliberately independent of the scenario implementation checks above.
    for sid, subject, final_class in (
        ("A01", "exact-owned", "exact-owned-teardown"),
        ("A02", "modified-owned-regular", "modified-owned-residual"),
        ("A03", "unowned-file", "unowned-sentinel-residual"),
    ):
        if resume_existing(sid):
            continue
        scenario, root, out = prepare(sid, "runtime")
        subject_paths, mutations, subject_snapshots = prepare_subject(root, subject, runtime_rows)
        operation = uninstall(root=root, output=out, runner=local_runner, engine=engine, contract=contract, artifact="runtime-base", name="final-uninstall")
        audit = final_state_audit(root=root, runtime_rows=runtime_rows, final_class=final_class, subject_paths=subject_paths, subject_snapshots=subject_snapshots)
        scenario_results[sid] = finish(out, {
            "id": sid, "group": "audit", "matrix": scenario, "subject_kind": subject, "mutations": mutations,
            "operation": operation, "final_audit": audit,
            "checks": {"operation": result_pass(operation), "audit": audit["pass"]},
        })

    if not resume_existing("A04"):
        scenario, root, out = prepare("A04", "composed")
        order_results = []
        for label, order in (("test-first", ["test-addon", "development-addon", "runtime-base"]), ("development-first", ["development-addon", "test-addon", "runtime-base"])):
            order_root = work / "scenarios/A04" / label
            clone = clone_seed(seeds["composed"], order_root, probes)
            order_out = out / label
            operations_list = [uninstall(root=order_root, output=order_out, runner=local_runner, engine=engine, contract=contract, artifact=artifact, name=f"uninstall-{artifact}") for artifact in order]
            audit = final_state_audit(root=order_root, runtime_rows=runtime_rows, final_class="exact-owned-teardown")
            order_results.append({"label": label, "clone": clone, "operations": operations_list, "audit": audit, "pass": all(result_pass(item) for item in operations_list) and audit["pass"]})
        residual_root = work / "scenarios/A04/residual"
        residual_clone = clone_seed(seeds["composed"], residual_root, probes)
        subject_paths, mutations, subject_snapshots = prepare_subject(residual_root, "unowned-file-under-shared-namespace", runtime_rows)
        residual_ops = [uninstall(root=residual_root, output=out / "residual", runner=local_runner, engine=engine, contract=contract, artifact=artifact, name=f"uninstall-{artifact}") for artifact in ("test-addon", "development-addon", "runtime-base")]
        residual_audit = final_state_audit(root=residual_root, runtime_rows=runtime_rows, final_class="unowned-sentinel-residual", subject_paths=subject_paths, subject_snapshots=subject_snapshots)
        scenario_results["A04"] = finish(out, {
            "id": "A04", "group": "audit", "matrix": scenario, "orders": order_results,
            "residual_clone": residual_clone, "residual_mutations": mutations, "residual_operations": residual_ops, "residual_audit": residual_audit,
            "checks": {
                "both_orders_exact": all(item["pass"] for item in order_results),
                "shared_namespace_removed_when_empty": all(item["audit"]["observed_paths"] == [] for item in order_results),
                "shared_namespace_retained_for_residual": residual_audit["pass"] and "lib" in residual_audit["observed_paths"] and "lib/python3.14" in residual_audit["observed_paths"],
                "no_addon_ownership_adoption": residual_audit["registry"]["owned_path_count"] == 0,
            },
        })

    if not resume_existing("A05"):
        scenario, root, out = prepare("A05", "runtime")
        recovery_refs = {sid: {"pass": scenario_results[sid]["pass"], "boundary": scenario_results[sid]["matrix"]["crash_boundary"], "transactions": scenario_results[sid]["after_recover_2"]["transactions"]} for sid in recovery_subjects}
        scenario_results["A05"] = finish(out, {
            "id": "A05", "group": "audit", "matrix": scenario, "recovery_references": recovery_refs,
            "checks": {
                "all_recovery_pass": all(item["pass"] for item in recovery_refs.values()),
                "precommit_tombstone_one": all(len(recovery_refs[sid]["transactions"]) == 1 and recovery_refs[sid]["transactions"][0].get("journal", {}).get("state") == "ROLLED_BACK" for sid in ("R01", "R02", "R04", "R05", "R07", "R08", "R10", "R11")),
                "committed_transactions_clean": all(recovery_refs[sid]["transactions"] == [] for sid in ("R03", "R06", "R09", "R12")),
            },
        })

    if not resume_existing("A06"):
        scenario, root, out = prepare("A06", "runtime")
        existing_scenarios = sorted(output.glob("scenarios/*/scenario.json"))
        process_files = sorted(output.glob("scenarios/**/*-process.json"))
        references_ok = True
        for process_path in process_files:
            process = read_json(process_path)
            for key in ("stdout_file", "stderr_file"):
                name = process.get(key)
                if name and not (process_path.parent / name).is_file():
                    references_ok = False
        scenario_results["A06"] = finish(out, {
            "id": "A06", "group": "audit", "matrix": scenario,
            "evidence_contract": {
                "existing_scenario_count_before_a06": len(existing_scenarios),
                "raw_process_count": len(process_files),
                "target_verifier": str(SCRIPT_DIR / "verify-gate3d-final-uninstall.py"),
                "target_wrapper": str(SCRIPT_DIR / "run-gate3d-final-uninstall-termux.sh"),
                "finalizer": str(SCRIPT_DIR / "finalize-gate3d-evidence.py"),
                "post_finalize_external_inspection_required": True,
            },
            "checks": {
                "prior_scenarios_43": len(existing_scenarios) == 43,
                "raw_stdout_stderr": references_ok and len(process_files) >= 100,
                "canonical_json": all(canonical(path) for path in existing_scenarios),
                "independent_verifier_present": (SCRIPT_DIR / "verify-gate3d-final-uninstall.py").is_file(),
                "archive_safety_and_index_finalizer_present": (SCRIPT_DIR / "finalize-gate3d-evidence.py").is_file(),
                "single_wrapper_present": (SCRIPT_DIR / "run-gate3d-final-uninstall-termux.sh").is_file(),
                "explicit_claim_boundary": "independently inspected Termux result archive" in matrix["claim_boundary"]["gate3d_close_requires"],
            },
        })

    ordered = [scenario_results[row["id"]] for row in matrix["scenarios"]]
    group_counts: dict[str, int] = {}
    group_pass: dict[str, int] = {}
    for row in ordered:
        group = row["group"]
        group_counts[group] = group_counts.get(group, 0) + 1
        group_pass[group] = group_pass.get(group, 0) + int(row.get("pass") is True)
    clone_summary = {
        "schema_version": 1,
        "roots": clone_results,
        "pass": len(clone_results) == 44 and all(all(value.values()) for value in clone_results.values()),
    }
    write_json(output / "clone-separation.json", clone_summary)
    summary = {
        "schema_version": 1,
        "verification_kind": "stage3c-phase5-gate3d-final-uninstall-target-scenarios",
        "scenario_count": len(ordered),
        "pass_count": sum(row.get("pass") is True for row in ordered),
        "failed_scenarios": [row["id"] for row in ordered if row.get("pass") is not True],
        "group_counts": group_counts,
        "group_pass_counts": group_pass,
        "authority_pass": authority["pass"],
        "seed_pass": all(row["pass"] for row in seed_summaries.values()),
        "clone_separation_pass": clone_summary["pass"],
        "registry_intent_ordinals": calibrations,
        "claim_boundary": "Target Gate 3D scenario execution evidence only. Gate 3D remains pending independent archive inspection; upgrade and downgrade remain unclaimed.",
    }
    summary["pass"] = (
        summary["scenario_count"] == 44
        and summary["pass_count"] == 44
        and summary["group_counts"] == EXPECTED_GROUPS
        and summary["group_pass_counts"] == EXPECTED_GROUPS
        and summary["authority_pass"]
        and summary["seed_pass"]
        and summary["clone_separation_pass"]
    )
    write_json(output / "scenario-summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
