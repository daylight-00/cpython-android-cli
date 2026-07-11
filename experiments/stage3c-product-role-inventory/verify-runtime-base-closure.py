#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED = {
    "runtime_entries": 714,
    "canonical_entries": 3155,
    "symlinks": 3,
    "elf_objects": 81,
    "needed_edges": 329,
    "classification_edges": {
        "ANDROID_SYSTEM": 249,
        "RUNTIME_INTERNAL": 80,
    },
    "unique_needed_sonames": 9,
    "classification_unique_sonames": {
        "ANDROID_SYSTEM": 5,
        "RUNTIME_INTERNAL": 4,
    },
    "android_system_sonames": 5,
    "extension_candidates": 67,
}

REQUIRED_OUTPUTS = (
    "files.tsv",
    "symlinks.tsv",
    "elf-objects.tsv",
    "elf-needed.tsv",
    "python-runtime.json",
    "closure-classification.tsv",
    "unresolved.tsv",
    "errors.tsv",
    "summary.json",
    "mutation-check.txt",
    "needed-sonames.tsv",
    "provider-ambiguity.tsv",
    "object-dependency-counts.tsv",
    "closure-analysis-summary.json",
    "system-soname-probe.tsv",
    "system-soname-probe-summary.json",
    "extension-discovery.json",
    "extension-import-probe.tsv",
    "extension-import-probe-summary.json",
    "workflow-status.json",
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


def data_row_count(path: Path) -> int | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    return max(len(lines) - 1, 0)


def same_path(value: object, expected: Path) -> bool:
    if not isinstance(value, str) or not value:
        return False
    return Path(value).resolve() == expected.resolve()


def path_is_within(value: object, root: Path) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        Path(value).resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--input-verification", required=True, type=Path)
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--canonical-prefix", required=True, type=Path)
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
    missing: list[str] = []
    errors: dict[str, str] = {}

    for name in REQUIRED_OUTPUTS:
        path = results / name
        if not path.is_file():
            missing.append(str(path))

    input_verification = read_json_safe(
        args.input_verification.resolve(), missing, errors
    )
    runtime_before = read_json_safe(args.runtime_before.resolve(), missing, errors)
    runtime_after = read_json_safe(args.runtime_after.resolve(), missing, errors)
    canonical_before = read_json_safe(
        args.canonical_before.resolve(), missing, errors
    )
    canonical_after = read_json_safe(args.canonical_after.resolve(), missing, errors)
    workflow = read_json_safe(results / "workflow-status.json", missing, errors)
    inventory = read_json_safe(results / "summary.json", missing, errors)
    runtime = read_json_safe(results / "python-runtime.json", missing, errors)
    closure = read_json_safe(
        results / "closure-analysis-summary.json", missing, errors
    )
    system_probe = read_json_safe(
        results / "system-soname-probe-summary.json", missing, errors
    )
    extension_probe = read_json_safe(
        results / "extension-import-probe-summary.json", missing, errors
    )
    inventory_mutation = read_key_values_safe(
        results / "mutation-check.txt", missing, errors
    )

    sysconfig_paths = runtime.get("sysconfig_paths", {})
    returncodes = workflow.get("returncodes", {})
    expected_returncode_keys = {
        "inventory",
        "closure_analysis",
        "extension_imports",
    }

    checks: dict[str, bool] = {
        "all_required_outputs_present": not missing,
        "all_required_outputs_parse": not errors,
        "input_verification_pass": input_verification.get("pass") is True,
        "input_verification_failed_checks_empty": input_verification.get(
            "failed_checks"
        )
        == [],
        "workflow_schema": workflow.get("schema_version") == 1,
        "workflow_pass": workflow.get("pass") is True,
        "workflow_returncode_keys_exact": set(returncodes)
        == expected_returncode_keys,
        "workflow_returncodes_zero": bool(returncodes)
        and all(value == 0 for value in returncodes.values()),
        "runtime_before_pass": runtime_before.get("pass") is True,
        "runtime_after_pass": runtime_after.get("pass") is True,
        "runtime_before_entry_count": runtime_before.get("entry_count")
        == EXPECTED["runtime_entries"],
        "runtime_after_entry_count": runtime_after.get("entry_count")
        == EXPECTED["runtime_entries"],
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
        "canonical_before_entry_count": canonical_before.get("entry_count")
        == EXPECTED["canonical_entries"],
        "canonical_after_entry_count": canonical_after.get("entry_count")
        == EXPECTED["canonical_entries"],
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
        "inventory_runtime_prefix": same_path(
            inventory.get("runtime_prefix"), runtime_prefix
        ),
        "inventory_symlink_count": inventory.get("symlink_count")
        == EXPECTED["symlinks"],
        "inventory_elf_object_count": inventory.get("elf_object_count")
        == EXPECTED["elf_objects"],
        "inventory_needed_edge_count": inventory.get("needed_edge_count")
        == EXPECTED["needed_edges"],
        "inventory_classification_counts": inventory.get(
            "classification_counts"
        )
        == EXPECTED["classification_edges"],
        "inventory_unresolved_zero": inventory.get("unresolved_edge_count") == 0,
        "inventory_inspection_errors_zero": inventory.get(
            "inspection_error_count"
        )
        == 0,
        "inventory_mutation_summary_pass": inventory.get("mutation_check")
        == "PASS",
        "inventory_mutation_file_pass": inventory_mutation.get(
            "MUTATION_CHECK"
        )
        == "PASS",
        "unresolved_tsv_zero": data_row_count(results / "unresolved.tsv") == 0,
        "errors_tsv_zero": data_row_count(results / "errors.tsv") == 0,
        "closure_needed_edge_count": closure.get("needed_edge_count")
        == EXPECTED["needed_edges"],
        "closure_unique_needed_sonames": closure.get(
            "unique_needed_soname_count"
        )
        == EXPECTED["unique_needed_sonames"],
        "closure_classification_edges": closure.get(
            "classification_edge_counts"
        )
        == EXPECTED["classification_edges"],
        "closure_classification_unique_sonames": closure.get(
            "classification_unique_soname_counts"
        )
        == EXPECTED["classification_unique_sonames"],
        "closure_unresolved_zero": closure.get("unresolved_edge_count", 0) == 0,
        "system_soname_count": system_probe.get(
            "unique_android_system_soname_count"
        )
        == EXPECTED["android_system_sonames"],
        "system_soname_dlopen_pass": system_probe.get("dlopen_pass_count")
        == EXPECTED["android_system_sonames"],
        "system_soname_dlopen_fail_zero": system_probe.get(
            "dlopen_fail_count"
        )
        == 0,
        "extension_candidate_count": extension_probe.get(
            "extension_candidate_count"
        )
        == EXPECTED["extension_candidates"],
        "extension_import_pass_count": extension_probe.get("import_pass_count")
        == EXPECTED["extension_candidates"],
        "extension_import_fail_zero": extension_probe.get("import_fail_count")
        == 0,
        "extension_discovery_from_sys_path": extension_probe.get(
            "extension_dir_discovery_method"
        )
        == "sys.path",
        "extension_dir_exact": same_path(
            extension_probe.get("extension_dir"),
            runtime_prefix / "lib/python3.14/lib-dynload",
        ),
        "runtime_executable": same_path(
            runtime.get("executable"), runtime_prefix / "bin/python"
        ),
        "runtime_prefix": same_path(runtime.get("prefix"), runtime_prefix),
        "runtime_base_prefix": same_path(
            runtime.get("base_prefix"), runtime_prefix
        ),
        "runtime_exec_prefix": same_path(
            runtime.get("exec_prefix"), runtime_prefix
        ),
        "runtime_base_exec_prefix": same_path(
            runtime.get("base_exec_prefix"), runtime_prefix
        ),
        "runtime_python_version": runtime.get("version_info", [])[:3]
        == [3, 14, 6],
        "runtime_platform": runtime.get("platform") == "android",
        "runtime_soabi": runtime.get("sysconfig_config_vars", {}).get("SOABI")
        == "cpython-314-aarch64-linux-android",
        "runtime_multiarch": runtime.get("sysconfig_config_vars", {}).get(
            "MULTIARCH"
        )
        == "aarch64-linux-android",
        "runtime_sysconfig_paths_within": bool(sysconfig_paths)
        and all(
            path_is_within(value, runtime_prefix)
            for value in sysconfig_paths.values()
        ),
        "runtime_sys_path_stdlib": any(
            same_path(value, runtime_prefix / "lib/python3.14")
            for value in runtime.get("path", [])
        ),
        "runtime_sys_path_lib_dynload": any(
            same_path(
                value,
                runtime_prefix / "lib/python3.14/lib-dynload",
            )
            for value in runtime.get("path", [])
        ),
        "runtime_ld_library_path": str(runtime_prefix / "lib")
        in (runtime.get("environment", {}).get("LD_LIBRARY_PATH") or "").split(
            ":"
        ),
        "runtime_ssl_cert_file": Path(
            runtime.get("environment", {}).get("SSL_CERT_FILE") or ""
        ).is_file(),
        "canonical_prefix_exists": canonical_prefix.is_dir(),
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
        "expected": EXPECTED,
        "observed": {
            "workflow": workflow,
            "inventory": inventory,
            "closure": closure,
            "system_soname_probe": system_probe,
            "extension_import_probe": extension_probe,
            "runtime_identity": {
                "executable": runtime.get("executable"),
                "prefix": runtime.get("prefix"),
                "base_prefix": runtime.get("base_prefix"),
                "version_info": runtime.get("version_info"),
                "platform": runtime.get("platform"),
            },
            "runtime_before": runtime_before,
            "runtime_after": runtime_after,
            "canonical_before": canonical_before,
            "canonical_after": canonical_after,
        },
        "non_gating": {
            "inventory_file_entry_count": inventory.get("file_entry_count"),
            "provider_ambiguity_sonames": closure.get(
                "ambiguous_provider_soname_count"
            ),
        },
        "claim_boundary": {
            "proved": (
                "The 714-entry runtime-base retains the frozen 81-object native "
                "closure and imports all 67 extension candidates without mutating "
                "the runtime-base or canonical promoted source."
            ),
            "not_proved": (
                "The runtime-base remains production-correct after whole-prefix "
                "relocation."
            ),
        },
    }
    output = results / "runtime-base-closure-verification.json"
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 20


if __name__ == "__main__":
    raise SystemExit(main())
