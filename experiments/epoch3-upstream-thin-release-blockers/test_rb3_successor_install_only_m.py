from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_rb3_successor_install_only_m as audit_module


class SuccessorInstallOnlyAuditTests(unittest.TestCase):
    def make_result(self, root: Path) -> dict[str, object]:
        (root / "artifacts").mkdir(parents=True)
        (root / "receipts").mkdir()
        artifact = root / "artifacts" / audit_module.EXPECTED["filename"]
        artifact.write_bytes(b"fixture")
        expected = {
            "filename": artifact.name,
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            "size_bytes": artifact.stat().st_size,
            "member_count": 3699,
        }
        result = {
            "pass": True,
            "failed_checks": [],
            "checks": {"x": True},
            "artifact": expected,
            "claim_boundary": {
                "successor_install_only_candidate": True,
                "successor_install_only_accepted": False,
                "successor_stripped_started": False,
                "predecessor_family_superseded": False,
                "rb3_closed": False,
                "selectable": False,
                "publication": False,
                "portable_raw_wheel_claim": False,
                "user_built_wheel_postprocessing": "out-of-scope-external-tool-responsibility",
            },
        }
        (root / "rb3-successor-install-only-m-result.json").write_text(json.dumps(result))
        for name in ("install-only-verification.json", "install-only-android-qualification.json"):
            (root / "receipts" / name).write_text(json.dumps({"pass": True, "failed_checks": []}))
        wheel = {
            "pass": True,
            "wheel_import_returncode": 0,
            "raw_policy_clean": False,
            "postprocessing_boundary": "out-of-scope-external-tool-responsibility",
            "raw_extension": {"all_load_alignments_16k": True},
        }
        (root / "receipts/native-wheel-elf-boundary.json").write_text(json.dumps(wheel))
        (root / "receipts/native-managed-wheel-elf-boundary.json").write_text(json.dumps(wheel))
        (root / "protected-state.json").write_text(json.dumps({"accepted_full_unchanged": True, "predecessor_install_only_unchanged": True, "real_managed_root_unchanged": True}))
        return expected

    def test_accepts_complete_candidate_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            expected = self.make_result(root)
            with mock.patch.dict(audit_module.EXPECTED, expected, clear=True):
                self.assertTrue(audit_module.audit(root)["pass"])

    def test_rejects_premature_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            expected = self.make_result(root)
            path = root / "rb3-successor-install-only-m-result.json"
            value = json.loads(path.read_text())
            value["claim_boundary"]["successor_install_only_accepted"] = True
            path.write_text(json.dumps(value))
            with mock.patch.dict(audit_module.EXPECTED, expected, clear=True):
                self.assertFalse(audit_module.audit(root)["pass"])

    def test_rejects_raw_policy_clean_claim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            expected = self.make_result(root)
            path = root / "receipts/native-wheel-elf-boundary.json"
            value = json.loads(path.read_text())
            value["raw_policy_clean"] = True
            path.write_text(json.dumps(value))
            with mock.patch.dict(audit_module.EXPECTED, expected, clear=True):
                result = audit_module.audit(root)
                self.assertFalse(result["pass"])
                self.assertIn("raw_policy_diagnostic_only", result["failed_checks"])

    def test_rejects_portable_raw_wheel_claim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            expected = self.make_result(root)
            path = root / "rb3-successor-install-only-m-result.json"
            value = json.loads(path.read_text())
            value["claim_boundary"]["portable_raw_wheel_claim"] = True
            path.write_text(json.dumps(value))
            with mock.patch.dict(audit_module.EXPECTED, expected, clear=True):
                result = audit_module.audit(root)
                self.assertFalse(result["pass"])
                self.assertIn("raw_policy_diagnostic_only", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
