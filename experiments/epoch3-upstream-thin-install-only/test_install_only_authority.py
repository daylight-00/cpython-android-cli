#!/usr/bin/env python3
from __future__ import annotations
import json, tempfile, unittest
from pathlib import Path
from verify_install_only_authority import AUTHORITY, ROOT, verify


class AuthorityTests(unittest.TestCase):
    def test_current_authority_passes(self) -> None:
        self.assertTrue(verify()["pass"])

    def test_missing_authority_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            result = verify(authority_path=Path(td) / "missing.json")
            self.assertFalse(result["pass"])

    def test_mutated_artifact_identity_fails(self) -> None:
        data = json.loads(AUTHORITY.read_text())
        data["artifact"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "authority.json"
            path.write_text(json.dumps(data))
            result = verify(authority_path=path)
            self.assertFalse(result["pass"])
            self.assertIn("artifact_exact", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
