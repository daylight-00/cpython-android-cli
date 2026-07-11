#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from recovery_scenario_applying import run_applying_and_registry_recovery
from recovery_scenario_context import ScenarioContext
from recovery_scenario_finalize import run_commit_lock_and_finalize
from recovery_scenario_seed import run_seed_and_early_recovery
from recovery_scenario_support import canonical_json_bytes, fingerprint


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate2-results", required=True, type=Path)
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    gate2 = args.gate2_results.resolve()
    engine = args.engine.resolve()
    work = args.work_root.resolve()
    output = args.output_dir.resolve()
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    output.mkdir(parents=True, exist_ok=True)
    (output / "snapshots").mkdir(exist_ok=True)

    ctx = ScenarioContext(gate2, engine, work, output)
    early = run_seed_and_early_recovery(ctx)
    applying = run_applying_and_registry_recovery(
        ctx,
        early["runtime_seed"],
        early["runtime_development_seed"],
    )
    final = run_commit_lock_and_finalize(
        ctx,
        early["prepared"],
        early["intent"],
        applying["applying_install"],
        applying["applying_uninstall"],
        applying["registry_crash"],
        str(applying["regular"]),
    )

    if len(ctx.checks) != 55:
        raise RuntimeError(f"unexpected check count: {len(ctx.checks)}")
    if ctx.sequence != 40:
        raise RuntimeError(f"unexpected scenario log count: {ctx.sequence}")
    failed = sorted(name for name, passed in ctx.checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(ctx.checks),
        "checks": ctx.checks,
        "failed_checks": failed,
        "observed": {
            "scenario_log_count": len(final["logs"]),
            "scenario_logs": final["logs"],
            "prepared_final_fingerprint": fingerprint(early["prepared"]),
            "intent_final_fingerprint": fingerprint(early["intent"]),
            "applying_install_final_fingerprint": fingerprint(applying["applying_install"]),
            "applying_uninstall_final_fingerprint": fingerprint(applying["applying_uninstall"]),
            "registry_crash_final_fingerprint": fingerprint(applying["registry_crash"]),
            "committed_final_fingerprint": fingerprint(final["committed"]),
            "lock_final_fingerprint": fingerprint(final["lock_root"]),
            "repaired_regular_path": final["regular"],
        },
        "claim_boundary": {
            "proved": "The prototype recovers isolated PREPARED, durable INTENT, durable APPLYING, registry-applied pre-commit, and COMMITTED-cleanup crash states; retained ROLLED_BACK recovery is idempotent; a nonblocking contender is rejected while the installation lock is held.",
            "not_proved": "Kernel or power-loss durability, parent-directory fsync, crashes inside an individual non-atomic filesystem primitive, multi-user adversarial mutation, fairness, upgrade or downgrade, or installed runtime behavior.",
        },
    }
    (output / "scenario.json").write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    print("\nSTAGE3C_PHASE4_RECOVERY_SCENARIOS=" + ("PASS" if result["pass"] else "FAIL"))
    if args.require_pass and not result["pass"]:
        return 45
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
