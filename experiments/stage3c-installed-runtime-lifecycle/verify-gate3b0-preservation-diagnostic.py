#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_GATE2R_INDEX = "69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c"
EXPECTED_CONTRACT_INDEX = "79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3"
EXPECTED_ENGINE_SHA = "33b55d94714fb96f401caefe0e72d6587da955a9d0c201f4eb18dfc5193eb87a"
EXPECTED_OPS_SHA = "61d20c68c7c5234a00328104914b83adc69859acca9791f3b14d9ff969e24021"
SCENARIOS = [
    "reinstall-owned-regular",
    "reinstall-owned-symlink",
    "reinstall-unowned-file",
    "reinstall-unowned-directory",
    "uninstall-owned-regular",
    "uninstall-owned-symlink",
    "uninstall-unowned-file",
    "uninstall-unowned-directory",
]
EXPECTED_CLASSIFICATIONS = {
    "reinstall-owned-regular": "ENFORCED_REPAIR",
    "reinstall-owned-symlink": "ENFORCED_REPAIR",
    "reinstall-unowned-file": "PRESERVED_NOOP",
    "reinstall-unowned-directory": "PRESERVED_NOOP",
    "uninstall-owned-regular": "PRESERVED_AND_DEREGISTERED",
    "uninstall-owned-symlink": "PRESERVED_AND_DEREGISTERED",
    "uninstall-unowned-file": "UNOWNED_PRESERVED",
    "uninstall-unowned-directory": "UNOWNED_PRESERVED",
}


def cjson(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def candidate_exact(row: dict[str, Any]) -> bool:
    subject = row.get("subject_after", {})
    candidate = row.get("candidate", {})
    if subject.get("type") != candidate.get("type") or subject.get("mode") != candidate.get("mode"):
        return False
    if candidate.get("type") == "regular":
        return subject.get("size") == candidate.get("size") and subject.get("sha256") == candidate.get("sha256")
    if candidate.get("type") == "symlink":
        return subject.get("target") == candidate.get("target")
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.results_dir.resolve()

    paths = {
        "authority": root / "accepted-authority.json",
        "summary": root / "scenario-summary.json",
        "clone": root / "clone-separation.json",
        "seed": root / "seed/summary.json",
        "seed_install_process": root / "seed/install-process.json",
        "seed_verify_process": root / "seed/verify-process.json",
        "gate2r_index": root / "input/gate2r-result-index.json",
        "gate2r_verification": root / "input/gate2r-verification.json",
        "gate2r_workflow": root / "input/gate2r-workflow-status.json",
        "historical": root / "input/historical-relocation-verification.json",
        "gate1_a": root / "input/gate1-a-verification.json",
        "gate1_b": root / "input/gate1-b-verification.json",
        "engine_authority": root / "input/gate2r-engine-authority.json",
        "contract_index": root / "input/contract/contract-index.json",
        "manifest": root / "input/contract/input/phase3/input/manifest-schema/manifests/runtime-base.manifest.json",
    }
    scenario_rows: dict[str, dict[str, Any]] = {}
    for name in SCENARIOS:
        paths[f"scenario:{name}"] = root / "scenarios" / name / "scenario.json"
        operation = "install" if name.startswith("reinstall-") else "uninstall"
        paths[f"process:{name}:{operation}"] = root / "scenarios" / name / f"{operation}-process.json"
        paths[f"process:{name}:verify"] = root / "scenarios" / name / "verify-process.json"

    missing = sorted(str(path) for path in paths.values() if not path.is_file())
    parse_errors: dict[str, str] = {}
    values: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        if not path.is_file():
            continue
        try:
            values[name] = read_json(path)
        except Exception as exc:
            parse_errors[str(path)] = repr(exc)

    authority = values.get("authority", {})
    summary = values.get("summary", {})
    clone = values.get("clone", {})
    seed = values.get("seed", {})
    gate2r_verification = values.get("gate2r_verification", {})
    gate2r_workflow = values.get("gate2r_workflow", {})
    historical = values.get("historical", {})
    gate1_a = values.get("gate1_a", {})
    gate1_b = values.get("gate1_b", {})
    engine_authority = values.get("engine_authority", {})
    for name in SCENARIOS:
        scenario_rows[name] = values.get(f"scenario:{name}", {})

    raw_match = True
    if seed:
        raw_match &= values.get("seed_install_process") == seed.get("install")
        raw_match &= values.get("seed_verify_process") == seed.get("verify")
    for name, row in scenario_rows.items():
        operation = "install" if name.startswith("reinstall-") else "uninstall"
        raw_match &= values.get(f"process:{name}:{operation}") == row.get(operation)
        raw_match &= values.get(f"process:{name}:verify") == row.get("verify")

    reinstall_owned = [scenario_rows[name] for name in SCENARIOS[:2]]
    reinstall_unowned = [scenario_rows[name] for name in SCENARIOS[2:4]]
    uninstall_owned = [scenario_rows[name] for name in SCENARIOS[4:6]]
    uninstall_unowned = [scenario_rows[name] for name in SCENARIOS[6:]]
    all_rows = [scenario_rows[name] for name in SCENARIOS]

    generated_jsons = [
        path for name, path in paths.items()
        if path.is_file() and not name.startswith("manifest")
    ]

    checks = {
        "all_required_outputs_present": not missing,
        "all_required_outputs_parse": not parse_errors,
        "accepted_gate2r_index_exact": paths["gate2r_index"].is_file() and sha256_file(paths["gate2r_index"]) == EXPECTED_GATE2R_INDEX,
        "authority_pass": authority.get("pass") is True,
        "authority_gate2r_exact": authority.get("gate2r_result_index_sha256") == EXPECTED_GATE2R_INDEX,
        "authority_engine_exact": authority.get("engine_sha256") == EXPECTED_ENGINE_SHA,
        "authority_operations_exact": authority.get("operations_sha256") == EXPECTED_OPS_SHA,
        "copied_contract_index_exact": paths["contract_index"].is_file() and sha256_file(paths["contract_index"]) == EXPECTED_CONTRACT_INDEX,
        "authority_contract_index_exact": authority.get("contract_index_sha256") == EXPECTED_CONTRACT_INDEX and authority.get("copied_contract_index_sha256") == EXPECTED_CONTRACT_INDEX,
        "gate2r_verification_15": gate2r_verification.get("pass") is True and gate2r_verification.get("check_count") == 15 and gate2r_verification.get("failed_checks") == [],
        "gate2r_workflow_zero": gate2r_workflow.get("pass") is True and bool(gate2r_workflow.get("returncodes")) and all(value == 0 for value in gate2r_workflow.get("returncodes", {}).values()),
        "historical_relocation_46": historical.get("pass") is True and historical.get("check_count") == 46 and historical.get("failed_checks") == [],
        "gate1_a_80": gate1_a.get("pass") is True and gate1_a.get("check_count") == 80 and gate1_a.get("failed_checks") == [],
        "gate1_b_80": gate1_b.get("pass") is True and gate1_b.get("check_count") == 80 and gate1_b.get("failed_checks") == [],
        "copied_engine_authority_exact": engine_authority.get("pass") is True and engine_authority.get("engine_sha256") == EXPECTED_ENGINE_SHA and engine_authority.get("operations_sha256") == EXPECTED_OPS_SHA,
        "seed_pass": seed.get("pass") is True,
        "seed_install_exact": seed.get("install", {}).get("returncode") == 0 and seed.get("install", {}).get("result", {}).get("action_counts") == {"create": 714} and seed.get("install", {}).get("result", {}).get("mutation_count") == 715,
        "seed_verify_exact": seed.get("verify", {}).get("returncode") == 0 and seed.get("verify", {}).get("result", {}).get("artifact_count") == 1 and seed.get("verify", {}).get("result", {}).get("owned_path_count") == 714 and seed.get("verify", {}).get("result", {}).get("bad_paths") == [],
        "clone_separation": clone.get("pass") is True and len(clone.get("scenarios", {})) == 8,
        "summary_16": summary.get("pass") is True and summary.get("check_count") == 16 and summary.get("failed_checks") == [],
        "scenario_order_exact": summary.get("scenario_order") == SCENARIOS,
        "classifications_exact": summary.get("classifications") == EXPECTED_CLASSIFICATIONS,
        "all_scenario_rows_pass": all(row.get("pass") is True for row in all_rows),
        "raw_process_outputs_match": raw_match,
        "reinstall_owned_repair_actions": all(row.get("install", {}).get("returncode") == 0 and row.get("install", {}).get("result", {}).get("action_counts") == {"noop": 713, "repair": 1} and row.get("install", {}).get("result", {}).get("mutation_count") == 2 for row in reinstall_owned),
        "reinstall_owned_restored": all(candidate_exact(row) and row.get("owned_digest_before") == row.get("owned_digest_after") for row in reinstall_owned),
        "reinstall_unowned_noop": all(row.get("install", {}).get("returncode") == 0 and row.get("install", {}).get("result", {}).get("noop") is True and row.get("install", {}).get("result", {}).get("action_counts") == {"noop": 714} and row.get("install", {}).get("result", {}).get("mutation_count") == 0 for row in reinstall_unowned),
        "reinstall_unowned_preserved": all(row.get("subject_before_operation") == row.get("subject_after") for row in reinstall_unowned),
        "reinstall_registry_unchanged": all(row.get("registry_before", {}).get("sha256") == row.get("registry_after", {}).get("sha256") for row in reinstall_owned + reinstall_unowned),
        "reinstall_verify_clean": all(row.get("verify", {}).get("returncode") == 0 and row.get("verify", {}).get("result", {}).get("bad_paths") == [] for row in reinstall_owned + reinstall_unowned),
        "uninstall_operations_pass": all(row.get("uninstall", {}).get("returncode") == 0 and row.get("uninstall", {}).get("result", {}).get("pass") is True for row in uninstall_owned + uninstall_unowned),
        "uninstall_owned_preserved_list": all(row.get("subject") in row.get("preserved_rows", []) for row in uninstall_owned),
        "uninstall_owned_subject_preserved": all(row.get("subject_before_operation") == row.get("subject_after") for row in uninstall_owned),
        "uninstall_unowned_subject_preserved": all(row.get("subject_before_operation") == row.get("subject_after") for row in uninstall_unowned),
        "uninstall_registry_empty": all(row.get("registry_after", {}).get("artifact_count") == 0 and row.get("registry_after", {}).get("owned_path_count") == 0 for row in uninstall_owned + uninstall_unowned),
        "uninstall_verify_empty_registry": all(row.get("verify", {}).get("returncode") == 0 and row.get("verify", {}).get("result", {}).get("artifact_count") == 0 and row.get("verify", {}).get("result", {}).get("owned_path_count") == 0 and row.get("verify", {}).get("result", {}).get("bad_paths") == [] for row in uninstall_owned + uninstall_unowned),
        "uninstall_remaining_leaves_exact": all(row.get("remaining_registered_leaves") == [row.get("subject")] for row in uninstall_owned) and all(row.get("remaining_registered_leaves") == [] for row in uninstall_unowned),
        "all_transactions_empty": all(row.get("transactions_after") == [] for row in all_rows),
        "generated_json_canonical": not missing and all(path.read_bytes() == cjson(read_json(path)) for path in generated_jsons),
        "diagnostic_claim_only": "No preservation policy is accepted" in summary.get("claim_boundary", {}).get("not_proved", ""),
    }
    if len(checks) != 40:
        raise RuntimeError(f"unexpected check count: {len(checks)}")
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": 40,
        "checks": checks,
        "failed_checks": failed,
        "missing_outputs": missing,
        "parse_errors": parse_errors,
        "observed": {
            "scenario_count": len(all_rows),
            "classifications": summary.get("classifications"),
            "gate2r_check_count": gate2r_verification.get("check_count"),
            "historical_relocation_check_count": historical.get("check_count"),
        },
        "claim_boundary": {
            "proved": "The current corrected engine behavior is independently classified for eight owned/unowned reinstall/uninstall preservation scenarios.",
            "not_proved": "This diagnostic does not accept a preservation policy, uninstall product contract, or crash-recovery behavior for preserved paths.",
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(cjson(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 102


if __name__ == "__main__":
    raise SystemExit(main())
