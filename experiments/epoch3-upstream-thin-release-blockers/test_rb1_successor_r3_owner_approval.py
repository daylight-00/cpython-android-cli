from __future__ import annotations
import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'experiments/epoch3-upstream-thin-release-blockers/verify_rb1_successor_r3_owner_approval.py'
S=importlib.util.spec_from_file_location('v',P);M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
class Tests(unittest.TestCase):
 def fixture(self):
  d=Path(tempfile.mkdtemp());shutil.copytree(ROOT,d/'repo',dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git','__pycache__'));self.addCleanup(shutil.rmtree,d);return d/'repo'
 def test_current(self):self.assertTrue(M.verify()['pass'],M.verify())
 def mutate(self,path,fn):
  r=self.fixture();p=r/path;o=json.loads(p.read_text());fn(o);p.write_text(json.dumps(o));self.assertFalse(M.verify(r)['pass'])
 def test_reject_publication(self):self.mutate('docs/current/STATE.json',lambda o:o['claim_boundaries'].__setitem__('publication_authorized',True))
 def test_reject_wrong_owner(self):self.mutate('experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval.json',lambda o:o['approver'].__setitem__('human_name','Other'))
 def test_reject_selectability(self):self.mutate('docs/current/STATE.json',lambda o:o['claim_boundaries'].__setitem__('selectable',True))
if __name__=='__main__':unittest.main()
