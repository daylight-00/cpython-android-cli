#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "experiments/epoch3-upstream-thin-artifact-family/verify_artifact_family_acceptance.py"


class ArtifactFamilyAcceptanceTests(unittest.TestCase):
    def run_verifier(self, root: Path) -> tuple[int, dict]:
        proc = subprocess.run([sys.executable, str(VERIFIER), "--root", str(root)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc.returncode, json.loads(proc.stdout)

    def make_fixture(self) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="artifact-family-acceptance-"))
        for rel in [
            "experiments/epoch3-upstream-thin-artifact-family",
            "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-artifact-family-r1.lock.json",
        ]:
            src = ROOT / rel
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def test_success(self) -> None:
        code, result = self.run_verifier(ROOT)
        self.assertEqual(code, 0)
        self.assertTrue(result["pass"])

    def test_expected_negative_identity_change(self) -> None:
        root = self.make_fixture()
        path = root / "experiments/epoch3-upstream-thin-artifact-family/accepted-r1-return.json"
        data = json.loads(path.read_text())
        data["release_family"]["file_count"] = 22
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        code, result = self.run_verifier(root)
        self.assertNotEqual(code, 0)
        self.assertFalse(result["pass"])

    def test_incomplete_missing_evidence(self) -> None:
        root = self.make_fixture()
        (root / "experiments/epoch3-upstream-thin-artifact-family/authority-evidence/independent-audit.json").unlink()
        code, result = self.run_verifier(root)
        self.assertNotEqual(code, 0)
        self.assertFalse(result["pass"])


if __name__ == "__main__":
    unittest.main()
