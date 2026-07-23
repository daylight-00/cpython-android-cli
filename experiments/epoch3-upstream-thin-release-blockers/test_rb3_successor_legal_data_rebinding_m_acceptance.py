#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "verifier", HERE / "verify_rb3_successor_legal_data_rebinding_m_acceptance.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)

AUTHORITY_REL = Path(
    "experiments/epoch3-upstream-thin-release-blockers/"
    "rb3-successor-legal-data-rebinding-m-authority.json"
)
EVIDENCE_REL = Path(
    "experiments/epoch3-upstream-thin-release-blockers/"
    "rb3-successor-legal-data-rebinding-m-authority-evidence"
)


def copy_authority_fixture(destination: Path) -> None:
    """Copy only files that the acceptance verifier is authorized to read."""
    authority = json.loads((MOD.ROOT / AUTHORITY_REL).read_text(encoding="utf-8"))
    relative_paths = {AUTHORITY_REL}
    relative_paths.update(Path(path) for path in authority["file_identities"])
    relative_paths.update(
        Path(entry["path"]) for entry in authority["source_authorities"].values()
    )

    for relative_path in sorted(relative_paths):
        source = MOD.ROOT / relative_path
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


class AcceptanceTests(unittest.TestCase):
    def test_repository_passes(self) -> None:
        self.assertTrue(MOD.verify()["pass"])

    def test_missing_evidence_fails_structured(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            copy_authority_fixture(root)
            (root / EVIDENCE_REL / "owner-result.json").unlink()
            result = MOD.verify(root)
            self.assertFalse(result["pass"])
            self.assertIn("file_identities", result["failed_checks"])

    def test_read_only_content_tamper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            copy_authority_fixture(root)
            evidence = root / EVIDENCE_REL / "rb2-data-runtime-rebinding.json"
            data = json.loads(evidence.read_text(encoding="utf-8"))
            data["install_root_invariance"]["content_identity_unchanged"] = False
            evidence.write_text(
                json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            result = MOD.verify(root)
            self.assertFalse(result["pass"])
            self.assertIn("file_identities", result["failed_checks"])
            self.assertIn("read_only", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
