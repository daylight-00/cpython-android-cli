from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from audit_rb3_successor_stripped_m import EXPECTED_CHANGED_PATHS, EXPECTED_FILENAME, EXPECTED_SOURCE, audit
from run_rb3_successor_stripped_m import qualify_candidate

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-stripped-m-contract.json"
LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-successor-install-only-r5.lock.json"
EXECUTION_CONTRACT = ROOT / "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-stripped-m-r1-execution-contract.json"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class RB3SuccessorStrippedTests(unittest.TestCase):
    def test_contract_and_lock_bind_exact_accepted_install_only(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual({key: contract["accepted_input"][key] for key in lock["artifact"]}, lock["artifact"])
        self.assertEqual(contract["accepted_input"]["authority"], "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-authority.json")
        self.assertEqual(contract["strip_policy"]["expected_eligible_path"], "bin/python3.14")
        self.assertFalse(contract["success_boundary"]["predecessor_family_superseded"])
        self.assertFalse(contract["success_boundary"]["rb3_closed"])

    def test_execution_contract_binds_live_runner_surface(self) -> None:
        contract = json.loads(EXECUTION_CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["status"], "prepared-owner-derivation-pending")
        for rel, expected in contract["file_identities"].items():
            actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, rel)
        boundary = contract["success_boundary"]
        self.assertTrue(boundary["successor_stripped_started"])
        self.assertTrue(boundary["successor_stripped_candidate"])
        self.assertFalse(boundary["successor_stripped_accepted"])
        self.assertFalse(boundary["successor_technical_family_started"])
        self.assertFalse(boundary["predecessor_family_superseded"])
        self.assertFalse(boundary["rb3_closed"])

    def make_result(self, root: Path) -> None:
        artifact = root / "artifacts" / EXPECTED_FILENAME
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"successor-stripped-candidate")
        identity = {
            "filename": EXPECTED_FILENAME,
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            "size_bytes": artifact.stat().st_size,
            "member_count": 3699,
        }
        checks = {"bounded": True, "qualified": True, "protected": True}
        write_json(root / "rb3-successor-stripped-m-result.json", {
            "schema_version": 1,
            "pass": True,
            "checks": checks,
            "failed_checks": [],
            "source_install_only": EXPECTED_SOURCE,
            "artifact": identity,
            "claim_boundary": {
                "successor_stripped_candidate": True,
                "successor_stripped_accepted": False,
                "successor_technical_family_started": False,
                "successor_technical_family_accepted": False,
                "predecessor_family_superseded": False,
                "portable_raw_wheel_claim": False,
                "rb3_closed": False,
                "selectable": False,
                "publication": False,
            },
        })
        write_json(root / "receipts/stripped-reproducibility.json", {"pass": True, "byte_identical": True, "first": {k: identity[k] for k in ("filename", "sha256", "size_bytes")}, "second": {k: identity[k] for k in ("filename", "sha256", "size_bytes")}})
        write_json(root / "receipts/stripped-mutation-receipt.json", {"decision": "distinct-archive", "regular_elf_count": 81, "eligible_elf_count": 1, "changed_elf_count": 1, "eligible_paths": EXPECTED_CHANGED_PATHS, "changed_paths": EXPECTED_CHANGED_PATHS})
        write_json(root / "receipts/stripped-verification.json", {"pass": True, "failed_checks": [], "eligible_paths": EXPECTED_CHANGED_PATHS, "changed_paths": EXPECTED_CHANGED_PATHS, "checks": {"non_elf_bytes_unchanged": True, "elf_dynamic_alignment_preserved": True, "removable_sections_absent_after": True}})
        write_json(root / "receipts/stripped-android-qualification.json", {"pass": True, "failed_checks": []})
        wheel = {"pass": True, "wheel_import_returncode": 0, "raw_policy_clean": False, "postprocessing_boundary": "out-of-scope-external-tool-responsibility", "raw_extension": {"all_load_alignments_16k": True}}
        write_json(root / "receipts/native-wheel-elf-boundary.json", wheel)
        write_json(root / "receipts/native-managed-wheel-elf-boundary.json", wheel)
        write_json(root / "protected-state.json", {"accepted_install_only_unchanged": True, "accepted_full_unchanged": True, "predecessor_stripped_unchanged": True, "frozen_authorities_unchanged": True, "real_managed_root_unchanged": True})

    def test_qualification_exception_is_structured_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "qualification.json"
            with patch("run_rb3_successor_stripped_m.qualify", side_effect=OSError("exec format error")):
                result = qualify_candidate(Path(td) / "candidate.tar.gz", output, "pkg-config")
            self.assertFalse(result["pass"])
            self.assertEqual(result["failed_checks"], ["qualification_completed_without_exception"])
            self.assertIn("OSError: exec format error", result["error"])
            self.assertTrue(result["claim_boundary"]["install_only_authority_frozen"])
            self.assertTrue(result["claim_boundary"]["stripped_started"])
            self.assertFalse(result["claim_boundary"]["stripped_authority_frozen"])
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)

    def test_audit_accepts_complete_candidate_only_result(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_result(root)
            result = audit(root)
            self.assertTrue(result["pass"], result)

    def test_audit_rejects_family_start_or_mutation_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_result(root)
            result_path = root / "rb3-successor-stripped-m-result.json"
            result = json.loads(result_path.read_text(encoding="utf-8"))
            result["claim_boundary"]["successor_technical_family_started"] = True
            write_json(result_path, result)
            mutation_path = root / "receipts/stripped-mutation-receipt.json"
            mutation = json.loads(mutation_path.read_text(encoding="utf-8"))
            mutation["changed_paths"] = ["bin/python3.14", "lib/libpython3.14.so.1.0"]
            write_json(mutation_path, mutation)
            audited = audit(root)
            self.assertFalse(audited["pass"])
            self.assertIn("bounded_mutation", audited["failed_checks"])
            self.assertIn("technical_family_not_started", audited["failed_checks"])


if __name__ == "__main__":
    unittest.main()
