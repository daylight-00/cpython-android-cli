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
VERIFIER = ROOT / "experiments/epoch3-upstream-thin-artifact-family/verify_artifact_family_authority.py"


class ArtifactFamilyAuthorityTests(unittest.TestCase):
    def run_verifier(self, root: Path, authority: Path | None = None) -> tuple[int, dict]:
        command = [sys.executable, str(VERIFIER), "--root", str(root)]
        if authority:
            command += ["--authority", str(authority)]
        proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc.returncode, json.loads(proc.stdout)

    def test_success(self) -> None:
        code, result = self.run_verifier(ROOT)
        self.assertEqual(code, 0)
        self.assertTrue(result["pass"])

    def test_expected_negative_claim_change(self) -> None:
        with tempfile.TemporaryDirectory(prefix="artifact-family-authority-") as tmp:
            path = Path(tmp) / "authority.json"
            data = json.loads((ROOT / "experiments/epoch3-upstream-thin-artifact-family/artifact-family-authority.json").read_text())
            data["claim_boundary"]["selectable"] = True
            path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
            code, result = self.run_verifier(ROOT, path)
            self.assertNotEqual(code, 0)
            self.assertFalse(result["pass"])

    def test_incomplete_missing_identity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="artifact-family-authority-") as tmp:
            fixture = Path(tmp)
            shutil.copytree(ROOT / "experiments/epoch3-upstream-thin-artifact-family", fixture / "experiments/epoch3-upstream-thin-artifact-family")
            shutil.copytree(ROOT / "components/upstream-thin", fixture / "components/upstream-thin")
            (fixture / "config/products").mkdir(parents=True)
            shutil.copy2(ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-artifact-family-r1.lock.json", fixture / "config/products/")
            (fixture / "components/upstream-thin/lib/release_family.py").unlink()
            code, result = self.run_verifier(fixture)
            self.assertNotEqual(code, 0)
            self.assertFalse(result["pass"])


if __name__ == "__main__":
    unittest.main()
