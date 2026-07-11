#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_OUTPUTS = (
    "workflow-status.txt",
    "candidate-runtime-mutation-check.txt",
    "frozen-runtime-mutation-check.txt",
    "relocated-runtime-fidelity-check.txt",
    "fidelity-diagnosis/tree-delta.json",
    "relocation-location-state.txt",
    "reconfirm/reconfirm.log",
    "promoted-relocation-verification.json",
    "relocated-fingerprint.json",
)


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


def read_key_values_safe(
    path: Path,
    missing: list[str],
    errors: dict[str, str],
) -> dict[str, str]:
    if not path.is_file():
        missing.append(str(path))
        return {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        errors[str(path)] = repr(exc)
        return {}
    result: dict[str, str] = {}
    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--input-verification", required=True, type=Path)
    parser.add_argument("--closure-verification", required=True, type=Path)
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--canonical-prefix", required=True, type=Path)
    parser.add_argument("--relocation-root", required=True, type=Path)
    parser.add_argument("--runtime-before", required=True, type=Path)
    parser.add_argument("--runtime-after", required=True, type=Path)
    parser.add_argument("--canonical-before", required=True, type=Path)
    parser.add_argument("--canonical-after", required=True, type=Path)
    parser.add_argument("--expected-runtime-fingerprint", required=True)
    parser.add_argument("--expected-canonical-fingerprint", required=True)
    args = parser.parse_args()

    results = args.results_dir.resolve()
    runtime_prefix = args.runtime_prefix.resolve()
    canonical_prefix = args.canonical_prefix.resolve()
    relocation_root = args.relocation_root.resolve()
    b_prefix = relocation_root / "location-b" / "prefix"
    missing: list[str] = []
    errors: dict[str, str] = {}

    for name in REQUIRED_OUTPUTS:
        path = results / name
        if not path.is_file():
            missing.append(str(path))

    input_verification = read_json_safe(
        args.input_verification.resolve(), missing, errors
    )
    closure_verification = read_json_safe(
        args.closure_verification.resolve(), missing, errors
    )
    engine = read_json_safe(
        results / "promoted-relocation-verification.json", missing, errors
    )
    fidelity = read_json_safe(
        results / "fidelity-diagnosis/tree-delta.json", missing, errors
    )
    relocated_fingerprint = read_json_safe(
        results / "relocated-fingerprint.json", missing, errors
    )
    runtime_before = read_json_safe(args.runtime_before.resolve(), missing, errors)
    runtime_after = read_json_safe(args.runtime_after.resolve(), missing, errors)
    canonical_before = read_json_safe(
        args.canonical_before.resolve(), missing, errors
    )
    canonical_after = read_json_safe(args.canonical_after.resolve(), missing, errors)
    workflow = read_key_values_safe(
        results / "workflow-status.txt", missing, errors
    )
    candidate_mutation = read_key_values_safe(
        results / "candidate-runtime-mutation-check.txt", missing, errors
    )
    frozen_mutation = read_key_values_safe(
        results / "frozen-runtime-mutation-check.txt", missing, errors
    )
    relocated_status = read_key_values_safe(
        results / "relocated-runtime-fidelity-check.txt", missing, errors
    )
    location_state = read_key_values_safe(
        results / "relocation-location-state.txt", missing, errors
    )

    checks: dict[str, bool] = {
        "all_required_outputs_present": not missing,
        "all_required_outputs_parse": not errors,
        "input_verification_pass": input_verification.get("pass") is True,
        "input_verification_check_count_47": input_verification.get(
            "check_count"
        )
        == 47,
        "closure_verification_pass": closure_verification.get("pass") is True,
        "closure_verification_check_count_63": closure_verification.get(
            "check_count"
        )
        == 63,
        "closure_failed_checks_empty": closure_verification.get("failed_checks")
        == [],
        "engine_schema": engine.get("schema_version") == 2,
        "engine_pass": engine.get("pass") is True,
        "engine_check_count_31": engine.get("check_count") == 31,
        "engine_failed_checks_empty": engine.get("failed_checks") == [],
        "engine_missing_outputs_empty": engine.get("missing_outputs") == [],
        "engine_parse_errors_empty": engine.get("parse_errors") == {},
        "engine_candidate_prefix": engine.get("candidate_prefix")
        == str(runtime_prefix),
        "engine_frozen_prefix": engine.get("frozen_prefix")
        == str(canonical_prefix),
        "engine_relocation_root": engine.get("relocation_root")
        == str(relocation_root),
        "workflow_exit_zero": workflow.get("returncode") == "0",
        "candidate_mutation_pass": candidate_mutation.get("pass") == "true",
        "candidate_mutation_fingerprint_equal": candidate_mutation.get("before")
        == candidate_mutation.get("after"),
        "candidate_mutation_prefix": candidate_mutation.get("candidate_prefix")
        == str(runtime_prefix),
        "canonical_mutation_pass": frozen_mutation.get("pass") == "true",
        "canonical_mutation_fingerprint_equal": frozen_mutation.get("before")
        == frozen_mutation.get("after"),
        "canonical_mutation_prefix": frozen_mutation.get("frozen_prefix")
        == str(canonical_prefix),
        "runtime_before_pass": runtime_before.get("pass") is True,
        "runtime_after_pass": runtime_after.get("pass") is True,
        "runtime_entry_count_714": runtime_before.get("entry_count")
        == runtime_after.get("entry_count")
        == 714,
        "runtime_before_expected_fingerprint": runtime_before.get("fingerprint")
        == args.expected_runtime_fingerprint,
        "runtime_not_mutated": runtime_before.get("fingerprint")
        == runtime_after.get("fingerprint"),
        "runtime_pycache_zero": runtime_before.get("pycache_paths") == []
        and runtime_after.get("pycache_paths") == [],
        "runtime_special_zero": runtime_before.get("special_paths") == []
        and runtime_after.get("special_paths") == [],
        "canonical_before_pass": canonical_before.get("pass") is True,
        "canonical_after_pass": canonical_after.get("pass") is True,
        "canonical_entry_count_3155": canonical_before.get("entry_count")
        == canonical_after.get("entry_count")
        == 3155,
        "canonical_before_expected_fingerprint": canonical_before.get(
            "fingerprint"
        )
        == args.expected_canonical_fingerprint,
        "canonical_not_mutated": canonical_before.get("fingerprint")
        == canonical_after.get("fingerprint"),
        "canonical_pycache_zero": canonical_before.get("pycache_paths") == []
        and canonical_after.get("pycache_paths") == [],
        "canonical_special_zero": canonical_before.get("special_paths") == []
        and canonical_after.get("special_paths") == [],
        "fidelity_schema": fidelity.get("schema_version") == 2,
        "fidelity_source_root": fidelity.get("source_root")
        == str(runtime_prefix),
        "fidelity_relocated_root": fidelity.get("relocated_root")
        == str(b_prefix),
        "fidelity_source_entry_count_714": fidelity.get("source_entry_count")
        == 714,
        "fidelity_relocated_entry_count_714": fidelity.get(
            "relocated_entry_count"
        )
        == 714,
        "fidelity_added_zero": fidelity.get("added_count") == 0,
        "fidelity_removed_zero": fidelity.get("removed_count") == 0,
        "fidelity_portable_changed_zero": fidelity.get(
            "portable_changed_count"
        )
        == 0,
        "fidelity_pycache_zero": fidelity.get("pycache_path_count") == 0,
        "fidelity_portable_pass": fidelity.get("portable_pass") is True,
        "fidelity_portable_fingerprints_equal": fidelity.get(
            "source_portable_fingerprint"
        )
        == fidelity.get("relocated_portable_fingerprint"),
        "fidelity_status_pass": relocated_status.get("pass") == "true",
        "fidelity_status_portable_pass": relocated_status.get("portable_pass")
        == "true",
        "fidelity_status_source_count_714": relocated_status.get(
            "source_entry_count"
        )
        == "714",
        "fidelity_status_relocated_count_714": relocated_status.get(
            "relocated_entry_count"
        )
        == "714",
        "location_a_absent": location_state.get("a_prefix_exists") == "false",
        "location_b_present": location_state.get("b_prefix_exists") == "true",
        "location_b_python_executable": location_state.get(
            "b_python_executable"
        )
        == "true",
        "relocated_fingerprint_schema": relocated_fingerprint.get(
            "schema_version"
        )
        == 1,
        "relocated_fingerprint_pass": relocated_fingerprint.get("pass") is True,
        "relocated_entry_count_714": relocated_fingerprint.get("entry_count")
        == 714,
        "relocated_pycache_zero": relocated_fingerprint.get("pycache_paths")
        == [],
        "relocated_special_zero": relocated_fingerprint.get("special_paths")
        == [],
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
        "runtime_prefix": str(runtime_prefix),
        "canonical_prefix": str(canonical_prefix),
        "relocation_root": str(relocation_root),
        "location_b_prefix": str(b_prefix),
        "engine_verification": engine,
        "fidelity": fidelity,
        "relocated_fingerprint": relocated_fingerprint,
        "runtime_before": runtime_before,
        "runtime_after": runtime_after,
        "canonical_before": canonical_before,
        "canonical_after": canonical_after,
        "claim_boundary": {
            "proved": (
                "The closure-validated 714-entry runtime-base survives an A-to-B "
                "whole-prefix move with production runtime, HTTPS, venv, uv-run, "
                "stale-prefix, and portable product-fidelity gates passing."
            ),
            "not_proved": (
                "Archive byte format, compression, extraction permissions, and "
                "installer transaction behavior are frozen."
            ),
        },
    }
    output = results / "runtime-base-relocation-verification.json"
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 21


if __name__ == "__main__":
    raise SystemExit(main())
