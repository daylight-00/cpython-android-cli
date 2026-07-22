#!/usr/bin/env python3
"""Independently audit a completed RB-3 C/H/U/M comparison result."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HOST_ASSEMBLY = ROOT / "experiments/epoch3-upstream-thin-release-blockers/rb3-sysconfig-profile-host-assembly.json"
RESULT_NAME = "rb3-sysconfig-boundary-probe-result.json"
PROTECTED_NAME = "protected-state.json"
PROFILE_IDS = ("C", "H", "U", "M")


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_profiles(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    data = load(root / HOST_ASSEMBLY.relative_to(ROOT))
    result = {}
    for row in data.get("profiles", []):
        if isinstance(row, dict) and row.get("id") in PROFILE_IDS:
            result[row["id"]] = {
                "filename": row.get("filename"),
                "sha256": row.get("sha256"),
                "size_bytes": row.get("size_bytes"),
                "header": row.get("header"),
            }
    if tuple(sorted(result)) != tuple(sorted(PROFILE_IDS)):
        raise ValueError("host profile identity set is incomplete")
    return result


def validate_result_data(data: dict[str, Any]) -> dict[str, bool]:
    profiles = data.get("profiles")
    ids = [row.get("profile") for row in profiles] if isinstance(profiles, list) else []
    checks = data.get("checks") if isinstance(data.get("checks"), dict) else {}
    selection = data.get("selection") if isinstance(data.get("selection"), dict) else {}
    boundary = data.get("claim_boundary") if isinstance(data.get("claim_boundary"), dict) else {}
    return {
        "result_pass": data.get("pass") is True,
        "experiment_checks_all_true": bool(checks) and all(value is True for value in checks.values()),
        "profile_order_exact": ids == list(PROFILE_IDS),
        "selection_withheld": selection.get("selected") is False,
        "canonical_bytes_unchanged": boundary.get("canonical_artifact_bytes_changed") is False,
        "family_not_superseded": boundary.get("artifact_family_superseded") is False,
        "rb3_open": boundary.get("rb3_closed") is False,
        "sdk_not_final": boundary.get("on_device_sdk_final") is False,
        "selectability_withheld": boundary.get("selectable") is False,
        "publication_withheld": boundary.get("publication") is False,
        "profile_summaries_complete": isinstance(profiles, list) and all(
            isinstance(row, dict)
            and isinstance(row.get("checks"), dict)
            and isinstance(row.get("managed"), dict)
            and isinstance(row.get("wheel"), dict)
            and isinstance(row.get("python_config_outputs"), list)
            and isinstance(row.get("pkg_config_output"), dict)
            for row in profiles
        ),
    }


def audit(result_dir: Path, root: Path = ROOT) -> dict[str, Any]:
    result_dir = result_dir.resolve()
    result_path = result_dir / RESULT_NAME
    protected_path = result_dir / PROTECTED_NAME
    data = load(result_path)
    protected = load(protected_path)
    checks = validate_result_data(data)
    expected = expected_profiles(root)

    profiles_by_id = {
        row.get("profile"): row
        for row in data.get("profiles", [])
        if isinstance(row, dict) and row.get("profile") in PROFILE_IDS
    }
    archive_checks = {}
    for profile in PROFILE_IDS:
        exp = expected[profile]
        path = result_dir / "profiles" / exp["filename"]
        row = profiles_by_id.get(profile, {})
        actual = {
            "exists": path.is_file(),
            "sha256": sha256_file(path) if path.is_file() else None,
            "size_bytes": path.stat().st_size if path.is_file() else None,
            "header": row.get("header"),
        }
        archive_checks[profile] = {
            "expected": exp,
            "actual": actual,
            "pass": actual["exists"]
            and actual["sha256"] == exp["sha256"]
            and actual["size_bytes"] == exp["size_bytes"]
            and actual["header"] == exp["header"],
        }
    checks["profile_archives_match_host_assembly"] = all(row["pass"] for row in archive_checks.values())

    control = profiles_by_id.get("C", {})
    control_managed = control.get("managed", {}) if isinstance(control, dict) else {}
    checks["control_reproduces_header_failure"] = (
        control_managed.get("install_returncode") not in (None, 0)
        and "header comment" in str(control_managed.get("install_stderr", ""))
    )
    checks["protected_family_unchanged"] = protected.get("family_unchanged") is True
    checks["protected_real_managed_root_unchanged"] = protected.get("real_managed_root_unchanged") is True

    required_logs = []
    for profile in PROFILE_IDS:
        required_logs.extend([
            f"{profile}-direct-identity.json",
            f"{profile}-system-find.json",
            f"{profile}-system-venv.json",
            f"{profile}-managed-install.json",
            f"{profile}-managed-find.json",
            f"{profile}-managed-venv.json",
            f"{profile}-managed-reinstall.json",
            f"{profile}-managed-uninstall.json",
            f"{profile}-wheel-venv.json",
        ])
    missing_logs = sorted(name for name in required_logs if not (result_dir / "process" / name).is_file())
    checks["required_process_logs_present"] = not missing_logs

    failed = sorted(name for name, passed in checks.items() if passed is not True)
    audit_data = {
        "schema_version": 1,
        "audit_kind": "epoch3-rb3-sysconfig-and-on-device-sdk-profile-probe-independent-audit",
        "pass": not failed,
        "checks": checks,
        "failed_checks": failed,
        "profile_archive_checks": archive_checks,
        "missing_process_logs": missing_logs,
        "claim_boundary": {
            "profile_selected": False,
            "canonical_artifact_bytes_changed": False,
            "artifact_family_superseded": False,
            "rb3_closed": False,
            "selectable": False,
            "publication": False,
        },
    }
    (result_dir / "independent-audit.json").write_text(
        json.dumps(audit_data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return audit_data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(args.result_dir)
    except Exception as exc:
        result = {
            "schema_version": 1,
            "pass": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
