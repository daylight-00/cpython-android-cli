#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from verify_full_authority import ROOT, verify


class FullAuthorityVerifierTests(unittest.TestCase):
    def test_success(self) -> None:
        self.assertTrue(verify()["pass"])

    def test_negative_artifact_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "authority.json"
            value = json.loads((ROOT / "experiments/epoch3-upstream-thin-full/full-authority.json").read_text())
            value["artifact"]["sha256"] = "0" * 64
            p.write_text(json.dumps(value))
            result = verify(authority_path=p)
            self.assertFalse(result["pass"])
            self.assertIn("artifact_exact", result["failed_checks"])

    def test_incomplete_missing_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = verify(authority_path=Path(tmp) / "missing.json")
            self.assertFalse(result["pass"])
            self.assertIn("authority_parse", result["failed_checks"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
