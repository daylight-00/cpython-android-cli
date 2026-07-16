#!/usr/bin/env python3
"""Exercise project-control fixtures through the Gate 5 documentation correction."""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True

import importlib.util
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("verify-project-control-plane.py")
SOURCE = Path(__file__).resolve().parents[1]


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def copy(rel: str, root: Path) -> None:
    source = SOURCE / rel
    destination = root / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def load_module():
    spec = importlib.util.spec_from_file_location("project_control", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_fixture(root: Path) -> None:
    copy("README.md", root)
    copy("docs/GITHUB_COLLABORATION_WORKFLOW.md", root)
    write(root / "docs/PROJECT_CONTEXT_STAGE3D.md", "frozen\n")
    write(root / "docs/PROJECT_CONTEXT_STAGE3E.md", "> **Status:** Stage 3-E frozen through Gate 5 independent distribution freeze\n")
    write(root / "docs/stages/STAGE3E_SCOPE.md", "> **Status:** FROZEN — Gate 5 independent distribution freeze complete\n")

    copy_paths = [
        "docs/PROJECT_CONTEXT_STAGE3F.md",
        "docs/stages/STAGE3F_SCOPE.md",
        "docs/PROJECT_ORIENTATION.md",
        "docs/handoff/README.md",
        "docs/handoff/2026-07-16-stage3f-gate2-contract-freeze.md",
        "docs/handoff/2026-07-16-stage3f-gate3-loopback-freeze.md",
        "docs/evidence/STAGE3F_GATE1_REPOSITORY_TRANSACTION_RESULT.md",
        "docs/evidence/STAGE3F_GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_RESULT.md",
        "docs/evidence/STAGE3F_GATE2_REPOSITORY_TRANSACTION_RESULT.md",
        "docs/evidence/STAGE3F_GATE3_LOOPBACK_TRANSPORT_ACQUISITION_RESULT.md",
        "docs/evidence/STAGE3F_GATE4_V1_DERIVATION_FAILURE.md",
        "docs/evidence/STAGE3F_GATE4_RETAINED_ARTIFACT_ACQUISITION_RESULT.md",
        "docs/handoff/2026-07-16-stage3f-gate4-retention-correction-acceptance.md",
        "experiments/stage3f-publication-acquisition/GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT.md",
        "experiments/stage3f-publication-acquisition/publication_snapshot.py",
        "experiments/stage3f-publication-acquisition/generate-gate2-publication-snapshot.py",
        "experiments/stage3f-publication-acquisition/verify-gate2-publication-snapshot.py",
        "experiments/stage3f-publication-acquisition/run-gate2-publication-snapshot.sh",
        "experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json",
        "experiments/stage3f-publication-acquisition/gate2-publication-snapshot-authority.json",
        "experiments/stage3f-publication-acquisition/GATE3_LOOPBACK_TRANSPORT_ACQUISITION_IMPLEMENTATION.md",
        "experiments/stage3f-publication-acquisition/loopback_acquisition.py",
        "experiments/stage3f-publication-acquisition/verify-gate3-loopback-acquisition.py",
        "experiments/stage3f-publication-acquisition/run-gate3-loopback-acquisition.sh",
        "experiments/stage3f-publication-acquisition/gate3-loopback-acquisition-authority.json",
        "experiments/stage3f-publication-acquisition/gate2-retention-correction-authority.json",
        "experiments/stage3f-publication-acquisition/GATE4_TERMUX_RETAINED_ARTIFACT_ACQUISITION.md",
        "experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json",
        "experiments/stage3f-publication-acquisition/gate4-retained-artifact-acquisition-authority.json",
        "experiments/stage3f-publication-acquisition/GATE5_INDEPENDENT_PUBLICATION_ACQUISITION_FREEZE.md",
        "experiments/stage3f-publication-acquisition/gate5-independent-publication-acquisition-freeze.json",
        "experiments/stage3f-publication-acquisition/verify-gate5-independent-freeze.py",
        "experiments/stage3f-publication-acquisition/test-verify-gate5-independent-freeze.py",
        "experiments/stage3f-publication-acquisition/run-gate5-independent-freeze.sh",
        "docs/evidence/STAGE3F_GATE5_INDEPENDENT_FREEZE.md",
        "docs/evidence/STAGE3F_FINAL_SUMMARY.md",
        "docs/handoff/2026-07-16-stage3f-independent-freeze.md",
        "docs/handoff/2026-07-16-stage3f-gate5-documentation-integrity-correction.md",
        "docs/evidence/STAGE3F_GATE5_DOCUMENTATION_INTEGRITY_CORRECTION.md",
        "experiments/stage3f-publication-acquisition/GATE5_DOCUMENTATION_INTEGRITY_CORRECTION.md",
        "experiments/stage3f-publication-acquisition/gate5-documentation-integrity-correction-authority.json",
        "experiments/stage3f-publication-acquisition/verify-gate5-documentation-integrity-correction.py",
        "experiments/stage3f-publication-acquisition/test-verify-gate5-documentation-integrity-correction.py",
        "experiments/stage3f-publication-acquisition/run-gate5-documentation-integrity-correction.sh",
    ]
    for rel in copy_paths:
        copy(rel, root)

    write(root / "docs/handoff/2026-07-16-stage3e-frozen-session-close.md", "close\n")
    write(
        root / "docs/handoff/2026-07-16-stage3f-gate1-authority-start.md",
        "6419e107e4aa8400ebd3d98f3583999075b8b935 e16edd99bfadf2135d0b632ddef4d292c0d80ea6 "
        "b5a2ca39d1250122312355dd3dbc6165b9409786 control-wrapper false negative\n",
    )
    write(root / "docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md", "3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2 117/117\n")
    write(root / "docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md", "4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112 794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a 191 186/186\n")
    write(root / "docs/evidence/STAGE3E_FINAL_SUMMARY.md", "3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2 5813305c22528354e6af686330e8f635db2b90a8a7a48ed5ed3c9ad4d1a4fb4d 4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112 794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a\n")
    write(root / "experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md", "> **Status:** DESIGN FROZEN\n")
    write(root / "docs/evidence/STAGE3F_GATE1_AUTHORITY_DESIGN_RESULT.md", "> **Status:** FROZEN — repository-only authority design\n")

    write_json(root / "experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json", {"status": "accepted-bounded-feasibility"})
    write_json(root / "experiments/stage3e-managed-python-distribution/gate1-authority.json", {"status": "design-frozen"})
    write_json(root / "experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json", {"status": "target-evidence-accepted-by-external-reaudit", "accepted_result": {"archive_sha256": "3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2"}})
    write_json(root / "experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json", {"accepted": True, "check_count": 117, "pass_count": 117})
    write_json(root / "experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json", {"status": "contract-frozen", "selection_contract": {"canonical": "exact-patch-version-request"}})
    write_json(root / "experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json", {"status": "accepted-target-evidence", "accepted_result": {"archive_sha256": "4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112", "archive_size": 54299, "safe_member_count": 191, "result_index_count": 186, "target_verification": {"check_count": 37, "pass_count": 37}, "independent_audit": {"sha256": "794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a", "check_count": 74, "pass_count": 74}}})
    write_json(root / "experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json", {"accepted": True, "check_count": 74, "pass_count": 74, "failed_checks": []})
    write(root / "experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md", "> **Status:** FROZEN\nGate 5 closes Stage 3-E\n")
    write_json(root / "experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json", {"status": "independent-freeze-complete", "claim_boundary": "Broader work require a new stage authority."})
    copy("experiments/stage3f-publication-acquisition/gate1-authority.json", root)

    (root / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT, root / "scripts/verify-project-control-plane.py")
    shutil.copy2(Path(__file__).resolve(), root / "scripts/test-verify-project-control-plane.py")

    subprocess.run(["git", "init", "-q", "-b", "agent/stage3f-publication-acquisition"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "fixture"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)


def main() -> int:
    module = load_module()
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "repo"
        root.mkdir()
        make_fixture(root)
        success = module.verify(root)
        if not success["pass"]:
            raise SystemExit(success)

        authority = root / "experiments/stage3f-publication-acquisition/gate5-documentation-integrity-correction-authority.json"
        value = json.loads(authority.read_text(encoding="utf-8"))
        value["status"] = "broken"
        write_json(authority, value)
        expected_negative = module.verify(root)
        if expected_negative["pass"] or expected_negative["failed_checks"] != ["gate5_docfix_status"]:
            raise SystemExit(expected_negative)

        value["status"] = "correction-v2-defined-and-locally-verified"
        write_json(authority, value)
        readme = root / "README.md"
        readme.write_text("Stage 3-F frozen\n", encoding="utf-8")
        shortened_document = module.verify(root)
        if shortened_document["pass"] or "readme_production_shape" not in shortened_document["failed_checks"]:
            raise SystemExit(shortened_document)

        copy("README.md", root)
        retained = root / "experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json"
        retained.unlink()
        incomplete = module.verify(root)
        rel = str(retained.relative_to(root))
        if incomplete["pass"] or "required_files" not in incomplete["failed_checks"] or rel not in incomplete["missing_files"]:
            raise SystemExit(incomplete)

        print(json.dumps({
            "schema_version": 1,
            "verification_kind": "project-control-plane-fixtures-through-stage3f-gate5-documentation-integrity-correction",
            "pass": True,
            "fixtures": {
                "success": success["check_count"],
                "expected_negative": expected_negative["failed_checks"],
                "shortened_document": shortened_document["failed_checks"],
                "incomplete": incomplete["missing_files"],
            },
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
