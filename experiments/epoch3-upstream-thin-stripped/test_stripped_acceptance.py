#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from verify_stripped_acceptance import ROOT, verify


class AcceptanceTests(unittest.TestCase):
    def test_current_evidence_passes(self) -> None:
        self.assertTrue(verify()["pass"])

    def test_missing_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td) / "evidence"
            shutil.copytree(ROOT / "experiments/epoch3-upstream-thin-stripped/authority-evidence", dst)
            (dst / "independent-audit.json").unlink()
            result = verify(evidence_dir=dst)
            self.assertFalse(result["pass"])
            self.assertIn("parse:independent-audit.json", result["failed_checks"])

    def test_mutated_change_surface_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td) / "evidence"
            shutil.copytree(ROOT / "experiments/epoch3-upstream-thin-stripped/authority-evidence", dst)
            path = dst / "stripped-mutation-receipt.json"
            data = json.loads(path.read_text())
            data["changed_paths"] = ["lib/libpython3.14.so"]
            path.write_text(json.dumps(data))
            result = verify(evidence_dir=dst)
            self.assertFalse(result["pass"])
            self.assertIn("strip_surface_exact", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
