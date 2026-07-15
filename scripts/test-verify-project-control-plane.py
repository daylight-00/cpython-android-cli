#!/usr/bin/env python3
"""Exercise project-control verification with success, expected-negative, and incomplete fixtures."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("verify-project-control-plane.py")


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_project_control_plane", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(root: Path) -> None:
    write(
        root / "README.md",
        "Stage 3-D  consumer integration                         frozen — Gate 6 bounded managed-Python feasibility complete\n"
        "Stage 3-E  managed-Python distribution                  active — Gate 1 authority frozen; Gate 2 next\n",
    )
    write(
        root / "docs/PROJECT_CONTEXT_STAGE3D.md",
        "> **Status:** Stage 3-D frozen through Gate 6 bounded managed-Python feasibility\n"
        "Gate 6  bounded managed-Python feasibility      FROZEN — A/B/C accepted\n",
    )
    write(
        root / "docs/stages/STAGE3D_SCOPE.md",
        "Gate 6  bounded managed-Python feasibility research     FROZEN — A/B/C accepted\n",
    )
    write(
        root / "docs/PROJECT_CONTEXT_STAGE3E.md",
        "> **Status:** Stage 3-E active — Gate 1 authority design frozen\n"
        "agent/stage3e-managed-python-distribution\n"
        "Gate 1  authority and productization-boundary design    FROZEN\n"
        "Gate 2  isolated dual-version boundary census           ACTIVE NEXT\n",
    )
    write(
        root / "docs/stages/STAGE3E_SCOPE.md",
        "> **Status:** ACTIVE — Gate 1 authority design frozen; Gate 2 next\n"
        "Gate 2  isolated dual-version boundary census           ACTIVE NEXT\n",
    )
    write(root / "docs/PROJECT_ORIENTATION.md", "Stage 3-E Gate 1 freezes the authority boundary\ndocs/PROJECT_CONTEXT_STAGE3E.md\n")
    write(root / "docs/handoff/README.md", "Stage 3-E Gate 2 isolated dual-version boundary census  ACTIVE NEXT\n")
    write(root / "docs/GITHUB_COLLABORATION_WORKFLOW.md", "docs/PROJECT_CONTEXT_STAGE3E.md\ngate1-authority.json\n")
    write(root / "docs/handoff/COLLABORATION_PROTOCOL.md", "docs/PROJECT_CONTEXT_STAGE3E.md\ngate1-authority.json\n")
    write(root / "docs/session-operations/LESSONS_AND_CHANGELOG.md", "minimum sufficient validation\n")
    write(
        root / "docs/evidence/STAGE3D_GATE4_CONSUMER_INTEGRATION_TARGET_VALIDATION_RESULT.md",
        "13ed73fdeaf5ea13339b2df70b69a4c79aa2920fb1d9207229fb64db828b283c\n697/697 exact\n",
    )
    write(
        root / "docs/evidence/STAGE3D_GATE6_MANAGED_PYTHON_FEASIBILITY_RESULT.md",
        "fa582b372b81feed68b76ee64bf304d364f9280b10a5569da6cb6fd9f9d43694\n"
        "73ef934e3a2346546c79032a80a4a791ac55f4858a02100301afd33f9bc8fa03\n"
        "a0e15ef45171af409df27fb2265bb7afed7c1631176ebe6e563be04725fd72d6\n",
    )
    write(
        root / "experiments/stage3e-managed-python-distribution/GATE1_AUTHORITY_DESIGN.md",
        "> **Status:** DESIGN FROZEN\n"
        "isolated offline dual-version managed-Python boundary census\n",
    )
    write_json(
        root / "experiments/stage3d-consumer-integration/gate2-consumer-census-authority.json",
        {"status": "target-evidence-accepted", "scenario_results": {"count": 64, "expectation_match": 64}},
    )
    write_json(
        root / "experiments/stage3d-consumer-integration/gate3-system-python-contract.json",
        {"status": "contract-frozen", "canonical_contract": {"selector": "explicit-absolute-interpreter-path"}},
    )
    write_json(
        root / "experiments/stage3d-consumer-integration/gate4-consumer-integration-validation-matrix.json",
        {"scenario_count": 48, "scenarios": [{} for _ in range(48)]},
    )
    write_json(
        root / "experiments/stage3d-consumer-integration/gate4-consumer-integration-authority.json",
        {
            "status": "accepted",
            "accepted_result": {"archive": {"sha256": "13ed73fdeaf5ea13339b2df70b69a4c79aa2920fb1d9207229fb64db828b283c"}},
            "acceptance": {"independent_verification": "27/27"},
        },
    )
    write_json(
        root / "experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json",
        {
            "status": "accepted-bounded-feasibility",
            "accepted_results": {
                "gate6a": {"archive_sha256": "fa582b372b81feed68b76ee64bf304d364f9280b10a5569da6cb6fd9f9d43694"},
                "gate6b": {"archive_sha256": "73ef934e3a2346546c79032a80a4a791ac55f4858a02100301afd33f9bc8fa03"},
                "gate6c": {"archive_sha256": "a0e15ef45171af409df27fb2265bb7afed7c1631176ebe6e563be04725fd72d6"},
            },
            "required_conditions": {"catalog": "custom JSON with linux-aarch64-none key", "network": "offline"},
            "excluded_claims": [
                "production catalog publication or artifact distribution",
                "CPython 3.14.6 or multi-version managed operation",
            ],
        },
    )
    write_json(
        root / "experiments/stage3e-managed-python-distribution/gate1-authority.json",
        {
            "status": "design-frozen",
            "stage": "stage3e-managed-python-distribution",
            "repository_transition": {
                "source_head": "c4f0333db196b7bf0e074b9556d566e0d33c91aa",
                "source_tree": "593695ee66270cb9f496df10bef624717ba7fc98",
                "active_branch": "agent/stage3e-managed-python-distribution",
            },
            "gate_sequence": {
                "gate1": "FROZEN_AUTHORITY_DESIGN",
                "gate2": "ACTIVE_NEXT_ISOLATED_DUAL_VERSION_BOUNDARY_CENSUS",
            },
            "selected_gate2": {
                "kind": "isolated-dual-version-managed-python-boundary-census",
                "products": ["CPython 3.14.5 runtime-only", "CPython 3.14.6 runtime-only"],
                "network": "offline",
                "catalog_keys": [
                    "cpython-3.14.5-linux-aarch64-none",
                    "cpython-3.14.6-linux-aarch64-none",
                ],
            },
        },
    )
    for path in (
        "experiments/stage3d-consumer-integration/verify-gate2-consumer-census.py",
        "experiments/stage3d-consumer-integration/verify-gate3-system-python-contract.py",
        "experiments/stage3d-consumer-integration/verify-gate4-consumer-integration.py",
    ):
        write(root / path, "pass\n")
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT, root / "scripts/verify-project-control-plane.py")
    shutil.copy2(Path(__file__).resolve(), root / "scripts/test-verify-project-control-plane.py")
    subprocess.run(["git", "init", "-q", "-b", "agent/stage3e-managed-python-distribution"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "fixture"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)


def main() -> int:
    verifier = load_verifier()
    with tempfile.TemporaryDirectory(prefix="project-control-fixtures-") as temp:
        root = Path(temp) / "repo"
        root.mkdir()
        fixture(root)

        success = verifier.verify(root)
        if not success["pass"]:
            raise SystemExit(f"success fixture failed: {success['failed_checks']}")

        scope = root / "docs/stages/STAGE3E_SCOPE.md"
        original_scope = scope.read_text(encoding="utf-8")
        scope.write_text(original_scope.replace("Gate 2  isolated dual-version boundary census           ACTIVE NEXT", "Gate 2  isolated dual-version boundary census           BROKEN", 1), encoding="utf-8")
        negative = verifier.verify(root)
        if negative["pass"] or negative["failed_checks"] != ["stage3e_scope_gate2"]:
            raise SystemExit(f"negative fixture mismatch: {negative['failed_checks']}")
        scope.write_text(original_scope, encoding="utf-8")

        authority = root / "experiments/stage3e-managed-python-distribution/gate1-authority.json"
        authority.unlink()
        incomplete = verifier.verify(root)
        if incomplete["pass"] or "required_files" not in incomplete["failed_checks"] or str(authority.relative_to(root)) not in incomplete["missing_files"]:
            raise SystemExit(f"incomplete fixture mismatch: {incomplete}")

        result = {
            "schema_version": 1,
            "verification_kind": "project-control-plane-fixtures",
            "pass": True,
            "fixtures": {
                "success": {"pass_count": success["pass_count"], "check_count": success["check_count"]},
                "expected_negative": {"failed_checks": negative["failed_checks"]},
                "incomplete": {"required_files_failed": True, "missing_files": incomplete["missing_files"]},
            },
        }
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
