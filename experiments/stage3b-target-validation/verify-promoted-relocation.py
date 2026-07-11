#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_MARKERS = (
    "LOCATION_RECONFIRM[A]=PASS",
    "LOCATION_RECONFIRM[B]=PASS",
    "STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS",
    "STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS",
)


def read_key_values_safe(
    path: Path,
    missing_outputs: list[str],
    parse_errors: dict[str, str],
) -> dict[str, str]:
    if not path.is_file():
        missing_outputs.append(str(path))
        return {}

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        parse_errors[str(path)] = repr(exc)
        return {}

    result: dict[str, str] = {}
    for line in lines:
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key] = value
    return result


def read_text_safe(
    path: Path,
    missing_outputs: list[str],
    parse_errors: dict[str, str],
) -> str:
    if not path.is_file():
        missing_outputs.append(str(path))
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        parse_errors[str(path)] = repr(exc)
        return ""


def read_json_safe(
    path: Path,
    missing_outputs: list[str],
    parse_errors: dict[str, str],
) -> dict[str, Any]:
    if not path.is_file():
        missing_outputs.append(str(path))
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parse_errors[str(path)] = repr(exc)
        return {}
    if not isinstance(value, dict):
        parse_errors[str(path)] = "top-level JSON value is not an object"
        return {}
    return value


def is_true(mapping: dict[str, str], key: str) -> bool:
    return mapping.get(key) == "true"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--candidate-prefix", required=True, type=Path)
    parser.add_argument("--frozen-prefix", required=True, type=Path)
    parser.add_argument("--relocation-root", required=True, type=Path)
    args = parser.parse_args()

    results_dir = args.results_dir.resolve()
    candidate_prefix = args.candidate_prefix.resolve()
    frozen_prefix = args.frozen_prefix.resolve()
    relocation_root = args.relocation_root.resolve()
    a_prefix = relocation_root / "location-a" / "prefix"
    b_prefix = relocation_root / "location-b" / "prefix"

    missing_outputs: list[str] = []
    parse_errors: dict[str, str] = {}

    workflow = read_key_values_safe(
        results_dir / "workflow-status.txt", missing_outputs, parse_errors
    )
    candidate_mutation = read_key_values_safe(
        results_dir / "candidate-runtime-mutation-check.txt",
        missing_outputs,
        parse_errors,
    )
    frozen_mutation = read_key_values_safe(
        results_dir / "frozen-runtime-mutation-check.txt",
        missing_outputs,
        parse_errors,
    )
    relocated_fidelity = read_key_values_safe(
        results_dir / "relocated-runtime-fidelity-check.txt",
        missing_outputs,
        parse_errors,
    )
    fidelity_diagnosis = read_json_safe(
        results_dir / "fidelity-diagnosis" / "tree-delta.json",
        missing_outputs,
        parse_errors,
    )
    location_state = read_key_values_safe(
        results_dir / "relocation-location-state.txt",
        missing_outputs,
        parse_errors,
    )
    log = read_text_safe(
        results_dir / "reconfirm" / "reconfirm.log",
        missing_outputs,
        parse_errors,
    )

    marker_counts = {marker: log.count(marker) for marker in REQUIRED_MARKERS}
    expected_path_lines = {
        "source": f"SOURCE_PREFIX={candidate_prefix}",
        "a": f"A_PREFIX={a_prefix}",
        "b": f"B_PREFIX={b_prefix}",
    }

    source_entry_count = fidelity_diagnosis.get("source_entry_count")
    relocated_entry_count = fidelity_diagnosis.get("relocated_entry_count")
    source_portable_fingerprint = fidelity_diagnosis.get(
        "source_portable_fingerprint"
    )
    relocated_portable_fingerprint = fidelity_diagnosis.get(
        "relocated_portable_fingerprint"
    )

    checks: dict[str, bool] = {
        "all_required_outputs_present": not missing_outputs,
        "all_required_outputs_parse": not parse_errors,
        "relocation_workflow_exit_zero": workflow.get("returncode") == "0",
        "candidate_runtime_not_mutated": is_true(candidate_mutation, "pass"),
        "frozen_runtime_not_mutated": is_true(frozen_mutation, "pass"),
        "relocated_runtime_matches_source": is_true(relocated_fidelity, "pass"),
        "fidelity_contract_is_portable_v2": relocated_fidelity.get("comparison")
        == "portable-tree-manifest-v2",
        "fidelity_status_portable_pass": is_true(
            relocated_fidelity, "portable_pass"
        ),
        "fidelity_diagnosis_schema": fidelity_diagnosis.get("schema_version") == 2,
        "fidelity_source_root_matches": fidelity_diagnosis.get("source_root")
        == str(candidate_prefix),
        "fidelity_relocated_root_matches": fidelity_diagnosis.get("relocated_root")
        == str(b_prefix),
        "fidelity_portable_pass": fidelity_diagnosis.get("portable_pass") is True,
        "fidelity_no_added_paths": fidelity_diagnosis.get("added_count") == 0,
        "fidelity_no_removed_paths": fidelity_diagnosis.get("removed_count") == 0,
        "fidelity_no_portable_changes": fidelity_diagnosis.get(
            "portable_changed_count"
        )
        == 0,
        "fidelity_entry_counts_equal": isinstance(source_entry_count, int)
        and source_entry_count > 0
        and source_entry_count == relocated_entry_count,
        "fidelity_portable_fingerprints_equal": isinstance(
            source_portable_fingerprint, str
        )
        and len(source_portable_fingerprint) == 64
        and source_portable_fingerprint == relocated_portable_fingerprint,
        "fidelity_status_source_count_matches": relocated_fidelity.get(
            "source_entry_count"
        )
        == str(source_entry_count),
        "fidelity_status_relocated_count_matches": relocated_fidelity.get(
            "relocated_entry_count"
        )
        == str(relocated_entry_count),
        "fidelity_status_source_fingerprint_matches": relocated_fidelity.get(
            "source_portable_fingerprint"
        )
        == source_portable_fingerprint,
        "fidelity_status_relocated_fingerprint_matches": relocated_fidelity.get(
            "relocated_portable_fingerprint"
        )
        == relocated_portable_fingerprint,
        "location_a_absent_after_move": location_state.get("a_prefix_exists")
        == "false",
        "location_b_present_after_move": location_state.get("b_prefix_exists")
        == "true",
        "location_b_python_executable": location_state.get("b_python_executable")
        == "true",
        "location_a_marker_once": marker_counts["LOCATION_RECONFIRM[A]=PASS"]
        == 1,
        "location_b_marker_once": marker_counts["LOCATION_RECONFIRM[B]=PASS"]
        == 1,
        "stale_a_assertion_marker_once": marker_counts[
            "STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS"
        ]
        == 1,
        "stage3a_relocation_engine_marker_once": marker_counts[
            "STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS"
        ]
        == 1,
        "log_source_prefix_matches_candidate": expected_path_lines["source"] in log,
        "log_location_a_prefix_matches": expected_path_lines["a"] in log,
        "log_location_b_prefix_matches": expected_path_lines["b"] in log,
    }

    failed_checks = sorted(name for name, passed in checks.items() if not passed)
    summary: dict[str, Any] = {
        "schema_version": 2,
        "pass": not failed_checks,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed_checks,
        "missing_outputs": sorted(set(missing_outputs)),
        "parse_errors": parse_errors,
        "candidate_prefix": str(candidate_prefix),
        "frozen_prefix": str(frozen_prefix),
        "relocation_root": str(relocation_root),
        "location_a_prefix": str(a_prefix),
        "location_b_prefix": str(b_prefix),
        "workflow": workflow,
        "candidate_mutation": candidate_mutation,
        "frozen_mutation": frozen_mutation,
        "relocated_fidelity": relocated_fidelity,
        "fidelity_diagnosis": fidelity_diagnosis,
        "location_state": location_state,
        "marker_counts": marker_counts,
    }

    output = results_dir / "promoted-relocation-verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["pass"] else 5


if __name__ == "__main__":
    raise SystemExit(main())
