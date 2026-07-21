#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, tempfile, unittest
from pathlib import Path
from verify_install_only_acceptance import ROOT, verify


class AcceptanceTests(unittest.TestCase):
    def test_current_evidence_passes(self) -> None:
        self.assertTrue(verify()["pass"])

    def test_missing_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td) / "evidence"
            shutil.copytree(ROOT / "experiments/epoch3-upstream-thin-install-only/authority-evidence", dst)
            (dst / "independent-audit.json").unlink()
            result = verify(evidence_dir=dst)
            self.assertFalse(result["pass"])
            self.assertIn("parse:independent-audit.json", result["failed_checks"])

    def test_mutated_projection_receipt_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td) / "evidence"
            shutil.copytree(ROOT / "experiments/epoch3-upstream-thin-install-only/authority-evidence", dst)
            p = dst / "install-only-verification.json"
            data = json.loads(p.read_text())
            data["checks"]["exact_projection"] = False
            p.write_text(json.dumps(data))
            result = verify(evidence_dir=dst)
            self.assertFalse(result["pass"])
            self.assertIn("projection_semantics", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
