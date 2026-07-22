#!/usr/bin/env python3
"""Static review of upstream, Astral, and HW-T sysconfig/SDK boundaries."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
from typing import Any

CANONICAL_HEADER = "# system configuration generated and used by the sysconfig module"

RUNTIME_PREFIX_KEYS = {
    "prefix", "exec_prefix", "base", "platbase", "installed_base",
    "installed_platbase", "projectbase", "host_prefix", "host_exec_prefix",
}
CONSUMER_PATH_KEYS = {
    "BINDIR", "BINLIBDEST", "DESTLIB", "DESTSHARED", "INCLUDEDIR",
    "CONFINCLUDEDIR", "INCLUDEPY", "CONFINCLUDEPY", "LIBDIR", "LIBDEST",
    "LIBPL", "SCRIPTDIR", "EXENAME", "DESTDIRS", "INCLDIRSTOMAKE",
    "datarootdir",
}
TOOLCHAIN_KEYS = {
    "CC", "CXX", "AR", "ARFLAGS", "CCSHARED", "CFLAGS", "CPPFLAGS",
    "LDFLAGS", "LDSHARED", "BLDSHARED", "LDCXXSHARED", "BLDLIBRARY",
    "PY_CFLAGS", "PY_CPPFLAGS", "PY_LDFLAGS", "PY_CORE_LDFLAGS",
    "PY_STDMODULE_CFLAGS", "LIBS", "SYSLIBS", "SHELL",
}
IDENTITY_KEYS = {
    "ANDROID_API_LEVEL", "SOABI", "MULTIARCH", "EXT_SUFFIX",
    "HOST_GNU_TYPE", "TZPATH",
}
PROVENANCE_KEYS = {
    "CONFIG_ARGS", "BUILD_GNU_TYPE", "abs_builddir", "abs_srcdir",
    "builddir", "srcdir", "CONFIGURE_CFLAGS", "CONFIGURE_CPPFLAGS",
    "CONFIGURE_LDFLAGS", "PYTHON_FOR_BUILD", "PYTHON_FOR_FREEZE",
    "FREEZE_MODULE", "FREEZE_MODULE_BOOTSTRAP", "TESTPYTHON", "TESTRUNNER",
    "COVERAGE_INFO", "COVERAGE_REPORT",
}

MUTATED_RELATIVE_PATHS = (
    "lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py",
    "lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json",
    "lib/python3.14/build-details.json",
    "lib/python3.14/config-3.14-aarch64-linux-android/Makefile",
    "lib/python3.14/config-3.14-aarch64-linux-android/python-config.py",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_build_time_vars(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "build_time_vars"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, dict):
                return value
    raise ValueError(f"build_time_vars not found: {path}")


def first_line(path: Path) -> str:
    return path.read_text(encoding="utf-8").splitlines()[0]


def dynamic_override_nodes(normalizer: Path) -> dict[str, dict[str, Any]]:
    source_tree = ast.parse(normalizer.read_text(encoding="utf-8"), filename=str(normalizer))
    payload: str | None = None
    for node in source_tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_dynamic_normalizer":
            for child in ast.walk(node):
                if isinstance(child, ast.Return) and isinstance(child.value, ast.Constant) and isinstance(child.value.value, str):
                    payload = child.value.value
                    break
    if payload is None:
        raise ValueError("_dynamic_normalizer string payload not found")
    tree = ast.parse(payload, filename="<dynamic-normalizer>")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "update" or not isinstance(node.func.value, ast.Name) or node.func.value.id != "build_time_vars":
            continue
        if len(node.args) != 1 or not isinstance(node.args[0], ast.Dict):
            continue
        result: dict[str, dict[str, Any]] = {}
        for key_node, value_node in zip(node.args[0].keys, node.args[0].values):
            key = ast.literal_eval(key_node)
            try:
                literal = ast.literal_eval(value_node)
                result[key] = {"kind": "literal", "value": literal}
            except Exception:
                result[key] = {"kind": "expression", "value": ast.unparse(value_node)}
        return result
    raise ValueError("build_time_vars.update dict not found")


def category(key: str) -> str:
    if key in PROVENANCE_KEYS:
        return "producer-provenance-or-build-only"
    if key in TOOLCHAIN_KEYS:
        return "on-device-sdk-toolchain"
    if key in CONSUMER_PATH_KEYS:
        return "consumer-path"
    if key in RUNTIME_PREFIX_KEYS:
        return "runtime-prefix"
    if key in IDENTITY_KEYS:
        return "target-identity"
    if key.startswith(("MODULE_", "PY_", "TEST", "FREEZE_", "COVERAGE_")):
        return "producer-build-only-or-module-build"
    return "other"


def recursive_absolute_strings(value: Any, pointer: str = "") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            rows.extend(recursive_absolute_strings(item, f"{pointer}/{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            rows.extend(recursive_absolute_strings(item, f"{pointer}/{index}"))
    elif isinstance(value, str):
        for token in value.replace("'", " ").replace('"', " ").split():
            token = token.strip("(),;:")
            if token.startswith("/"):
                rows.append({"pointer": pointer or "/", "value": token})
    return rows


def file_mutations(official_prefix: Path, candidate_install: Path) -> list[dict[str, Any]]:
    rels = list(MUTATED_RELATIVE_PATHS)
    # Only compare Python pkg-config files that are part of the canonical
    # install surface. Upstream dependency .pc files are intentionally filtered
    # elsewhere by the artifact assembly policy and are not a sysconfig
    # normalization failure.
    for name in ("python-3.14.pc", "python-3.14-embed.pc"):
        rels.append(f"lib/pkgconfig/{name}")
    rows: list[dict[str, Any]] = []
    for rel in sorted(set(rels)):
        before = official_prefix / rel
        after = candidate_install / rel
        row: dict[str, Any] = {"path": rel, "official_present": before.is_file(), "candidate_present": after.is_file()}
        if before.is_file():
            row["official_sha256"] = sha256_file(before)
            row["official_size_bytes"] = before.stat().st_size
        if after.is_file():
            row["candidate_sha256"] = sha256_file(after)
            row["candidate_size_bytes"] = after.stat().st_size
        row["changed"] = bool(before.is_file() and after.is_file() and row["official_sha256"] != row["candidate_sha256"])
        rows.append(row)
    return rows


def analyze(
    official_prefix: Path,
    candidate_install: Path,
    normalizer: Path,
    astral_observation: Path,
    ut2_authority: Path,
    ut3_authority: Path,
) -> dict[str, Any]:
    rel = "lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py"
    upstream_path = official_prefix / rel
    candidate_path = candidate_install / rel
    upstream = parse_build_time_vars(upstream_path)
    candidate_literal = parse_build_time_vars(candidate_path)
    overrides = dynamic_override_nodes(normalizer)

    literal_diffs = []
    for key in sorted(set(upstream) | set(candidate_literal)):
        if upstream.get(key) != candidate_literal.get(key):
            literal_diffs.append({
                "key": key,
                "category": category(key),
                "upstream": upstream.get(key),
                "candidate_literal": candidate_literal.get(key),
            })

    override_rows = [
        {"key": key, "category": category(key), **value}
        for key, value in sorted(overrides.items())
    ]
    overridden_provenance = [row for row in override_rows if row["category"] == "producer-provenance-or-build-only"]
    redundant_identity = []
    for row in override_rows:
        if row["category"] != "target-identity" or row["kind"] != "literal":
            continue
        if upstream.get(row["key"]) == row["value"]:
            redundant_identity.append(row["key"])

    astral = json.loads(astral_observation.read_text(encoding="utf-8"))
    astral_vars = astral.get("python_json", {}).get("value", {}).get("python_config_vars", {})
    astral_abs = recursive_absolute_strings(astral_vars)
    astral_build_install = [row for row in astral_abs if row["value"].startswith(("/build", "/install", "/tools"))]

    ut2 = json.loads(ut2_authority.read_text(encoding="utf-8"))
    ut3 = json.loads(ut3_authority.read_text(encoding="utf-8"))
    wheel_norm = ut3.get("native_extension_wheel", {}).get("extension_normalization", {})
    before_runpath = wheel_norm.get("before", {}).get("runpath", [])
    after_runpath = wheel_norm.get("after", {}).get("runpath", [])

    mutations = file_mutations(official_prefix, candidate_install)
    changed_files = [row["path"] for row in mutations if row.get("changed")]
    checks = {
        "official_header_is_cpython_canonical": first_line(upstream_path) == CANONICAL_HEADER,
        "candidate_header_is_not_cpython_canonical": first_line(candidate_path) != CANONICAL_HEADER,
        "literal_dictionary_rewritten": len(literal_diffs) > 0,
        "dynamic_override_exists": len(overrides) > 0,
        "producer_provenance_overridden": any(row["key"] in {"CONFIG_ARGS", "BUILD_GNU_TYPE"} for row in overridden_provenance),
        "astral_golden_retains_build_or_install_absolute_paths": len(astral_build_install) > 0,
        "ut2_proved_runtime_and_relocation_before_ut3_normalization": (
            ut2.get("claim_boundary", {}).get("whole_prefix_relocation") is True
            and ut2.get("status") == "frozen-pass-bounded-android-runtime-and-relocation"
        ),
        "ut3_native_wheel_required_post_build_runpath_removal": bool(before_runpath) and not after_runpath,
        "all_expected_metadata_files_compared": all(row["official_present"] and row["candidate_present"] for row in mutations),
    }
    failed = sorted(name for name, ok in checks.items() if not ok)
    return {
        "schema_version": 1,
        "review_kind": "epoch3-rb3-sysconfig-and-on-device-sdk-static-boundary-review",
        "status": "passed-static-review-target-profile-probe-required" if not failed else "failed-static-review",
        "pass": not failed,
        "checks": checks,
        "failed_checks": failed,
        "inputs": {
            "official_sysconfigdata": {"sha256": sha256_file(upstream_path), "header": first_line(upstream_path), "key_count": len(upstream)},
            "candidate_sysconfigdata": {"sha256": sha256_file(candidate_path), "header": first_line(candidate_path), "key_count": len(candidate_literal)},
            "normalizer_sha256": sha256_file(normalizer),
            "astral_observation_sha256": sha256_file(astral_observation),
            "ut2_authority_sha256": sha256_file(ut2_authority),
            "ut3_authority_sha256": sha256_file(ut3_authority),
        },
        "measurements": {
            "literal_changed_key_count": len(literal_diffs),
            "dynamic_override_key_count": len(overrides),
            "mutated_metadata_file_count": len(changed_files),
            "astral_absolute_path_token_count": len(astral_abs),
            "astral_build_install_tool_path_token_count": len(astral_build_install),
            "ut3_before_runpath": before_runpath,
            "ut3_after_runpath": after_runpath,
        },
        "literal_differences": literal_diffs,
        "dynamic_overrides": override_rows,
        "producer_provenance_overrides": overridden_provenance,
        "redundant_identity_overrides": sorted(redundant_identity),
        "metadata_file_mutations": mutations,
        "astral_absolute_path_examples": astral_build_install[:40],
        "finding": {
            "runtime_normalization_required_by_ut2": False,
            "zero_producer_absolute_paths_is_astral_derived": False,
            "current_normalizer_is_minimal": False,
            "current_normalizer_conflates": [
                "runtime relocation",
                "consumer path convenience",
                "on-device compiler policy",
                "producer provenance sanitization",
                "target identity",
            ],
            "on_device_sdk_contract_complete": False,
            "reason": "UT-3 removed a Termux RUNPATH after wheel build; the canonical consumer flow does not yet own that output normalization step.",
        },
        "required_target_profiles": [
            "C-current-control",
            "H-current-plus-canonical-header",
            "U-upstream-metadata-restored",
            "M-upstream-preserved-minimal-consumer-overlay",
        ],
        "claim_boundary": {
            "canonical_artifact_bytes_changed": False,
            "profile_selected": False,
            "artifact_family_superseded": False,
            "rb3_closed": False,
            "selectable": False,
            "publication": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-prefix", type=Path, required=True)
    parser.add_argument("--candidate-install", type=Path, required=True)
    parser.add_argument("--normalizer", type=Path, required=True)
    parser.add_argument("--astral-observation", type=Path, required=True)
    parser.add_argument("--ut2-authority", type=Path, required=True)
    parser.add_argument("--ut3-authority", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(
        args.official_prefix.resolve(), args.candidate_install.resolve(),
        args.normalizer.resolve(), args.astral_observation.resolve(),
        args.ut2_authority.resolve(), args.ut3_authority.resolve(),
    )
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
