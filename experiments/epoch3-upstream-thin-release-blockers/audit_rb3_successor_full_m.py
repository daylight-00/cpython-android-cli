#!/usr/bin/env python3
"""Independently audit an RB-3 profile-M successor full qualification result."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

RESULT = "rb3-successor-full-m-result.json"
STRUCTURAL = "full-structural-verification.json"
QUALIFICATION = "full-android-qualification.json"
PROTECTED = "protected-state.json"
WHEEL = "native-wheel-elf-boundary.json"
MANAGED_WHEEL = "native-managed-wheel-elf-boundary.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(result_dir: Path) -> dict[str, Any]:
    result_dir = result_dir.resolve()
    result = load(result_dir / RESULT)
    structural = load(result_dir / STRUCTURAL)
    qualification = load(result_dir / QUALIFICATION)
    protected = load(result_dir / PROTECTED)
    wheel = load(result_dir / WHEEL)
    managed_wheel = load(result_dir / MANAGED_WHEEL)
    checks = result.get("checks", {}) if isinstance(result.get("checks"), dict) else {}
    boundary = result.get("claim_boundary", {}) if isinstance(result.get("claim_boundary"), dict) else {}
    projection = result.get("temporary_install_only_projection", {})
    projection_archive = projection.get("archive", {}) if isinstance(projection, dict) else {}
    projection_path = result_dir / "artifacts/successor-install-only-projection.tar.gz"

    audit_checks = {
        "result_pass": result.get("pass") is True,
        "result_checks_all_true": bool(checks) and all(value is True for value in checks.values()),
        "structural_verification_pass": structural.get("pass") is True,
        "android_qualification_pass": qualification.get("pass") is True,
        "profile_M_exact": result.get("profile") == {"id": "M", "name": "upstream-preserved-minimal-consumer-overlay"},
        "projection_present": projection_path.is_file(),
        "projection_identity_bound": projection_path.is_file() and projection_archive.get("size_bytes") == projection_path.stat().st_size and projection_archive.get("sha256") == sha256_file(projection_path),
        "native_wheel_build_import_pass": wheel.get("pass") is True and wheel.get("wheel_import_returncode") == 0,
        "native_wheel_elf_recorded": isinstance(wheel.get("raw_extension"), dict),
        "native_wheel_16k_alignment_pass": wheel.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "managed_native_wheel_build_import_pass": managed_wheel.get("pass") is True and managed_wheel.get("wheel_import_returncode") == 0,
        "managed_native_wheel_elf_recorded": isinstance(managed_wheel.get("raw_extension"), dict),
        "managed_native_wheel_16k_alignment_pass": managed_wheel.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "wheel_postprocessing_out_of_scope": boundary.get("user_built_wheel_postprocessing") == "out-of-scope-external-tool-responsibility",
        "portable_raw_wheel_not_claimed": boundary.get("portable_raw_wheel_claim") is False,
        "candidate_protected": protected.get("candidate_full_unchanged") is True,
        "predecessor_protected": protected.get("predecessor_full_unchanged") is True,
        "real_managed_root_protected": protected.get("real_managed_root_unchanged") is True,
        "successor_not_promoted": boundary.get("successor_full_accepted") is False,
        "install_only_not_started": boundary.get("successor_install_only_started") is False,
        "family_not_superseded": boundary.get("predecessor_family_superseded") is False,
        "rb3_open": boundary.get("rb3_closed") is False,
        "selectability_withheld": boundary.get("selectable") is False,
        "publication_withheld": boundary.get("publication") is False,
    }
    required_logs = [
        "system-identity.json", "system-find.json", "system-venv.json", "system-run.json", "system-sync.json",
        "managed-catalog.json", "managed-install.json", "managed-find.json", "managed-identity.json",
        "managed-venv.json", "managed-reinstall.json", "managed-uninstall.json", "managed-find-empty.json",
        "successor-M-wheel-venv.json", "successor-M-wheel-setuptools.json", "successor-M-wheel-build.json",
        "successor-M-wheel-install.json", "successor-M-wheel-import.json",
        "successor-M-managed-wheel-venv.json", "successor-M-managed-wheel-setuptools.json",
        "successor-M-managed-wheel-build.json", "successor-M-managed-wheel-install.json",
        "successor-M-managed-wheel-import.json",
    ]
    missing = sorted(name for name in required_logs if not (result_dir / "process" / name).is_file())
    audit_checks["required_process_logs_present"] = not missing
    failed = sorted(name for name, passed in audit_checks.items() if passed is not True)
    data = {
        "schema_version": 1,
        "audit_kind": "epoch3-rb3-profile-M-successor-full-independent-audit",
        "pass": not failed,
        "checks": dict(sorted(audit_checks.items())),
        "failed_checks": failed,
        "missing_process_logs": missing,
        "claim_boundary": {
            "successor_full_accepted": False,
            "predecessor_family_superseded": False,
            "rb3_closed": False,
            "selectable": False,
            "publication": False,
        },
    }
    (result_dir / "independent-audit.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(args.result_dir)
    except Exception as exc:  # noqa: BLE001
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
