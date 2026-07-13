#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

EXPECTED_MATRIX_SHA = "52c622450e9664c6738a75fbc947b809cf1f4766e61b04a68a1a8dcc24b6c14a"
EXPECTED_GROUPS = {"preflight": 10, "composition": 10, "uninstall": 9, "recovery": 12, "locking": 2, "behavior": 7}
EXPECTED_IDS = [f"P{i:02d}" for i in range(1, 11)] + [f"C{i:02d}" for i in range(1, 11)] + [f"U{i:02d}" for i in range(1, 10)] + [f"R{i:02d}" for i in range(1, 13)] + ["L01", "L02"] + [f"B{i:02d}" for i in range(1, 8)]


def cjson(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha256(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(path: Path) -> bool:
    try:
        return path.read_bytes() == cjson(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.results_dir.resolve()
    checks: dict[str, bool] = {}

    authority = read_json(root / "accepted-authority.json")
    summary = read_json(root / "scenario-summary.json")
    matrix_path = root / "input/gate3c-addon-lifecycle-matrix.json"
    matrix = read_json(matrix_path)
    clone = read_json(root / "clone-separation.json")

    checks["authority_pass"] = authority.get("pass") is True and authority.get("failed_checks") == []
    checks["authority_canonical"] = canonical(root / "accepted-authority.json")
    checks["matrix_sha"] = sha256(matrix_path) == EXPECTED_MATRIX_SHA
    checks["matrix_count"] = matrix.get("scenario_count") == 50 and len(matrix.get("scenarios", [])) == 50
    checks["matrix_ids"] = [row.get("id") for row in matrix.get("scenarios", [])] == EXPECTED_IDS
    checks["matrix_groups"] = matrix.get("scenario_group_counts") == EXPECTED_GROUPS
    checks["summary_pass"] = summary.get("pass") is True
    checks["summary_50"] = summary.get("scenario_count") == 50 and summary.get("pass_count") == 50 and summary.get("failed_scenarios") == []
    checks["summary_groups"] = summary.get("group_counts") == EXPECTED_GROUPS and summary.get("group_pass_counts") == EXPECTED_GROUPS
    checks["summary_claim_boundary"] = "pending independent archive inspection" in summary.get("claim_boundary", "") and "Gate 3D" in summary.get("claim_boundary", "")
    checks["summary_runtime_not_skipped"] = summary.get("runtime_regression_skipped") is False
    checks["clone_50"] = clone.get("pass") is True and len(clone.get("roots", {})) == 50
    checks["summary_canonical"] = canonical(root / "scenario-summary.json")
    checks["clone_canonical"] = canonical(root / "clone-separation.json")

    matrix_by_id = {row["id"]: row for row in matrix["scenarios"]}
    for sid in EXPECTED_IDS:
        path = root / "scenarios" / sid / "scenario.json"
        if not path.is_file():
            checks[f"scenario_{sid}"] = False
            continue
        row = read_json(path)
        checks[f"scenario_{sid}"] = (
            row.get("id") == sid
            and row.get("group") == matrix_by_id[sid]["group"]
            and row.get("matrix") == matrix_by_id[sid]
            and row.get("pass") is True
            and isinstance(row.get("checks"), dict)
            and bool(row.get("checks"))
            and all(value is True for value in row["checks"].values())
            and canonical(path)
        )

    # Independent recovery topology and tombstone policy checks.
    for sid in ("R01", "R02", "R04", "R05", "R07", "R08", "R10", "R11"):
        row = read_json(root / "scenarios" / sid / "scenario.json")
        tx = row.get("after_recover_2", {}).get("transactions", [])
        checks[f"rollback_tombstone_{sid}"] = len(tx) == 1 and tx[0].get("journal", {}).get("state") == "ROLLED_BACK"
    for sid in ("R03", "R06", "R09", "R12"):
        row = read_json(root / "scenarios" / sid / "scenario.json")
        checks[f"commit_cleanup_{sid}"] = row.get("after_recover_2", {}).get("transactions") == []

    # Raw process return-code cross-checks for externally significant boundaries.
    for sid in ("P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10", "U09", "L01", "L02"):
        row = read_json(root / "scenarios" / sid / "scenario.json")
        process = row.get("operation") or row.get("reinstall") or row.get("contender")
        checks[f"rc44_{sid}"] = isinstance(process, dict) and process.get("returncode") == 44
    expected_crash = {"PREPARED": 90, "LATE_APPLYING": 93, "COMMITTED": 92}
    for sid in (f"R{i:02d}" for i in range(1, 13)):
        row = read_json(root / "scenarios" / sid / "scenario.json")
        boundary = row["matrix"]["crash_boundary"]
        checks[f"crash_rc_{sid}"] = row.get("crash", {}).get("returncode") == expected_crash[boundary]

    # Every referenced raw stdout/stderr/process file must exist.
    referenced_ok = True
    for process_path in root.glob("scenarios/*/*-process.json"):
        process = read_json(process_path)
        for key in ("stdout_file", "stderr_file"):
            name = process.get(key)
            if name and not (process_path.parent / name).is_file():
                referenced_ok = False
    checks["raw_process_files"] = referenced_ok and len(list(root.glob("scenarios/*/*-process.json"))) >= 100

    failed = sorted(key for key, value in checks.items() if not value)
    result = {
        "schema_version": 1,
        "verification_kind": "stage3c-phase5-gate3c-addon-lifecycle-independent-verification",
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "pass": not failed,
        "claim_boundary": "Independent repository verifier over target evidence. Final Gate 3C acceptance still requires archive safety, root-index, and external raw-process inspection.",
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_bytes(cjson(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
