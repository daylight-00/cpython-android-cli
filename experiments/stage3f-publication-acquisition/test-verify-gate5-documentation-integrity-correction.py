#!/usr/bin/env python3
"""Fixtures for the Gate 5 documentation-integrity correction verifier."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRIPT = HERE / "verify-gate5-documentation-integrity-correction.py"

COPY_PATHS = [
    "README.md",
    "docs/GITHUB_COLLABORATION_WORKFLOW.md",
    "docs/PROJECT_CONTEXT_STAGE3F.md",
    "docs/PROJECT_ORIENTATION.md",
    "docs/handoff/README.md",
    "docs/stages/STAGE3F_SCOPE.md",
    "docs/evidence/STAGE3F_FINAL_SUMMARY.md",
    "docs/evidence/STAGE3F_GATE5_INDEPENDENT_FREEZE.md",
    "docs/evidence/STAGE3F_GATE5_DOCUMENTATION_INTEGRITY_CORRECTION.md",
    "docs/handoff/2026-07-16-stage3f-independent-freeze.md",
    "docs/handoff/2026-07-16-stage3f-gate5-documentation-integrity-correction.md",
    "experiments/stage3f-publication-acquisition/GATE5_INDEPENDENT_PUBLICATION_ACQUISITION_FREEZE.md",
    "experiments/stage3f-publication-acquisition/GATE5_DOCUMENTATION_INTEGRITY_CORRECTION.md",
    "experiments/stage3f-publication-acquisition/gate5-independent-publication-acquisition-freeze.json",
    "experiments/stage3f-publication-acquisition/gate5-documentation-integrity-correction-authority.json",
    "experiments/stage3f-publication-acquisition/run-gate5-documentation-integrity-correction.sh",
    "experiments/stage3f-publication-acquisition/test-verify-gate5-documentation-integrity-correction.py",
    "experiments/stage3f-publication-acquisition/verify-gate5-documentation-integrity-correction.py",
]


def load_module():
    spec = importlib.util.spec_from_file_location("gate5_doc_correction", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_fixture(dst: Path) -> None:
    for rel in COPY_PATHS:
        source = ROOT / rel
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_file():
            shutil.copy2(source, target)
        elif rel == "experiments/stage3f-publication-acquisition/GATE5_INDEPENDENT_PUBLICATION_ACQUISITION_FREEZE.md":
            target.write_text("# Gate 5 independent freeze fixture\n", encoding="utf-8")
        else:
            raise FileNotFoundError(source)
    subprocess.run(["git", "init", "-q", "-b", "agent/stage3f-publication-acquisition"], cwd=dst, check=True)
    subprocess.run(["git", "config", "user.name", "fixture"], cwd=dst, check=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=dst, check=True)
    subprocess.run(["git", "add", "-A"], cwd=dst, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=dst, check=True)


def main() -> int:
    module = load_module()
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "repo"
        root.mkdir()
        copy_fixture(root)

        success = module.verify(root, set())
        if not success["pass"]:
            raise SystemExit(success)

        readme = root / "README.md"
        readme.write_text("Stage 3-F frozen\n", encoding="utf-8")
        shortened_document = module.verify(root, set())
        expected_negative = {"readme_minimum_lines", "readme_sentinels", "readme_final_status", "retained_snapshot_preserved"}
        if shortened_document["pass"] or not expected_negative.issubset(shortened_document["failed_checks"]):
            raise SystemExit(shortened_document)

        shutil.copy2(ROOT / "README.md", readme)
        residue = root / "scratch" / "__pycache__" / "generated.cpython-314.pyc"
        residue.parent.mkdir(parents=True)
        residue.write_bytes(b"fixture-bytecode")
        bytecode_delta = module.verify(root, set())
        if bytecode_delta["pass"] or bytecode_delta["failed_checks"] != ["no_new_bytecode_residue"]:
            raise SystemExit(bytecode_delta)
        shutil.rmtree(root / "scratch")

        missing = root / "experiments/stage3f-publication-acquisition/gate5-documentation-integrity-correction-authority.json"
        missing.unlink()
        incomplete = module.verify(root, set())
        rel = str(missing.relative_to(root))
        if incomplete["pass"] or "required_files" not in incomplete["failed_checks"] or rel not in incomplete["missing_files"]:
            raise SystemExit(incomplete)

        print(json.dumps({
            "schema_version": 2,
            "verification_kind": "stage3f-gate5-documentation-integrity-correction-fixtures",
            "pass": True,
            "fixtures": {
                "success": success["check_count"],
                "expected_negative_shortened_document": sorted(expected_negative),
                "expected_negative_bytecode_delta": ["no_new_bytecode_residue"],
                "incomplete": [rel],
            },
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
