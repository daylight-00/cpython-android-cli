from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRIPT=Path(__file__).with_name('verify_rb3_successor_legal_family_m_acceptance.py')
spec=importlib.util.spec_from_file_location('legal_accept',SCRIPT); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
class Tests(unittest.TestCase):
 def test_verifier(self): self.assertTrue(mod.verify()['pass'])
 def test_family_lock(self):
  d=json.loads((ROOT/'config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-successor-legal-family-r3.lock.json').read_text()); self.assertEqual(len(d['files']),128); self.assertTrue(d['claim_boundary']['successor_legal_family_accepted'])
 def test_owner_approval_remains_pending(self):
  d=json.loads((SCRIPT.with_name('rb3-successor-legal-family-m-authority.json')).read_text()); self.assertFalse(d['invariants']['owner_approved'])
 def test_rebinding_is_next_not_completed(self):
  d=json.loads((SCRIPT.with_name('rb3-successor-legal-data-rebinding-m-contract.json')).read_text()); self.assertEqual(d['status'],'authorized-not-started'); self.assertFalse(d['failure_boundary']['rb1_rebound']); self.assertFalse(d['failure_boundary']['rb2_rebound'])
 def test_no_supersession(self):
  d=json.loads((SCRIPT.with_name('accepted-rb3-successor-legal-family-m-r2-return.json')).read_text()); self.assertFalse(d['claim_boundary']['predecessor_family_superseded'])
if __name__=='__main__':unittest.main()
