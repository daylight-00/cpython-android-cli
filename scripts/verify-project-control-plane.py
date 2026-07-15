#!/usr/bin/env python3
"""Verify the frozen Stage 3-D repository control plane through Gate 5."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]


def t(path: str) -> str:
    return (R / path).read_text(encoding="utf-8")


def j(path: str):
    return json.loads(t(path))


ctx = t("docs/PROJECT_CONTEXT_STAGE3D.md")
scope = t("docs/stages/STAGE3D_SCOPE.md")
readme = t("README.md")
orient = t("docs/PROJECT_ORIENTATION.md")
handoff = t("docs/handoff/README.md")
ledger = t("docs/handoff/STAGE3D_EVIDENCE_LEDGER.md")
evidence = t("docs/evidence/STAGE3D_GATE4_CONSUMER_INTEGRATION_TARGET_VALIDATION_RESULT.md")
workflow = t("docs/GITHUB_COLLABORATION_WORKFLOW.md")
protocol = t("docs/handoff/COLLABORATION_PROTOCOL.md")
lessons = t("docs/session-operations/LESSONS_AND_CHANGELOG.md")
g2 = j("experiments/stage3d-consumer-integration/gate2-consumer-census-authority.json")
g3 = j("experiments/stage3d-consumer-integration/gate3-system-python-contract.json")
matrix = j("experiments/stage3d-consumer-integration/gate4-consumer-integration-validation-matrix.json")
g4 = j("experiments/stage3d-consumer-integration/gate4-consumer-integration-authority.json")

accepted_sha = "13ed73fdeaf5ea13339b2df70b69a4c79aa2920fb1d9207229fb64db828b283c"
checks = {
    "readme_gate4e": "Gate 4E independent freeze complete" in readme,
    "readme_stage3d_frozen": "frozen — Gate 5 independent freeze complete; Gate 6 deferred" in readme,
    "context_status": "> **Status:** Stage 3-D consumer integration frozen through Gate 5" in ctx,
    "context_branch": "agent/stage3d-consumer-integration" in ctx,
    "context_gate4": "Gate 4  target implementation/validation       FROZEN — 48/48, independent 27/27" in ctx,
    "context_gate5": "Gate 5  independent consumer-integration freeze FROZEN" in ctx,
    "context_archive": accepted_sha in ctx and "697/697 exact" in ctx,
    "context_run_sync_accepted": "`uv python find`, `uv venv`, `uv run`, and `uv sync` are accepted" in ctx,
    "scope_status": "FROZEN — Gate 5 independent consumer-integration freeze complete" in scope,
    "scope_gate4": "Gate 4  target implementation and validation            FROZEN — 48/48" in scope,
    "scope_gate5": "Gate 5  independent consumer-integration freeze         FROZEN — 27/27" in scope,
    "scope_commands": "`uv python find`, `uv venv`, `uv run`, and `uv sync` are accepted" in scope,
    "scope_prohibitions": "root/proot/Shizuku/Docker" in scope,
    "orientation_current": "GATE3_SYSTEM_PYTHON_INTEGRATION_CONTRACT.md" in orient and "gate4-consumer-integration-validation-matrix.json" in orient,
    "handoff_current": "Stage 3-D Gate 5 independent consumer freeze            FROZEN — 27/27" in handoff,
    "ledger_gate4": accepted_sha in ledger and "48/48 expectation match" in ledger and "27/27 independent checks" in ledger,
    "evidence_status": "TARGET EVIDENCE ACCEPTED — GATE 5 INDEPENDENT FREEZE" in evidence,
    "evidence_archive": accepted_sha in evidence and "self-index               697/697 exact" in evidence,
    "evidence_surface": "uv run exact-product execution       8/8" in evidence and "uv sync exact-product execution      8/8" in evidence,
    "workflow_current": "GATE3_SYSTEM_PYTHON_INTEGRATION_CONTRACT.md" in workflow and "gate4-consumer-integration-validation-matrix.json" in workflow,
    "protocol_current": "GATE3_SYSTEM_PYTHON_INTEGRATION_CONTRACT.md" in protocol and "gate4-consumer-integration-validation-matrix.json" in protocol,
    "lesson_prune": "transient workspace versus evidence archive" in lessons,
    "g2_status": g2["status"] == "target-evidence-accepted",
    "g2_64": g2["scenario_results"]["count"] == 64 and g2["scenario_results"]["expectation_match"] == 64,
    "g2_coverage": g2["process_coverage"]["uv_run"] == 0 and g2["process_coverage"]["uv_sync"] == 0,
    "g3_status": g3["status"] == "contract-frozen",
    "g3_selector": g3["canonical_contract"]["selector"] == "explicit-absolute-interpreter-path",
    "g3_historical_gate4": g3["gate_sequence"]["gate4"] == "ACTIVE_NEXT_TARGET_IMPLEMENTATION_VALIDATION",
    "matrix_48": matrix["scenario_count"] == 48 and len(matrix["scenarios"]) == 48,
    "matrix_run_sync": sum(x["operation"] == "uv-run-explicit-interpreter" for x in matrix["scenarios"]) == 8 and sum(x["operation"] == "uv-sync-explicit-interpreter" for x in matrix["scenarios"]) == 8,
    "g4_status": g4["status"] == "accepted",
    "g4_archive": g4["accepted_result"]["archive"]["sha256"] == accepted_sha and g4["accepted_result"]["archive"]["result_index_count"] == 697,
    "g4_acceptance": g4["acceptance"]["expectation_match"] == "48/48" and g4["acceptance"]["harness_complete"] == "48/48" and g4["acceptance"]["independent_verification"] == "27/27",
    "g4_invariants": all(g4["invariants"].values()),
    "reading_paths": all(
        (R / path).is_file()
        for path in [
            "docs/PROJECT_CONTEXT_STAGE3D.md",
            "docs/stages/STAGE3D_SCOPE.md",
            "experiments/stage3d-consumer-integration/GATE2_READ_ONLY_CONSUMER_CENSUS.md",
            "experiments/stage3d-consumer-integration/GATE3_SYSTEM_PYTHON_INTEGRATION_CONTRACT.md",
            "experiments/stage3d-consumer-integration/gate4-consumer-integration-validation-matrix.json",
            "experiments/stage3d-consumer-integration/gate4-consumer-integration-authority.json",
            "experiments/stage3d-consumer-integration/verify-gate4-consumer-integration.py",
            "docs/evidence/STAGE3D_GATE4_CONSUMER_INTEGRATION_TARGET_VALIDATION_RESULT.md",
            "docs/handoff/STAGE3D_EVIDENCE_LEDGER.md",
        ]
    ),
    "git_diff_check": subprocess.run(
        ["git", "-C", str(R), "diff", "--check", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).returncode
    == 0,
}

compile_paths = [
    Path(__file__),
    R / "experiments/stage3d-consumer-integration/verify-gate2-consumer-census.py",
    R / "experiments/stage3d-consumer-integration/verify-gate3-system-python-contract.py",
    R / "experiments/stage3d-consumer-integration/verify-gate4-consumer-integration.py",
]
checks["python_compile"] = (
    subprocess.run(
        [sys.executable, "-m", "py_compile", *(str(path) for path in compile_paths)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).returncode
    == 0
)

failed = sorted(key for key, value in checks.items() if not value)
out = {
    "schema_version": 1,
    "verification_kind": "project-control-plane-reconciliation",
    "pass": not failed,
    "check_count": len(checks),
    "pass_count": sum(checks.values()),
    "failed_checks": failed,
    "checks": dict(sorted(checks.items())),
    "observed": {
        "head": subprocess.check_output(["git", "-C", str(R), "rev-parse", "HEAD"], text=True).strip(),
        "tree_before_commit": subprocess.check_output(["git", "-C", str(R), "write-tree"], text=True).strip(),
        "gate3_authority_sha256": hashlib.sha256((R / "experiments/stage3d-consumer-integration/gate3-system-python-contract.json").read_bytes()).hexdigest(),
        "gate4_authority_sha256": hashlib.sha256((R / "experiments/stage3d-consumer-integration/gate4-consumer-integration-authority.json").read_bytes()).hexdigest(),
        "gate4_archive_sha256": g4["accepted_result"]["archive"]["sha256"],
    },
    "claim_boundary": "Stage 3-D is frozen through Gate 5 for the exact system-Python consumer surface. Gate 6 managed-Python feasibility remains deferred.",
}
print(json.dumps(out, indent=2, sort_keys=True))
raise SystemExit(0 if out["pass"] else 1)
