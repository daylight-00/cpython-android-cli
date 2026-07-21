#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from verify_stripped_authority import AUTHORITY, verify


class AuthorityTests(unittest.TestCase):
    def test_current_authority_passes(self) -> None:
        self.assertTrue(verify()["pass"])

    def test_missing_authority_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse(verify(authority_path=Path(td) / "missing.json")["pass"])

    def test_mutated_change_surface_fails(self) -> None:
        data = json.loads(AUTHORITY.read_text())
        data["strip_surface"]["changed_paths"] = ["lib/libpython3.14.so"]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "authority.json"
            path.write_text(json.dumps(data))
            result = verify(authority_path=path)
            self.assertFalse(result["pass"])
            self.assertIn("strip_surface_exact", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
