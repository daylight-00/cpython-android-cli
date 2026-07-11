#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_MODULES = ("venv", "test", "test.support")
OBSERVED_MODULES = (
    "venv",
    "ensurepip",
    "test",
    "test.support",
    "__phello__",
    "turtle",
    "idlelib",
    "idlelib.pyshell",
    "turtledemo",
)
INTERPRETATION_KEYS = {
    "test_internal_suite",
    "ensurepip_importable",
    "tkinter_python_package_importable",
    "_tkinter_binary_importable",
    "tcl_interpreter_usable",
    "turtle_importable",
    "idlelib_pyshell_importable",
    "turtledemo_importable",
    "sysconfig_runtime_service_usable",
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("top-level JSON value is not an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--expected-entry-count", type=int, default=3155)
    args = parser.parse_args()

    input_path = args.input.resolve()
    output_path = args.output.resolve()
    runtime_prefix = args.runtime_prefix.resolve()
    missing_outputs: list[str] = []
    parse_errors: dict[str, str] = {}
    data: dict[str, Any] = {}

    if not input_path.is_file():
        missing_outputs.append(str(input_path))
    else:
        try:
            data = read_json(input_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            parse_errors[str(input_path)] = repr(exc)

    before = data.get("before_tree", {})
    after = data.get("after_tree", {})
    modules = data.get("module_probes", {})
    sysconfig = data.get("sysconfig", {})
    tkinter = data.get("tkinter_capability", {})
    interpretation = data.get("interpretation_inputs", {})
    path_states = sysconfig.get("paths_under_prefix", {})
    data_import = sysconfig.get("sysconfigdata_import") or {}

    expected_python = (runtime_prefix / "bin" / "python3.14").resolve()
    observed_python = Path(data.get("sys_executable", "/nonexistent")).resolve()

    module_schema_pass = all(
        isinstance(modules.get(name), dict)
        and isinstance(modules[name].get("success"), bool)
        and isinstance(modules[name].get("spec"), dict)
        for name in OBSERVED_MODULES
    )
    required_modules_pass = all(
        modules.get(name, {}).get("success") is True
        for name in REQUIRED_MODULES
    )

    checks: dict[str, bool] = {
        "all_required_outputs_present": not missing_outputs,
        "all_required_outputs_parse": not parse_errors,
        "schema_version": data.get("schema_version") == 1,
        "probe_pass": data.get("pass") is True,
        "runtime_prefix_matches": data.get("runtime_prefix")
        == str(runtime_prefix),
        "sys_executable_matches": observed_python == expected_python,
        "expected_entry_count_contract": data.get("expected_entry_count")
        == args.expected_entry_count,
        "before_entry_count_matches": before.get("entry_count")
        == args.expected_entry_count,
        "after_entry_count_matches": after.get("entry_count")
        == args.expected_entry_count,
        "tree_fingerprint_nonempty": isinstance(before.get("fingerprint"), str)
        and len(before.get("fingerprint", "")) == 64,
        "tree_fingerprint_unchanged": before.get("fingerprint")
        == after.get("fingerprint"),
        "mutation_pass": data.get("mutation_pass") is True,
        "before_pycache_zero": before.get("pycache_paths") == [],
        "after_pycache_zero": after.get("pycache_paths") == [],
        "before_special_zero": before.get("special_paths") == [],
        "after_special_zero": after.get("special_paths") == [],
        "module_probe_set_exact": set(modules) == set(OBSERVED_MODULES),
        "module_probe_schema_complete": module_schema_pass,
        "required_module_names_exact": data.get("required_module_names")
        == list(REQUIRED_MODULES),
        "required_modules_pass": required_modules_pass,
        "required_modules_summary_pass": data.get("required_modules_pass")
        is True,
        "test_internal_suite_observed": interpretation.get(
            "test_internal_suite"
        )
        is True,
        "ensurepip_observation_present": isinstance(
            interpretation.get("ensurepip_importable"), bool
        ),
        "sysconfig_success": sysconfig.get("success") is True,
        "sysconfig_config_vars_nonempty": isinstance(
            sysconfig.get("config_var_count"), int
        )
        and sysconfig.get("config_var_count", 0) > 0,
        "sysconfig_paths_present": isinstance(path_states, dict)
        and bool(path_states),
        "sysconfig_paths_under_prefix": bool(path_states)
        and all(value is True for value in path_states.values()),
        "sysconfigdata_name_present": isinstance(
            sysconfig.get("sysconfigdata_name"), str
        )
        and bool(sysconfig.get("sysconfigdata_name")),
        "sysconfigdata_import_pass": data_import.get("success") is True,
        "sysconfig_vars_json_present": sysconfig.get(
            "sysconfig_vars_json_count"
        )
        == 1,
        "build_details_exists": sysconfig.get("build_details_exists")
        is True,
        "build_details_parses": sysconfig.get(
            "build_details_parse_success"
        )
        is True,
        "makefile_exists": sysconfig.get("makefile_exists") is True,
        "config_h_exists": sysconfig.get("config_h_exists") is True,
        "tkinter_probe_schema": isinstance(tkinter.get("_tkinter"), dict)
        and isinstance(tkinter.get("tkinter"), dict)
        and isinstance(tkinter.get("tcl_interpreter_success"), bool),
        "tkinter_dependency_consistent": (
            tkinter.get("tkinter", {}).get("success") is not True
            or tkinter.get("_tkinter", {}).get("success") is True
        ),
        "interpretation_keys_exact": set(interpretation)
        == INTERPRETATION_KEYS,
        "sysconfig_interpretation_pass": interpretation.get(
            "sysconfig_runtime_service_usable"
        )
        is True,
    }

    failed_checks = sorted(
        name for name, passed in checks.items() if not passed
    )
    result = {
        "schema_version": 1,
        "pass": not failed_checks,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed_checks,
        "missing_outputs": missing_outputs,
        "parse_errors": parse_errors,
        "runtime_prefix": str(runtime_prefix),
        "expected_entry_count": args.expected_entry_count,
        "observations": {
            "module_success": {
                name: modules.get(name, {}).get("success")
                for name in OBSERVED_MODULES
            },
            "tkinter": tkinter,
            "sysconfig": {
                "config_var_count": sysconfig.get("config_var_count"),
                "paths_under_prefix": path_states,
                "sysconfigdata_name": sysconfig.get("sysconfigdata_name"),
                "sysconfig_vars_json_count": sysconfig.get(
                    "sysconfig_vars_json_count"
                ),
                "build_details_parse_success": sysconfig.get(
                    "build_details_parse_success"
                ),
                "makefile": sysconfig.get("makefile"),
                "makefile_exists": sysconfig.get("makefile_exists"),
                "config_h": sysconfig.get("config_h"),
                "config_h_exists": sysconfig.get("config_h_exists"),
            },
            "interpretation_inputs": interpretation,
            "tree_fingerprint": before.get("fingerprint"),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 8


if __name__ == "__main__":
    raise SystemExit(main())
