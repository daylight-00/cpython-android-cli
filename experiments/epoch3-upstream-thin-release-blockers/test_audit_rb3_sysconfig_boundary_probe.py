#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("audit_rb3_sysconfig_boundary_probe.py")
spec = importlib.util.spec_from_file_location("audit_probe", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class AuditTests(unittest.TestCase):
    def good_result(self):
        return {
            "pass": True,
            "checks": {"a": True},
            "profiles": [
                {
                    "profile": profile,
                    "checks": {},
                    "managed": {},
                    "wheel": {},
                    "python_config_outputs": [],
                    "pkg_config_output": {},
                }
                for profile in mod.PROFILE_IDS
            ],
            "selection": {"selected": False},
            "claim_boundary": {
                "canonical_artifact_bytes_changed": False,
                "artifact_family_superseded": False,
                "rb3_closed": False,
                "on_device_sdk_final": False,
                "selectable": False,
                "publication": False,
            },
        }

    def test_bounded_result_is_valid(self):
        checks = mod.validate_result_data(self.good_result())
        self.assertTrue(all(checks.values()))

    def test_selected_profile_is_rejected(self):
        data = self.good_result()
        data["selection"]["selected"] = True
        self.assertFalse(mod.validate_result_data(data)["selection_withheld"])

    def test_closed_rb3_is_rejected(self):
        data = self.good_result()
        data["claim_boundary"]["rb3_closed"] = True
        self.assertFalse(mod.validate_result_data(data)["rb3_open"])

    def test_expected_host_profiles_are_exact(self):
        rows = mod.expected_profiles()
        self.assertEqual(set(rows), set(mod.PROFILE_IDS))
        self.assertEqual(rows["C"]["sha256"], "84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76")


if __name__ == "__main__":
    unittest.main()
