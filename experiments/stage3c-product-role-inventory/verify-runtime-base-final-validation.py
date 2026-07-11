#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json_safe(
    path: Path,
    missing: list[str],
    errors: dict[str, str],
) -> dict[str, Any]:
    if not path.is_file():
        missing.append(str(path))
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors[str(path)] = repr(exc)
        return {}
    if not isinstance(value, dict):
        errors[str(path)] = "top-level JSON is not an object"
        return {}
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-component-manifest", required=True)
    parser.add_argument("--expected-runtime-fingerprint", required=True)
    parser.add_argument("--expected-canonical-fingerprint", required=True)
    args = parser.parse_args()

    results = args.results_dir.resolve()
    output = args.output.resolve()
    missing: list[str] = []
    errors: dict[str, str] = {}

    workflow = read_json_safe(results / "workflow-status.json", missing, errors)
    input_verification = read_json_safe(
        results / "input-verification.json", missing, errors
    )
    closure = read_json_safe(
        results / "closure" / "runtime-base-closure-verification.json",
        missing,
        errors,
    )
    relocation_engine = read_json_safe(
        results / "relocation" / "promoted-relocation-verification.json",
        missing,
        errors,
    )
    relocation = read_json_safe(
        results / "relocation" / "runtime-base-relocation-verification.json",
        missing,
        errors,
    )

    returncodes = workflow.get("returncodes", {})
    expected_returncode_keys = {
        "input_verification",
        "closure_workflow",
        "closure_verification",
        "relocation_workflow",
        "relocation_engine_verification",
        "relocation_verification",
    }
    closure_expected = closure.get("expected", {})
    closure_observed = closure.get("observed", {})
    extension_probe = closure_observed.get("extension_import_probe", {})
    inventory = closure_observed.get("inventory", {})
    fidelity = relocation.get("fidelity", {})

    checks: dict[str, bool] = {
        "all_required_outputs_present": not missing,
        "all_required_outputs_parse": not errors,
        "workflow_schema": workflow.get("schema_version") == 1,
        "workflow_pass": workflow.get("pass") is True,
        "workflow_returncode_keys_exact": set(returncodes)
        == expected_returncode_keys,
        "workflow_returncodes_zero": bool(returncodes)
        and all(value == 0 for value in returncodes.values()),
        "input_schema": input_verification.get("schema_version") == 1,
        "input_pass": input_verification.get("pass") is True,
        "input_check_count_47": input_verification.get("check_count") == 47,
        "input_failed_checks_empty": input_verification.get("failed_checks")
        == [],
        "input_component_manifest": input_verification.get("expected", {}).get(
            "component_manifest_sha256"
        )
        == args.expected_component_manifest,
        "input_runtime_fingerprint": input_verification.get("expected", {}).get(
            "runtime_fingerprint"
        )
        == args.expected_runtime_fingerprint,
        "input_canonical_fingerprint": input_verification.get("expected", {}).get(
            "canonical_fingerprint"
        )
        == args.expected_canonical_fingerprint,
        "closure_schema": closure.get("schema_version") == 1,
        "closure_pass": closure.get("pass") is True,
        "closure_check_count_63": closure.get("check_count") == 63,
        "closure_failed_checks_empty": closure.get("failed_checks") == [],
        "closure_missing_outputs_empty": closure.get("missing_outputs") == [],
        "closure_parse_errors_empty": closure.get("parse_errors") == {},
        "closure_runtime_entries_714": closure_expected.get("runtime_entries")
        == 714,
        "closure_symlinks_3": closure_expected.get("symlinks") == 3,
        "closure_elf_objects_81": inventory.get("elf_object_count") == 81,
        "closure_needed_edges_329": inventory.get("needed_edge_count") == 329,
        "closure_unresolved_zero": inventory.get("unresolved_edge_count") == 0,
        "extension_candidates_67": extension_probe.get(
            "extension_candidate_count"
        )
        == 67,
        "extension_imports_67": extension_probe.get("import_pass_count") == 67,
        "extension_import_failures_zero": extension_probe.get(
            "import_fail_count"
        )
        == 0,
        "relocation_engine_schema": relocation_engine.get("schema_version") == 2,
        "relocation_engine_pass": relocation_engine.get("pass") is True,
        "relocation_engine_check_count_31": relocation_engine.get("check_count")
        == 31,
        "relocation_engine_failed_checks_empty": relocation_engine.get(
            "failed_checks"
        )
        == [],
        "relocation_engine_missing_outputs_empty": relocation_engine.get(
            "missing_outputs"
        )
        == [],
        "relocation_engine_parse_errors_empty": relocation_engine.get(
            "parse_errors"
        )
        == {},
        "relocation_schema": relocation.get("schema_version") == 1,
        "relocation_pass": relocation.get("pass") is True,
        "relocation_check_count_60": relocation.get("check_count") == 60,
        "relocation_failed_checks_empty": relocation.get("failed_checks") == [],
        "relocation_missing_outputs_empty": relocation.get("missing_outputs")
        == [],
        "relocation_parse_errors_empty": relocation.get("parse_errors") == {},
        "relocation_source_entries_714": fidelity.get("source_entry_count")
        == 714,
        "relocation_target_entries_714": fidelity.get(
            "relocated_entry_count"
        )
        == 714,
        "relocation_portable_pass": fidelity.get("portable_pass") is True,
        "relocation_added_zero": fidelity.get("added_count") == 0,
        "relocation_removed_zero": fidelity.get("removed_count") == 0,
        "relocation_changed_zero": fidelity.get("portable_changed_count") == 0,
        "relocation_pycache_zero": fidelity.get("pycache_path_count") == 0,
        "relocation_portable_fingerprints_equal": fidelity.get(
            "source_portable_fingerprint"
        )
        == fidelity.get("relocated_portable_fingerprint"),
    }

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "missing_outputs": sorted(set(missing)),
        "parse_errors": errors,
        "expected": {
            "component_manifest_sha256": args.expected_component_manifest,
            "runtime_fingerprint": args.expected_runtime_fingerprint,
            "canonical_fingerprint": args.expected_canonical_fingerprint,
        },
        "workflow": workflow,
        "input_verification": input_verification,
        "closure_verification": closure,
        "relocation_engine_verification": relocation_engine,
        "relocation_verification": relocation,
        "summary": {
            "runtime_entries": closure_expected.get("runtime_entries"),
            "symlinks": closure_expected.get("symlinks"),
            "elf_objects": inventory.get("elf_object_count"),
            "needed_edges": inventory.get("needed_edge_count"),
            "unresolved_edges": inventory.get("unresolved_edge_count"),
            "extension_candidates": extension_probe.get(
                "extension_candidate_count"
            ),
            "extension_import_passes": extension_probe.get("import_pass_count"),
            "relocated_entries": fidelity.get("relocated_entry_count"),
            "relocation_portable_fingerprint": fidelity.get(
                "relocated_portable_fingerprint"
            ),
        },
        "claim_boundary": {
            "proved": (
                "The selected 714-entry runtime-base retains the frozen native "
                "closure, imports all 67 extension modules, and passes production-"
                "shape whole-prefix relocation with exact portable fidelity."
            ),
            "not_proved": (
                "The distribution archive bytes, compression profile, extraction "
                "contract, and installer transaction semantics are frozen."
            ),
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 22


if __name__ == "__main__":
    raise SystemExit(main())
