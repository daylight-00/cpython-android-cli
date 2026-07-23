#!/usr/bin/env python3
"""Independently audit RB-5 API 24 runtime candidate evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_RELEASE_ID = "cpython-3.14.6+e3-r3-aarch64-linux-android"
EXPECTED_RELEASE_SHA = "2c31578f95a11291eee1693db80048568a7b533e77877f36a8b1570241ce1e1c"
EXPECTED_FINGERPRINT = "c8d76b6dcb934c12098efb2de985c5ab4799e4b5db5ae1c2b7c0f5a68438a82a"
EXPECTED_INSTALL_SHA = "c904a4d1da527e512c715a3227c62da99728ec62747487795292320cee71ab56"
REQUIRED_CHECKS = (
    "exact_family_result", "exact_data_result", "exact_install_only", "exact_current_data",
    "extension_inventory_67", "pkg_config", "exact_target_available", "target_setup", "target_push",
    "target_extract", "target_api24", "target_aarch64", "probe_push", "startup_location_a",
    "relocation_move", "startup_and_relocation", "native_extensions", "subprocess_reentry",
    "runtime_data", "sysconfig_api24", "python_aliases", "bounded_pip", "venv", "python_config",
    "read_only_execution", "target_tree_content_invariance", "frozen_family_invariance",
)


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def verify(root: Path) -> dict[str, Any]:
    result = load(root / "result.json")
    checks = result.get("checks") if isinstance(result.get("checks"), dict) else {}
    release = result.get("release") if isinstance(result.get("release"), dict) else {}
    target = result.get("target") if isinstance(result.get("target"), dict) else {}
    boundary = result.get("claim_boundary") if isinstance(result.get("claim_boundary"), dict) else {}
    audit_checks = {
        "result_kind": result.get("result_kind") == "epoch3-rb5-api24-runtime-candidate",
        "result_pass": result.get("pass") is True and result.get("failed_checks") == [] and result.get("errors") == [],
        "required_checks": all(checks.get(k) is True for k in REQUIRED_CHECKS),
        "release_identity": release == {
            "release_id": EXPECTED_RELEASE_ID,
            "release_sha256": EXPECTED_RELEASE_SHA,
            "family_fingerprint_sha256": EXPECTED_FINGERPRINT,
            "install_only_sha256": EXPECTED_INSTALL_SHA,
        },
        "exact_target": target.get("required_android_api") == 24 and target.get("architecture") == "aarch64" and target.get("mode") in ("local", "adb"),
        "candidate_only": boundary.get("api24_runtime_started") is True and boundary.get("api24_runtime_candidate") is True and boundary.get("api24_runtime_accepted") is False and boundary.get("rb5_closed") is False,
        "other_claims_withheld": boundary.get("actual_16k_runtime_qualified") is False and boundary.get("non_termux_android_context_qualified") is False and boundary.get("selectable") is False and boundary.get("publication") is False,
        "artifact_unchanged": boundary.get("artifact_bytes_changed") is False,
    }
    failed = sorted(k for k, v in audit_checks.items() if v is not True)
    return {"schema_version": 1, "audit_kind": "epoch3-rb5-api24-runtime-independent-audit", "pass": not failed, "checks": audit_checks, "failed_checks": failed}


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--result-dir", required=True); ap.add_argument("--output")
    args = ap.parse_args(); report = verify(Path(args.result_dir).resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["pass"] else 1


if __name__ == "__main__": raise SystemExit(main())
