#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_PHASE4_RESULT_INDEX = "878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce"
EXPECTED_RUNTIME_FINGERPRINT = "9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796"
EXPECTED_ARTIFACT_ID = "cpython-android-cli-3.14.6-android24-aarch64-runtime-base"
EXPECTED_TYPES = {"directory": 57, "regular": 654, "symlink": 3}


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


def record_from_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": entry["payload_path"],
        "owner_artifact": "runtime-base",
        "type": entry["type"],
        "mode": entry["mode"],
        "size": entry.get("size"),
        "sha256": entry.get("sha256"),
        "symlink_target": entry.get("symlink_target"),
        "component": entry.get("component", ""),
        "elf": entry.get("elf") is True,
    }


def data_rows(path: Path) -> int:
    return max(len(path.read_text(encoding="utf-8").splitlines()) - 1, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase4-results", required=True, type=Path)
    parser.add_argument("--installed-prefix", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--install-result", required=True, type=Path)
    parser.add_argument("--engine-verification", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--installed-before", required=True, type=Path)
    parser.add_argument("--installed-after", required=True, type=Path)
    parser.add_argument("--input-before", required=True, type=Path)
    parser.add_argument("--input-after", required=True, type=Path)
    parser.add_argument("--base-probe", required=True, type=Path)
    parser.add_argument("--venv-probe", required=True, type=Path)
    parser.add_argument("--uv-run-probe", required=True, type=Path)
    parser.add_argument("--smoke-log", required=True, type=Path)
    parser.add_argument("--closure-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    phase4 = args.phase4_results.resolve()
    prefix = args.installed_prefix.resolve()
    manifest = read_json(args.manifest.resolve())
    install = read_json(args.install_result.resolve())
    engine = read_json(args.engine_verification.resolve())
    registry = read_json(args.registry.resolve())
    installed_before = read_json(args.installed_before.resolve())
    installed_after = read_json(args.installed_after.resolve())
    input_before = read_json(args.input_before.resolve())
    input_after = read_json(args.input_after.resolve())
    base = read_json(args.base_probe.resolve())
    venv = read_json(args.venv_probe.resolve())
    uv_run = read_json(args.uv_run_probe.resolve())
    smoke = args.smoke_log.resolve().read_text(encoding="utf-8")
    closure_dir = args.closure_dir.resolve()
    closure_workflow = read_json(closure_dir / "workflow-status.json")
    inventory = read_json(closure_dir / "summary.json")
    runtime = read_json(closure_dir / "python-runtime.json")
    closure = read_json(closure_dir / "closure-analysis-summary.json")
    system_probe = read_json(closure_dir / "system-soname-probe-summary.json")
    extension_probe = read_json(closure_dir / "extension-import-probe-summary.json")

    phase4_source = read_json(phase4 / "source-integration.json")
    phase4_recovery = read_json(phase4 / "recovery-replay/scenario.json")
    phase4_recovery_verify = read_json(phase4 / "recovery-replay/verification.json")
    phase4_durability = read_json(phase4 / "durability-replay/scenario.json")
    phase4_durability_verify = read_json(phase4 / "durability-replay/verification.json")
    phase4_exercise = read_json(phase4 / "exercises/exercise.json")
    phase4_trace = read_json(phase4 / "trace-verification.json")
    phase4_overall = read_json(phase4 / "verification.json")
    phase4_workflow = read_json(phase4 / "workflow-status.json")

    owned = [entry for entry in manifest["entries"] if entry["entry_class"] == "OWNED_PAYLOAD"]
    expected_rows = [record_from_entry(entry) for entry in owned]
    expected_by_path = {row["path"]: row for row in expected_rows}
    registry_rows = registry.get("owned_paths", [])
    registry_by_path = {row.get("path"): row for row in registry_rows}
    type_counts = {
        kind: sum(1 for entry in owned if entry["type"] == kind)
        for kind in EXPECTED_TYPES
    }
    sysconfig_paths = base.get("sysconfig_paths", {})

    required_closure_outputs = {
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
    }

    checks = {
        "phase4_result_index_exact": sha256_file(phase4 / "result-index.json")
        == EXPECTED_PHASE4_RESULT_INDEX,
        "phase4_source_29": phase4_source.get("pass") is True
        and phase4_source.get("check_count") == 29,
        "phase4_recovery_55": phase4_recovery.get("pass") is True
        and phase4_recovery.get("check_count") == 55,
        "phase4_recovery_verify_82": phase4_recovery_verify.get("pass") is True
        and phase4_recovery_verify.get("check_count") == 82,
        "phase4_durability_64": phase4_durability.get("pass") is True
        and phase4_durability.get("check_count") == 64,
        "phase4_durability_verify_53": phase4_durability_verify.get("pass") is True
        and phase4_durability_verify.get("check_count") == 53,
        "phase4_exercise_20": phase4_exercise.get("pass") is True
        and phase4_exercise.get("check_count") == 20,
        "phase4_trace_29": phase4_trace.get("pass") is True
        and phase4_trace.get("check_count") == 29
        and phase4_trace.get("violations") == [],
        "phase4_overall_36": phase4_overall.get("pass") is True
        and phase4_overall.get("check_count") == 36,
        "phase4_workflow_zero": phase4_workflow.get("pass") is True
        and all(value == 0 for value in phase4_workflow.get("returncodes", {}).values()),
        "phase4_input_unchanged": input_before.get("pass") is True
        and input_after.get("pass") is True
        and input_before.get("entry_count") == input_after.get("entry_count")
        and input_before.get("fingerprint") == input_after.get("fingerprint"),
        "manifest_schema": manifest.get("schema_version") == 1,
        "manifest_artifact": manifest.get("artifact", {}).get("name") == "runtime-base",
        "manifest_artifact_id": manifest.get("artifact", {}).get("artifact_id")
        == EXPECTED_ARTIFACT_ID,
        "manifest_runtime_fingerprint": manifest.get("compatibility", {}).get(
            "runtime_base_fingerprint"
        )
        == EXPECTED_RUNTIME_FINGERPRINT,
        "manifest_owned_count_714": len(owned) == 714,
        "manifest_type_counts_exact": type_counts == EXPECTED_TYPES,
        "install_pass": install.get("pass") is True,
        "install_operation_exact": install.get("operation") == "install"
        and install.get("artifact") == "runtime-base",
        "install_create_714": install.get("action_counts") == {"create": 714},
        "install_mutation_count_715": install.get("mutation_count") == 715,
        "install_not_noop": install.get("noop") is False,
        "engine_verify_pass": engine.get("pass") is True,
        "engine_verify_artifact_count_1": engine.get("artifact_count") == 1,
        "engine_verify_owned_count_714": engine.get("owned_path_count") == 714,
        "engine_verify_bad_paths_empty": engine.get("bad_paths") == [],
        "registry_schema": registry.get("schema_version") == 1,
        "registry_kind": registry.get("registry_kind")
        == "cpython-android-cli-installed-ownership-registry",
        "registry_artifact_count_1": len(registry.get("artifacts", [])) == 1,
        "registry_artifact_name": registry.get("artifacts", [{}])[0].get("artifact")
        == "runtime-base",
        "registry_artifact_id": registry.get("artifacts", [{}])[0].get("artifact_id")
        == EXPECTED_ARTIFACT_ID,
        "registry_owned_count_714": len(registry_rows) == 714,
        "registry_paths_sorted": [row.get("path") for row in registry_rows]
        == sorted(row.get("path") for row in registry_rows),
        "registry_paths_unique": len(registry_by_path) == 714,
        "registry_path_set_exact": set(registry_by_path) == set(expected_by_path),
        "registry_rows_exact": registry_by_path == expected_by_path,
        "installed_before_pass": installed_before.get("pass") is True,
        "installed_after_pass": installed_after.get("pass") is True,
        "installed_entry_count_714": installed_before.get("entry_count") == 714
        and installed_after.get("entry_count") == 714,
        "installed_fingerprint_exact": installed_before.get("fingerprint")
        == EXPECTED_RUNTIME_FINGERPRINT,
        "installed_not_mutated": installed_before.get("fingerprint")
        == installed_after.get("fingerprint"),
        "installed_pycache_zero": installed_before.get("pycache_paths") == []
        and installed_after.get("pycache_paths") == [],
        "installed_special_zero": installed_before.get("special_paths") == []
        and installed_after.get("special_paths") == [],
        "base_probe_pass": base.get("pass") is True,
        "base_probe_identity": same_path(base.get("executable"), prefix / "bin/python")
        and same_path(base.get("prefix"), prefix)
        and same_path(base.get("base_prefix"), prefix)
        and same_path(base.get("exec_prefix"), prefix)
        and same_path(base.get("base_exec_prefix"), prefix),
        "base_probe_version": base.get("version_info") == [3, 14, 6],
        "base_probe_platform": base.get("platform") == "android",
        "base_probe_machine": base.get("machine") == "aarch64",
        "base_probe_abi": base.get("soabi") == "cpython-314-aarch64-linux-android"
        and base.get("multiarch") == "aarch64-linux-android",
        "base_probe_sysconfig_within": bool(sysconfig_paths)
        and all(path_within(value, prefix) for value in sysconfig_paths.values()),
        "base_probe_https_200": base.get("https_status") == 200,
        "base_probe_child_identity": same_path(
            base.get("child_identity", {}).get("executable"), prefix / "bin/python"
        )
        and same_path(base.get("child_identity", {}).get("prefix"), prefix)
        and same_path(base.get("child_identity", {}).get("base_prefix"), prefix),
        "base_probe_imports": all(
            base.get("imports", {}).get(name)
            for name in ("ssl", "sqlite3", "bz2", "ctypes", "lzma", "zlib")
        ),
        "smoke_marker": "STAGE2C_SMOKE=PASS" in smoke,
        "smoke_https": "HTTPS status: 200" in smoke,
        "smoke_uv_venv": "== uv venv ==" in smoke,
        "smoke_uv_run": "== uv run ==" in smoke and "anyio" in smoke,
        "venv_probe_pass": venv.get("pass") is True,
        "venv_probe_is_venv": venv.get("prefix") != venv.get("base_prefix"),
        "venv_probe_base_installed": same_path(venv.get("base_prefix"), prefix),
        "venv_probe_executable_within": path_within(venv.get("executable"), args.venv_probe.resolve().parent / "venv"),
        "uv_run_probe_pass": uv_run.get("pass") is True,
        "uv_run_probe_is_venv": uv_run.get("prefix") != uv_run.get("base_prefix"),
        "uv_run_probe_base_installed": same_path(uv_run.get("base_prefix"), prefix),
        "uv_run_anyio": uv_run.get("imports", {}).get("anyio") == "anyio",
        "closure_outputs_complete": required_closure_outputs
        <= {path.name for path in closure_dir.iterdir() if path.is_file()},
        "closure_workflow_zero": closure_workflow.get("pass") is True
        and set(closure_workflow.get("returncodes", {}))
        == {"inventory", "closure_analysis", "extension_imports"}
        and all(value == 0 for value in closure_workflow.get("returncodes", {}).values()),
        "closure_inventory_identity": same_path(inventory.get("runtime_prefix"), prefix),
        "closure_inventory_counts": inventory.get("symlink_count") == 3
        and inventory.get("elf_object_count") == 81
        and inventory.get("needed_edge_count") == 329,
        "closure_inventory_classes": inventory.get("classification_counts")
        == {"ANDROID_SYSTEM": 249, "RUNTIME_INTERNAL": 80},
        "closure_inventory_clean": inventory.get("unresolved_edge_count") == 0
        and inventory.get("inspection_error_count") == 0
        and inventory.get("mutation_check") == "PASS",
        "closure_tsv_clean": data_rows(closure_dir / "unresolved.tsv") == 0
        and data_rows(closure_dir / "errors.tsv") == 0,
        "closure_analysis_counts": closure.get("needed_edge_count") == 329
        and closure.get("unique_needed_soname_count") == 9,
        "closure_analysis_classes": closure.get("classification_edge_counts")
        == {"ANDROID_SYSTEM": 249, "RUNTIME_INTERNAL": 80}
        and closure.get("classification_unique_soname_counts")
        == {"ANDROID_SYSTEM": 5, "RUNTIME_INTERNAL": 4},
        "closure_analysis_unresolved_zero": closure.get("unresolved_edge_count", 0) == 0,
        "system_soname_probe_5_5": system_probe.get("unique_android_system_soname_count") == 5
        and system_probe.get("dlopen_pass_count") == 5
        and system_probe.get("dlopen_fail_count") == 0,
        "extension_imports_67_67": extension_probe.get("extension_candidate_count") == 67
        and extension_probe.get("import_pass_count") == 67
        and extension_probe.get("import_fail_count") == 0,
        "extension_directory_exact": same_path(
            extension_probe.get("extension_dir"), prefix / "lib/python3.14/lib-dynload"
        )
        and extension_probe.get("extension_dir_discovery_method") == "sys.path",
        "closure_runtime_identity": same_path(runtime.get("executable"), prefix / "bin/python")
        and same_path(runtime.get("prefix"), prefix)
        and same_path(runtime.get("base_prefix"), prefix),
        "all_machine_json_canonical": all(
            path.read_bytes() == canonical_json_bytes(read_json(path))
            for path in (
                args.install_result.resolve(),
                args.engine_verification.resolve(),
                args.registry.resolve(),
                args.installed_before.resolve(),
                args.installed_after.resolve(),
                args.base_probe.resolve(),
                args.venv_probe.resolve(),
                args.uv_run_probe.resolve(),
            )
        ),
    }
    if len(checks) != 76:
        raise RuntimeError(f"unexpected check count: {len(checks)}")
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "observed": {
            "manifest_owned_count": len(owned),
            "registry_owned_count": len(registry_rows),
            "installed_fingerprint": installed_before.get("fingerprint"),
            "elf_object_count": inventory.get("elf_object_count"),
            "needed_edge_count": inventory.get("needed_edge_count"),
            "extension_import_pass_count": extension_probe.get("import_pass_count"),
            "https_status": base.get("https_status"),
        },
        "claim_boundary": {
            "proved": "The frozen runtime-base was installed through the frozen Phase 4 engine and retained exact registry, tree, runtime, HTTPS, uv, native-closure, and extension-import behavior on its original installation path.",
            "not_proved": "Relocation, later reinstall and repair lifecycle, exact uninstall preservation, upgrade, and downgrade remain separate gates.",
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 61


if __name__ == "__main__":
    raise SystemExit(main())
