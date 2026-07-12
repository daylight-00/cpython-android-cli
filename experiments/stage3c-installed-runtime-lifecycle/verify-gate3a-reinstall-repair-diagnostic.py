#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_PHASE4_RESULT_INDEX = "878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce"
EXPECTED_PORTABLE_FINGERPRINT = "f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978"
SCENARIOS = {"exact-noop", "regular-bytes", "regular-mode", "symlink-target", "regular-wrong-type", "missing-regular", "missing-symlink"}
SUPPORTED = {"regular-bytes", "regular-mode", "symlink-target", "regular-wrong-type"}
MISSING = {"missing-regular", "missing-symlink"}


def cjson(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def readj(path: Path) -> dict[str, Any]:
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


def engine_result(results: Path, scenario: str, name: str) -> dict[str, Any]:
    return readj(results / "scenarios" / scenario / f"{name}.json")


def final_matches_candidate(scenario: dict[str, Any]) -> bool:
    candidate = scenario.get("candidate", {})
    final_path = scenario.get("final_path", {})
    if final_path.get("type") != candidate.get("type") or final_path.get("mode") != candidate.get("mode"):
        return False
    if candidate.get("type") == "regular":
        return final_path.get("size") == candidate.get("size") and final_path.get("sha256") == candidate.get("sha256")
    if candidate.get("type") == "symlink":
        return final_path.get("target") == candidate.get("symlink_target")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase4-results", required=True, type=Path)
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    phase4 = args.phase4_results.resolve()
    results = args.results_dir.resolve()
    output = args.output.resolve()

    accepted = readj(results / "accepted-inputs.json")
    summary = readj(results / "scenario-summary.json")
    clones = readj(results / "clone-separation.json")
    seed_install = readj(results / "seed/install.json")
    seed_verify = readj(results / "seed/verify.json")
    seed_identity = readj(results / "seed/identity.json")
    scenarios = {name: readj(results / "scenarios" / name / "scenario.json") for name in sorted(SCENARIOS)}

    required_files = {
        results / "accepted-inputs.json",
        results / "scenario-summary.json",
        results / "clone-separation.json",
        results / "seed/install.json",
        results / "seed/install.log",
        results / "seed/verify.json",
        results / "seed/verify.log",
        results / "seed/identity.json",
    }
    for name in SCENARIOS:
        base = results / "scenarios" / name
        required_files.add(base / "scenario.json")
        stages = ("install", "verify") if name == "exact-noop" else (("pre-verify", "install", "recover-1", "recover-2", "post-verify") if name in MISSING else ("pre-verify", "install", "post-verify"))
        for stage in stages:
            required_files.add(base / f"{stage}.json")
            required_files.add(base / f"{stage}.log")

    missing_files = sorted(str(path) for path in required_files if not path.is_file())
    candidate_paths = {name: value.get("candidate", {}).get("path") for name, value in scenarios.items() if name != "exact-noop"}

    noop = scenarios["exact-noop"]
    noop_install = engine_result(results, "exact-noop", "install")
    noop_verify = engine_result(results, "exact-noop", "verify")

    supported_checks: dict[str, bool] = {}
    for name in sorted(SUPPORTED):
        scenario = scenarios[name]
        relative = candidate_paths[name]
        pre = engine_result(results, name, "pre-verify")
        install = engine_result(results, name, "install")
        post = engine_result(results, name, "post-verify")
        supported_checks[name] = (
            scenario.get("classification") == "in-place-registered-repair-supported"
            and scenario.get("pre_verify", {}).get("result") == pre
            and scenario.get("operation", {}).get("result") == install
            and scenario.get("post_verify", {}).get("result") == post
            and pre.get("pass") is False
            and pre.get("bad_paths") == [relative]
            and install.get("pass") is True
            and install.get("noop") is False
            and install.get("action_counts") == {"noop": 713, "repair": 1}
            and install.get("mutation_count") == 2
            and post.get("pass") is True
            and post.get("bad_paths") == []
            and scenario.get("after", {}).get("portable", {}).get("fingerprint") == EXPECTED_PORTABLE_FINGERPRINT
            and scenario.get("before", {}).get("registry") == scenario.get("after", {}).get("registry")
            and scenario.get("after", {}).get("transactions") == []
            and final_matches_candidate(scenario)
        )

    missing_checks: dict[str, bool] = {}
    for name in sorted(MISSING):
        scenario = scenarios[name]
        relative = candidate_paths[name]
        pre = engine_result(results, name, "pre-verify")
        install = engine_result(results, name, "install")
        recover1 = engine_result(results, name, "recover-1")
        recover2 = engine_result(results, name, "recover-2")
        post = engine_result(results, name, "post-verify")
        before_recover = scenario.get("transactions_before_recover", [])
        after_recover1 = scenario.get("transactions_after_recover_1", [])
        after_recover2 = scenario.get("transactions_after_recover_2", [])
        missing_checks[name] = (
            scenario.get("classification") == "missing-leaf-repair-unsupported"
            and pre.get("pass") is False
            and pre.get("bad_paths") == [relative]
            and install.get("pass") is False
            and "FileNotFoundError" in install.get("error", "")
            and len(before_recover) == 1
            and before_recover[0].get("state") == "APPLYING"
            and recover1.get("pass") is True
            and recover1.get("transaction_count") == 1
            and recover1.get("actions", [{}])[0].get("action") == "ROLLED_BACK"
            and len(after_recover1) == 1
            and after_recover1[0].get("state") == "ROLLED_BACK"
            and recover2.get("pass") is True
            and recover2.get("transaction_count") == 1
            and recover2.get("actions", [{}])[0].get("action") == "NOOP_ROLLED_BACK"
            and after_recover2 == after_recover1
            and post.get("pass") is False
            and post.get("bad_paths") == [relative]
            and scenario.get("final_path", {}).get("type") == "absent"
            and scenario.get("registry_row_present") is True
        )

    canonical_paths = [path for path in required_files if path.suffix == ".json"]
    checks = {
        "required_outputs_present": not missing_files,
        "accepted_phase4_file_exact": sha256_file(phase4 / "result-index.json") == EXPECTED_PHASE4_RESULT_INDEX,
        "accepted_evidence_exact": accepted.get("pass") is True and accepted.get("observed_result_index_sha256") == EXPECTED_PHASE4_RESULT_INDEX,
        "scenario_names_exact": set(scenarios) == SCENARIOS and set(summary.get("scenario_names", [])) == SCENARIOS,
        "summary_check_count_17": summary.get("check_count") == 17,
        "clone_summary_pass": clones.get("pass") is True,
        "clone_scenarios_exact": set(clones.get("scenarios", {})) == SCENARIOS,
        "clone_all_inode_separate": all(row.get("root_inode_separate") is True and row.get("registry_inode_separate") is True and row.get("probe_inode_separate") is True for row in clones.get("scenarios", {}).values()),
        "seed_install_exact": seed_install.get("pass") is True and seed_install.get("noop") is False and seed_install.get("action_counts") == {"create": 714} and seed_install.get("mutation_count") == 715,
        "seed_verify_exact": seed_verify.get("pass") is True and seed_verify.get("artifact_count") == 1 and seed_verify.get("owned_path_count") == 714 and seed_verify.get("bad_paths") == [],
        "seed_portable_exact": seed_identity.get("portable", {}).get("fingerprint") == EXPECTED_PORTABLE_FINGERPRINT,
        "seed_shape_exact": seed_identity.get("portable", {}).get("entry_count") == 714 and seed_identity.get("portable", {}).get("type_counts") == {"directory": 57, "regular": 654, "symlink": 3, "special": 0},
        "seed_registry_exact": seed_identity.get("registry", {}).get("artifact_count") == 1 and seed_identity.get("registry", {}).get("owned_path_count") == 714,
        "seed_transactions_empty": seed_identity.get("transactions") == [],
        "noop_classification_exact": noop.get("classification") == "exact-same-version-noop",
        "noop_result_exact": noop_install.get("pass") is True and noop_install.get("noop") is True and noop_install.get("action_counts") == {"noop": 714} and noop_install.get("mutation_count") == 0,
        "noop_verify_exact": noop_verify.get("pass") is True and noop_verify.get("bad_paths") == [],
        "noop_identity_unchanged": noop.get("before") == noop.get("after"),
        "supported_names_exact": set(supported_checks) == SUPPORTED,
        "supported_all_exact": all(supported_checks.values()),
        "supported_count_four": sum(supported_checks.values()) == 4,
        "missing_names_exact": set(missing_checks) == MISSING,
        "missing_all_expected_failure": all(missing_checks.values()),
        "missing_count_two": sum(missing_checks.values()) == 2,
        "regular_candidate_consistent": candidate_paths["regular-bytes"] == candidate_paths["regular-mode"] == candidate_paths["regular-wrong-type"] == candidate_paths["missing-regular"],
        "symlink_candidate_consistent": candidate_paths["symlink-target"] == candidate_paths["missing-symlink"],
        "classification_set_exact": set(summary.get("classifications", {}).values()) == {"exact-same-version-noop", "in-place-registered-repair-supported", "missing-leaf-repair-unsupported"},
        "raw_and_embedded_engine_results_match": all(scenarios[name].get("operation", {}).get("result") == engine_result(results, name, "install") for name in SCENARIOS),
        "machine_json_canonical": not missing_files and all(path.read_bytes() == cjson(readj(path)) for path in canonical_paths),
        "diagnostic_summary_pass": summary.get("pass") is True and summary.get("failed_checks") == [],
        "diagnostic_not_product_acceptance": "product acceptance" in summary.get("claim_boundary", {}).get("not_proved", "").lower(),
    }
    if len(checks) != 31:
        raise RuntimeError(f"unexpected verifier check count: {len(checks)}")

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "missing_files": missing_files,
        "supported_repairs": supported_checks,
        "missing_leaf_observations": missing_checks,
        "observed": {
            "regular_candidate": candidate_paths["regular-bytes"],
            "symlink_candidate": candidate_paths["symlink-target"],
            "portable_fingerprint": seed_identity.get("portable", {}).get("fingerprint"),
        },
        "claim_boundary": {
            "proved": "The diagnostic evidence matches the frozen engine's exact NOOP, in-place repair, and missing-leaf failure/recovery classifications.",
            "not_proved": "Gate 3A product acceptance and missing-leaf repair remain unproved.",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(cjson(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 72


if __name__ == "__main__":
    raise SystemExit(main())
