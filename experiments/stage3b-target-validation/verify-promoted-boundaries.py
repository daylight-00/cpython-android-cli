#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


SCENARIOS_CA = (
    "clean_default",
    "explicit_termux_ca",
    "missing_file_repair",
    "existing_empty_file",
)
SCENARIOS_ZONE = ("default", "tzdata_only", "termux_zoneinfo")
ZONE_KEYS = ("UTC", "Asia/Seoul", "America/New_York")


def load_json_safe(
    path: Path,
    missing_outputs: list[str],
    parse_errors: dict[str, str],
) -> dict[str, Any]:
    if not path.is_file():
        missing_outputs.append(str(path))
        return {}

    try:
        with path.open(encoding="utf-8") as f:
            value = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        parse_errors[str(path)] = repr(exc)
        return {}

    if not isinstance(value, dict):
        parse_errors[str(path)] = "top-level JSON value is not an object"
        return {}
    return value


def read_mutation_check_safe(
    path: Path,
    missing_outputs: list[str],
    parse_errors: dict[str, str],
) -> dict[str, str]:
    if not path.is_file():
        missing_outputs.append(str(path))
        return {}

    result: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        parse_errors[str(path)] = repr(exc)
        return {}

    for line in lines:
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key] = value
    return result


def read_workflow_status_safe(
    path: Path,
    missing_outputs: list[str],
    parse_errors: dict[str, str],
) -> list[dict[str, Any]]:
    if not path.is_file():
        missing_outputs.append(str(path))
        return []

    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                try:
                    returncode: int | None = int(row.get("returncode", ""))
                except ValueError:
                    returncode = None
                rows.append(
                    {
                        "runtime": row.get("runtime"),
                        "probe": row.get("probe"),
                        "returncode": returncode,
                    }
                )
    except OSError as exc:
        parse_errors[str(path)] = repr(exc)
    return rows


def ca_semantics(data: dict[str, Any]) -> dict[str, Any]:
    termux_ca = data.get("termux_ca_path")
    empty_ca = data.get("empty_ca_path")
    scenarios = data.get("scenarios", {})
    scenarios = scenarios if isinstance(scenarios, dict) else {}
    normalized: dict[str, Any] = {
        "termux_ca_exists": data.get("termux_ca_exists"),
        "scenarios": {},
    }

    for name in SCENARIOS_CA:
        scenario = scenarios.get(name, {})
        parsed = scenario.get("parsed") if isinstance(scenario, dict) else None
        parsed = parsed if isinstance(parsed, dict) else {}
        observed_path = parsed.get("ssl_cert_file_env")
        if observed_path == termux_ca:
            path_class = "TERMUX_CA"
        elif observed_path == empty_ca:
            path_class = "EMPTY_CONTROL"
        elif observed_path is None:
            path_class = "UNSET"
        else:
            path_class = "OTHER"
        normalized["scenarios"][name] = {
            "returncode": scenario.get("returncode")
            if isinstance(scenario, dict)
            else None,
            "https_result": parsed.get("https_result"),
            "https_status": parsed.get("https_status"),
            "ssl_cert_file_class": path_class,
        }
    return normalized


def zone_semantics(data: dict[str, Any]) -> dict[str, Any]:
    scenarios = data.get("scenarios", {})
    scenarios = scenarios if isinstance(scenarios, dict) else {}
    normalized: dict[str, Any] = {
        "child_args": data.get("child_args"),
        "termux_zoneinfo_exists": data.get("termux_zoneinfo_exists"),
        "scenarios": {},
    }

    for name in SCENARIOS_ZONE:
        scenario = scenarios.get(name, {})
        parsed = scenario.get("parsed") if isinstance(scenario, dict) else None
        parsed = parsed if isinstance(parsed, dict) else {}
        keys = parsed.get("keys")
        keys = keys if isinstance(keys, dict) else {}
        normalized["scenarios"][name] = {
            "pass": scenario.get("pass") if isinstance(scenario, dict) else None,
            "returncode": scenario.get("returncode")
            if isinstance(scenario, dict)
            else None,
            "pythontzpath_env": parsed.get("pythontzpath_env"),
            "zoneinfo_tzpath": parsed.get("zoneinfo_tzpath"),
            "tzdata_spec_found": parsed.get("tzdata_spec_found"),
            "flags": parsed.get("flags"),
            "key_results": {
                key: (keys.get(key) or {}).get("result")
                if isinstance(keys.get(key), dict)
                else None
                for key in ZONE_KEYS
            },
        }
    return normalized


def uv_semantics(data: dict[str, Any]) -> dict[str, Any]:
    keys = data.get("keys")
    keys = keys if isinstance(keys, dict) else {}
    return {
        "python_tzpath_env": data.get("python_tzpath_env"),
        "tzdata_spec_found": data.get("tzdata_spec_found"),
        "tzdata_version": data.get("tzdata_version"),
        "all_keys_pass": data.get("all_keys_pass"),
        "key_results": {
            key: (keys.get(key) or {}).get("result")
            if isinstance(keys.get(key), dict)
            else None
            for key in ZONE_KEYS
        },
    }


def resolved_path_matches(value: Any, expected: Path) -> bool:
    return isinstance(value, str) and bool(value) and Path(value).resolve() == expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--candidate-prefix", required=True, type=Path)
    parser.add_argument("--frozen-prefix", required=True, type=Path)
    parser.add_argument("--termux-prefix", required=True, type=Path)
    args = parser.parse_args()

    results_dir = args.results_dir.resolve()
    candidate_prefix = args.candidate_prefix.resolve()
    frozen_prefix = args.frozen_prefix.resolve()
    termux_prefix = args.termux_prefix.resolve()
    candidate_dir = results_dir / "candidate"
    frozen_dir = results_dir / "frozen"

    missing_outputs: list[str] = []
    parse_errors: dict[str, str] = {}

    candidate_ca = load_json_safe(
        candidate_dir / "ca-boundary-probe.json", missing_outputs, parse_errors
    )
    frozen_ca = load_json_safe(
        frozen_dir / "ca-boundary-probe.json", missing_outputs, parse_errors
    )
    candidate_zone = load_json_safe(
        candidate_dir / "zoneinfo-boundary-probe.json",
        missing_outputs,
        parse_errors,
    )
    frozen_zone = load_json_safe(
        frozen_dir / "zoneinfo-boundary-probe.json", missing_outputs, parse_errors
    )
    candidate_uv = load_json_safe(
        candidate_dir / "zoneinfo-uv-tzdata-probe.json",
        missing_outputs,
        parse_errors,
    )
    frozen_uv = load_json_safe(
        frozen_dir / "zoneinfo-uv-tzdata-probe.json", missing_outputs, parse_errors
    )
    candidate_mutation = read_mutation_check_safe(
        results_dir / "candidate-runtime-mutation-check.txt",
        missing_outputs,
        parse_errors,
    )
    frozen_mutation = read_mutation_check_safe(
        results_dir / "frozen-runtime-mutation-check.txt",
        missing_outputs,
        parse_errors,
    )
    workflow_status = read_workflow_status_safe(
        results_dir / "workflow-status.tsv", missing_outputs, parse_errors
    )

    candidate_ca_norm = ca_semantics(candidate_ca)
    frozen_ca_norm = ca_semantics(frozen_ca)
    candidate_zone_norm = zone_semantics(candidate_zone)
    frozen_zone_norm = zone_semantics(frozen_zone)
    candidate_uv_norm = uv_semantics(candidate_uv)
    frozen_uv_norm = uv_semantics(frozen_uv)

    expected_ca = {
        "termux_ca_exists": True,
        "scenarios": {
            "clean_default": {
                "returncode": 0,
                "https_result": "PASS",
                "https_status": 200,
                "ssl_cert_file_class": "TERMUX_CA",
            },
            "explicit_termux_ca": {
                "returncode": 0,
                "https_result": "PASS",
                "https_status": 200,
                "ssl_cert_file_class": "TERMUX_CA",
            },
            "missing_file_repair": {
                "returncode": 0,
                "https_result": "PASS",
                "https_status": 200,
                "ssl_cert_file_class": "TERMUX_CA",
            },
            "existing_empty_file": {
                "returncode": 4,
                "https_result": "FAIL",
                "https_status": None,
                "ssl_cert_file_class": "EMPTY_CONTROL",
            },
        },
    }

    termux_zoneinfo = str(termux_prefix / "share" / "zoneinfo")
    expected_zone_inputs = {
        "default": None,
        "tzdata_only": "",
        "termux_zoneinfo": termux_zoneinfo,
    }
    expected_flags = {
        "isolated": 0,
        "safe_path": True,
        "no_user_site": 1,
        "dont_write_bytecode": True,
    }
    expected_workflow_steps = {
        (runtime, probe)
        for runtime in ("candidate", "frozen")
        for probe in ("ca-boundary", "zoneinfo-boundary", "uv-tzdata-fallback")
    }
    observed_workflow_steps = {
        (row.get("runtime"), row.get("probe")) for row in workflow_status
    }

    checks: dict[str, bool] = {
        "all_required_outputs_present": not missing_outputs,
        "all_required_outputs_parse": not parse_errors,
        "all_workflow_steps_recorded": observed_workflow_steps
        == expected_workflow_steps,
        "all_workflow_steps_exit_zero": len(workflow_status) == 6
        and all(row.get("returncode") == 0 for row in workflow_status),
        "candidate_ca_contract": candidate_ca_norm == expected_ca,
        "frozen_ca_contract": frozen_ca_norm == expected_ca,
        "ca_semantic_equivalence": candidate_ca_norm == frozen_ca_norm,
        "zone_child_contract": candidate_zone_norm.get("child_args")
        == ["-B", "-P", "-s", "-c"]
        and frozen_zone_norm.get("child_args") == ["-B", "-P", "-s", "-c"],
        "zone_semantic_equivalence": candidate_zone_norm == frozen_zone_norm,
        "candidate_uv_tzdata_pass": candidate_uv_norm.get("all_keys_pass") is True
        and candidate_uv_norm.get("python_tzpath_env") == ""
        and candidate_uv_norm.get("tzdata_spec_found") is True
        and isinstance(candidate_uv_norm.get("tzdata_version"), str)
        and all(
            value == "PASS"
            for value in candidate_uv_norm.get("key_results", {}).values()
        ),
        "frozen_uv_tzdata_pass": frozen_uv_norm.get("all_keys_pass") is True
        and frozen_uv_norm.get("python_tzpath_env") == ""
        and frozen_uv_norm.get("tzdata_spec_found") is True
        and isinstance(frozen_uv_norm.get("tzdata_version"), str)
        and all(
            value == "PASS"
            for value in frozen_uv_norm.get("key_results", {}).values()
        ),
        "uv_tzdata_semantic_equivalence": candidate_uv_norm == frozen_uv_norm,
        "candidate_uv_base_prefix": resolved_path_matches(
            candidate_uv.get("sys_base_prefix"), candidate_prefix
        ),
        "frozen_uv_base_prefix": resolved_path_matches(
            frozen_uv.get("sys_base_prefix"), frozen_prefix
        ),
        "candidate_runtime_not_mutated": candidate_mutation.get("pass") == "true",
        "frozen_runtime_not_mutated": frozen_mutation.get("pass") == "true",
    }

    for name, expected_env in expected_zone_inputs.items():
        candidate_scenario = candidate_zone_norm["scenarios"].get(name, {})
        frozen_scenario = frozen_zone_norm["scenarios"].get(name, {})
        checks[f"candidate_zone_input_{name}"] = (
            candidate_scenario.get("pythontzpath_env") == expected_env
        )
        checks[f"frozen_zone_input_{name}"] = (
            frozen_scenario.get("pythontzpath_env") == expected_env
        )
        checks[f"candidate_zone_flags_{name}"] = (
            candidate_scenario.get("flags") == expected_flags
        )
        checks[f"frozen_zone_flags_{name}"] = (
            frozen_scenario.get("flags") == expected_flags
        )

    failed_checks = sorted(name for name, passed in checks.items() if not passed)
    summary = {
        "schema_version": 1,
        "pass": not failed_checks,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed_checks,
        "missing_outputs": sorted(set(missing_outputs)),
        "parse_errors": parse_errors,
        "candidate_prefix": str(candidate_prefix),
        "frozen_prefix": str(frozen_prefix),
        "termux_prefix": str(termux_prefix),
        "workflow_status": workflow_status,
        "observed": {
            "candidate": {
                "ca": candidate_ca_norm,
                "zoneinfo": candidate_zone_norm,
                "uv_tzdata": candidate_uv_norm,
            },
            "frozen": {
                "ca": frozen_ca_norm,
                "zoneinfo": frozen_zone_norm,
                "uv_tzdata": frozen_uv_norm,
            },
        },
    }

    output = results_dir / "promoted-boundary-verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["pass"] else 5


if __name__ == "__main__":
    raise SystemExit(main())
