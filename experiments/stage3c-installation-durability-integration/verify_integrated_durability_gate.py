#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_GATE5A_RESULT_INDEX = "ac11225ae6b45ac45f1e378ecf7bba9cd074a1f779009318e001d5694d89ead8"
EXPECTED_INTEGRATED_BLOBS = {
    "recovery_common.py": "3183ba0861ef45e7a395201bec0085f3f69fb248",
    "recovery_operations.py": "8a307065e00fd7a7332541f4911c5478945374ee",
    "recovery_engine.py": "aebf5b9a33d163f7f8758f785ca621c94c0e478b",
    "recovery_durability.py": "61bfb859f73acccb0dfcce1d2a630bfd1ffc2d3f",
}


def canonical_json_bytes(value: Any) -> bytes:
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate5a-results", required=True, type=Path)
    parser.add_argument("--source-integration", required=True, type=Path)
    parser.add_argument("--recovery-results", required=True, type=Path)
    parser.add_argument("--durability-results", required=True, type=Path)
    parser.add_argument("--exercise-results", required=True, type=Path)
    parser.add_argument("--trace-verification", required=True, type=Path)
    parser.add_argument("--input-before", required=True, type=Path)
    parser.add_argument("--input-after", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    gate5a = args.gate5a_results.resolve()
    source = read_json(args.source_integration.resolve())
    recovery_dir = args.recovery_results.resolve()
    durability_dir = args.durability_results.resolve()
    exercise_dir = args.exercise_results.resolve()
    traces = read_json(args.trace_verification.resolve())
    before = read_json(args.input_before.resolve())
    after = read_json(args.input_after.resolve())

    gate5a_scenario = read_json(gate5a / "scenario.json")
    gate5a_verification = read_json(gate5a / "verification.json")
    gate5a_workflow = read_json(gate5a / "workflow-status.json")
    recovery_scenario = read_json(recovery_dir / "scenario.json")
    recovery_verification = read_json(recovery_dir / "verification.json")
    durability_scenario = read_json(durability_dir / "scenario.json")
    durability_verification = read_json(durability_dir / "verification.json")
    exercise = read_json(exercise_dir / "exercise.json")

    recovery_logs = sorted(recovery_dir.glob("[0-9][0-9]-*.json"))
    durability_traces = sorted(durability_dir.glob("trace-*.json"))
    exercise_logs = sorted(exercise_dir.glob("[0-9][0-9]-*.json"))

    checks = {
        "gate5a_scenario_pass_32": gate5a_scenario.get("pass") is True
        and gate5a_scenario.get("check_count") == 32
        and gate5a_scenario.get("failed_checks") == [],
        "gate5a_verification_pass_29": gate5a_verification.get("pass") is True
        and gate5a_verification.get("check_count") == 29
        and gate5a_verification.get("failed_checks") == [],
        "gate5a_workflow_pass": gate5a_workflow.get("pass") is True
        and all(value == 0 for value in gate5a_workflow.get("returncodes", {}).values()),
        "gate5a_result_index_exact": sha256_file(gate5a / "result-index.json")
        == EXPECTED_GATE5A_RESULT_INDEX,
        "source_integration_pass_29": source.get("pass") is True
        and source.get("check_count") == 29
        and source.get("failed_checks") == [],
        "integrated_source_blobs_exact": source.get("integrated_source_blobs")
        == EXPECTED_INTEGRATED_BLOBS,
        "direct_violations_absent": source.get("direct_violations") == [],
        "helper_missing_absent": source.get("helper_missing") == {},
        "recovery_scenario_pass_55": recovery_scenario.get("pass") is True
        and recovery_scenario.get("check_count") == 55
        and recovery_scenario.get("failed_checks") == [],
        "recovery_verification_pass_82": recovery_verification.get("pass") is True
        and recovery_verification.get("check_count") == 82
        and recovery_verification.get("failed_checks") == [],
        "recovery_log_count_40": len(recovery_logs) == 40,
        "recovery_logs_canonical": all(
            path.read_bytes() == canonical_json_bytes(read_json(path)) for path in recovery_logs
        ),
        "recovery_snapshots_complete": len(list((recovery_dir / "snapshots").glob("*-registry.json"))) == 5
        and len(list((recovery_dir / "snapshots").glob("*-observed-owned-paths.json"))) == 5,
        "durability_scenario_pass_64": durability_scenario.get("pass") is True
        and durability_scenario.get("check_count") == 64
        and durability_scenario.get("failed_checks") == [],
        "durability_verification_pass_53": durability_verification.get("pass") is True
        and durability_verification.get("check_count") == 53
        and durability_verification.get("failed_checks") == [],
        "durability_trace_count_7": len(durability_traces) == 7,
        "durability_traces_canonical": all(
            path.read_bytes() == canonical_json_bytes(read_json(path))
            for path in durability_traces
        ),
        "exercise_pass_20": exercise.get("pass") is True
        and exercise.get("check_count") == 20
        and exercise.get("failed_checks") == [],
        "exercise_log_count_16": len(exercise_logs) == 16,
        "exercise_logs_canonical": all(
            path.read_bytes() == canonical_json_bytes(read_json(path))
            for path in exercise_logs
        ),
        "trace_verification_pass_29": traces.get("pass") is True
        and traces.get("check_count") == 29
        and traces.get("failed_checks") == [],
        "trace_violations_absent": traces.get("violations") == [],
        "trace_files_nonempty": traces.get("trace_file_count", 0) > 0,
        "trace_events_nonempty": traces.get("event_count", 0) > 0,
        "trace_chmod_observed": traces.get("operations", {}).get("CHMOD", 0) > 0,
        "trace_move_observed": traces.get("operations", {}).get("MOVE", 0) > 0,
        "trace_atomic_replace_observed": traces.get("operations", {}).get("REPLACE", 0) > 0,
        "trace_file_fsync_observed": traces.get("operations", {}).get("FSYNC_FILE", 0) > 0,
        "trace_directory_fsync_observed": traces.get("operations", {}).get("FSYNC_DIR", 0) > 0,
        "input_tree_unchanged": before.get("pass") is True
        and after.get("pass") is True
        and before.get("entry_count") == after.get("entry_count")
        and before.get("fingerprint") == after.get("fingerprint"),
        "source_json_canonical": args.source_integration.resolve().read_bytes()
        == canonical_json_bytes(source),
        "trace_verification_canonical": args.trace_verification.resolve().read_bytes()
        == canonical_json_bytes(traces),
        "exercise_json_canonical": (exercise_dir / "exercise.json").read_bytes()
        == canonical_json_bytes(exercise),
        "recovery_claim_boundary_retained": "power-loss durability"
        in recovery_scenario.get("claim_boundary", {}).get("not_proved", ""),
        "durability_claim_boundary_retained": "sudden power loss"
        in durability_scenario.get("claim_boundary", {}).get("not_proved", ""),
        "integrated_claim_boundary_exact": "actual sudden power loss"
        in traces.get("claim_boundary", {}).get("not_proved", ""),
    }
    if len(checks) != 36:
        raise RuntimeError(f"unexpected check count: {len(checks)}")
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "observed": {
            "recovery_log_count": len(recovery_logs),
            "durability_trace_count": len(durability_traces),
            "exercise_log_count": len(exercise_logs),
            "integrated_trace_file_count": traces.get("trace_file_count"),
            "integrated_trace_event_count": traces.get("event_count"),
        },
        "claim_boundary": {
            "proved": "The integrated recovery sources satisfy the Gate 5A mapping, replay the frozen Gate 3 and Gate 4 checks, pass focused lifecycle exercises, and emit ordered durability traces for exercised production paths.",
            "not_proved": "Actual sudden power-loss persistence, kernel panic, storage-controller failure, or interruption inside one filesystem primitive remain unproved.",
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 57


if __name__ == "__main__":
    raise SystemExit(main())
