#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from verify_full_acceptance import ROOT, verify


class FullAcceptanceVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="e3-full-authority-test-")
        self.root = Path(self.temp.name)
        self.evidence = self.root / "evidence"
        shutil.copytree(ROOT / "experiments/epoch3-upstream-thin-full/authority-evidence", self.evidence)
        self.accepted = self.root / "accepted.json"
        shutil.copyfile(ROOT / "experiments/epoch3-upstream-thin-full/accepted-r4-return.json", self.accepted)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_success_fixture(self) -> None:
        self.assertTrue(verify(root=ROOT, evidence_dir=self.evidence, accepted_path=self.accepted)["pass"])

    def test_expected_negative_identity_mismatch(self) -> None:
        path = self.evidence / "full-reproducibility.json"
        value = json.loads(path.read_text())
        value["second"]["sha256"] = "0" * 64
        path.write_text(json.dumps(value))
        result = verify(root=ROOT, evidence_dir=self.evidence, accepted_path=self.accepted)
        self.assertFalse(result["pass"])
        self.assertIn("full_byte_reproducible", result["failed_checks"])

    def test_incomplete_missing_receipt(self) -> None:
        (self.evidence / "independent-audit.json").unlink()
        result = verify(root=ROOT, evidence_dir=self.evidence, accepted_path=self.accepted)
        self.assertFalse(result["pass"])
        self.assertIn("parse:independent-audit.json", result["failed_checks"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
