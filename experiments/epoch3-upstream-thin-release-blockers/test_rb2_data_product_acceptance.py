from __future__ import annotations
import importlib.util, json, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/'experiments/epoch3-upstream-thin-release-blockers/verify_rb2_data_product_acceptance.py'
spec=importlib.util.spec_from_file_location('rb2verify',SCRIPT); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
class TestRB2Acceptance(unittest.TestCase):
    def test_frozen_acceptance_passes(self): self.assertTrue(mod.verify()['pass'])
    def test_result_claims_remain_bounded(self):
        r=json.loads((ROOT/'experiments/epoch3-upstream-thin-release-blockers/rb2-data-product-authority-evidence/result.json').read_text())
        self.assertFalse(r['claim_boundary']['rb2_closed']); self.assertFalse(r['claim_boundary']['selectable']); self.assertFalse(r['claim_boundary']['publication'])
    def test_exact_artifact_identities(self):
        r=json.loads((ROOT/'experiments/epoch3-upstream-thin-release-blockers/rb2-data-product-authority-evidence/result.json').read_text())
        self.assertEqual(r['current']['artifact']['sha256'],'e7dcdfa84f093d8bbdea50c80f25b9f20bddd8619199610405c4ba344790268d')
        self.assertEqual(r['rollback']['artifact']['sha256'],'144d96b8f301309fc2269cc73c9f888a37b663afc0ae3e485966834b635d750d')
if __name__=='__main__': unittest.main()
