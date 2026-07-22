#!/usr/bin/env python3
from __future__ import annotations
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_rb1_legal_integration_acceptance as V
ROOT=Path(__file__).resolve().parents[2];REL=Path('experiments/epoch3-upstream-thin-release-blockers')
class T(unittest.TestCase):
 def test_pass(self):self.assertTrue(V.verify(ROOT)['pass'])
 def fx(self):
  t=Path(tempfile.mkdtemp());shutil.copytree(ROOT/REL,t/REL,symlinks=True);return t
 def test_gap_tamper(self):
  t=self.fx();p=t/REL/'rb1-legal-integration-authority-evidence/legal/updated-gap-register.json';d=json.loads(p.read_text());d['blocking_gap_count']=0;p.write_text(json.dumps(d));self.assertFalse(V.verify(t)['pass'])
 def test_notice_tamper(self):
  t=self.fx();p=t/REL/'rb1-legal-integration-authority-evidence/legal/THIRD-PARTY-NOTICES.candidate.txt';p.write_text(p.read_text()+'x');self.assertFalse(V.verify(t)['pass'])
 def test_approval_tamper(self):
  t=self.fx();p=t/REL/'accepted-rb1-legal-integration-r1-return.json';d=json.loads(p.read_text());d['claim_boundary']['owner_approved']=True;p.write_text(json.dumps(d));self.assertFalse(V.verify(t)['pass'])
if __name__=='__main__':unittest.main()
