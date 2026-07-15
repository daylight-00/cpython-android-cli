#!/usr/bin/env python3
"""Verify the frozen Stage 3-D control plane and active Stage 3-E boundary."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "agent/stage3e-managed-python-distribution"
GATE4_ARCHIVE = "13ed73fdeaf5ea13339b2df70b69a4c79aa2920fb1d9207229fb64db828b283c"
GATE6_RESULTS = {
    "gate6a": "fa582b372b81feed68b76ee64bf304d364f9280b10a5569da6cb6fd9f9d43694",
    "gate6b": "73ef934e3a2346546c79032a80a4a791ac55f4858a02100301afd33f9bc8fa03",
    "gate6c": "a0e15ef45171af409df27fb2265bb7afed7c1631176ebe6e563be04725fd72d6",
}
SOURCE_HEAD = "c4f0333db196b7bf0e074b9556d566e0d33c91aa"
SOURCE_TREE = "593695ee66270cb9f496df10bef624717ba7fc98"


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(root, "git", *args)


def _dig(value: Any, *keys: str, default: Any = None) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def verify(root: Path) -> dict[str, Any]:
    root = root.resolve()
    missing: list[str] = []
    parse_errors: dict[str, str] = {}

    def text(path: str) -> str:
        file = root / path
        if not file.is_file():
            missing.append(path)
            return ""
        try:
            return file.read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover - defensive evidence path
            parse_errors[path] = f"{type(exc).__name__}: {exc}"
            return ""

    def data(path: str) -> dict[str, Any]:
        raw = text(path)
        if not raw:
            return {}
        try:
            value = json.loads(raw)
        except Exception as exc:
            parse_errors[path] = f"{type(exc).__name__}: {exc}"
            return {}
        if not isinstance(value, dict):
            parse_errors[path] = "top-level JSON value is not an object"
            return {}
        return value

    readme = text("README.md")
    stage3d_ctx = text("docs/PROJECT_CONTEXT_STAGE3D.md")
    stage3d_scope = text("docs/stages/STAGE3D_SCOPE.md")
    stage3e_ctx = text("docs/PROJECT_CONTEXT_STAGE3E.md")
    stage3e_scope = text("docs/stages/STAGE3E_SCOPE.md")
    orientation = text("docs/PROJECT_ORIENTATION.md")
    handoff = text("docs/handoff/README.md")
    workflow = text("docs/GITHUB_COLLABORATION_WORKFLOW.md")
    protocol = text("docs/handoff/COLLABORATION_PROTOCOL.md")
    lessons = text("docs/session-operations/LESSONS_AND_CHANGELOG.md")
    gate4_evidence = text("docs/evidence/STAGE3D_GATE4_CONSUMER_INTEGRATION_TARGET_VALIDATION_RESULT.md")
    gate6_evidence = text("docs/evidence/STAGE3D_GATE6_MANAGED_PYTHON_FEASIBILITY_RESULT.md")
    gate1_design = text("experiments/stage3e-managed-python-distribution/GATE1_AUTHORITY_DESIGN.md")

    g2 = data("experiments/stage3d-consumer-integration/gate2-consumer-census-authority.json")
    g3 = data("experiments/stage3d-consumer-integration/gate3-system-python-contract.json")
    matrix = data("experiments/stage3d-consumer-integration/gate4-consumer-integration-validation-matrix.json")
    g4 = data("experiments/stage3d-consumer-integration/gate4-consumer-integration-authority.json")
    g6 = data("experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json")
    g1 = data("experiments/stage3e-managed-python-distribution/gate1-authority.json")

    branch_result = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    head_result = _git(root, "rev-parse", "HEAD")
    tree_result = _git(root, "write-tree")
    diff_result = _git(root, "diff", "--check", "HEAD")

    required_paths = [
        "README.md",
        "docs/PROJECT_CONTEXT_STAGE3D.md",
        "docs/stages/STAGE3D_SCOPE.md",
        "docs/PROJECT_CONTEXT_STAGE3E.md",
        "docs/stages/STAGE3E_SCOPE.md",
        "docs/PROJECT_ORIENTATION.md",
        "docs/handoff/README.md",
        "docs/GITHUB_COLLABORATION_WORKFLOW.md",
        "docs/handoff/COLLABORATION_PROTOCOL.md",
        "docs/evidence/STAGE3D_GATE4_CONSUMER_INTEGRATION_TARGET_VALIDATION_RESULT.md",
        "docs/evidence/STAGE3D_GATE6_MANAGED_PYTHON_FEASIBILITY_RESULT.md",
        "experiments/stage3d-consumer-integration/gate2-consumer-census-authority.json",
        "experiments/stage3d-consumer-integration/gate3-system-python-contract.json",
        "experiments/stage3d-consumer-integration/gate4-consumer-integration-validation-matrix.json",
        "experiments/stage3d-consumer-integration/gate4-consumer-integration-authority.json",
        "experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json",
        "experiments/stage3e-managed-python-distribution/GATE1_AUTHORITY_DESIGN.md",
        "experiments/stage3e-managed-python-distribution/gate1-authority.json",
        "scripts/test-verify-project-control-plane.py",
    ]

    gate6_results = _dig(g6, "accepted_results", default={})
    selected_gate2 = _dig(g1, "selected_gate2", default={})
    transition = _dig(g1, "repository_transition", default={})
    gate_sequence = _dig(g1, "gate_sequence", default={})

    checks: dict[str, bool] = {
        "required_files": all((root / path).is_file() for path in required_paths),
        "parse_clean": not parse_errors,
        "branch_active": branch_result.returncode == 0 and branch_result.stdout.strip() == EXPECTED_BRANCH,
        "readme_stage3d_gate6": "Stage 3-D  consumer integration                         frozen — Gate 6 bounded managed-Python feasibility complete" in readme,
        "readme_stage3e_active": "Stage 3-E  managed-Python distribution                  active — Gate 1 authority frozen; Gate 2 next" in readme,
        "stage3d_complete": "> **Status:** Stage 3-D frozen through Gate 6 bounded managed-Python feasibility" in stage3d_ctx,
        "stage3d_gate6": "Gate 6  bounded managed-Python feasibility      FROZEN — A/B/C accepted" in stage3d_ctx,
        "stage3d_scope_gate6": "Gate 6  bounded managed-Python feasibility research     FROZEN — A/B/C accepted" in stage3d_scope,
        "stage3e_context_status": "> **Status:** Stage 3-E active — Gate 1 authority design frozen" in stage3e_ctx,
        "stage3e_context_branch": EXPECTED_BRANCH in stage3e_ctx,
        "stage3e_context_gate1": "Gate 1  authority and productization-boundary design    FROZEN" in stage3e_ctx,
        "stage3e_context_gate2": "Gate 2  isolated dual-version boundary census           ACTIVE NEXT" in stage3e_ctx,
        "stage3e_scope_status": "> **Status:** ACTIVE — Gate 1 authority design frozen; Gate 2 next" in stage3e_scope,
        "stage3e_scope_gate2": "Gate 2  isolated dual-version boundary census           ACTIVE NEXT" in stage3e_scope,
        "gate1_design_status": "> **Status:** DESIGN FROZEN" in gate1_design,
        "gate1_design_next": "isolated offline dual-version managed-Python boundary census" in gate1_design,
        "orientation_current": "Stage 3-E Gate 1 freezes the authority boundary" in orientation and "docs/PROJECT_CONTEXT_STAGE3E.md" in orientation,
        "handoff_current": "Stage 3-E Gate 2 isolated dual-version boundary census  ACTIVE NEXT" in handoff,
        "workflow_current": "docs/PROJECT_CONTEXT_STAGE3E.md" in workflow and "gate1-authority.json" in workflow,
        "protocol_current": "docs/PROJECT_CONTEXT_STAGE3E.md" in protocol and "gate1-authority.json" in protocol,
        "lesson_minimum_validation": "minimum sufficient validation" in lessons,
        "gate4_evidence": GATE4_ARCHIVE in gate4_evidence and "697/697 exact" in gate4_evidence,
        "gate6_evidence": all(value in gate6_evidence for value in GATE6_RESULTS.values()),
        "g2_status": _dig(g2, "status") == "target-evidence-accepted",
        "g2_scenarios": _dig(g2, "scenario_results", "count") == 64 and _dig(g2, "scenario_results", "expectation_match") == 64,
        "g3_status": _dig(g3, "status") == "contract-frozen",
        "g3_selector": _dig(g3, "canonical_contract", "selector") == "explicit-absolute-interpreter-path",
        "matrix_48": _dig(matrix, "scenario_count") == 48 and len(_dig(matrix, "scenarios", default=[])) == 48,
        "g4_status": _dig(g4, "status") == "accepted",
        "g4_archive": _dig(g4, "accepted_result", "archive", "sha256") == GATE4_ARCHIVE,
        "g4_independent": _dig(g4, "acceptance", "independent_verification") == "27/27",
        "g6_status": _dig(g6, "status") == "accepted-bounded-feasibility",
        "g6_results": isinstance(gate6_results, dict) and all(_dig(gate6_results, key, "archive_sha256") == value for key, value in GATE6_RESULTS.items()),
        "g6_conditions": _dig(g6, "required_conditions", "catalog") == "custom JSON with linux-aarch64-none key" and _dig(g6, "required_conditions", "network") == "offline",
        "g6_exclusions": "production catalog publication or artifact distribution" in _dig(g6, "excluded_claims", default=[]) and "CPython 3.14.6 or multi-version managed operation" in _dig(g6, "excluded_claims", default=[]),
        "gate1_status": _dig(g1, "status") == "design-frozen" and _dig(g1, "stage") == "stage3e-managed-python-distribution",
        "gate1_source": transition.get("source_head") == SOURCE_HEAD and transition.get("source_tree") == SOURCE_TREE and transition.get("active_branch") == EXPECTED_BRANCH,
        "gate1_sequence": gate_sequence.get("gate1") == "FROZEN_AUTHORITY_DESIGN" and gate_sequence.get("gate2") == "ACTIVE_NEXT_ISOLATED_DUAL_VERSION_BOUNDARY_CENSUS",
        "gate1_gate2_contract": selected_gate2.get("kind") == "isolated-dual-version-managed-python-boundary-census" and selected_gate2.get("products") == ["CPython 3.14.5 runtime-only", "CPython 3.14.6 runtime-only"] and selected_gate2.get("network") == "offline",
        "gate1_two_keys": selected_gate2.get("catalog_keys") == ["cpython-3.14.5-linux-aarch64-none", "cpython-3.14.6-linux-aarch64-none"],
        "git_diff_check": diff_result.returncode == 0,
    }

    compile_paths = [
        Path(__file__).resolve(),
        root / "scripts/test-verify-project-control-plane.py",
        root / "experiments/stage3d-consumer-integration/verify-gate2-consumer-census.py",
        root / "experiments/stage3d-consumer-integration/verify-gate3-system-python-contract.py",
        root / "experiments/stage3d-consumer-integration/verify-gate4-consumer-integration.py",
    ]
    if all(path.is_file() for path in compile_paths):
        with tempfile.TemporaryDirectory(prefix="project-control-pycache-") as cache_dir:
            env = os.environ.copy()
            env["PYTHONPYCACHEPREFIX"] = cache_dir
            compile_result = subprocess.run(
                [sys.executable, "-m", "py_compile", *(str(path) for path in compile_paths)],
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                env=env,
            )
        checks["python_compile"] = compile_result.returncode == 0
    else:
        checks["python_compile"] = False

    failed = sorted(key for key, value in checks.items() if not value)
    gate6_path = root / "experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json"
    gate1_path = root / "experiments/stage3e-managed-python-distribution/gate1-authority.json"
    return {
        "schema_version": 2,
        "verification_kind": "project-control-plane-reconciliation",
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "missing_files": sorted(set(missing)),
        "parse_errors": dict(sorted(parse_errors.items())),
        "observed": {
            "branch": branch_result.stdout.strip() if branch_result.returncode == 0 else None,
            "head": head_result.stdout.strip() if head_result.returncode == 0 else None,
            "tree_before_commit": tree_result.stdout.strip() if tree_result.returncode == 0 else None,
            "gate6_authority_sha256": hashlib.sha256(gate6_path.read_bytes()).hexdigest() if gate6_path.is_file() else None,
            "gate1_authority_sha256": hashlib.sha256(gate1_path.read_bytes()).hexdigest() if gate1_path.is_file() else None,
        },
        "claim_boundary": "Stage 3-D is frozen through Gate 6. Stage 3-E Gate 1 freezes only the authority design for an isolated dual-version census; production distribution remains unaccepted.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    result = verify(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
