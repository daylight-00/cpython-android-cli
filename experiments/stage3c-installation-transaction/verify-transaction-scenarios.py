#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

import transaction_engine as engine

EXPECTED_CONTRACT_INDEX = "79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3"
EXPECTED_LOGS = [
    "01-runtime-install.json",
    "02-runtime-verify.json",
    "03-development-install.json",
    "04-test-install.json",
    "05-composed-verify.json",
    "06-runtime-uninstall-blocked.json",
    "07-runtime-noop-reinstall.json",
    "08-corrupted-runtime-verify.json",
    "09-runtime-repair.json",
    "10-runtime-repaired-verify.json",
    "11-test-uninstall-injected-failure.json",
    "12-test-uninstall-rollback-verify.json",
    "13-unowned-collision.json",
    "14-addon-prerequisite-rejection.json",
    "15-install-rollback-runtime.json",
    "16-development-install-injected-failure.json",
    "17-development-install-rollback-verify.json",
    "18-test-uninstall.json",
    "19-after-test-uninstall-verify.json",
    "20-development-uninstall.json",
    "21-after-development-uninstall-verify.json",
    "22-runtime-uninstall.json",
    "23-after-runtime-uninstall-verify.json",
    "24-runtime-reinstall-retained-directories.json",
    "25-final-primary-verify.json",
]


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint_installation(root: Path) -> str:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if relative.startswith(".cpython-android-cli/transactions/"):
            continue
        observed = path.lstat()
        mode = f"{stat.S_IMODE(observed.st_mode):04o}"
        if path.is_symlink():
            row = {"path": relative, "type": "symlink", "mode": mode, "target": os.readlink(path)}
        elif path.is_dir():
            row = {"path": relative, "type": "directory", "mode": mode}
        elif path.is_file():
            row = {
                "path": relative,
                "type": "regular",
                "mode": mode,
                "size": observed.st_size,
                "sha256": sha256_file(path),
            }
        else:
            row = {"path": relative, "type": "special", "mode": mode}
        rows.append(row)
    canonical = "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def transaction_journals(root: Path) -> list[dict[str, Any]]:
    txroot = root / ".cpython-android-cli/transactions"
    if not txroot.is_dir():
        return []
    return [read_json(path) for path in sorted(txroot.glob("*/journal.json"))]


def registry_matches(root: Path) -> dict[str, Any]:
    return engine.verify(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-results", required=True, type=Path)
    parser.add_argument("--scenario-results", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--input-before", required=True, type=Path)
    parser.add_argument("--input-after", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    contract_results = args.contract_results.resolve()
    results = args.scenario_results.resolve()
    work = args.work_root.resolve()
    scenario = read_json(results / "scenario.json")
    derivation = read_json(contract_results / "derivation.json")
    gate1_verification = read_json(contract_results / "verification.json")
    gate1_workflow = read_json(contract_results / "workflow-status.json")
    before = read_json(args.input_before.resolve())
    after = read_json(args.input_after.resolve())
    logs = {name: read_json(results / name) for name in EXPECTED_LOGS}

    primary = work / "primary"
    collision = work / "collision"
    prerequisite = work / "prerequisite"
    install_rollback = work / "install-rollback"
    primary_registry = engine.load_registry(primary / ".cpython-android-cli/registry.json")
    rollback_registry = engine.load_registry(install_rollback / ".cpython-android-cli/registry.json")
    primary_verify = registry_matches(primary)
    rollback_verify = registry_matches(install_rollback)
    primary_journals = transaction_journals(primary)
    install_journals = transaction_journals(install_rollback)
    observed = scenario["observed"]
    modified_test = primary / "prefix" / observed["modified_test_leaf_preserved"]
    sentinel = primary / "prefix" / observed["sentinel_path"]

    checks: dict[str, bool] = {
        "gate1_derivation_pass_54": derivation.get("pass") is True
        and derivation.get("check_count") == 54
        and derivation.get("failed_checks") == [],
        "gate1_verification_pass_59": gate1_verification.get("pass") is True
        and gate1_verification.get("check_count") == 59
        and gate1_verification.get("failed_checks") == [],
        "gate1_workflow_pass": gate1_workflow.get("pass") is True
        and all(value == 0 for value in gate1_workflow.get("returncodes", {}).values()),
        "gate1_contract_index_hash_exact": sha256_file(contract_results / "contract-index.json")
        == EXPECTED_CONTRACT_INDEX,
        "input_tree_fingerprint_unchanged": before.get("pass") is True
        and after.get("pass") is True
        and before.get("entry_count") == after.get("entry_count")
        and before.get("fingerprint") == after.get("fingerprint"),
        "scenario_pass_61": scenario.get("pass") is True
        and scenario.get("check_count") == 61
        and scenario.get("failed_checks") == [],
        "scenario_all_internal_checks_true": len(scenario.get("checks", {})) == 61
        and all(scenario["checks"].values()),
        "scenario_log_set_exact": sorted(path.name for path in results.glob("[0-9][0-9]-*.json"))
        == EXPECTED_LOGS,
        "scenario_logs_canonical_json": all(
            (results / name).read_bytes() == canonical_json_bytes(logs[name])
            for name in EXPECTED_LOGS
        ),
        "scenario_json_canonical": (results / "scenario.json").read_bytes()
        == canonical_json_bytes(scenario),
        "runtime_fresh_create_714": logs["01-runtime-install.json"].get("action_counts") == {"create": 714},
        "runtime_fresh_registry_714": logs["02-runtime-verify.json"].get("pass") is True
        and logs["02-runtime-verify.json"].get("owned_path_count") == 714,
        "development_fresh_create_454": logs["03-development-install.json"].get("action_counts") == {"create": 454},
        "test_fresh_create_1788": logs["04-test-install.json"].get("action_counts") == {"create": 1788},
        "composed_registry_2956": logs["05-composed-verify.json"].get("pass") is True
        and logs["05-composed-verify.json"].get("artifact_count") == 3
        and logs["05-composed-verify.json"].get("owned_path_count") == 2956,
        "runtime_uninstall_dependency_blocked": logs["06-runtime-uninstall-blocked.json"].get("preflight_failure") is True
        and "dependent addons installed" in logs["06-runtime-uninstall-blocked.json"].get("error", ""),
        "runtime_noop_714_zero_mutation": logs["07-runtime-noop-reinstall.json"].get("pass") is True
        and logs["07-runtime-noop-reinstall.json"].get("noop") is True
        and logs["07-runtime-noop-reinstall.json"].get("action_counts") == {"noop": 714}
        and logs["07-runtime-noop-reinstall.json"].get("mutation_count") == 0,
        "runtime_corruption_detected": logs["08-corrupted-runtime-verify.json"].get("pass") is False
        and logs["08-corrupted-runtime-verify.json"].get("bad_paths")
        == [observed["runtime_regular_repaired"]],
        "runtime_repair_exact": logs["09-runtime-repair.json"].get("pass") is True
        and logs["09-runtime-repair.json"].get("action_counts") == {"noop": 713, "repair": 1}
        and logs["09-runtime-repair.json"].get("mutation_count") == 2,
        "runtime_repair_registry_restored": logs["10-runtime-repaired-verify.json"].get("pass") is True
        and logs["10-runtime-repaired-verify.json"].get("owned_path_count") == 2956,
        "uninstall_failure_rollback_exact": logs["11-test-uninstall-injected-failure.json"].get("rolled_back") is True
        and logs["11-test-uninstall-injected-failure.json"].get("mutation_count") == 5,
        "uninstall_rollback_registry_restored": logs["12-test-uninstall-rollback-verify.json"].get("pass") is True
        and logs["12-test-uninstall-rollback-verify.json"].get("owned_path_count") == 2956,
        "collision_preflight_failure_exact": logs["13-unowned-collision.json"].get("preflight_failure") is True
        and "unowned collision bin/python3.14" in logs["13-unowned-collision.json"].get("error", ""),
        "prerequisite_preflight_failure_exact": logs["14-addon-prerequisite-rejection.json"].get("preflight_failure") is True
        and "prerequisite not installed" in logs["14-addon-prerequisite-rejection.json"].get("error", ""),
        "install_rollback_runtime_seed_714": logs["15-install-rollback-runtime.json"].get("pass") is True
        and logs["15-install-rollback-runtime.json"].get("action_counts") == {"create": 714},
        "install_failure_rollback_exact": logs["16-development-install-injected-failure.json"].get("rolled_back") is True
        and logs["16-development-install-injected-failure.json"].get("mutation_count") == 5,
        "install_rollback_registry_runtime_only": logs["17-development-install-rollback-verify.json"].get("pass") is True
        and logs["17-development-install-rollback-verify.json"].get("artifact_count") == 1
        and logs["17-development-install-rollback-verify.json"].get("owned_path_count") == 714,
        "test_uninstall_modified_leaf_reported": logs["18-test-uninstall.json"].get("pass") is True
        and observed["modified_test_leaf_preserved"] in logs["18-test-uninstall.json"].get("preserved", []),
        "test_uninstall_registry_1168": logs["19-after-test-uninstall-verify.json"].get("pass") is True
        and logs["19-after-test-uninstall-verify.json"].get("owned_path_count") == 1168,
        "development_uninstall_pass": logs["20-development-uninstall.json"].get("pass") is True,
        "development_uninstall_registry_714": logs["21-after-development-uninstall-verify.json"].get("pass") is True
        and logs["21-after-development-uninstall-verify.json"].get("owned_path_count") == 714,
        "runtime_uninstall_nonempty_dirs_reported": logs["22-runtime-uninstall.json"].get("pass") is True
        and set(logs["22-runtime-uninstall.json"].get("preserved", [])) >= {"lib", "lib/python3.14"},
        "runtime_uninstall_registry_zero": logs["23-after-runtime-uninstall-verify.json"].get("pass") is True
        and logs["23-after-runtime-uninstall-verify.json"].get("owned_path_count") == 0,
        "runtime_reinstall_reuses_two_directories": logs["24-runtime-reinstall-retained-directories.json"].get("pass") is True
        and logs["24-runtime-reinstall-retained-directories.json"].get("action_counts")
        == {"create": 712, "reuse-dir": 2},
        "final_primary_registry_714": logs["25-final-primary-verify.json"].get("pass") is True
        and logs["25-final-primary-verify.json"].get("artifact_count") == 1
        and logs["25-final-primary-verify.json"].get("owned_path_count") == 714,
        "final_primary_registry_matches_filesystem": primary_verify.get("pass") is True
        and primary_verify.get("owned_path_count") == 714,
        "final_primary_artifact_runtime_only": [item["artifact"] for item in primary_registry["artifacts"]]
        == ["runtime-base"],
        "final_primary_owned_paths_unique": len(primary_registry["owned_paths"])
        == len({row["path"] for row in primary_registry["owned_paths"]})
        == 714,
        "final_primary_registry_mode_0600": stat.S_IMODE((primary / ".cpython-android-cli/registry.json").stat().st_mode)
        == 0o600,
        "final_primary_lock_mode_0600": stat.S_IMODE((primary / ".cpython-android-cli/lock").stat().st_mode)
        == 0o600,
        "modified_test_leaf_preserved_exact": modified_test.read_bytes() == b"locally-modified-test-entry\n",
        "modified_test_leaf_unregistered": all(
            row["path"] != observed["modified_test_leaf_preserved"]
            for row in primary_registry["owned_paths"]
        ),
        "sentinel_preserved_exact": sentinel.read_bytes() == b"sentinel-content\n",
        "sentinel_unregistered": all(
            row["path"] != observed["sentinel_path"]
            for row in primary_registry["owned_paths"]
        ),
        "primary_final_fingerprint_exact": fingerprint_installation(primary)
        == observed["primary_final_fingerprint"],
        "primary_final_registry_hash_exact": sha256_file(primary / ".cpython-android-cli/registry.json")
        == observed["primary_final_registry_sha256"],
        "collision_final_fingerprint_exact": fingerprint_installation(collision)
        == observed["collision_final_fingerprint"],
        "collision_registry_absent": not (collision / ".cpython-android-cli/registry.json").exists(),
        "collision_sentinel_exact": (collision / "prefix/bin/python3.14").read_bytes()
        == b"unowned-collision-sentinel\n",
        "prerequisite_final_fingerprint_exact": fingerprint_installation(prerequisite)
        == observed["prerequisite_final_fingerprint"],
        "prerequisite_registry_absent": not (prerequisite / ".cpython-android-cli/registry.json").exists(),
        "install_rollback_final_fingerprint_exact": fingerprint_installation(install_rollback)
        == observed["install_rollback_final_fingerprint"],
        "install_rollback_registry_matches_filesystem": rollback_verify.get("pass") is True
        and rollback_verify.get("owned_path_count") == 714,
        "install_rollback_artifact_runtime_only": [item["artifact"] for item in rollback_registry["artifacts"]]
        == ["runtime-base"],
        "primary_rolled_back_journal_exact": len(primary_journals) == 1
        and primary_journals[0].get("operation") == "uninstall"
        and primary_journals[0].get("artifact") == "test-addon"
        and primary_journals[0].get("state") == "ROLLED_BACK",
        "install_rolled_back_journal_exact": len(install_journals) == 1
        and install_journals[0].get("operation") == "install"
        and install_journals[0].get("artifact") == "development-addon"
        and install_journals[0].get("state") == "ROLLED_BACK",
        "work_root_set_exact": {path.name for path in work.iterdir()}
        == {"primary", "collision", "prerequisite", "install-rollback"},
        "scenario_claim_boundary_exact": scenario.get("claim_boundary", {}).get("not_proved")
        == "Crash-process recovery, concurrent lock contention, upgrade or downgrade, durable directory fsync, or installed runtime behavior.",
    }

    failed = sorted(name for name, passed in checks.items() if not passed)
    if len(checks) != 58:
        raise RuntimeError(f"unexpected check count: {len(checks)}")
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "observed": {
            "primary_registry_owned_paths": len(primary_registry["owned_paths"]),
            "install_rollback_registry_owned_paths": len(rollback_registry["owned_paths"]),
            "primary_rolled_back_journals": len(primary_journals),
            "install_rolled_back_journals": len(install_journals),
            "scenario_check_count": scenario["check_count"],
            "scenario_log_count": len(EXPECTED_LOGS),
        },
        "claim_boundary": scenario["claim_boundary"],
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 42


if __name__ == "__main__":
    raise SystemExit(main())
