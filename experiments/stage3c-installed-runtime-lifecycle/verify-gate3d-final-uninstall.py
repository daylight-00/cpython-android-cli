#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_MATRIX_SHA = "a36f86d82ad04b71dfa0afb4ab4fd2da764354402cb8db3fdd73d1903606797f"
EXPECTED_GROUPS = {"preflight": 6, "teardown": 8, "residual": 10, "recovery": 12, "locking": 2, "audit": 6}
EXPECTED_IDS = (
    [f"P{i:02d}" for i in range(1, 7)]
    + [f"T{i:02d}" for i in range(1, 9)]
    + [f"S{i:02d}" for i in range(1, 11)]
    + [f"R{i:02d}" for i in range(1, 13)]
    + ["L01", "L02"]
    + [f"A{i:02d}" for i in range(1, 7)]
)
CRASH_RC = {"prepared": 90, "applying-late": 93, "committed": 92}


def cjson(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha256(path: Path) -> str:
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


def process_ref_ok(process_path: Path) -> bool:
    value = read_json(process_path)
    for key in ("stdout_file", "stderr_file"):
        name = value.get(key)
        if name and not (process_path.parent / name).is_file():
            return False
    output_name = value.get("output_file")
    if value.get("output_exists") is True and output_name and not (process_path.parent / output_name).is_file():
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.results_dir.resolve()
    checks: dict[str, bool] = {}

    authority = read_json(root / "accepted-authority.json")
    summary = read_json(root / "scenario-summary.json")
    clone = read_json(root / "clone-separation.json")
    ordinals = read_json(root / "registry-intent-ordinals.json")
    matrix_path = root / "input/gate3d-final-uninstall-matrix.json"
    matrix = read_json(matrix_path)

    checks["authority_pass"] = authority.get("pass") is True and authority.get("failed_checks") == []
    checks["authority_canonical"] = canonical(root / "accepted-authority.json")
    checks["matrix_sha"] = sha256(matrix_path) == EXPECTED_MATRIX_SHA
    checks["matrix_count"] = matrix.get("scenario_count") == 44 and len(matrix.get("scenarios", [])) == 44
    checks["matrix_ids"] = [row.get("id") for row in matrix.get("scenarios", [])] == EXPECTED_IDS
    checks["matrix_groups"] = matrix.get("scenario_group_counts") == EXPECTED_GROUPS
    checks["summary_pass"] = summary.get("pass") is True
    checks["summary_44"] = summary.get("scenario_count") == 44 and summary.get("pass_count") == 44 and summary.get("failed_scenarios") == []
    checks["summary_groups"] = summary.get("group_counts") == EXPECTED_GROUPS and summary.get("group_pass_counts") == EXPECTED_GROUPS
    checks["summary_claim_boundary"] = "pending independent archive inspection" in summary.get("claim_boundary", "") and "upgrade" in summary.get("claim_boundary", "")
    checks["summary_canonical"] = canonical(root / "scenario-summary.json")
    checks["clone_44"] = clone.get("pass") is True and len(clone.get("roots", {})) == 44
    checks["clone_canonical"] = canonical(root / "clone-separation.json")
    checks["ordinals_exact"] = ordinals == {"exact-owned": 715, "modified-owned-regular": 714, "modified-owned-symlink": 714, "unowned-file": 715}

    matrix_by_id = {row["id"]: row for row in matrix["scenarios"]}
    scenario_rows: dict[str, dict[str, Any]] = {}
    for sid in EXPECTED_IDS:
        path = root / "scenarios" / sid / "scenario.json"
        if not path.is_file():
            checks[f"scenario_{sid}"] = False
            continue
        row = read_json(path)
        scenario_rows[sid] = row
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

    # Preflight boundaries: real rc 44 and no mutation at the rejected operation.
    for sid in ("P01", "P02", "P03", "P06"):
        row = scenario_rows.get(sid, {})
        checks[f"preflight_rc44_{sid}"] = row.get("operation", {}).get("returncode") == 44
        checks[f"preflight_zero_mutation_{sid}"] = row.get("before", {}).get("identity_sha256") == row.get("after", {}).get("identity_sha256")
    for sid in ("P04", "P05"):
        row = scenario_rows.get(sid, {})
        checks[f"preflight_rc44_{sid}"] = row.get("operation", {}).get("returncode") == 44
        checks[f"preflight_zero_mutation_{sid}"] = row.get("before_reject", {}).get("identity_sha256") == row.get("after_reject", {}).get("identity_sha256")

    # Exact teardown always reaches registry-empty, owned-payload-absent, physically empty prefix.
    for sid in (f"T{i:02d}" for i in range(1, 9)):
        row = scenario_rows.get(sid, {})
        audit = row.get("final_audit", {})
        checks[f"teardown_final_{sid}"] = (
            audit.get("pass") is True
            and audit.get("final_state_class") == "exact-owned-teardown"
            and audit.get("observed_paths") == []
            and audit.get("registry", {}).get("artifact_count") == 0
            and audit.get("registry", {}).get("owned_path_count") == 0
            and audit.get("transactions") == []
        )

    # Residual scenarios must deregister all ownership while preserving only approved residual membership.
    for sid in (f"S{i:02d}" for i in range(1, 10)):
        row = scenario_rows.get(sid, {})
        audit = row.get("final_audit", {})
        checks[f"residual_final_{sid}"] = (
            audit.get("pass") is True
            and audit.get("registry", {}).get("artifact_count") == 0
            and audit.get("registry", {}).get("owned_path_count") == 0
            and audit.get("exact_owned_leaves") == []
            and audit.get("observed_paths") == audit.get("expected_residual_paths")
            and audit.get("transactions") == []
        )
    row = scenario_rows.get("S10", {})
    checks["residual_collision_S10"] = (
        row.get("final_audit", {}).get("pass") is True
        and row.get("reinstall", {}).get("returncode") == 44
        and row.get("before_reinstall", {}).get("identity_sha256") == row.get("after_reinstall", {}).get("identity_sha256")
    )

    # Recovery cross-product: raw crash RC, action, second recovery and topology.
    for sid in (f"R{i:02d}" for i in range(1, 13)):
        row = scenario_rows.get(sid, {})
        boundary = matrix_by_id[sid]["crash_boundary"]
        committed = boundary == "committed"
        actions1 = row.get("recover_1", {}).get("result", {}).get("actions", [])
        actions2 = row.get("recover_2", {}).get("result", {}).get("actions", [])
        checks[f"recovery_crash_rc_{sid}"] = row.get("crash", {}).get("returncode") == CRASH_RC[boundary]
        checks[f"recovery_action_{sid}"] = len(actions1) == 1 and actions1[0].get("action") == ("FINALIZED_COMMIT" if committed else "ROLLED_BACK")
        if committed:
            checks[f"recovery_second_{sid}"] = actions2 == [] and row.get("after_recover_2", {}).get("transactions") == [] and row.get("final_audit", {}).get("pass") is True
        else:
            tx = row.get("after_recover_2", {}).get("transactions", [])
            checks[f"recovery_second_{sid}"] = len(actions2) == 1 and actions2[0].get("action") == "NOOP_ROLLED_BACK" and len(tx) == 1 and tx[0].get("journal", {}).get("state") == "ROLLED_BACK"

    checks["locking_rc44_L01"] = scenario_rows.get("L01", {}).get("contender", {}).get("returncode") == 44
    checks["locking_rc44_L02"] = scenario_rows.get("L02", {}).get("contender", {}).get("returncode") == 44

    for sid in (f"A{i:02d}" for i in range(1, 7)):
        checks[f"audit_{sid}"] = scenario_rows.get(sid, {}).get("pass") is True

    process_files = sorted(root.glob("scenarios/**/*-process.json"))
    checks["raw_process_files"] = len(process_files) >= 100 and all(process_ref_ok(path) for path in process_files)
    checks["all_scenario_json_canonical"] = all(canonical(root / "scenarios" / sid / "scenario.json") for sid in EXPECTED_IDS)
    checks["transient_work_not_archived"] = not any("target-work" in path.as_posix() or "/work/" in path.as_posix() for path in root.rglob("*"))
    checks["input_gate3b_authority"] = sha256(root / "input/gate3b-result-index.json") == "f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9"
    checks["input_gate3c_authority"] = sha256(root / "input/gate3c-result-index.json") == "fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c"
    checks["input_gate3c_safety"] = sha256(root / "input/gate3c-result-tree-safety.json") == "ab338579025da63dec1750e3a7649c9a5f260cd4556f60ab3b3ade6140187bb9"

    failed = sorted(key for key, value in checks.items() if not value)
    result = {
        "schema_version": 1,
        "verification_kind": "stage3c-phase5-gate3d-final-uninstall-independent-verification",
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "checks": checks,
        "failed_checks": failed,
        "pass": not failed,
        "claim_boundary": "Independent repository verifier over Gate 3D target evidence. Final Gate 3D acceptance still requires external archive safety, root-index, and raw-process inspection. Upgrade and downgrade remain unclaimed.",
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_bytes(cjson(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
