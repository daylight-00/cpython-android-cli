#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, os, shutil, stat
from pathlib import Path
from typing import Any
import transaction_engine as tx

EXPECTED_CONTRACT_INDEX = "79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3"


def cjson(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def readj(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint(root: Path) -> str:
    rows = []
    if root.exists():
        for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
            relative = path.relative_to(root).as_posix()
            if relative.startswith(".cpython-android-cli/transactions/"):
                continue
            observed = path.lstat()
            row = {"path": relative, "mode": f"{stat.S_IMODE(observed.st_mode):04o}"}
            if path.is_symlink():
                row.update(type="symlink", target=os.readlink(path))
            elif path.is_dir():
                row["type"] = "directory"
            elif path.is_file():
                row.update(type="regular", size=observed.st_size, sha256=sha(path))
            else:
                row["type"] = "special"
            rows.append(row)
    payload = "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows)
    return hashlib.sha256(payload.encode()).hexdigest()


def registry(root: Path) -> dict[str, Any]:
    return tx.load_registry(root / ".cpython-android-cli/registry.json")


def first_regular(root: Path, artifact: str) -> str:
    return next(
        row["path"]
        for row in registry(root)["owned_paths"]
        if row["owner_artifact"] == artifact and row["type"] == "regular"
    )


def write_snapshot(output: Path, name: str, root: Path) -> None:
    target = output / "snapshots"
    target.mkdir(exist_ok=True)
    current = registry(root)
    observed = []
    for row in current["owned_paths"]:
        path = root / "prefix" / row["path"]
        item = dict(row)
        item["observed_type"] = tx.actual_kind(path)
        item["observed_match"] = tx.matches(path, row)
        if item["observed_type"] == "regular":
            item.update(observed_size=path.stat().st_size, observed_sha256=sha(path))
        elif item["observed_type"] == "symlink":
            item["observed_symlink_target"] = os.readlink(path)
        observed.append(item)
    (target / f"{name}-registry.json").write_bytes(cjson(current))
    (target / f"{name}-observed-owned-paths.json").write_bytes(
        cjson({"schema_version": 1, "owned_path_count": len(observed), "all_match": all(x["observed_match"] for x in observed), "rows": observed})
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-results", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    contract, work, output = map(Path.resolve, (args.contract_results, args.work_root, args.output_dir))
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    output.mkdir(parents=True, exist_ok=True)
    checks: dict[str, bool] = {}

    def check(name: str, value: bool) -> None:
        checks[name] = bool(value)

    def save(name: str, value: dict[str, Any]) -> dict[str, Any]:
        (output / name).write_bytes(cjson(value))
        return value

    derivation, verification, workflow = (readj(contract / name) for name in ("derivation.json", "verification.json", "workflow-status.json"))
    model, index = readj(contract / "installation-contract.json"), readj(contract / "contract-index.json")
    check("gate1_derivation_pass_54", derivation.get("pass") is True and derivation.get("check_count") == 54 and derivation.get("failed_checks") == [])
    check("gate1_verification_pass_59", verification.get("pass") is True and verification.get("check_count") == 59 and verification.get("failed_checks") == [])
    check("gate1_workflow_pass", workflow.get("pass") is True)
    check("gate1_workflow_returncodes_zero", bool(workflow.get("returncodes")) and all(v == 0 for v in workflow["returncodes"].values()))
    check("gate1_contract_index_hash_exact", sha(contract / "contract-index.json") == EXPECTED_CONTRACT_INDEX)
    check("gate1_contract_model_only", model.get("status") == "model-only-no-target-mutation")
    check("gate1_contract_index_files_exact", set(index.get("files", {})) == {"collision_policy", "contract_summary", "installation_contract", "installed_owned_paths", "operation_order", "registry_template", "structural_paths"})

    primary = work / "primary"
    r1 = save("01-runtime-install.json", tx.install(contract, primary, "runtime-base", None))
    r2 = save("02-runtime-verify.json", tx.verify(primary))
    r3 = save("03-development-install.json", tx.install(contract, primary, "development-addon", None))
    r4 = save("04-test-install.json", tx.install(contract, primary, "test-addon", None))
    r5 = save("05-composed-verify.json", tx.verify(primary))
    check("fresh_runtime_install_pass", r1.get("pass") is True)
    check("fresh_runtime_install_create_714", r1.get("action_counts") == {"create": 714})
    check("fresh_runtime_registry_714", r2.get("pass") is True and r2.get("artifact_count") == 1 and r2.get("owned_path_count") == 714)
    check("development_install_pass", r3.get("pass") is True)
    check("development_install_create_454", r3.get("action_counts") == {"create": 454})
    check("test_install_pass", r4.get("pass") is True)
    check("test_install_create_1788", r4.get("action_counts") == {"create": 1788})
    check("composed_registry_2956", r5.get("pass") is True and r5.get("artifact_count") == 3 and r5.get("owned_path_count") == 2956)

    before = fingerprint(primary)
    try:
        tx.uninstall(contract, primary, "runtime-base", None)
        blocked = {"pass": True, "unexpected": True}
    except Exception as exc:
        blocked = {"pass": False, "preflight_failure": True, "error": repr(exc)}
    save("06-runtime-uninstall-blocked.json", blocked)
    check("runtime_uninstall_with_addons_blocked", blocked.get("preflight_failure") is True and "dependent addons installed" in blocked.get("error", ""))
    check("blocked_runtime_uninstall_no_mutation", before == fingerprint(primary))

    before = fingerprint(primary)
    noop = save("07-runtime-noop-reinstall.json", tx.install(contract, primary, "runtime-base", None))
    check("runtime_reinstall_noop_pass", noop.get("pass") is True and noop.get("noop") is True)
    check("runtime_reinstall_noop_714", noop.get("action_counts") == {"noop": 714})
    check("runtime_reinstall_zero_mutations", noop.get("mutation_count") == 0)
    check("runtime_reinstall_noop_fingerprint_unchanged", before == fingerprint(primary))

    runtime_regular = first_regular(primary, "runtime-base")
    (primary / "prefix" / runtime_regular).write_bytes(b"corrupted-runtime-entry\n")
    corrupted = save("08-corrupted-runtime-verify.json", tx.verify(primary))
    repair = save("09-runtime-repair.json", tx.install(contract, primary, "runtime-base", None))
    repaired = save("10-runtime-repaired-verify.json", tx.verify(primary))
    check("corruption_detected_exactly_one", corrupted.get("pass") is False and corrupted.get("bad_paths") == [runtime_regular])
    check("runtime_repair_pass", repair.get("pass") is True)
    check("runtime_repair_one_path", repair.get("action_counts") == {"noop": 713, "repair": 1})
    check("runtime_repair_two_mutations", repair.get("mutation_count") == 2)
    check("runtime_repair_restores_composed_registry", repaired.get("pass") is True and repaired.get("owned_path_count") == 2956)

    before = fingerprint(primary)
    failed_uninstall = save("11-test-uninstall-injected-failure.json", tx.uninstall(contract, primary, "test-addon", 5))
    uninstall_journal = readj(Path(failed_uninstall["transaction"]) / "journal.json")
    rollback_verify = save("12-test-uninstall-rollback-verify.json", tx.verify(primary))
    check("uninstall_failure_injected_after_5", failed_uninstall.get("pass") is False and failed_uninstall.get("rolled_back") is True and failed_uninstall.get("mutation_count") == 5)
    check("uninstall_rollback_journal_state", uninstall_journal.get("state") == "ROLLED_BACK")
    check("uninstall_rollback_fingerprint_exact", before == fingerprint(primary))
    check("uninstall_rollback_registry_2956", rollback_verify.get("pass") is True and rollback_verify.get("owned_path_count") == 2956)

    collision = work / "collision"
    (collision / "prefix/bin").mkdir(parents=True)
    for path in (collision / "prefix", collision / "prefix/bin"):
        os.chmod(path, 0o700)
    (collision / ".cpython-android-cli").mkdir()
    (collision / ".cpython-android-cli/lock").write_bytes(b"")
    os.chmod(collision / ".cpython-android-cli/lock", 0o600)
    collision_leaf = collision / "prefix/bin/python3.14"
    collision_leaf.write_bytes(b"unowned-collision-sentinel\n")
    before = fingerprint(collision)
    try:
        tx.install(contract, collision, "runtime-base", None)
        collision_result = {"pass": True, "unexpected": True}
    except Exception as exc:
        collision_result = {"pass": False, "preflight_failure": True, "error": repr(exc)}
    save("13-unowned-collision.json", collision_result)
    check("unowned_leaf_collision_blocked", collision_result.get("preflight_failure") is True and "unowned collision bin/python3.14" in collision_result.get("error", ""))
    check("unowned_collision_no_mutation", before == fingerprint(collision))
    check("unowned_collision_registry_absent", not (collision / ".cpython-android-cli/registry.json").exists())
    check("unowned_collision_sentinel_exact", collision_leaf.read_bytes() == b"unowned-collision-sentinel\n")

    prerequisite = work / "prerequisite"
    (prerequisite / "prefix").mkdir(parents=True)
    (prerequisite / ".cpython-android-cli").mkdir()
    (prerequisite / ".cpython-android-cli/lock").write_bytes(b"")
    before = fingerprint(prerequisite)
    try:
        tx.install(contract, prerequisite, "development-addon", None)
        prerequisite_result = {"pass": True, "unexpected": True}
    except Exception as exc:
        prerequisite_result = {"pass": False, "preflight_failure": True, "error": repr(exc)}
    save("14-addon-prerequisite-rejection.json", prerequisite_result)
    check("addon_without_runtime_rejected", prerequisite_result.get("preflight_failure") is True and "prerequisite not installed" in prerequisite_result.get("error", ""))
    check("addon_prerequisite_rejection_no_mutation", before == fingerprint(prerequisite))
    check("addon_prerequisite_registry_absent", not (prerequisite / ".cpython-android-cli/registry.json").exists())

    install_rollback = work / "install-rollback"
    save("15-install-rollback-runtime.json", tx.install(contract, install_rollback, "runtime-base", None))
    before = fingerprint(install_rollback)
    failed_install = save("16-development-install-injected-failure.json", tx.install(contract, install_rollback, "development-addon", 5))
    install_journal = readj(Path(failed_install["transaction"]) / "journal.json")
    install_verify = save("17-development-install-rollback-verify.json", tx.verify(install_rollback))
    check("install_failure_injected_after_5", failed_install.get("pass") is False and failed_install.get("rolled_back") is True and failed_install.get("mutation_count") == 5)
    check("install_rollback_journal_state", install_journal.get("state") == "ROLLED_BACK")
    check("install_rollback_fingerprint_exact", before == fingerprint(install_rollback))
    check("install_rollback_runtime_registry_714", install_verify.get("pass") is True and install_verify.get("artifact_count") == 1 and install_verify.get("owned_path_count") == 714)

    test_regular = first_regular(primary, "test-addon")
    test_leaf = primary / "prefix" / test_regular
    test_leaf.write_bytes(b"locally-modified-test-entry\n")
    sentinel_relative = "lib/python3.14/unowned-sentinel.txt"
    sentinel = primary / "prefix" / sentinel_relative
    sentinel.write_bytes(b"sentinel-content\n")
    test_uninstall = save("18-test-uninstall.json", tx.uninstall(contract, primary, "test-addon", None))
    after_test = save("19-after-test-uninstall-verify.json", tx.verify(primary))
    check("test_uninstall_pass", test_uninstall.get("pass") is True)
    check("test_uninstall_modified_leaf_preserved", test_regular in test_uninstall.get("preserved", []) and test_leaf.read_bytes() == b"locally-modified-test-entry\n")
    check("test_uninstall_registry_1168", after_test.get("pass") is True and after_test.get("artifact_count") == 2 and after_test.get("owned_path_count") == 1168)
    check("test_uninstall_sentinel_preserved", sentinel.read_bytes() == b"sentinel-content\n")

    dev_uninstall = save("20-development-uninstall.json", tx.uninstall(contract, primary, "development-addon", None))
    after_dev = save("21-after-development-uninstall-verify.json", tx.verify(primary))
    runtime_uninstall = save("22-runtime-uninstall.json", tx.uninstall(contract, primary, "runtime-base", None))
    after_runtime = save("23-after-runtime-uninstall-verify.json", tx.verify(primary))
    check("development_uninstall_pass", dev_uninstall.get("pass") is True)
    check("development_uninstall_registry_714", after_dev.get("pass") is True and after_dev.get("artifact_count") == 1 and after_dev.get("owned_path_count") == 714)
    check("runtime_uninstall_pass", runtime_uninstall.get("pass") is True)
    check("runtime_uninstall_registry_zero", after_runtime.get("pass") is True and after_runtime.get("artifact_count") == 0 and after_runtime.get("owned_path_count") == 0)
    check("runtime_uninstall_owned_directories_preserved_nonempty", set(runtime_uninstall.get("preserved", [])) >= {"lib", "lib/python3.14"})
    check("runtime_uninstall_modified_test_leaf_preserved", test_leaf.read_bytes() == b"locally-modified-test-entry\n")
    check("runtime_uninstall_sentinel_preserved", sentinel.read_bytes() == b"sentinel-content\n")

    reinstall = save("24-runtime-reinstall-retained-directories.json", tx.install(contract, primary, "runtime-base", None))
    final_verify = save("25-final-primary-verify.json", tx.verify(primary))
    final_registry = registry(primary)
    check("runtime_reinstall_retained_directories_pass", reinstall.get("pass") is True)
    check("runtime_reinstall_reuses_two_directories", reinstall.get("action_counts") == {"create": 712, "reuse-dir": 2})
    check("runtime_reinstall_final_registry_714", final_verify.get("pass") is True and final_verify.get("artifact_count") == 1 and final_verify.get("owned_path_count") == 714)
    check("runtime_reinstall_final_artifact_exact", [item["artifact"] for item in final_registry["artifacts"]] == ["runtime-base"])
    check("runtime_reinstall_does_not_adopt_test_leaf", all(row["path"] != test_regular for row in final_registry["owned_paths"]) and test_leaf.read_bytes() == b"locally-modified-test-entry\n")
    check("runtime_reinstall_does_not_adopt_sentinel", all(row["path"] != sentinel_relative for row in final_registry["owned_paths"]) and sentinel.read_bytes() == b"sentinel-content\n")

    write_snapshot(output, "primary-final", primary)
    write_snapshot(output, "install-rollback-final", install_rollback)
    snapshots = output / "snapshots"
    (snapshots / "primary-uninstall-rollback-journal.json").write_bytes(cjson(uninstall_journal))
    (snapshots / "install-rollback-journal.json").write_bytes(cjson(install_journal))
    (snapshots / "preserved-unowned.json").write_bytes(cjson({"schema_version": 1, "modified_test_leaf": {"path": test_regular, "sha256": sha(test_leaf), "size": test_leaf.stat().st_size}, "sentinel": {"path": sentinel_relative, "sha256": sha(sentinel), "size": sentinel.stat().st_size}, "registered": False}))
    (snapshots / "collision-state.json").write_bytes(cjson({"schema_version": 1, "fingerprint": fingerprint(collision), "registry_exists": False, "sentinel_path": "bin/python3.14", "sentinel_sha256": sha(collision_leaf)}))
    (snapshots / "prerequisite-state.json").write_bytes(cjson({"schema_version": 1, "fingerprint": fingerprint(prerequisite), "registry_exists": False}))

    logs = sorted(path.name for path in output.glob("[0-9][0-9]-*.json"))
    check("scenario_log_count_25", len(logs) == 25)
    check("scenario_logs_canonical_json", all(path.read_bytes() == cjson(readj(path)) for path in output.glob("[0-9][0-9]-*.json")))
    check("work_roots_exact", {path.name for path in work.iterdir()} == {"primary", "collision", "prerequisite", "install-rollback"})
    if len(checks) != 61:
        raise RuntimeError(f"unexpected check count: {len(checks)}")

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "observed": {
            "primary_final_fingerprint": fingerprint(primary),
            "collision_final_fingerprint": fingerprint(collision),
            "prerequisite_final_fingerprint": fingerprint(prerequisite),
            "install_rollback_final_fingerprint": fingerprint(install_rollback),
            "primary_final_registry_sha256": sha(primary / ".cpython-android-cli/registry.json"),
            "scenario_logs": logs,
            "runtime_regular_repaired": runtime_regular,
            "modified_test_leaf_preserved": test_regular,
            "sentinel_path": sentinel_relative,
            "uninstall_rollback_transaction": failed_uninstall["transaction"],
            "install_rollback_transaction": failed_install["transaction"],
        },
        "claim_boundary": {
            "proved": "The isolated transaction prototype executes fresh composition, exact no-op reinstall, registered repair, prerequisite and collision preflight, install and uninstall rollback, exact artifact uninstall, modified-path preservation, sentinel preservation, and retained-directory reuse.",
            "not_proved": "Crash-process recovery, concurrent lock contention, upgrade or downgrade, durable directory fsync, or installed runtime behavior.",
        },
    }
    (output / "scenario.json").write_bytes(cjson(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    print("\nSTAGE3C_PHASE4_TRANSACTION_SCENARIOS=" + ("PASS" if result["pass"] else "FAIL"))
    if args.require_pass and not result["pass"]:
        return 41
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
