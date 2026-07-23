from __future__ import annotations
import importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/'experiments/epoch3-upstream-thin-release-blockers/run_rb3_successor_legal_data_rebinding_m.py'
spec=importlib.util.spec_from_file_location('rebind',SCRIPT);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class RebindingTests(unittest.TestCase):
    def test_candidate_boundary_is_fail_closed(self):
        b=mod.candidate_claim_boundary(); self.assertTrue(b['successor_legal_data_rebinding_candidate']); self.assertFalse(b['successor_legal_data_rebinding_accepted']); self.assertFalse(b['rb1_rebound']); self.assertFalse(b['rb2_rebound']); self.assertFalse(b['predecessor_family_superseded']); self.assertFalse(b['selectable']); self.assertFalse(b['publication'])
    def test_frozen_source_authorities_match(self):
        self.assertEqual(mod.sha256_file(mod.RB1_AUTHORITY),mod.RB1_AUTHORITY_SHA); self.assertEqual(mod.sha256_file(mod.RB2_AUTHORITY),mod.RB2_AUTHORITY_SHA)
    def test_missing_family_fails_exact_verification(self):
        with tempfile.TemporaryDirectory() as td:
            r=mod.verify_exact_successor_family(Path(td)); self.assertFalse(r['pass']); self.assertIn('exact_file_set',r['failed_checks'])
    def test_execution_contract_requires_separate_acceptance(self):
        d=json.loads(SCRIPT.with_name('rb3-successor-legal-data-rebinding-m-r1-execution-contract.json').read_text()); self.assertEqual(d['status'],'prepared-owner-qualification-not-run'); self.assertFalse(d['owner_result_boundary']['rb1_rebound']); self.assertFalse(d['owner_result_boundary']['rb2_rebound']); self.assertIn('separate repository acceptance',d['acceptance_rule'].lower())
    def test_host_inspection_is_static_only(self):
        d=json.loads(SCRIPT.with_name('rb3-successor-legal-data-rebinding-m-r1-host-inspection.json').read_text()); self.assertTrue(d['pass']); self.assertTrue(d['successor_family_verification']['pass']); self.assertTrue(d['rb1_static_rebinding']['pass']); self.assertTrue(d['target_required']['host_execution_is_not_substitute']); self.assertFalse(d['claim_boundary']['successor_legal_data_rebinding_candidate'])

if __name__=='__main__': unittest.main()
