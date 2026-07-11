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


def read_text_safe(
    path: Path,
    missing: list[str],
    errors: dict[str, str],
) -> str:
    if not path.is_file():
        missing.append(str(path))
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        errors[str(path)] = repr(exc)
        return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-source-fingerprint", required=True)
    parser.add_argument("--expected-component-manifest", required=True)
    args = parser.parse_args()

    results = args.results_dir.resolve()
    output = args.output.resolve()
    missing: list[str] = []
    errors: dict[str, str] = {}

    materialization = read_json_safe(
        results / "materialization.json", missing, errors
    )
    fidelity_before = read_json_safe(
        results / "variant-fidelity-before.json", missing, errors
    )
    fidelity_after = read_json_safe(
        results / "variant-fidelity-after.json", missing, errors
    )
    workflow = read_json_safe(results / "workflow-status.json", missing, errors)
    source_before = read_json_safe(results / "source-before.json", missing, errors)
    source_after = read_json_safe(results / "source-after.json", missing, errors)
    smoke_log = read_text_safe(results / "runtime-base-smoke.log", missing, errors)
    development_log = read_text_safe(
        results / "development-extension.log", missing, errors
    )
    test_log = read_text_safe(results / "test-addon.log", missing, errors)

    capabilities = {
        variant: read_json_safe(
            results / "capabilities" / f"{variant}.json", missing, errors
        )
        for variant in VARIANTS
    }
    before_variants = {
        variant: read_json_safe(
            results / "fingerprints" / f"{variant}-before.json", missing, errors
        )
        for variant in VARIANTS
    }
    after_variants = {
        variant: read_json_safe(
            results / "fingerprints" / f"{variant}-after.json", missing, errors
        )
        for variant in VARIANTS
    }

    status = workflow.get("returncodes", {})
    checks: dict[str, bool] = {
        "all_required_outputs_present": not missing,
        "all_required_outputs_parse": not errors,
        "materialization_pass": materialization.get("pass") is True,
        "materialization_check_count": materialization.get("check_count") == 7,
        "materialization_manifest_matches": materialization.get(
            "component_manifest_sha256"
        )
        == args.expected_component_manifest,
        "fidelity_before_pass": fidelity_before.get("pass") is True,
        "fidelity_before_check_count": fidelity_before.get("check_count") == 15,
        "fidelity_after_pass": fidelity_after.get("pass") is True,
        "fidelity_after_check_count": fidelity_after.get("check_count") == 15,
        "workflow_status_pass": workflow.get("pass") is True,
        "smoke_returncode_zero": status.get("runtime_base_smoke") == 0,
        "development_compile_returncode_zero": status.get(
            "development_extension_compile"
        )
        == 0,
        "development_import_returncode_zero": status.get(
            "development_extension_import"
        )
        == 0,
        "test_addon_returncode_zero": status.get("test_addon") == 0,
        "smoke_marker_present": "STAGE2C_SMOKE=PASS" in smoke_log,
        "development_extension_marker_present": "DEV_EXTENSION_RESULT=42"
        in development_log,
        "test_addon_marker_present": "STAGE3C_TEST_ADDON_REPRESENTATIVE=PASS"
        in test_log,
        "source_before_pass": source_before.get("pass") is True,
        "source_after_pass": source_after.get("pass") is True,
        "source_fingerprint_expected": source_before.get("fingerprint")
        == args.expected_source_fingerprint,
        "source_fingerprint_unchanged": source_before.get("fingerprint")
        == source_after.get("fingerprint"),
        "source_entry_count_unchanged": source_before.get("entry_count")
        == source_after.get("entry_count")
        == 3155,
    }

    for variant in VARIANTS:
        capability = capabilities[variant]
        before = before_variants[variant]
        after = after_variants[variant]
        checks[f"{variant}_capability_pass"] = capability.get("pass") is True
        checks[f"{variant}_capability_check_count"] = (
            capability.get("check_count") == 15
        )
        checks[f"{variant}_before_fingerprint_pass"] = before.get("pass") is True
        checks[f"{variant}_after_fingerprint_pass"] = after.get("pass") is True
        checks[f"{variant}_entry_count_expected"] = (
            before.get("entry_count") == EXPECTED_COUNTS[variant]
            and after.get("entry_count") == EXPECTED_COUNTS[variant]
        )
        checks[f"{variant}_fingerprint_unchanged"] = before.get(
            "fingerprint"
        ) == after.get("fingerprint")

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "missing_outputs": sorted(set(missing)),
        "parse_errors": errors,
        "expected_source_fingerprint": args.expected_source_fingerprint,
        "expected_component_manifest": args.expected_component_manifest,
        "workflow": workflow,
        "source_before": source_before,
        "source_after": source_after,
        "variant_fingerprints": {
            variant: {
                "before": before_variants[variant].get("fingerprint"),
                "after": after_variants[variant].get("fingerprint"),
                "entry_count": before_variants[variant].get("entry_count"),
            }
            for variant in VARIANTS
        },
        "capability_summary": {
            variant: {
                "pass": capabilities[variant].get("pass"),
                "failed_checks": capabilities[variant].get("failed_checks"),
                "module_expectations": capabilities[variant].get(
                    "module_expectations"
                ),
            }
            for variant in VARIANTS
        },
        "claim_boundary": {
            "proved": "All four exact-path isolated variants preserve their trees and pass selected runtime, development, and test capability gates.",
            "not_proved": "The runtime-base candidate preserves full native closure and whole-prefix relocation after the product split.",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 17


if __name__ == "__main__":
    raise SystemExit(main())
