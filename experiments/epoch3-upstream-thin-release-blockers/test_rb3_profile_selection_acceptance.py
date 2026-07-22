from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/epoch3-upstream-thin-release-blockers"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RB3ProfileSelectionAcceptanceTests(unittest.TestCase):
    def test_authority_binds_evidence_and_selects_only_m(self) -> None:
        authority = json.loads((BASE / "rb3-sysconfig-profile-selection-authority.json").read_text())
        self.assertEqual(authority["selected_profile"]["id"], "M")
        self.assertEqual(authority["decision"]["production_normalization_kind"], "upstream-preserved-minimal-consumer-overlay")
        self.assertTrue(authority["claim_boundary"]["sysconfig_profile_selected"])
        self.assertFalse(authority["claim_boundary"]["rb3_closed"])
        self.assertFalse(authority["claim_boundary"]["artifact_family_superseded"])
        for rel, expected in authority["file_identities"].items():
            self.assertEqual(sha(ROOT / rel), expected, rel)

    def test_result_comparison_supports_selection(self) -> None:
        result = json.loads((BASE / "rb3-sysconfig-profile-selection-authority-evidence/target-result.json").read_text())
        profiles = {row["profile"]: row for row in result["profiles"]}
        self.assertFalse(profiles["C"]["checks"]["managed_install"])
        self.assertTrue(profiles["H"]["checks"]["managed_install"])
        self.assertFalse(profiles["U"]["checks"]["raw_native_wheel_build"])
        self.assertTrue(profiles["M"]["checks"]["managed_install"])
        self.assertTrue(profiles["M"]["checks"]["raw_native_wheel_build"])
        self.assertFalse(profiles["M"]["checks"]["raw_native_wheel_policy_clean"])
        self.assertEqual(profiles["M"]["identity"]["build_gnu_type"], "aarch64-apple-darwin24.6.0")
        self.assertNotIn("consumer-normalized-binary-derived", profiles["M"]["identity"]["config_args"])


if __name__ == "__main__":
    unittest.main()
