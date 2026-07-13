#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import stat
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from gate3c_addon_lifecycle_support import (  # noqa: E402
    EXPECTED_ARTIFACTS,
    EXPECTED_CONTRACT_INDEX_SHA,
    EXPECTED_ENGINE_SHA,
    EXPECTED_GATE3B_INDEX_SHA,
    EXPECTED_MANIFEST_INDEX_SHA,
    EXPECTED_MATRIX_SHA,
    EXPECTED_OPS_SHA,
    EXPECTED_STATES,
    cjson,
    choose_regular,
    clone_seed,
    exact_match,
    invoke_engine,
    kind,
    owned_digest,
    path_snapshot,
    product_snapshot,
    read_json,
    registry_value,
    rows_from_manifest,
    run_command,
    sha256_file,
    start_lock_holder,
    state_check,
    stop_lock_holder,
    transaction_inventory,
    verify_result_index,
    write_json,
)

STATE_INSTALL_ORDER = {
    "runtime": ("runtime-base",),
    "runtime-development": ("runtime-base", "development-addon"),
    "runtime-test": ("runtime-base", "test-addon"),
    "composed": ("runtime-base", "development-addon", "test-addon"),
    "composed-test-first": ("runtime-base", "test-addon", "development-addon"),
}
CRASH_RC = {"PREPARED": 90, "LATE_APPLYING": 93, "COMMITTED": 92}
INTENT_ORDINAL = {"development-addon": 455, "test-addon": 1789}


def clean_runtime_env(output: Path) -> dict[str, str | None]:
    return {
        "PYTHONHOME": None,
        "PYTHONPATH": None,
        "CPYTHON_HOME": None,
        "LD_LIBRARY_PATH": None,
        "SSL_CERT_FILE": None,
        "SSL_CERT_DIR": None,
        "VIRTUAL_ENV": None,
        "UV_PYTHON": None,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPYCACHEPREFIX": str(output / "pycache"),
    }


def copy_root(seed: Path, destination: Path, probes: list[str]) -> dict[str, bool]:
    if destination.exists():
        shutil.rmtree(destination)
    if seed.exists():
        return clone_seed(seed, destination, probes)
    destination.mkdir(parents=True)
    return {"root_inode_separate": True, "empty_seed": True}


def result_pass(process: dict[str, Any]) -> bool:
    return process.get("returncode") == 0 and process.get("result", {}).get("pass") is True


def error_contains(process: dict[str, Any], text: str) -> bool:
    return text in str(process.get("result", {}).get("error", ""))


def state_verify(
    *, runner: Path, engine: Path, contract: Path, root: Path, state: str, output: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    verify = invoke_engine(
        runner=runner,
        engine=engine,
        contract=contract,
        root=root,
        operation="verify",
        output=output,
    )
    shape = state_check(root, state)
    return verify, shape


def manifest_map(manifest_dir: Path) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    manifests: dict[str, dict[str, Any]] = {}
    rows: dict[str, list[dict[str, Any]]] = {}
    for artifact in EXPECTED_ARTIFACTS:
        manifest = read_json(manifest_dir / f"{artifact}.manifest.json")
        manifests[artifact] = manifest
        rows[artifact] = rows_from_manifest(manifest)
    return manifests, rows


def install_seed(
    *, name: str, order: tuple[str, ...], root: Path, output: Path, runner: Path, engine: Path, contract: Path
) -> dict[str, Any]:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    operations: list[dict[str, Any]] = []
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
    expected_state = "composed" if name == "composed-test-first" else name
    verify, shape = state_verify(
        runner=runner,
        engine=engine,
        contract=contract,
        root=root,
        state=expected_state,
        output=output / "verify.json",
    )
    summary = {
        "schema_version": 1,
        "seed": name,
        "order": list(order),
        "operations": operations,
        "verify": verify,
        "shape": shape,
        "transactions": transaction_inventory(root),
    }
    summary["pass"] = all(result_pass(item) for item in operations) and result_pass(verify) and shape["pass"] and not summary["transactions"]
    write_json(output / "summary.json", summary)
    return summary


def setup_scenario(seed: Path, root: Path, probes: list[str], output: Path) -> dict[str, Any]:
    clone = copy_root(seed, root, probes)
    write_json(output / "clone-separation.json", clone)
    return clone


def finish_scenario(output: Path, value: dict[str, Any]) -> dict[str, Any]:
    value.setdefault("schema_version", 1)
    write_json(output / "scenario.json", value)
    return value


def run_rejection(
    *, scenario: dict[str, Any], root: Path, output: Path, runner: Path, engine: Path, contract: Path,
    operation: str, artifact: str, expected_error: str, expected_rc: int = 44,
) -> dict[str, Any]:
    before = product_snapshot(root)
    process = invoke_engine(
        runner=runner, engine=engine, contract=contract, root=root, operation=operation,
        artifact=artifact, output=output / "operation.json",
    )
    after = product_snapshot(root)
    value = {
        "id": scenario["id"], "group": scenario["group"], "matrix": scenario,
        "before": before, "operation": process, "after": after,
        "checks": {
            "returncode": process["returncode"] == expected_rc,
            "error": error_contains(process, expected_error),
            "product_unchanged": before["identity_sha256"] == after["identity_sha256"],
            "no_transactions": after["transactions"] == [],
        },
    }
    value["pass"] = all(value["checks"].values())
    return finish_scenario(output, value)


def run_install_pass(
    *, scenario: dict[str, Any], root: Path, output: Path, runner: Path, engine: Path, contract: Path,
    artifact: str, expected_state: str, expected_actions: dict[str, int], expected_mutations: int,
) -> dict[str, Any]:
    before = product_snapshot(root)
    process = invoke_engine(
        runner=runner, engine=engine, contract=contract, root=root, operation="install",
        artifact=artifact, output=output / "install.json",
    )
    verify, shape = state_verify(runner=runner, engine=engine, contract=contract, root=root, state=expected_state, output=output / "verify.json")
    after = product_snapshot(root)
    value = {
        "id": scenario["id"], "group": scenario["group"], "matrix": scenario,
        "before": before, "install": process, "verify": verify, "shape": shape, "after": after,
        "checks": {
            "install_rc": result_pass(process),
            "actions": process.get("result", {}).get("action_counts") == expected_actions,
            "mutation_count": process.get("result", {}).get("mutation_count") == expected_mutations,
            "verify": result_pass(verify),
            "state": shape["pass"],
            "no_transactions": after["transactions"] == [],
        },
    }
    value["pass"] = all(value["checks"].values())
    return finish_scenario(output, value)


def run_uninstall_pass(
    *, scenario: dict[str, Any], root: Path, output: Path, runner: Path, engine: Path, contract: Path,
    artifact: str, expected_state: str,
) -> dict[str, Any]:
    before = product_snapshot(root)
    process = invoke_engine(
        runner=runner, engine=engine, contract=contract, root=root, operation="uninstall",
        artifact=artifact, output=output / "uninstall.json",
    )
    verify, shape = state_verify(runner=runner, engine=engine, contract=contract, root=root, state=expected_state, output=output / "verify.json")
    after = product_snapshot(root)
    value = {
        "id": scenario["id"], "group": scenario["group"], "matrix": scenario,
        "before": before, "uninstall": process, "verify": verify, "shape": shape, "after": after,
        "checks": {
            "uninstall_rc": result_pass(process),
            "mutation_count": process.get("result", {}).get("mutation_count") == EXPECTED_ARTIFACTS[artifact]["owned"] + 1,
            "verify": result_pass(verify), "state": shape["pass"], "no_transactions": after["transactions"] == [],
        },
    }
    value["pass"] = all(value["checks"].values())
    return finish_scenario(output, value)


def mutate_regular(root: Path, row: dict[str, Any], marker: bytes) -> dict[str, Any]:
    path = root / "prefix" / row["path"]
    before = path_snapshot(path)
    path.write_bytes(marker)
    os.chmod(path, int(row["mode"], 8))
    return {"path": row["path"], "before": before, "after": path_snapshot(path)}


def remove_regular(root: Path, row: dict[str, Any]) -> dict[str, Any]:
    path = root / "prefix" / row["path"]
    before = path_snapshot(path)
    path.unlink()
    return {"path": row["path"], "before": before, "after": path_snapshot(path)}


def run_recovery(
    *, scenario: dict[str, Any], root: Path, output: Path, runner: Path, engine: Path, contract: Path,
    operation: str, artifact: str, prior_state: str, committed_state: str, boundary: str,
) -> dict[str, Any]:
    before = product_snapshot(root)
    crash = invoke_engine(
        runner=runner, engine=engine, contract=contract, root=root, operation=operation, artifact=artifact,
        output=output / "crash.json", crash_boundary=boundary, intent_ordinal=INTENT_ORDINAL[artifact],
    )
    tx_after_crash = transaction_inventory(root)
    recover1 = invoke_engine(runner=runner, engine=engine, contract=contract, root=root, operation="recover", output=output / "recover-1.json")
    after_recover1 = product_snapshot(root)
    verify1 = invoke_engine(runner=runner, engine=engine, contract=contract, root=root, operation="verify", output=output / "verify-1.json")
    recover2 = invoke_engine(runner=runner, engine=engine, contract=contract, root=root, operation="recover", output=output / "recover-2.json")
    after_recover2 = product_snapshot(root)
    verify2 = invoke_engine(runner=runner, engine=engine, contract=contract, root=root, operation="verify", output=output / "verify-2.json")
    expected_state = committed_state if boundary == "COMMITTED" else prior_state
    shape = state_check(root, expected_state)
    actions1 = recover1.get("result", {}).get("actions", [])
    actions2 = recover2.get("result", {}).get("actions", [])
    expected_action1 = "FINALIZED_COMMIT" if boundary == "COMMITTED" else "ROLLED_BACK"
    expected_action2 = None if boundary == "COMMITTED" else "NOOP_ROLLED_BACK"
    payload_registry_restored = (
        before["prefix_digest"] == after_recover1["prefix_digest"]
        and before["registry"]["sha256"] == after_recover1["registry"]["sha256"]
    ) if boundary != "COMMITTED" else True
    tombstone_ok = (
        after_recover2["transactions"] == []
        if boundary == "COMMITTED"
        else len(after_recover2["transactions"]) == 1
        and after_recover2["transactions"][0].get("journal", {}).get("state") == "ROLLED_BACK"
    )
    value = {
        "id": scenario["id"], "group": scenario["group"], "matrix": scenario,
        "before": before, "crash": crash, "transactions_after_crash": tx_after_crash,
        "recover_1": recover1, "after_recover_1": after_recover1, "verify_1": verify1,
        "recover_2": recover2, "after_recover_2": after_recover2, "verify_2": verify2, "shape": shape,
        "recovery_retention_policy": "PREPARED/APPLYING retain one ROLLED_BACK audit tombstone; COMMITTED recovery cleans the transaction.",
        "checks": {
            "crash_rc": crash["returncode"] == CRASH_RC[boundary],
            "one_crash_transaction": len(tx_after_crash) == 1,
            "recover_1_rc": result_pass(recover1),
            "recover_1_action": len(actions1) == 1 and actions1[0].get("action") == expected_action1,
            "payload_registry_restored": payload_registry_restored,
            "verify_1": result_pass(verify1),
            "recover_2_rc": result_pass(recover2),
            "recover_2_action": (actions2 == [] if expected_action2 is None else len(actions2) == 1 and actions2[0].get("action") == expected_action2),
            "verify_2": result_pass(verify2),
            "state": shape["pass"],
            "transaction_retention": tombstone_ok,
        },
    }
    value["pass"] = all(value["checks"].values())
    return finish_scenario(output, value)


def verify_gate3b_authority(gate3b: Path, contract: Path, matrix: Path, engine: Path, operations: Path, output: Path) -> dict[str, Any]:
    manifest_root = contract / "input/phase3/input/manifest-schema"
    result_index = gate3b / "result-index.json"
    verification = read_json(gate3b / "verification.json")
    scenario = read_json(gate3b / "scenario-summary.json")
    workflow = read_json(gate3b / "workflow-status.json")
    wrapper = read_json(gate3b / "termux-wrapper-status.json")
    checks = {
        "gate3b_result_index_sha": sha256_file(result_index) == EXPECTED_GATE3B_INDEX_SHA,
        "gate3b_result_index_contents": verify_result_index(gate3b, result_index)["pass"],
        "gate3b_verification_62": verification.get("pass") is True and verification.get("check_count") == 62,
        "gate3b_scenarios_29": scenario.get("pass") is True and scenario.get("check_count") == 29,
        "gate3b_workflow": workflow.get("pass") is True and workflow.get("workflow_returncode") == 0,
        "gate3b_wrapper": wrapper.get("pass") is True and wrapper.get("workflow_returncode") == 0,
        "contract_index": sha256_file(contract / "contract-index.json") == EXPECTED_CONTRACT_INDEX_SHA,
        "manifest_index": sha256_file(manifest_root / "manifest-index.json") == EXPECTED_MANIFEST_INDEX_SHA,
        "matrix": sha256_file(matrix) == EXPECTED_MATRIX_SHA,
        "engine": sha256_file(engine) == EXPECTED_ENGINE_SHA,
        "operations": sha256_file(operations) == EXPECTED_OPS_SHA,
    }
    for artifact, expected in EXPECTED_ARTIFACTS.items():
        manifest = manifest_root / "manifests" / f"{artifact}.manifest.json"
        checks[f"{artifact}_manifest"] = sha256_file(manifest) == expected["manifest_sha256"]
        matches = list((contract / "input/phase3/archives").glob(f"*{artifact}.tar.gz"))
        checks[f"{artifact}_archive_count"] = len(matches) == 1
        checks[f"{artifact}_archive"] = len(matches) == 1 and sha256_file(matches[0]) == expected["archive_sha256"]
    result = {
        "schema_version": 1,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": sorted(key for key, value in checks.items() if not value),
        "pass": all(checks.values()),
    }
    write_json(output, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("gate3b-results", "contract-results", "matrix", "engine", "operations", "local-script-runner", "work-root", "output-dir"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--skip-runtime-regression", action="store_true", help="development-only local self-test; never accepted as target evidence")
    args = parser.parse_args()

    gate3b = args.gate3b_results.resolve()
    contract = args.contract_results.resolve()
    matrix_path = args.matrix.resolve()
    engine = args.engine.resolve()
    operations = args.operations.resolve()
    local_runner = args.local_script_runner.resolve()
    work = args.work_root.resolve()
    output = args.output_dir.resolve()
    shutil.rmtree(work, ignore_errors=True)
    shutil.rmtree(output, ignore_errors=True)
    work.mkdir(parents=True)
    output.mkdir(parents=True)
    (output / "input").mkdir()

    authority = verify_gate3b_authority(gate3b, contract, matrix_path, engine, operations, output / "accepted-authority.json")
    shutil.copy2(matrix_path, output / "input/gate3c-addon-lifecycle-matrix.json")
    for source, name in (
        (gate3b / "result-index.json", "gate3b-result-index.json"),
        (gate3b / "verification.json", "gate3b-verification.json"),
        (gate3b / "scenario-summary.json", "gate3b-scenario-summary.json"),
        (gate3b / "workflow-status.json", "gate3b-workflow-status.json"),
        (gate3b / "termux-wrapper-status.json", "gate3b-wrapper-status.json"),
    ):
        shutil.copy2(source, output / "input" / name)
    shutil.copytree(contract, output / "input/contract", symlinks=True, copy_function=shutil.copy2)

    matrix = read_json(matrix_path)
    scenario_by_id = {row["id"]: row for row in matrix["scenarios"]}
    manifest_dir = contract / "input/phase3/input/manifest-schema/manifests"
    manifests, artifact_rows = manifest_map(manifest_dir)
    dev_regular = choose_regular(artifact_rows["development-addon"], preferred="include/python3.14/Python.h")
    test_regular = choose_regular(artifact_rows["test-addon"], preferred="lib/python3.14/__phello__/__init__.py")
    runtime_probe = choose_regular(artifact_rows["runtime-base"], preferred="lib/python3.14/LICENSE.txt")
    probes = [runtime_probe["path"], dev_regular["path"], test_regular["path"]]

    seed_root = work / "seeds"
    seed_out = output / "seeds"
    seeds: dict[str, Path] = {"empty": seed_root / "empty"}
    seeds["empty"].mkdir(parents=True)
    seed_summaries: dict[str, dict[str, Any]] = {}
    for name, order in STATE_INSTALL_ORDER.items():
        root = seed_root / name
        seeds[name] = root
        seed_summaries[name] = install_seed(name=name, order=order, root=root, output=seed_out / name, runner=local_runner, engine=engine, contract=contract)

    scenario_results: dict[str, dict[str, Any]] = {}
    clone_results: dict[str, dict[str, bool]] = {}

    def prepare(sid: str, seed_name: str) -> tuple[dict[str, Any], Path, Path]:
        scenario = scenario_by_id[sid]
        root = work / "scenarios" / sid
        out = output / "scenarios" / sid
        out.mkdir(parents=True, exist_ok=True)
        clone = setup_scenario(seeds[seed_name], root, probes, out)
        clone_results[sid] = clone
        return scenario, root, out

    # Preflight and dependency rejection.
    for sid, artifact in (("P01", "development-addon"), ("P02", "test-addon")):
        scenario, root, out = prepare(sid, "empty")
        scenario_results[sid] = run_rejection(scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract, operation="install", artifact=artifact, expected_error="prerequisite not installed")

    for sid, artifact in (("P03", "development-addon"), ("P04", "test-addon")):
        scenario, root, out = prepare(sid, "runtime")
        registry_path = root / ".cpython-android-cli/registry.json"
        value = read_json(registry_path)
        value["artifacts"][0]["artifact_id"] += "-forged"
        registry_path.write_bytes(cjson(value))
        scenario_results[sid] = run_rejection(scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract, operation="install", artifact=artifact, expected_error="prerequisite not installed")

    for sid, seed in (("P05", "runtime-development"), ("P06", "runtime-test"), ("P07", "composed")):
        scenario, root, out = prepare(sid, seed)
        scenario_results[sid] = run_rejection(scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract, operation="uninstall", artifact="runtime-base", expected_error="dependent addons installed")

    for sid, artifact, row in (("P08", "development-addon", dev_regular), ("P09", "test-addon", test_regular)):
        scenario, root, out = prepare(sid, "runtime")
        path = root / "prefix" / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((sid + "-unowned\n").encode())
        os.chmod(path, int(row["mode"], 8))
        scenario_results[sid] = run_rejection(scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract, operation="install", artifact=artifact, expected_error="unowned collision")

    scenario, root, out = prepare("P10", "runtime")
    registry_path = root / ".cpython-android-cli/registry.json"
    value = read_json(registry_path)
    adversarial = {
        "path": dev_regular["path"], "owner_artifact": "test-addon", "type": dev_regular["type"],
        "mode": dev_regular["mode"], "size": dev_regular["size"], "sha256": dev_regular["sha256"],
        "symlink_target": None, "component": "ADVERSARIAL_TEST_ONLY", "elf": False,
    }
    value["owned_paths"].append(adversarial)
    value["owned_paths"] = sorted(value["owned_paths"], key=lambda row: row["path"])
    registry_path.write_bytes(cjson(value))
    scenario_results["P10"] = run_rejection(scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract, operation="install", artifact="development-addon", expected_error="other owner")

    # Composition and repair.
    for sid, seed, artifact, state, actions, mutations in (
        ("C01", "empty", "runtime-base", "runtime", {"create": 714}, 715),
        ("C02", "runtime", "development-addon", "runtime-development", {"create": 454}, 455),
        ("C03", "runtime", "test-addon", "runtime-test", {"create": 1788}, 1789),
        ("C04", "runtime-development", "test-addon", "composed", {"create": 1788}, 1789),
        ("C05", "runtime-test", "development-addon", "composed", {"create": 454}, 455),
        ("C06", "runtime-development", "development-addon", "runtime-development", {"noop": 454}, 0),
        ("C07", "runtime-test", "test-addon", "runtime-test", {"noop": 1788}, 0),
        ("C08", "composed", "runtime-base", "composed", {"noop": 714}, 0),
    ):
        scenario, root, out = prepare(sid, seed)
        scenario_results[sid] = run_install_pass(scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract, artifact=artifact, expected_state=state, expected_actions=actions, expected_mutations=mutations)

    scenario, root, out = prepare("C09", "runtime-development")
    mutation = mutate_regular(root, dev_regular, b"gate3c-development-modified\n")
    preverify = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="verify", output=out / "preverify.json")
    install = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="install", artifact="development-addon", output=out / "repair.json")
    postverify, shape = state_verify(runner=local_runner, engine=engine, contract=contract, root=root, state="runtime-development", output=out / "postverify.json")
    value = {"id": "C09", "group": "composition", "matrix": scenario, "mutation": mutation, "preverify": preverify, "repair": install, "postverify": postverify, "shape": shape,
             "checks": {"preverify_rc44": preverify["returncode"] == 44 and preverify.get("result", {}).get("bad_paths") == [dev_regular["path"]], "repair": result_pass(install), "actions": install.get("result", {}).get("action_counts") == {"noop": 453, "repair": 1}, "mutations": install.get("result", {}).get("mutation_count") == 2, "exact": exact_match(root / "prefix" / dev_regular["path"], dev_regular), "verify": result_pass(postverify), "state": shape["pass"], "transactions": transaction_inventory(root) == []}}
    value["pass"] = all(value["checks"].values()); scenario_results["C09"] = finish_scenario(out, value)

    scenario, root, out = prepare("C10", "runtime-test")
    mutation = remove_regular(root, test_regular)
    preverify = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="verify", output=out / "preverify.json")
    install = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="install", artifact="test-addon", output=out / "repair.json")
    postverify, shape = state_verify(runner=local_runner, engine=engine, contract=contract, root=root, state="runtime-test", output=out / "postverify.json")
    value = {"id": "C10", "group": "composition", "matrix": scenario, "mutation": mutation, "preverify": preverify, "repair": install, "postverify": postverify, "shape": shape,
             "checks": {"preverify_rc44": preverify["returncode"] == 44 and preverify.get("result", {}).get("bad_paths") == [test_regular["path"]], "repair": result_pass(install), "actions": install.get("result", {}).get("action_counts") == {"noop": 1787, "repair": 1}, "mutations": install.get("result", {}).get("mutation_count") == 2, "exact": exact_match(root / "prefix" / test_regular["path"], test_regular), "verify": result_pass(postverify), "state": shape["pass"], "transactions": transaction_inventory(root) == []}}
    value["pass"] = all(value["checks"].values()); scenario_results["C10"] = finish_scenario(out, value)

    # Normal uninstall order.
    for sid, seed, artifact, state in (
        ("U01", "composed", "test-addon", "runtime-development"),
        ("U02", "composed", "development-addon", "runtime-test"),
        ("U03", "runtime-development", "development-addon", "runtime"),
        ("U04", "runtime-test", "test-addon", "runtime"),
    ):
        scenario, root, out = prepare(sid, seed)
        scenario_results[sid] = run_uninstall_pass(scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract, artifact=artifact, expected_state=state)

    for sid, seed, artifact, row in (("U05", "runtime-development", "development-addon", dev_regular), ("U06", "runtime-test", "test-addon", test_regular)):
        scenario, root, out = prepare(sid, seed)
        mutation = mutate_regular(root, row, (sid + "-preserved\n").encode())
        before_subject = path_snapshot(root / "prefix" / row["path"])
        uninstall = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="uninstall", artifact=artifact, output=out / "uninstall.json")
        after_subject = path_snapshot(root / "prefix" / row["path"])
        verify, shape = state_verify(runner=local_runner, engine=engine, contract=contract, root=root, state="runtime", output=out / "verify.json")
        preserved = uninstall.get("result", {}).get("preserved", [])
        value = {"id": sid, "group": "uninstall", "matrix": scenario, "mutation": mutation, "uninstall": uninstall, "subject_before": before_subject, "subject_after": after_subject, "verify": verify, "shape": shape, "preserved": preserved,
                 "checks": {"uninstall": result_pass(uninstall), "modified_leaf_preserved": before_subject == after_subject, "leaf_reported": row["path"] in preserved, "leaf_deregistered": row["path"] not in {x["path"] for x in registry_value(root)["value"]["owned_paths"]}, "verify": result_pass(verify), "state": shape["pass"], "transactions": transaction_inventory(root) == []}}
        value["pass"] = all(value["checks"].values()); scenario_results[sid] = finish_scenario(out, value)

    scenario, root, out = prepare("U07", "composed")
    sentinels = {}
    file_path = root / "prefix/lib/python3.14/test/gate3c-unowned-file.txt"
    file_path.write_bytes(b"gate3c-unowned-file\n"); os.chmod(file_path, 0o600)
    dir_path = root / "prefix/lib/python3.14/test/gate3c-unowned-dir"
    dir_path.mkdir(mode=0o700); (dir_path / "payload.txt").write_bytes(b"gate3c-unowned-directory\n")
    sentinels["file_before"] = path_snapshot(file_path); sentinels["directory_before"] = path_snapshot(dir_path, recursive=True)
    uninstall = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="uninstall", artifact="test-addon", output=out / "uninstall.json")
    verify, shape = state_verify(runner=local_runner, engine=engine, contract=contract, root=root, state="runtime-development", output=out / "verify.json")
    sentinels["file_after"] = path_snapshot(file_path); sentinels["directory_after"] = path_snapshot(dir_path, recursive=True)
    value = {"id": "U07", "group": "uninstall", "matrix": scenario, "sentinels": sentinels, "uninstall": uninstall, "verify": verify, "shape": shape,
             "checks": {"uninstall": result_pass(uninstall), "file_preserved": sentinels["file_before"] == sentinels["file_after"], "directory_preserved": sentinels["directory_before"] == sentinels["directory_after"], "verify": result_pass(verify), "state": shape["pass"], "transactions": transaction_inventory(root) == []}}
    value["pass"] = all(value["checks"].values()); scenario_results["U07"] = finish_scenario(out, value)

    scenario, root, out = prepare("U08", "composed")
    shared_before = {path: path_snapshot(root / "prefix" / path) for path in ("lib", "lib/python3.14")}
    uninstall = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="uninstall", artifact="development-addon", output=out / "uninstall.json")
    shared_after = {path: path_snapshot(root / "prefix" / path) for path in ("lib", "lib/python3.14")}
    registry = registry_value(root)
    owners = {row["path"]: row["owner_artifact"] for row in registry["value"]["owned_paths"] if row["path"] in shared_after}
    verify, shape = state_verify(runner=local_runner, engine=engine, contract=contract, root=root, state="runtime-test", output=out / "verify.json")
    value = {"id": "U08", "group": "uninstall", "matrix": scenario, "shared_before": shared_before, "shared_after": shared_after, "owners": owners, "uninstall": uninstall, "verify": verify, "shape": shape,
             "checks": {"uninstall": result_pass(uninstall), "shared_exact": shared_before == shared_after, "runtime_owner": owners == {"lib": "runtime-base", "lib/python3.14": "runtime-base"}, "verify": result_pass(verify), "state": shape["pass"]}}
    value["pass"] = all(value["checks"].values()); scenario_results["U08"] = finish_scenario(out, value)

    scenario, root, out = prepare("U09", "runtime-development")
    mutation = mutate_regular(root, dev_regular, b"gate3c-preserved-residual\n")
    uninstall = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="uninstall", artifact="development-addon", output=out / "uninstall.json")
    before_reinstall = product_snapshot(root)
    reinstall = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="install", artifact="development-addon", output=out / "reinstall.json")
    after_reinstall = product_snapshot(root)
    verify, shape = state_verify(runner=local_runner, engine=engine, contract=contract, root=root, state="runtime", output=out / "verify.json")
    value = {"id": "U09", "group": "uninstall", "matrix": scenario, "mutation": mutation, "uninstall": uninstall, "before_reinstall": before_reinstall, "reinstall": reinstall, "after_reinstall": after_reinstall, "verify": verify, "shape": shape,
             "checks": {"setup_uninstall": result_pass(uninstall), "reinstall_rc44": reinstall["returncode"] == 44, "collision": error_contains(reinstall, "unowned collision"), "unchanged": before_reinstall["identity_sha256"] == after_reinstall["identity_sha256"], "verify": result_pass(verify), "state": shape["pass"]}}
    value["pass"] = all(value["checks"].values()); scenario_results["U09"] = finish_scenario(out, value)

    # Recovery cross product.
    recovery_specs = (
        ("R01", "runtime", "install", "development-addon", "runtime", "runtime-development", "PREPARED"),
        ("R02", "runtime", "install", "development-addon", "runtime", "runtime-development", "LATE_APPLYING"),
        ("R03", "runtime", "install", "development-addon", "runtime", "runtime-development", "COMMITTED"),
        ("R04", "runtime", "install", "test-addon", "runtime", "runtime-test", "PREPARED"),
        ("R05", "runtime", "install", "test-addon", "runtime", "runtime-test", "LATE_APPLYING"),
        ("R06", "runtime", "install", "test-addon", "runtime", "runtime-test", "COMMITTED"),
        ("R07", "runtime-development", "uninstall", "development-addon", "runtime-development", "runtime", "PREPARED"),
        ("R08", "runtime-development", "uninstall", "development-addon", "runtime-development", "runtime", "LATE_APPLYING"),
        ("R09", "runtime-development", "uninstall", "development-addon", "runtime-development", "runtime", "COMMITTED"),
        ("R10", "runtime-test", "uninstall", "test-addon", "runtime-test", "runtime", "PREPARED"),
        ("R11", "runtime-test", "uninstall", "test-addon", "runtime-test", "runtime", "LATE_APPLYING"),
        ("R12", "runtime-test", "uninstall", "test-addon", "runtime-test", "runtime", "COMMITTED"),
    )
    for sid, seed, operation, artifact, prior, committed, boundary in recovery_specs:
        scenario, root, out = prepare(sid, seed)
        scenario_results[sid] = run_recovery(scenario=scenario, root=root, output=out, runner=local_runner, engine=engine, contract=contract, operation=operation, artifact=artifact, prior_state=prior, committed_state=committed, boundary=boundary)

    # Lock exclusion.
    for sid, seed, operation, artifact in (("L01", "runtime", "install", "development-addon"), ("L02", "composed", "uninstall", "test-addon")):
        scenario, root, out = prepare(sid, seed)
        before = product_snapshot(root)
        ready = out / "lock.ready"
        holder = start_lock_holder(runner=local_runner, engine=engine, root=root, output=out / "holder.json", ready=ready)
        contender = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation=operation, artifact=artifact, output=out / "contender.json", nonblocking=True)
        holder_rc = stop_lock_holder(holder)
        after = product_snapshot(root)
        verify = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="verify", output=out / "verify.json")
        value = {"id": sid, "group": "locking", "matrix": scenario, "before": before, "contender": contender, "holder_terminated_returncode": holder_rc, "after": after, "verify": verify,
                 "checks": {"contender_rc44": contender["returncode"] == 44, "lock_busy": error_contains(contender, "installation lock busy"), "unchanged": before["identity_sha256"] == after["identity_sha256"], "verify": result_pass(verify), "transactions": transaction_inventory(root) == []}}
        value["pass"] = all(value["checks"].values()); scenario_results[sid] = finish_scenario(out, value)

    # Behavior and final state audit.
    scenario, root, out = prepare("B01", "runtime-development")
    header = root / "prefix/include/python3.14/Python.h"
    value = {"id": "B01", "group": "behavior", "matrix": scenario, "header": path_snapshot(header), "checks": {"present": header.is_file(), "exact": exact_match(header, dev_regular)}}
    value["pass"] = all(value["checks"].values()); scenario_results["B01"] = finish_scenario(out, value)

    scenario, root, out = prepare("B02", "runtime-test")
    py = root / "prefix/bin/python"
    process = run_command([str(py), "-I", "-B", "-c", "import test.support; print(test.support.__file__)"], output_prefix=out / "import-test-support", env=clean_runtime_env(out))
    value = {"id": "B02", "group": "behavior", "matrix": scenario, "process": process, "checks": {"returncode": process["returncode"] == 0, "support_exact": exact_match(root / "prefix/lib/python3.14/test/support/__init__.py", {**{row["path"]: row for row in artifact_rows["test-addon"]}["lib/python3.14/test/support/__init__.py"]})}}
    value["pass"] = all(value["checks"].values()); scenario_results["B02"] = finish_scenario(out, value)

    scenario, root, out = prepare("B03", "runtime-test")
    py = root / "prefix/bin/python"
    process = run_command([str(py), "-I", "-B", "-m", "test", "-j1", "test_json", "test_hashlib"], output_prefix=out / "selected-tests", env=clean_runtime_env(out))
    value = {"id": "B03", "group": "behavior", "matrix": scenario, "process": process, "checks": {"returncode": process["returncode"] == 0}}
    value["pass"] = all(value["checks"].values()); scenario_results["B03"] = finish_scenario(out, value)

    scenario, root, out = prepare("B04", "runtime-test")
    uninstall = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="uninstall", artifact="test-addon", output=out / "uninstall.json")
    absent = [row["path"] for row in artifact_rows["test-addon"] if kind(root / "prefix" / row["path"]) == "absent"]
    verify, shape = state_verify(runner=local_runner, engine=engine, contract=contract, root=root, state="runtime", output=out / "verify.json")
    value = {"id": "B04", "group": "behavior", "matrix": scenario, "uninstall": uninstall, "absent_count": len(absent), "verify": verify, "shape": shape, "checks": {"uninstall": result_pass(uninstall), "all_test_payload_absent": len(absent) == 1788, "verify": result_pass(verify), "state": shape["pass"]}}
    value["pass"] = all(value["checks"].values()); scenario_results["B04"] = finish_scenario(out, value)

    scenario, root, out = prepare("B05", "runtime-development")
    uninstall = invoke_engine(runner=local_runner, engine=engine, contract=contract, root=root, operation="uninstall", artifact="development-addon", output=out / "uninstall.json")
    absent = [row["path"] for row in artifact_rows["development-addon"] if kind(root / "prefix" / row["path"]) == "absent"]
    verify, shape = state_verify(runner=local_runner, engine=engine, contract=contract, root=root, state="runtime", output=out / "verify.json")
    value = {"id": "B05", "group": "behavior", "matrix": scenario, "uninstall": uninstall, "absent_count": len(absent), "verify": verify, "shape": shape, "checks": {"uninstall": result_pass(uninstall), "all_development_payload_absent": len(absent) == 454, "header_absent": kind(root / "prefix/include/python3.14/Python.h") == "absent", "verify": result_pass(verify), "state": shape["pass"]}}
    value["pass"] = all(value["checks"].values()); scenario_results["B05"] = finish_scenario(out, value)

    scenario, root, out = prepare("B06", "runtime")
    before = product_snapshot(root)
    regression: dict[str, Any] = {"skipped": args.skip_runtime_regression}
    checks: dict[str, bool] = {}
    if args.skip_runtime_regression:
        checks["development_only_skip"] = False
    else:
        py = root / "prefix/bin/python"
        env = clean_runtime_env(out)
        probe = run_command([str(py), "-I", "-B", "-S", str(SCRIPT_DIR.parent / "stage3c-installed-runtime-baseline/probe-installed-runtime.py"), "--output", str(out / "runtime-probe.json"), "--https"], output_prefix=out / "runtime-probe-command", env=env)
        smoke = run_command(["bash", str(SCRIPT_DIR.parent.parent / "scripts/test/smoke-termux.sh")], output_prefix=out / "smoke", env={**env, "RUNTIME_ROOT_OVERRIDE": str(root), "TERMUX_RESULTS_ROOT_OVERRIDE": str(root / "smoke-results")})
        closure_dir = out / "closure"
        inventory = run_command(["bash", str(SCRIPT_DIR.parent / "stage3a-runtime-closure/inventory-runtime.sh")], output_prefix=out / "closure-inventory", env={**env, "RUNTIME_PREFIX": str(root / "prefix"), "PYTHON_BIN": str(py), "OUTPUT_DIR": str(closure_dir)})
        analyze = run_command(["bash", str(SCRIPT_DIR.parent / "stage3a-runtime-closure/analyze-and-probe.sh")], output_prefix=out / "closure-analysis", env={**env, "RUNTIME_PREFIX": str(root / "prefix"), "PYTHON_BIN": str(py), "RESULTS_DIR": str(closure_dir)})
        extensions = run_command([str(py), "-I", "-B", "-S", str(SCRIPT_DIR.parent / "stage3a-runtime-closure/probe-extension-imports.py"), "--python-bin", str(py), "--output-dir", str(out / "extension-imports")], output_prefix=out / "extension-import-command", env=env)
        probe_json = read_json(out / "runtime-probe.json") if (out / "runtime-probe.json").is_file() else {}
        closure_json = read_json(closure_dir / "closure-analysis-summary.json") if (closure_dir / "closure-analysis-summary.json").is_file() else {}
        ext_json = read_json(out / "extension-imports/extension-import-probe-summary.json") if (out / "extension-imports/extension-import-probe-summary.json").is_file() else {}
        unresolved = closure_dir / "unresolved.tsv"
        unresolved_count = max(0, len(unresolved.read_text(encoding="utf-8").splitlines()) - 1) if unresolved.is_file() else -1
        smoke_stdout = (out / "smoke.stdout.txt").read_text(encoding="utf-8") if (out / "smoke.stdout.txt").is_file() else ""
        regression = {"probe": probe, "smoke": smoke, "inventory": inventory, "analyze": analyze, "extensions": extensions, "runtime_probe": probe_json, "closure_summary": closure_json, "extension_summary": ext_json, "unresolved_count": unresolved_count}
        checks = {
            "probe": probe["returncode"] == 0 and probe_json.get("pass") is True and probe_json.get("https_status") == 200,
            "smoke": smoke["returncode"] == 0 and "STAGE2C_SMOKE=PASS" in smoke_stdout,
            "inventory": inventory["returncode"] == 0,
            "analyze": analyze["returncode"] == 0,
            "closure_81": closure_json.get("object_count_with_needed_edges") == 81,
            "closure_329": closure_json.get("needed_edge_count") == 329,
            "unresolved_zero": unresolved_count == 0,
            "extensions": extensions["returncode"] == 0 and ext_json.get("extension_candidate_count") == 67 and ext_json.get("import_pass_count") == 67 and ext_json.get("import_fail_count") == 0,
        }
    after = product_snapshot(root)
    checks["runtime_product_unchanged"] = before["identity_sha256"] == after["identity_sha256"]
    value = {"id": "B06", "group": "behavior", "matrix": scenario, "before": before, "regression": regression, "after": after, "checks": checks}
    value["pass"] = all(checks.values()); scenario_results["B06"] = finish_scenario(out, value)

    scenario, root, out = prepare("B07", "runtime")
    verify, shape = state_verify(runner=local_runner, engine=engine, contract=contract, root=root, state="runtime", output=out / "verify.json")
    final = product_snapshot(root)
    value = {"id": "B07", "group": "behavior", "matrix": scenario, "verify": verify, "shape": shape, "final": final, "checks": {"verify": result_pass(verify), "state_1_714": shape["pass"], "zero_transactions": final["transactions"] == []}}
    value["pass"] = all(value["checks"].values()); scenario_results["B07"] = finish_scenario(out, value)

    ordered = [scenario_results[row["id"]] for row in matrix["scenarios"]]
    group_counts: dict[str, int] = {}
    group_pass: dict[str, int] = {}
    for row in ordered:
        group = row["group"]
        group_counts[group] = group_counts.get(group, 0) + 1
        group_pass[group] = group_pass.get(group, 0) + int(row.get("pass") is True)
    clone_summary = {"schema_version": 1, "roots": clone_results, "pass": len(clone_results) == 50 and all(all(v.values()) for v in clone_results.values())}
    write_json(output / "clone-separation.json", clone_summary)
    summary = {
        "schema_version": 1,
        "verification_kind": "stage3c-phase5-gate3c-addon-lifecycle-target-scenarios",
        "scenario_count": len(ordered),
        "pass_count": sum(row.get("pass") is True for row in ordered),
        "failed_scenarios": [row["id"] for row in ordered if row.get("pass") is not True],
        "group_counts": group_counts,
        "group_pass_counts": group_pass,
        "authority_pass": authority["pass"],
        "seed_pass": all(row["pass"] for row in seed_summaries.values()),
        "clone_separation_pass": clone_summary["pass"],
        "runtime_regression_skipped": args.skip_runtime_regression,
        "claim_boundary": "Target scenario execution evidence only. Gate 3C remains pending independent archive inspection; Gate 3D final uninstall, upgrade, and downgrade remain unclaimed.",
    }
    summary["pass"] = (
        summary["scenario_count"] == 50
        and summary["pass_count"] == 50
        and summary["authority_pass"]
        and summary["seed_pass"]
        and summary["clone_separation_pass"]
        and not summary["runtime_regression_skipped"]
    )
    write_json(output / "scenario-summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.require_pass and not summary["pass"]:
        return 1
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
