#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

RUNTIME_COMPONENTS = ["RUNTIME_BASE", "RUNTIME_METADATA", "LICENSE"]


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


def artifact_by_name(policy: dict[str, Any], name: str) -> dict[str, Any]:
    for item in policy.get("artifacts", []):
        if isinstance(item, dict) and item.get("artifact") == name:
            return item
    return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--policy-verification", required=True, type=Path)
    parser.add_argument("--reassessment-verification", required=True, type=Path)
    parser.add_argument("--runtime-fingerprint", required=True, type=Path)
    parser.add_argument("--canonical-fingerprint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-component-manifest", required=True)
    parser.add_argument("--expected-runtime-fingerprint", required=True)
    parser.add_argument("--expected-canonical-fingerprint", required=True)
    parser.add_argument("--expected-runtime-entry-count", type=int, default=714)
    parser.add_argument("--expected-canonical-entry-count", type=int, default=3155)
    args = parser.parse_args()

    missing: list[str] = []
    errors: dict[str, str] = {}
    policy = read_json_safe(args.policy.resolve(), missing, errors)
    policy_verification = read_json_safe(
        args.policy_verification.resolve(), missing, errors
    )
    reassessment = read_json_safe(
        args.reassessment_verification.resolve(), missing, errors
    )
    runtime = read_json_safe(args.runtime_fingerprint.resolve(), missing, errors)
    canonical = read_json_safe(
        args.canonical_fingerprint.resolve(), missing, errors
    )

    runtime_artifact = artifact_by_name(policy, "runtime-base")
    runtime_variant = reassessment.get("variant_summary", {}).get(
        "runtime-base", {}
    )
    runtime_types = runtime.get("type_counts", {})
    canonical_types = canonical.get("type_counts", {})

    checks: dict[str, bool] = {
        "all_required_inputs_present": not missing,
        "all_required_inputs_parse": not errors,
        "policy_schema": policy.get("schema_version") == 1,
        "policy_pass": policy.get("pass") is True,
        "policy_check_count_18": policy.get("check_count") == 18,
        "policy_failed_checks_empty": policy.get("failed_checks") == [],
        "policy_component_manifest_matches": policy.get(
            "component_manifest_sha256"
        )
        == args.expected_component_manifest,
        "policy_verification_schema": policy_verification.get("schema_version")
        == 1,
        "policy_verification_pass": policy_verification.get("pass") is True,
        "policy_verification_check_count_34": policy_verification.get(
            "check_count"
        )
        == 34,
        "policy_verification_failed_checks_empty": policy_verification.get(
            "failed_checks"
        )
        == [],
        "policy_verification_missing_outputs_empty": policy_verification.get(
            "missing_outputs"
        )
        == [],
        "policy_verification_parse_errors_empty": policy_verification.get(
            "parse_errors"
        )
        == {},
        "policy_verification_manifest_matches": policy_verification.get(
            "component_manifest_sha256"
        )
        == args.expected_component_manifest,
        "runtime_artifact_components_exact": runtime_artifact.get("components")
        == RUNTIME_COMPONENTS,
        "runtime_artifact_entry_count": runtime_artifact.get("entry_count")
        == args.expected_runtime_entry_count,
        "runtime_artifact_file_bytes": runtime_artifact.get("file_bytes")
        == 38_759_749,
        "runtime_artifact_selected": runtime_artifact.get("disposition")
        == "selected-candidate",
        "reassessment_schema": reassessment.get("schema_version") == 1,
        "reassessment_pass": reassessment.get("pass") is True,
        "reassessment_check_count_114": reassessment.get("check_count") == 114,
        "reassessment_failed_checks_empty": reassessment.get("failed_checks")
        == [],
        "reassessment_missing_outputs_empty": reassessment.get(
            "missing_outputs"
        )
        == [],
        "reassessment_parse_errors_empty": reassessment.get("parse_errors")
        == {},
        "reassessment_component_manifest_matches": reassessment.get(
            "expected_component_manifest"
        )
        == args.expected_component_manifest,
        "reassessment_source_fingerprint_matches": reassessment.get(
            "expected_source_fingerprint"
        )
        == args.expected_canonical_fingerprint,
        "reassessment_runtime_capability_pass": runtime_variant.get(
            "corrected_capability_pass"
        )
        is True,
        "reassessment_runtime_entry_count": runtime_variant.get("entry_count")
        == args.expected_runtime_entry_count,
        "reassessment_runtime_fingerprint": runtime_variant.get("fingerprint")
        == args.expected_runtime_fingerprint,
        "reassessment_runtime_phello_frozen": runtime_variant.get(
            "phello_origin"
        )
        == "frozen",
        "reassessment_runtime_test_demo_absent": runtime_variant.get(
            "test_demo_present"
        )
        is False,
        "runtime_fingerprint_schema": runtime.get("schema_version") == 1,
        "runtime_fingerprint_pass": runtime.get("pass") is True,
        "runtime_entry_count": runtime.get("entry_count")
        == args.expected_runtime_entry_count,
        "runtime_fingerprint_expected": runtime.get("fingerprint")
        == args.expected_runtime_fingerprint,
        "runtime_type_counts_exact": runtime_types
        == {
            "DIRECTORY": 57,
            "REGULAR": 654,
            "SPECIAL": 0,
            "SYMLINK": 3,
        },
        "runtime_pycache_zero": runtime.get("pycache_paths") == [],
        "runtime_special_zero": runtime.get("special_paths") == [],
        "canonical_fingerprint_schema": canonical.get("schema_version") == 1,
        "canonical_fingerprint_pass": canonical.get("pass") is True,
        "canonical_entry_count": canonical.get("entry_count")
        == args.expected_canonical_entry_count,
        "canonical_fingerprint_expected": canonical.get("fingerprint")
        == args.expected_canonical_fingerprint,
        "canonical_type_counts_exact": canonical_types
        == {
            "DIRECTORY": 216,
            "REGULAR": 2934,
            "SPECIAL": 0,
            "SYMLINK": 5,
        },
        "canonical_pycache_zero": canonical.get("pycache_paths") == [],
        "canonical_special_zero": canonical.get("special_paths") == [],
        "runtime_current_matches_reassessment": runtime.get("fingerprint")
        == runtime_variant.get("fingerprint"),
        "canonical_current_matches_reassessment": canonical.get("fingerprint")
        == reassessment.get("expected_source_fingerprint"),
    }

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "missing_inputs": sorted(set(missing)),
        "parse_errors": errors,
        "expected": {
            "component_manifest_sha256": args.expected_component_manifest,
            "runtime_fingerprint": args.expected_runtime_fingerprint,
            "canonical_fingerprint": args.expected_canonical_fingerprint,
            "runtime_entry_count": args.expected_runtime_entry_count,
            "canonical_entry_count": args.expected_canonical_entry_count,
        },
        "observed": {
            "runtime_artifact": runtime_artifact,
            "runtime_variant": runtime_variant,
            "runtime_fingerprint": runtime,
            "canonical_fingerprint": canonical,
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 19


if __name__ == "__main__":
    raise SystemExit(main())
