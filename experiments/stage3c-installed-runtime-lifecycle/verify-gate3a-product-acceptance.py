#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PHASE4_INDEX = "878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce"
PHASE4I_INDEX = "7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6"
STRICT = "9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796"
PORTABLE = "f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978"
REPAIRS = [
    "regular-bytes",
    "regular-mode",
    "regular-wrong-type",
    "symlink-target",
    "missing-regular",
    "missing-symlink",
]


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


def same_path(value: object, expected: Path) -> bool:
    return isinstance(value, str) and Path(value).resolve() == expected.resolve()


def path_within(value: object, root: Path) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        Path(value).resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def final_matches(row: dict[str, Any]) -> bool:
    final = row.get("final_path", {})
    candidate = row.get("candidate", {})
    if final.get("type") != candidate.get("type") or final.get("mode") != candidate.get("mode"):
        return False
    if candidate.get("type") == "regular":
        return final.get("size") == candidate.get("size") and final.get("sha256") == candidate.get("sha256")
    if candidate.get("type") == "symlink":
        return final.get("target") == candidate.get("symlink_target")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase4-results", required=True, type=Path)
    parser.add_argument("--phase4i-results", required=True, type=Path)
    parser.add_argument("--scenario-results", required=True, type=Path)
    parser.add_argument("--runtime-results", required=True, type=Path)
    parser.add_argument("--gate1-verification", required=True, type=Path)
    parser.add_argument("--input-before", required=True, type=Path)
    parser.add_argument("--input-after", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    phase4 = args.phase4_results.resolve()
    phase4i = args.phase4i_results.resolve()
    scenarios_root = args.scenario_results.resolve()
    runtime_root = args.runtime_results.resolve()
    output = args.output.resolve()

    scenario_summary = read_json(scenarios_root / "scenario-summary.json")
    accepted = read_json(scenarios_root / "accepted-inputs.json")
    clones = read_json(scenarios_root / "clone-separation.json")
    sequential = read_json(scenarios_root / "sequential/summary.json")
    gate1 = read_json(args.gate1_verification.resolve())
    engine = read_json(runtime_root / "engine-verification.json")
    registry = read_json(runtime_root / "registry.json")
    strict_before = read_json(runtime_root / "installed-before.json")
    strict_after = read_json(runtime_root / "installed-after.json")
    portable_before = read_json(runtime_root / "installed-portable-before.json")
    portable_after = read_json(runtime_root / "installed-portable-after.json")
    base = read_json(runtime_root / "base-probe.json")
    venv = read_json(runtime_root / "smoke/venv-probe.json")
    uv_run = read_json(runtime_root / "smoke/uv-run-probe.json")
    closure_workflow = read_json(runtime_root / "closure/workflow-status.json")
    inventory = read_json(runtime_root / "closure/summary.json")
    closure = read_json(runtime_root / "closure/closure-analysis-summary.json")
    system_probe = read_json(runtime_root / "closure/system-soname-probe-summary.json")
    extension_probe = read_json(runtime_root / "closure/extension-import-probe-summary.json")
    input_before = read_json(args.input_before.resolve())
    input_after = read_json(args.input_after.resolve())
    smoke_text = (runtime_root / "smoke.log").read_text(encoding="utf-8")

    sequential_root = Path(scenario_summary["sequential_root"]).resolve()
    prefix = sequential_root / "prefix"

    isolated: dict[str, dict[str, Any]] = {
        "exact-noop": read_json(scenarios_root / "isolated/exact-noop/scenario.json")
    }
    for name in REPAIRS:
        isolated[name] = read_json(scenarios_root / "isolated" / name / "scenario.json")

    sequential_steps: dict[str, dict[str, Any]] = {}
    for index, name in enumerate(REPAIRS, start=1):
        sequential_steps[name] = read_json(scenarios_root / "sequential" / f"{index:02d}-{name}" / "scenario.json")

    required = {
        scenarios_root / "scenario-summary.json",
        scenarios_root / "accepted-inputs.json",
        scenarios_root / "clone-separation.json",
        scenarios_root / "sequential/install.json",
        scenarios_root / "sequential/install-process.json",
        scenarios_root / "sequential/noop.json",
        scenarios_root / "sequential/noop-process.json",
        scenarios_root / "sequential/final-verify.json",
        scenarios_root / "sequential/final-verify-process.json",
        scenarios_root / "sequential/summary.json",
        runtime_root / "engine-verification.json",
        runtime_root / "registry.json",
        runtime_root / "installed-before.json",
        runtime_root / "installed-after.json",
        runtime_root / "installed-portable-before.json",
        runtime_root / "installed-portable-after.json",
        runtime_root / "base-probe.json",
        runtime_root / "smoke/venv-probe.json",
        runtime_root / "smoke/uv-run-probe.json",
        runtime_root / "closure/workflow-status.json",
        runtime_root / "closure/summary.json",
        runtime_root / "closure/closure-analysis-summary.json",
        runtime_root / "closure/system-soname-probe-summary.json",
        runtime_root / "closure/extension-import-probe-summary.json",
        args.gate1_verification.resolve(),
        args.input_before.resolve(),
        args.input_after.resolve(),
    }
    for name in isolated:
        base_dir = scenarios_root / "isolated" / name
        required.add(base_dir / "scenario.json")
        stages = ("install", "verify") if name == "exact-noop" else ("pre-verify", "install", "post-verify")
        for stage in stages:
            required.add(base_dir / f"{stage}.json")
            required.add(base_dir / f"{stage}-process.json")
    for index, name in enumerate(REPAIRS, start=1):
        base_dir = scenarios_root / "sequential" / f"{index:02d}-{name}"
        required.add(base_dir / "scenario.json")
        for stage in ("pre-verify", "install", "post-verify"):
            required.add(base_dir / f"{stage}.json")
            required.add(base_dir / f"{stage}-process.json")

    missing_files = sorted(str(path) for path in required if not path.is_file())
    repair_rows = [isolated[name] for name in REPAIRS]
    sequential_rows = [sequential_steps[name] for name in REPAIRS]

    raw_embedded_match = True
    noop = isolated["exact-noop"]
    raw_embedded_match &= read_json(scenarios_root / "isolated/exact-noop/install-process.json") == noop["install"]
    raw_embedded_match &= read_json(scenarios_root / "isolated/exact-noop/verify-process.json") == noop["verify"]
    for name, row in [(name, isolated[name]) for name in REPAIRS]:
        directory = scenarios_root / "isolated" / name
        raw_embedded_match &= read_json(directory / "pre-verify-process.json") == row["pre_verify"]
        raw_embedded_match &= read_json(directory / "install-process.json") == row["install"]
        raw_embedded_match &= read_json(directory / "post-verify-process.json") == row["post_verify"]
    for index, name in enumerate(REPAIRS, start=1):
        row = sequential_steps[name]
        directory = scenarios_root / "sequential" / f"{index:02d}-{name}"
        raw_embedded_match &= read_json(directory / "pre-verify-process.json") == row["pre_verify"]
        raw_embedded_match &= read_json(directory / "install-process.json") == row["install"]
        raw_embedded_match &= read_json(directory / "post-verify-process.json") == row["post_verify"]

    generated_jsons = [path for path in required if path.suffix == ".json"]

    checks = {
        "required_outputs_present": not missing_files,
        "phase4_result_index_exact": sha256_file(phase4 / "result-index.json") == PHASE4_INDEX,
        "phase4i_result_index_exact": sha256_file(phase4i / "result-index.json") == PHASE4I_INDEX,
        "accepted_inputs_exact": accepted.get("pass") is True
        and accepted.get("phase4_observed") == PHASE4_INDEX
        and accepted.get("phase4i_observed") == PHASE4I_INDEX,
        "scenario_summary_29": scenario_summary.get("pass") is True
        and scenario_summary.get("check_count") == 29
        and scenario_summary.get("failed_checks") == [],
        "clone_separation_pass": clones.get("pass") is True,
        "isolated_names_exact": set(isolated) == {"exact-noop", *REPAIRS},
        "isolated_all_pass": all(row.get("pass") is True for row in isolated.values()),
        "isolated_noop_exact": noop["install"]["returncode"] == 0
        and noop["install"]["result"].get("action_counts") == {"noop": 714}
        and noop["install"]["result"].get("mutation_count") == 0
        and noop["before"] == noop["after"],
        "isolated_repairs_six": len(repair_rows) == 6,
        "isolated_existing_repairs_four": all(isolated[name].get("pass") is True for name in REPAIRS[:4]),
        "isolated_missing_repairs_two": isolated["missing-regular"].get("pass") is True
        and isolated["missing-symlink"].get("pass") is True,
        "isolated_preverify_exact": all(
            row["pre_verify"]["returncode"] == 44
            and row["pre_verify"]["result"].get("bad_paths") == [row["candidate"]["path"]]
            for row in repair_rows
        ),
        "isolated_install_exact": all(
            row["install"]["returncode"] == 0
            and row["install"]["result"].get("action_counts") == {"noop": 713, "repair": 1}
            and row["install"]["result"].get("mutation_count") == 2
            for row in repair_rows
        ),
        "isolated_postverify_exact": all(
            row["post_verify"]["returncode"] == 0
            and row["post_verify"]["result"].get("bad_paths") == []
            for row in repair_rows
        ),
        "isolated_final_candidates_exact": all(final_matches(row) for row in repair_rows),
        "isolated_registry_unchanged": all(row["before"]["registry"] == row["after"]["registry"] for row in repair_rows),
        "isolated_unaffected_exact": all(row["unaffected_before"] == row["unaffected_after"] for row in repair_rows),
        "isolated_strict_exact": all(row["after"]["strict"]["result"].get("fingerprint") == STRICT for row in repair_rows),
        "isolated_portable_exact": all(row["after"]["portable"]["result"].get("fingerprint") == PORTABLE for row in repair_rows),
        "isolated_transactions_empty": all(row["after"]["transactions"] == [] for row in isolated.values()),
        "sequential_summary_pass": sequential.get("pass") is True,
        "sequential_install_exact": sequential["install"]["returncode"] == 0
        and sequential["install"]["result"].get("action_counts") == {"create": 714}
        and sequential["install"]["result"].get("mutation_count") == 715,
        "sequential_noop_exact": sequential["noop"]["returncode"] == 0
        and sequential["noop"]["result"].get("action_counts") == {"noop": 714}
        and sequential["noop"]["result"].get("mutation_count") == 0,
        "sequential_order_exact": scenario_summary.get("sequential_order") == REPAIRS,
        "sequential_steps_six": len(sequential_rows) == 6,
        "sequential_all_pass": all(row.get("pass") is True for row in sequential_rows),
        "sequential_preverify_exact": all(
            row["pre_verify"]["returncode"] == 44
            and row["pre_verify"]["result"].get("bad_paths") == [row["candidate"]["path"]]
            for row in sequential_rows
        ),
        "sequential_install_repairs_exact": all(
            row["install"]["returncode"] == 0
            and row["install"]["result"].get("action_counts") == {"noop": 713, "repair": 1}
            and row["install"]["result"].get("mutation_count") == 2
            for row in sequential_rows
        ),
        "sequential_postverify_exact": all(
            row["post_verify"]["returncode"] == 0
            and row["post_verify"]["result"].get("bad_paths") == []
            for row in sequential_rows
        ),
        "sequential_final_candidates_exact": all(final_matches(row) for row in sequential_rows),
        "sequential_registry_unchanged_each": all(row["before"]["registry"] == row["after"]["registry"] for row in sequential_rows),
        "sequential_unaffected_exact_each": all(row["unaffected_before"] == row["unaffected_after"] for row in sequential_rows),
        "sequential_final_verify": sequential["final_verify"]["returncode"] == 0
        and sequential["final_verify"]["result"].get("bad_paths") == [],
        "sequential_final_strict": sequential["final_identity"]["strict"]["result"].get("fingerprint") == STRICT,
        "sequential_final_portable": sequential["final_identity"]["portable"]["result"].get("fingerprint") == PORTABLE,
        "sequential_transactions_empty": sequential["final_identity"]["transactions"] == [],
        "raw_process_outputs_match": raw_embedded_match,
        "gate1_regression_pass": gate1.get("pass") is True,
        "gate1_regression_80": gate1.get("check_count") == 80,
        "gate1_regression_failed_empty": gate1.get("failed_checks") == [],
        "gate1_regression_checks_all": all(gate1.get("checks", {}).values())
        and len(gate1.get("checks", {})) == 80,
        "engine_verify_pass": engine.get("pass") is True,
        "engine_verify_counts": engine.get("artifact_count") == 1
        and engine.get("owned_path_count") == 714
        and engine.get("bad_paths") == [],
        "registry_counts": len(registry.get("artifacts", [])) == 1
        and len(registry.get("owned_paths", [])) == 714,
        "strict_before_exact": strict_before.get("pass") is True
        and strict_before.get("fingerprint") == STRICT,
        "strict_after_exact": strict_after.get("pass") is True
        and strict_after.get("fingerprint") == STRICT,
        "strict_runtime_immutable": strict_before.get("fingerprint") == strict_after.get("fingerprint"),
        "portable_before_exact": portable_before.get("pass") is True
        and portable_before.get("fingerprint") == PORTABLE,
        "portable_after_exact": portable_after.get("pass") is True
        and portable_after.get("fingerprint") == PORTABLE,
        "portable_runtime_immutable": portable_before.get("fingerprint") == portable_after.get("fingerprint"),
        "base_probe_pass": base.get("pass") is True,
        "base_probe_identity": same_path(base.get("executable"), prefix / "bin/python")
        and same_path(base.get("prefix"), prefix)
        and same_path(base.get("base_prefix"), prefix),
        "base_probe_version_platform": base.get("version_info") == [3, 14, 6]
        and base.get("platform") == "android"
        and base.get("machine") == "aarch64",
        "base_probe_abi": base.get("soabi") == "cpython-314-aarch64-linux-android"
        and base.get("multiarch") == "aarch64-linux-android",
        "base_probe_sysconfig_within": bool(base.get("sysconfig_paths"))
        and all(path_within(value, prefix) for value in base.get("sysconfig_paths", {}).values()),
        "base_probe_https_200": base.get("https_status") == 200,
        "base_probe_imports": all(base.get("imports", {}).get(name) for name in ("ssl", "sqlite3", "bz2", "ctypes", "lzma", "zlib")),
        "venv_probe_pass": venv.get("pass") is True
        and same_path(venv.get("base_prefix"), prefix),
        "uv_run_probe_pass": uv_run.get("pass") is True
        and same_path(uv_run.get("base_prefix"), prefix)
        and uv_run.get("imports", {}).get("anyio") == "anyio",
        "smoke_markers": "STAGE2C_SMOKE=PASS" in smoke_text
        and "HTTPS status: 200" in smoke_text
        and "== uv venv ==" in smoke_text
        and "== uv run ==" in smoke_text,
        "closure_workflow_zero": closure_workflow.get("pass") is True
        and all(value == 0 for value in closure_workflow.get("returncodes", {}).values()),
        "closure_counts": inventory.get("elf_object_count") == 81
        and inventory.get("needed_edge_count") == 329
        and inventory.get("unresolved_edge_count") == 0,
        "closure_classes": inventory.get("classification_counts") == {"ANDROID_SYSTEM": 249, "RUNTIME_INTERNAL": 80}
        and closure.get("classification_edge_counts") == {"ANDROID_SYSTEM": 249, "RUNTIME_INTERNAL": 80},
        "system_soname_5_5": system_probe.get("unique_android_system_soname_count") == 5
        and system_probe.get("dlopen_pass_count") == 5
        and system_probe.get("dlopen_fail_count") == 0,
        "extension_imports_67_67": extension_probe.get("extension_candidate_count") == 67
        and extension_probe.get("import_pass_count") == 67
        and extension_probe.get("import_fail_count") == 0,
        "input_identity_unchanged": input_before.get("pass") is True
        and input_after.get("pass") is True
        and input_before.get("entry_count") == input_after.get("entry_count")
        and input_before.get("fingerprint") == input_after.get("fingerprint"),
        "machine_json_canonical": not missing_files
        and all(path.read_bytes() == cjson(read_json(path)) for path in generated_jsons),
        "claim_boundary_gate2_separate": "relocation" in scenario_summary.get("claim_boundary", {}).get("not_proved", "").lower()
        or "runtime behavior" in scenario_summary.get("claim_boundary", {}).get("not_proved", "").lower(),
    }
    if len(checks) != 69:
        raise RuntimeError(f"unexpected acceptance check count: {len(checks)}")

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "missing_files": missing_files,
        "observed": {
            "isolated_repair_count": len(repair_rows),
            "sequential_repair_count": len(sequential_rows),
            "gate1_regression_check_count": gate1.get("check_count"),
            "https_status": base.get("https_status"),
            "elf_object_count": inventory.get("elf_object_count"),
            "needed_edge_count": inventory.get("needed_edge_count"),
            "extension_import_pass_count": extension_probe.get("import_pass_count"),
        },
        "claim_boundary": {
            "proved": "The accepted corrected engine passed exact reinstall, all six registered repair classes, and the complete Gate 1 installed-runtime behavior contract after sequential repairs.",
            "not_proved": "Corrected-engine relocation, preservation boundaries, addon lifecycle, uninstall, upgrade, and downgrade remain separate gates.",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(cjson(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 92


if __name__ == "__main__":
    raise SystemExit(main())
