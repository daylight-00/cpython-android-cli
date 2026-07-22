#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("audit_rb3_successor_full_m.py")
spec = importlib.util.spec_from_file_location("audit_successor", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class AuditTests(unittest.TestCase):
    def test_required_authority_files_are_named(self):
        self.assertEqual(mod.RESULT, "rb3-successor-full-m-result.json")
        self.assertEqual(mod.STRUCTURAL, "full-structural-verification.json")
        self.assertEqual(mod.QUALIFICATION, "full-android-qualification.json")

    def test_claim_boundary_remains_open(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"successor_full_accepted": False', text)
        self.assertIn('"rb3_closed": False', text)
        self.assertIn('"native_wheel_16k_alignment_pass"', text)
        self.assertIn('"wheel_postprocessing_out_of_scope"', text)
        self.assertNotIn('"explicit_wheel_normalization_pass"', text)


if __name__ == "__main__":
    unittest.main()
