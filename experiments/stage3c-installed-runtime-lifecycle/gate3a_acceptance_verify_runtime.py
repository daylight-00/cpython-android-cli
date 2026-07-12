#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

from gate3a_acceptance_verify_support import PORTABLE, cjson, path_within, read_json, same_path


def runtime_checks(ctx: Any) -> dict[str, bool]:
    gate1 = ctx.gate1
    engine = ctx.engine
    registry = ctx.registry
    strict_before = ctx.strict_before
    strict_after = ctx.strict_after
    portable_before = ctx.portable_before
    portable_after = ctx.portable_after
    base = ctx.base
    venv = ctx.venv
    uv_run = ctx.uv_run
    inventory = ctx.inventory
    closure = ctx.closure
    system_probe = ctx.system_probe
    extension_probe = ctx.extension_probe
    prefix = ctx.prefix
    return {
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
        "strict_before_shape_safe": strict_before.get("pass") is True
        and strict_before.get("entry_count") == 714
        and strict_before.get("pycache_paths") == []
        and strict_before.get("special_paths") == [],
        "strict_after_shape_safe": strict_after.get("pass") is True
        and strict_after.get("entry_count") == 714
        and strict_after.get("pycache_paths") == []
        and strict_after.get("special_paths") == [],
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
        "smoke_markers": "STAGE2C_SMOKE=PASS" in ctx.smoke_text
        and "HTTPS status: 200" in ctx.smoke_text
        and "== uv venv ==" in ctx.smoke_text
        and "== uv run ==" in ctx.smoke_text,
        "closure_workflow_zero": ctx.closure_workflow.get("pass") is True
        and all(value == 0 for value in ctx.closure_workflow.get("returncodes", {}).values()),
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
        "input_identity_unchanged": ctx.input_before.get("pass") is True
        and ctx.input_after.get("pass") is True
        and ctx.input_before.get("entry_count") == ctx.input_after.get("entry_count")
        and ctx.input_before.get("fingerprint") == ctx.input_after.get("fingerprint"),
        "machine_json_canonical": not ctx.missing_files
        and all(path.read_bytes() == cjson(read_json(path)) for path in ctx.generated_jsons),
        "claim_boundary_gate2_separate": "relocation" in ctx.scenario_summary.get("claim_boundary", {}).get("not_proved", "").lower()
        or "runtime behavior" in ctx.scenario_summary.get("claim_boundary", {}).get("not_proved", "").lower(),
    }
