from __future__ import annotations
import json,tempfile,unittest,shutil
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v',ROOT/'experiments/epoch3-upstream-thin-release-blockers/verify_rb1_source_provenance_acceptance.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class T(unittest.TestCase):
 def test_real(self):self.assertTrue(m.verify(ROOT)['pass'])
 def test_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   x=Path(d)/'r';shutil.copytree(ROOT,x);p=x/'experiments/epoch3-upstream-thin-release-blockers/rb1-source-provenance-authority-evidence/source-provenance.json';p.write_text('{}\n');self.assertFalse(m.verify(x)['pass'])
 def test_claim_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   x=Path(d)/'r';shutil.copytree(ROOT,x);p=x/'experiments/epoch3-upstream-thin-release-blockers/accepted-rb1-source-provenance-r1-return.json';q=json.loads(p.read_text());q['claim_boundary']['selectable']=True;p.write_text(json.dumps(q));self.assertFalse(m.verify(x)['pass'])
if __name__=='__main__':unittest.main()
