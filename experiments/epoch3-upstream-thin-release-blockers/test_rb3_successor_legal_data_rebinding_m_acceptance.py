#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,tempfile,unittest,shutil,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('verifier',HERE/'verify_rb3_successor_legal_data_rebinding_m_acceptance.py'); MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)
class AcceptanceTests(unittest.TestCase):
 def test_repository_passes(self): self.assertTrue(MOD.verify()['pass'])
 def test_missing_evidence_fails_structured(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); shutil.copytree(MOD.ROOT,root,dirs_exist_ok=True); (root/'experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-data-rebinding-m-authority-evidence/owner-result.json').unlink(); r=MOD.verify(root); self.assertFalse(r['pass']); self.assertIn('file_identities',r['failed_checks'])
 def test_read_only_content_tamper_fails(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); shutil.copytree(MOD.ROOT,root,dirs_exist_ok=True); p=root/'experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-data-rebinding-m-authority-evidence/rb2-data-runtime-rebinding.json'; d=json.loads(p.read_text()); d['install_root_invariance']['content_identity_unchanged']=False; p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n'); r=MOD.verify(root); self.assertFalse(r['pass']); self.assertIn('file_identities',r['failed_checks']); self.assertIn('read_only',r['failed_checks'])
if __name__=='__main__':unittest.main()
