from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRIPT=Path(__file__).with_name('verify_rb3_successor_technical_family_m_acceptance.py')
spec=importlib.util.spec_from_file_location('tech_accept',SCRIPT); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
class AcceptanceTests(unittest.TestCase):
 def test_acceptance_verifier(self): self.assertTrue(mod.verify()['pass'])
 def test_author_rewrite_tree_equivalence(self):
  d=json.loads((SCRIPT.with_name('rb3-successor-technical-family-m-author-rewrite-map.json')).read_text())
  self.assertEqual(d['rewrite_scope']['mapped_commit_count'],12); self.assertEqual(d['receipt_binding']['post_tree'],'3db24449b8009c4056cf5ec29c526a8307e1fe99')
 def test_accepted_family_identity(self):
  d=json.loads((ROOT/'config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-successor-technical-family-r2.lock.json').read_text())
  self.assertEqual(d['release_family']['file_count'],23); self.assertEqual(d['release_family']['fingerprint_sha256'],'1d3714c21c328c10ad356e29971784e550c8b107c570383b36b1ef5cbdef85b5')
 def test_stripped_temporal_amendment_is_verifier_only(self):
  d=json.loads((SCRIPT.with_name('rb3-successor-stripped-m-temporal-verifier-amendment.json')).read_text()); self.assertFalse(d['invariants']['accepted_stripped_bytes_changed']); self.assertFalse(d['invariants']['authority_bytes_changed'])
 def test_next_gate_remains_bounded(self):
  d=json.loads((SCRIPT.with_name('rb3-successor-legal-family-m-contract.json')).read_text())
  b=d['success_boundary']; self.assertTrue(b['successor_legal_family_candidate']); self.assertFalse(b['successor_legal_family_accepted']); self.assertFalse(b['predecessor_family_superseded']); self.assertFalse(b['rb3_closed'])
if __name__=='__main__':unittest.main()
