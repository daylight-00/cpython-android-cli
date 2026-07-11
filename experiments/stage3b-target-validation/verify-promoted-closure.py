#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


BASELINE = {
    "file_entry_count": 3280,
    "symlink_count": 5,
    "elf_object_count": 81,
    "needed_edge_count": 329,
    "classification_edge_counts": {
        "ANDROID_SYSTEM": 249,
        "RUNTIME_INTERNAL": 80,
    },
    "unique_needed_soname_count": 9,
    "classification_unique_soname_counts": {
        "ANDROID_SYSTEM": 5,
        "RUNTIME_INTERNAL": 4,
    },
    "android_system_soname_count": 5,
    "extension_candidate_count": 67,
}

REQUIRED_OUTPUTS = [
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
    "candidate-runtime-mutation-check.txt",
    "frozen-runtime-mutation-check.txt",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def load_key_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key] = value
    return values


def same_path(value: object, expected: Path) -> bool:
    if not isinstance(value, str) or not value:
        return False
    return Path(value).resolve() == expected.resolve()


def path_is_within(value: object, root: Path) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        Path(value).resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def write_result(path: Path, result: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--expected-runtime-prefix", required=True, type=Path)
    parser.add_argument("--frozen-runtime-prefix", required=True, type=Path)
    args = parser.parse_args()

    results_dir = args.results_dir.resolve()
    expected_prefix = args.expected_runtime_prefix.resolve()
    frozen_prefix = args.frozen_runtime_prefix.resolve()
    result_path = results_dir / "promoted-closure-verification.json"
    results_dir.mkdir(parents=True, exist_ok=True)

    checks: dict[str, bool] = {}
    missing_outputs = [
        name for name in REQUIRED_OUTPUTS if not (results_dir / name).is_file()
    ]
    checks["all_required_outputs_present"] = not missing_outputs

    result: dict[str, Any] = {
        "schema_version": 1,
        "baseline": "frozen-stage3a-runtime-closure",
        "baseline_invariants": BASELINE,
        "expected_runtime_prefix": str(expected_prefix),
        "frozen_runtime_prefix": str(frozen_prefix),
        "results_dir": str(results_dir),
        "missing_outputs": missing_outputs,
        "checks": checks,
    }

    if missing_outputs:
        result["failed_checks"] = [
            name for name, passed in checks.items() if not passed
        ]
        result["pass"] = False
        write_result(result_path, result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 4

    inventory = load_json(results_dir / "summary.json")
    runtime = load_json(results_dir / "python-runtime.json")
    closure = load_json(results_dir / "closure-analysis-summary.json")
    system_probe = load_json(results_dir / "system-soname-probe-summary.json")
    extension_probe = load_json(
        results_dir / "extension-import-probe-summary.json"
    )
    inventory_mutation = load_key_values(results_dir / "mutation-check.txt")
    candidate_mutation = load_key_values(
        results_dir / "candidate-runtime-mutation-check.txt"
    )
    frozen_mutation = load_key_values(
        results_dir / "frozen-runtime-mutation-check.txt"
    )
    sysconfig_paths = runtime.get("sysconfig_paths", {})

    checks.update(
        {
            "inventory_runtime_prefix": same_path(
                inventory.get("runtime_prefix"), expected_prefix
            ),
            "inventory_symlink_count": inventory.get("symlink_count")
            == BASELINE["symlink_count"],
            "inventory_elf_object_count": inventory.get("elf_object_count")
            == BASELINE["elf_object_count"],
            "inventory_needed_edge_count": inventory.get("needed_edge_count")
            == BASELINE["needed_edge_count"],
            "inventory_classification_counts": inventory.get(
                "classification_counts"
            )
            == BASELINE["classification_edge_counts"],
            "inventory_unresolved_edge_count": inventory.get(
                "unresolved_edge_count"
            )
            == 0,
            "inventory_inspection_error_count": inventory.get(
                "inspection_error_count"
            )
            == 0,
            "inventory_mutation_check": inventory.get("mutation_check") == "PASS"
            and inventory_mutation.get("MUTATION_CHECK") == "PASS",
            "closure_needed_edge_count": closure.get("needed_edge_count")
            == BASELINE["needed_edge_count"],
            "closure_unique_needed_soname_count": closure.get(
                "unique_needed_soname_count"
            )
            == BASELINE["unique_needed_soname_count"],
            "closure_classification_edge_counts": closure.get(
                "classification_edge_counts"
            )
            == BASELINE["classification_edge_counts"],
            "closure_classification_unique_soname_counts": closure.get(
                "classification_unique_soname_counts"
            )
            == BASELINE["classification_unique_soname_counts"],
            "system_soname_count": system_probe.get(
                "unique_android_system_soname_count"
            )
            == BASELINE["android_system_soname_count"],
            "system_soname_dlopen_pass_count": system_probe.get(
                "dlopen_pass_count"
            )
            == BASELINE["android_system_soname_count"],
            "system_soname_dlopen_fail_count": system_probe.get(
                "dlopen_fail_count"
            )
            == 0,
            "extension_candidate_count": extension_probe.get(
                "extension_candidate_count"
            )
            == BASELINE["extension_candidate_count"],
            "extension_import_pass_count": extension_probe.get(
                "import_pass_count"
            )
            == BASELINE["extension_candidate_count"],
            "extension_import_fail_count": extension_probe.get(
                "import_fail_count"
            )
            == 0,
            "extension_dir_discovered_from_sys_path": extension_probe.get(
                "extension_dir_discovery_method"
            )
            == "sys.path",
            "extension_dir_under_candidate": same_path(
                extension_probe.get("extension_dir"),
                expected_prefix / "lib/python3.14/lib-dynload",
            ),
            "runtime_executable": same_path(
                runtime.get("executable"), expected_prefix / "bin/python"
            ),
            "runtime_prefix": same_path(runtime.get("prefix"), expected_prefix),
            "runtime_base_prefix": same_path(
                runtime.get("base_prefix"), expected_prefix
            ),
            "runtime_exec_prefix": same_path(
                runtime.get("exec_prefix"), expected_prefix
            ),
            "runtime_base_exec_prefix": same_path(
                runtime.get("base_exec_prefix"), expected_prefix
            ),
            "runtime_python_version": runtime.get("version_info", [])[:3]
            == [3, 14, 6],
            "runtime_platform": runtime.get("platform") == "android",
            "runtime_soabi": runtime.get("sysconfig_config_vars", {}).get(
                "SOABI"
            )
            == "cpython-314-aarch64-linux-android",
            "runtime_multiarch": runtime.get("sysconfig_config_vars", {}).get(
                "MULTIARCH"
            )
            == "aarch64-linux-android",
            "runtime_sysconfig_paths": bool(sysconfig_paths)
            and all(
                path_is_within(value, expected_prefix)
                for value in sysconfig_paths.values()
            ),
            "runtime_sys_path_contains_stdlib": any(
                same_path(value, expected_prefix / "lib/python3.14")
                for value in runtime.get("path", [])
            ),
            "runtime_sys_path_contains_lib_dynload": any(
                same_path(
                    value, expected_prefix / "lib/python3.14/lib-dynload"
                )
                for value in runtime.get("path", [])
            ),
            "runtime_ld_library_path": str(
                expected_prefix / "lib"
            )
            in (runtime.get("environment", {}).get("LD_LIBRARY_PATH") or "").split(
                ":"
            ),
            "runtime_ssl_cert_file": Path(
                runtime.get("environment", {}).get("SSL_CERT_FILE") or ""
            ).is_file(),
            "candidate_runtime_not_mutated": candidate_mutation.get("pass")
            == "true"
            and candidate_mutation.get("before")
            == candidate_mutation.get("after")
            and same_path(candidate_mutation.get("runtime_prefix"), expected_prefix),
            "frozen_runtime_not_mutated": frozen_mutation.get("pass") == "true"
            and frozen_mutation.get("before") == frozen_mutation.get("after")
            and same_path(frozen_mutation.get("runtime_prefix"), frozen_prefix),
        }
    )

    result["observed"] = {
        "inventory": inventory,
        "closure": closure,
        "system_soname_probe": system_probe,
        "extension_import_probe": extension_probe,
        "runtime_identity": {
            "executable": runtime.get("executable"),
            "prefix": runtime.get("prefix"),
            "base_prefix": runtime.get("base_prefix"),
            "platform": runtime.get("platform"),
            "version_info": runtime.get("version_info"),
            "sysconfig_platform": runtime.get("sysconfig_platform"),
        },
    }
    result["non_gating_comparisons"] = {
        "file_entry_count": {
            "baseline": BASELINE["file_entry_count"],
            "candidate": inventory.get("file_entry_count"),
            "delta": (
                inventory.get("file_entry_count", 0)
                - BASELINE["file_entry_count"]
            ),
            "reason": (
                "complete row-level inventory is retained for review; the aggregate "
                "count may include generated runtime state and is not a semantic "
                "closure gate"
            ),
        },
        "ambiguous_provider_soname_count": {
            "baseline": 8,
            "candidate": closure.get("ambiguous_provider_soname_count"),
            "reason": (
                "filesystem provider candidates depend on the tested Android/APEX "
                "image; edge and unique-SONAME classifications are the gate"
            ),
        },
    }
    result["failed_checks"] = [
        name for name, passed in checks.items() if not passed
    ]
    result["check_count"] = len(checks)
    result["pass"] = all(checks.values())

    write_result(result_path, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
