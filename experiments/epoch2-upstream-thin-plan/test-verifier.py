#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "experiments/epoch2-upstream-thin-plan/verify-plan.py"

def run(root: Path) -> int:
    return subprocess.run([sys.executable, str(VERIFIER), "--root", str(root)],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).returncode

def copy_root() -> Path:
    d = Path(tempfile.mkdtemp(prefix="e2-plan-fixture-"))
    for rel in [
        "docs/decisions",
        "docs/epochs",
        "docs/roadmap",
        "docs/evidence",
        "docs/references",
        "docs/architecture",
        "docs/CURRENT_CONTEXT.md",
        "docs/INDEX.md",
        "experiments/epoch2-upstream-thin-plan",
        "experiments/epoch2-recalibration/recalibration-authority.json",
    ]:
        src = ROOT / rel
        dst = d / rel
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return d

def mutate_json(path: Path, fn) -> None:
    data = json.loads(path.read_text())
    fn(data)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

def expect_negative(name: str, mutation) -> None:
    d = copy_root()
    try:
        mutation(d)
        rc = run(d)
        if rc == 0:
            raise SystemExit(f"{name}: verifier unexpectedly accepted fixture")
        print(f"EXPECTED_NEGATIVE_PASS {name}")
    finally:
        shutil.rmtree(d)

if run(ROOT) != 0:
    raise SystemExit("success fixture failed")
print("SUCCESS_FIXTURE_PASS")

expect_negative("api36_not_required",
    lambda d: mutate_json(d / "experiments/epoch2-upstream-thin-plan/plan-authority.json",
                          lambda x: x["decisions"].__setitem__("api36_epoch2_required", False)))

expect_negative("success_auto_inclusion",
    lambda d: mutate_json(d / "experiments/epoch2-upstream-thin-plan/plan-authority.json",
                          lambda x: x["decisions"].__setitem__("experiment_success_implies_epoch3_inclusion", True)))

expect_negative("raw_input_mutation",
    lambda d: (d / "docs/references/raw/2026-07-19-upstream-thin-plan/UPSTREAM_THIN_RESEARCH_AND_DESIGN_PLAN.md").write_text("mutated\n"))

expect_negative("missing_e3_g10",
    lambda d: (d / "docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md").write_text(
        (d / "docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md").read_text().replace(
            "### E3-G10 — Epoch 4 substitution boundary", "### removed gate")))

expect_negative("base_pip_mandatory",
    lambda d: (d / "docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md").write_text(
        (d / "docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md").read_text() + "\nbase pip is mandatory\n"))

expect_negative("epoch3_source_producer",
    lambda d: (d / "docs/epochs/EPOCH3_CHARTER.md").write_text(
        (d / "docs/epochs/EPOCH3_CHARTER.md").read_text() + "\nEpoch 3 owns the full CPython/dependency source producer\n"))

print("ALL_FIXTURES_PASS")
