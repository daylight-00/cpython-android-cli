#!/usr/bin/env python3
from __future__ import annotations
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_rb1_license_payload_acceptance as verifier
ROOT=Path(__file__).resolve().parents[2];REL=Path('experiments/epoch3-upstream-thin-release-blockers')
class Tests(unittest.TestCase):
 def test_authority_passes(self):self.assertTrue(verifier.verify(ROOT)['pass'])
 def fixture(self):
  t=Path(tempfile.mkdtemp());dst=t/REL;shutil.copytree(ROOT/REL,dst,symlinks=True);return t
 def test_tampered_gap_fails(self):
  t=self.fixture();p=t/REL/'rb1-license-payload-authority-evidence/updated-gap-register.json';d=json.loads(p.read_text());d['blocking_gap_count']=0;p.write_text(json.dumps(d));self.assertFalse(verifier.verify(t)['pass'])
 def test_missing_evidence_fails(self):
  t=self.fixture();(t/REL/'rb1-license-payload-authority-evidence/independent-audit.json').unlink();self.assertFalse(verifier.verify(t)['pass'])
if __name__=='__main__':unittest.main()
