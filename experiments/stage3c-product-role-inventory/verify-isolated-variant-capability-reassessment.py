#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VARIANTS = (
    "runtime-base",
    "runtime-development",
    "runtime-test",
    "runtime-supported",
)
EXPECTED_COUNTS = {
    "runtime-base": 714,
    "runtime-development": 1168,
    "runtime-test": 2502,
    "runtime-supported": 2956,
}
EXPECTED_TEST_DEMO = {
    "runtime-base": False,
    "runtime-development": False,
    "runtime-test": True,
    "runtime-supported": True,
}
EXPECTED_ORIGINAL_FAILED_CHECKS = {
    "runtime-base_capability_pass",
    "runtime-development_capability_pass",
    "workflow_status_pass",
}
EXPECTED_WORKFLOW_KEYS = {
    "capabilities",
    "runtime_base_smoke",
    "development_extension_compile",
    "development_extension_import",
    "test_addon",
    "fidelity_after",
    "runtime_base_fingerprint_after",
    "runtime_development_fingerprint_after",
    "runtime_test_fingerprint_after",
    "runtime_supported_fingerprint_after",
    "source_fingerprint_after",
}


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


def phello_is_frozen(capability: dict[str, Any]) -> bool:
    module = capability.get("modules", {}).get("__phello__", {})
    return module.get("success") is True and module.get("spec", {}).get(
        "origin"
    ) == "frozen"


def all_module_expectations_true(capability: dict[str, Any]) -> bool:
    values = capability.get("module_expectations", {})
    return bool(values) and all(value is True for value in values.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-results", required=True, type=Path)
    parser.add_argument("--reassessment-results", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-source-fingerprint", required=True)
    parser.add_argument("--expected-component-manifest", required=True)
    args = parser.parse_args()

    original = args.original_results.resolve()
    reassessment = args.reassessment_results.resolve()
    output = args.output.resolve()
    missing: list[str] = []
    errors: dict[str, str] = {}

    original_verification = read_json_safe(
        original / "verification.json", missing, errors
    )
    original_workflow = read_json_safe(
        original / "workflow-status.json", missing, errors
    )
    materialization = read_json_safe(
        original / "materialization.json", missing, errors
    )
    fidelity_before = read_json_safe(
        original / "variant-fidelity-before.json", missing, errors
    )
    fidelity_after = read_json_safe(
        original / "variant-fidelity-after.json", missing, errors
    )
    original_source_before = read_json_safe(
        original / "source-before.json", missing, errors
    )
    original_source_after = read_json_safe(
        original / "source-after.json", missing, errors
    )
    current_source_before = read_json_safe(
        reassessment / "source-before.json", missing, errors
    )
    current_source_after = read_json_safe(
        reassessment / "source-after.json", missing, errors
    )

    original_capabilities = {
        variant: read_json_safe(
            original / "capabilities" / f"{variant}.json", missing, errors
        )
        for variant in VARIANTS
    }
    corrected_capabilities = {
        variant: read_json_safe(
            reassessment / "capabilities" / f"{variant}.json", missing, errors
        )
        for variant in VARIANTS
    }
    original_variant_before = {
        variant: read_json_safe(
            original / "fingerprints" / f"{variant}-before.json",
            missing,
            errors,
        )
        for variant in VARIANTS
    }
    original_variant_after = {
        variant: read_json_safe(
            original / "fingerprints" / f"{variant}-after.json",
            missing,
            errors,
        )
        for variant in VARIANTS
    }
    current_variant_before = {
        variant: read_json_safe(
            reassessment / "fingerprints" / f"{variant}-before.json",
            missing,
            errors,
        )
        for variant in VARIANTS
    }
    current_variant_after = {
        variant: read_json_safe(
            reassessment / "fingerprints" / f"{variant}-after.json",
            missing,
            errors,
        )
        for variant in VARIANTS
    }

    workflow_returncodes = original_workflow.get("returncodes", {})
    noncapability_returncodes = {
        key: value
        for key, value in workflow_returncodes.items()
        if key != "capabilities"
    }

    checks: dict[str, bool] = {
        "all_required_outputs_present": not missing,
        "all_required_outputs_parse": not errors,
        "original_verification_schema": original_verification.get(
            "schema_version"
        )
        == 1,
        "original_verification_expected_failure": original_verification.get(
            "pass"
        )
        is False,
        "original_verification_check_count": original_verification.get(
            "check_count"
        )
        == 46,
        "original_failed_checks_exact": set(
            original_verification.get("failed_checks", [])
        )
        == EXPECTED_ORIGINAL_FAILED_CHECKS,
        "original_missing_outputs_empty": original_verification.get(
            "missing_outputs"
        )
        == [],
        "original_parse_errors_empty": original_verification.get("parse_errors")
        == {},
        "original_workflow_expected_failure": original_workflow.get("pass")
        is False,
        "original_workflow_keys_exact": set(workflow_returncodes)
        == EXPECTED_WORKFLOW_KEYS,
        "original_capability_returncode_16": workflow_returncodes.get(
            "capabilities"
        )
        == 16,
        "original_noncapability_returncodes_zero": bool(
            noncapability_returncodes
        )
        and all(value == 0 for value in noncapability_returncodes.values()),
        "materialization_pass_7": materialization.get("pass") is True
        and materialization.get("check_count") == 7,
        "component_manifest_matches": materialization.get(
            "component_manifest_sha256"
        )
        == args.expected_component_manifest,
        "fidelity_before_pass_15": fidelity_before.get("pass") is True
        and fidelity_before.get("check_count") == 15,
        "fidelity_after_pass_15": fidelity_after.get("pass") is True
        and fidelity_after.get("check_count") == 15,
        "original_source_before_pass": original_source_before.get("pass") is True,
        "original_source_after_pass": original_source_after.get("pass") is True,
        "original_source_fingerprint_expected": original_source_before.get(
            "fingerprint"
        )
        == args.expected_source_fingerprint,
        "original_source_unchanged": original_source_before.get("fingerprint")
        == original_source_after.get("fingerprint"),
        "current_source_before_pass": current_source_before.get("pass") is True,
        "current_source_after_pass": current_source_after.get("pass") is True,
        "current_source_fingerprint_expected": current_source_before.get(
            "fingerprint"
        )
        == args.expected_source_fingerprint,
        "current_source_unchanged": current_source_before.get("fingerprint")
        == current_source_after.get("fingerprint"),
        "current_source_matches_original": current_source_before.get(
            "fingerprint"
        )
        == original_source_after.get("fingerprint"),
        "source_entry_count_3155": original_source_before.get("entry_count")
        == original_source_after.get("entry_count")
        == current_source_before.get("entry_count")
        == current_source_after.get("entry_count")
        == 3155,
    }

    for variant in VARIANTS:
        first = original_capabilities[variant]
        corrected = corrected_capabilities[variant]
        expected_original_pass = variant in {"runtime-test", "runtime-supported"}
        expected_original_failures = (
            [] if expected_original_pass else ["module_expectations_match"]
        )
        expected_original_phello_expectation = expected_original_pass

        checks[f"{variant}_original_capability_schema"] = (
            first.get("schema_version") == 1
        )
        checks[f"{variant}_original_capability_pass_state"] = (
            first.get("pass") is expected_original_pass
        )
        checks[f"{variant}_original_failed_checks_exact"] = (
            first.get("failed_checks") == expected_original_failures
        )
        checks[f"{variant}_original_check_count_15"] = (
            first.get("check_count") == 15
        )
        checks[f"{variant}_original_phello_frozen"] = phello_is_frozen(first)
        checks[f"{variant}_original_phello_expectation_observed"] = (
            first.get("module_expectations", {}).get("__phello__")
            is expected_original_phello_expectation
        )
        checks[f"{variant}_original_only_phello_expectation_differs"] = all(
            value is True
            for name, value in first.get("module_expectations", {}).items()
            if name != "__phello__"
        )

        checks[f"{variant}_corrected_capability_pass"] = (
            corrected.get("pass") is True
        )
        checks[f"{variant}_corrected_schema_2"] = (
            corrected.get("schema_version") == 2
        )
        checks[f"{variant}_corrected_check_count_17"] = (
            corrected.get("check_count") == 17
        )
        checks[f"{variant}_corrected_failed_checks_empty"] = (
            corrected.get("failed_checks") == []
        )
        checks[f"{variant}_corrected_module_expectations_all_true"] = (
            all_module_expectations_true(corrected)
        )
        checks[f"{variant}_corrected_phello_frozen"] = phello_is_frozen(
            corrected
        )
        checks[f"{variant}_physical_test_demo_matches"] = corrected.get(
            "test_demo", {}
        ).get("present") is EXPECTED_TEST_DEMO[variant]
        checks[f"{variant}_physical_test_demo_expected_matches"] = corrected.get(
            "test_demo", {}
        ).get("expected_present") is EXPECTED_TEST_DEMO[variant]
        checks[f"{variant}_physical_contract_explicit"] = corrected.get(
            "test_demo", {}
        ).get("import_contract") == "frozen-independent-of-physical-source"

        original_before = original_variant_before[variant]
        original_after = original_variant_after[variant]
        current_before = current_variant_before[variant]
        current_after = current_variant_after[variant]
        checks[f"{variant}_original_fingerprints_pass"] = (
            original_before.get("pass") is True
            and original_after.get("pass") is True
        )
        checks[f"{variant}_original_fingerprint_unchanged"] = (
            original_before.get("fingerprint") == original_after.get("fingerprint")
        )
        checks[f"{variant}_current_fingerprints_pass"] = (
            current_before.get("pass") is True and current_after.get("pass") is True
        )
        checks[f"{variant}_current_fingerprint_unchanged"] = (
            current_before.get("fingerprint") == current_after.get("fingerprint")
        )
        checks[f"{variant}_current_matches_original"] = (
            current_before.get("fingerprint") == original_after.get("fingerprint")
        )
        checks[f"{variant}_entry_count_expected"] = (
            original_before.get("entry_count")
            == original_after.get("entry_count")
            == current_before.get("entry_count")
            == current_after.get("entry_count")
            == EXPECTED_COUNTS[variant]
        )

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "missing_outputs": sorted(set(missing)),
        "parse_errors": errors,
        "original_results": str(original),
        "reassessment_results": str(reassessment),
        "expected_source_fingerprint": args.expected_source_fingerprint,
        "expected_component_manifest": args.expected_component_manifest,
        "incident": {
            "first_run_failed_checks": original_verification.get("failed_checks"),
            "first_run_workflow_returncodes": workflow_returncodes,
            "root_cause": (
                "__phello__ is a frozen CPython package and remains importable when "
                "its optional physical source rows are absent."
            ),
            "corrected_contract": (
                "Importability is required in every variant; physical "
                "lib/python3.14/__phello__ presence follows test-addon ownership."
            ),
        },
        "variant_summary": {
            variant: {
                "entry_count": current_variant_after[variant].get("entry_count"),
                "fingerprint": current_variant_after[variant].get("fingerprint"),
                "corrected_capability_pass": corrected_capabilities[variant].get(
                    "pass"
                ),
                "phello_origin": corrected_capabilities[variant]
                .get("modules", {})
                .get("__phello__", {})
                .get("spec", {})
                .get("origin"),
                "test_demo_present": corrected_capabilities[variant]
                .get("test_demo", {})
                .get("present"),
            }
            for variant in VARIANTS
        },
        "claim_boundary": {
            "proved": (
                "The first isolated-variant failure was an exact frozen-module "
                "expectation false negative; all retained physical and behavior "
                "gates pass under the corrected non-mutating capability contract."
            ),
            "not_proved": (
                "The runtime-base candidate preserves full native closure and "
                "whole-prefix relocation after the component split."
            ),
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 18


if __name__ == "__main__":
    raise SystemExit(main())
