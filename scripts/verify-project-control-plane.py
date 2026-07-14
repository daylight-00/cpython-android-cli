#!/usr/bin/env python3
"""Verify the current repository control-plane documentation contract."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXPECTED = {
    "gate3b_archive": "0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b",
    "gate3b_index": "f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9",
    "gate3c_archive": "43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a",
    "gate3c_index": "fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c",
    "gate3d_archive": "579b880495098e9a46b40e2d96c9555178d0ad8c725d40768e6b854227d66143",
    "gate3d_index": "5f9aa64cb4e0679a4784c9c3b8ebd6d8d91829704984672186dc9f9c0d96ed60",
    "gate3d_safety": "47b571d79990cf6c5f1157f7784a5acfa47478b04a7c6f55185d3c4f38ab8a00",
}


def text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def contains(path: str, needle: str) -> bool:
    return needle in text(path)


def absent(path: str, needle: str) -> bool:
    return needle not in text(path)


readme = text("README.md")
current = text("docs/PROJECT_CONTEXT_STAGE3C.md")
historical = text("docs/PROJECT_CONTEXT_STAGE3.md")
workflow = text("docs/GITHUB_COLLABORATION_WORKFLOW.md")
protocol = text("docs/handoff/COLLABORATION_PROTOCOL.md")
handoff_index = text("docs/handoff/README.md")
ledger = text("docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md")
gate4 = text("docs/handoff/PHASE5_GATE4_UPGRADE_DOWNGRADE_HANDOFF_20260713.md")
experiment = text("experiments/stage3c-installed-runtime-lifecycle/README.md")

checks: dict[str, bool] = {
    "readme_gate3d_frozen": "frozen through Gate 3D" in readme,
    "readme_gate4b_design_frozen": "Gate 4B design frozen; implementation pending" in readme,
    "readme_current_context_path": "docs/PROJECT_CONTEXT_STAGE3C.md" in readme,
    "readme_drive_tar_zst_exchange": "Google Drive, normally one .tar.zst per direction" in readme,
    "readme_no_stage3c_next": "Stage 3-C  distribution archive/installation contract  next" not in readme,
    "readme_no_old_next_sentence": "The next work is Stage 3-C archive and installation contract design" not in readme,
    "historical_context_marked": "HISTORICAL SNAPSHOT" in historical,
    "historical_context_points_current": "PROJECT_CONTEXT_STAGE3C.md" in historical,
    "current_context_status": "> **Status:** Current handoff context" in current,
    "current_context_gate4_active": "Gate 4C transition coordinator implementation" in current,
    "current_context_authority_hierarchy": "complete independently inspected Termux target evidence" in current,
    "current_context_three_artifacts": all(x in current for x in ("runtime-base", "development-addon", "test-addon")),
    "current_context_preserve_report": "preserve-and-report" in current,
    "current_context_recovery_rcs": all(x in current for x in ("rc 90", "rc 93", "rc 92")),
    "current_context_transition_design_first": "Gate 4B has frozen those choices" in current,
    "current_context_no_gate4_target_claim": "No upgrade, downgrade, compatibility, migration, or Gate 4 transition target claim" in current,
    "current_context_patch_bundle_policy": all(x in current for x in ("patch", "partial bundle", "full bundle")),
    "current_context_single_archive_policy": "one `.tar.zst` per direction" in current,
    "current_context_authorship_policy": "daylight-00 <hwjang00@snu.ac.kr>" in current,
    "workflow_local_git_default": "real local Git repository or an exact bundle reconstruction" in workflow,
    "workflow_no_connector_default": "GitHub connector operations are not the default" in workflow,
    "workflow_single_archive": "one `.tar.zst` per direction" in workflow,
    "workflow_patch_partial_full": all(x in workflow for x in ("patch", "partial bundle", "full bundle")),
    "workflow_flexible_timing": "Commit and push timing is deliberately flexible" in workflow,
    "workflow_authorship_exact": "daylight-00 <hwjang00@snu.ac.kr>" in workflow,
    "workflow_surgical_history": "modify only the commits and metadata fields actually affected" in workflow,
    "workflow_target_archive_audit": "A console marker alone is never acceptance" in workflow,
    "protocol_minimum_user_work": "minimum manual work" in protocol,
    "protocol_single_archive": "one `.tar.zst` per direction" in protocol,
    "protocol_bundle_selection": all(x in protocol for x in ("patch", "partial bundle", "full bundle")),
    "protocol_authorship_exact": "daylight-00 <hwjang00@snu.ac.kr>" in protocol,
    "protocol_main_after_validation": "fast-forward the canonical branch only after validation" in protocol,
    "protocol_gate4_authority_first": "does not begin with transition implementation" in protocol,
    "handoff_reading_current_context": "../PROJECT_CONTEXT_STAGE3C.md" in handoff_index,
    "handoff_reading_workflow": "../GITHUB_COLLABORATION_WORKFLOW.md" in handoff_index,
    "ledger_archive_generic": "accepted Termux target archives" in ledger,
    "ledger_historical_tgz_immutable": "Historical `.tgz` authorities remain immutable" in ledger,
    "gate4_control_plane_prerequisite": "Repository control-plane prerequisite" in gate4,
    "gate4_second_product_required": "second product must have its own complete, reproducible authority" in gate4,
    "experiment_old_active_removed": "> **Status:** ACTIVE — authoritative Termux diagnostic pending" not in experiment,
    "experiment_historical_marker": "HISTORICAL — diagnostic completed" in experiment,
}

for name, value in EXPECTED.items():
    checks[f"current_{name}"] = value in current

# Ensure the current reading path exists and the old snapshot is not advertised as current.
checks["all_current_reading_paths_exist"] = all(
    (REPO / path).exists()
    for path in (
        "README.md",
        "docs/PROJECT_CONTEXT_STAGE3C.md",
        "docs/stages/STAGE3C_PHASE5_SCOPE.md",
        "docs/handoff/STAGE3C_PHASE5_EVIDENCE_LEDGER.md",
        "docs/handoff/PHASE5_GATE4_UPGRADE_DOWNGRADE_HANDOFF_20260713.md",
        "docs/GITHUB_COLLABORATION_WORKFLOW.md",
        "docs/handoff/COLLABORATION_PROTOCOL.md",
    )
)
checks["old_context_not_called_current_in_readme"] = (
    "PROJECT_CONTEXT_STAGE3.md` is the current" not in readme
)

# Repository consistency checks.
checks["git_diff_check"] = subprocess.run(
    ["git", "-C", str(REPO), "diff", "--check", "HEAD"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
).returncode == 0
checks["python_source_compiles"] = subprocess.run(
    ["python3", "-m", "py_compile", str(Path(__file__))],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
).returncode == 0

failed = sorted(name for name, passed in checks.items() if not passed)
result = {
    "schema_version": 1,
    "verification_kind": "project-control-plane-reconciliation",
    "pass": not failed,
    "check_count": len(checks),
    "pass_count": sum(checks.values()),
    "failed_checks": failed,
    "checks": dict(sorted(checks.items())),
    "observed": {
        "head": subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True
        ).strip(),
        "tree_before_commit": subprocess.check_output(
            ["git", "-C", str(REPO), "write-tree"], text=True
        ).strip(),
        "current_context_sha256": hashlib.sha256(
            (REPO / "docs/PROJECT_CONTEXT_STAGE3C.md").read_bytes()
        ).hexdigest(),
    },
    "claim_boundary": (
        "This verifier checks repository documentation and workflow alignment only. "
        "It does not implement or prove any Gate 4 transition target behavior."
    ),
}
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result["pass"] else 1)
