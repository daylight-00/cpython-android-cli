from __future__ import annotations
import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'experiments/epoch3-upstream-thin-release-blockers/verify_rb5_rb7_runtime_support_policy_correction.py'
S=importlib.util.spec_from_file_location('v',P);M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
class Tests(unittest.TestCase):
 def fixture(self):
  d=Path(tempfile.mkdtemp());shutil.copytree(ROOT,d/'repo',dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git'));self.addCleanup(shutil.rmtree,d);return d/'repo'
 def test_current_tree_passes(self):self.assertTrue(M.verify()['pass'],M.verify())
 def mutate(self,path,fn):
  r=self.fixture();p=r/path;o=json.loads(p.read_text());fn(o);p.write_text(json.dumps(o));self.assertFalse(M.verify(r)['pass'])
 def test_reject_api24_validated_overclaim(self):self.mutate('docs/current/STATE.json',lambda o:o['claim_boundaries'].__setitem__('api24_runtime_device_validated',True))
 def test_reject_broad_nontermux_overclaim(self):self.mutate('docs/current/STATE.json',lambda o:o['claim_boundaries'].__setitem__('other_non_termux_android_contexts_supported',True))
 def test_reject_16k_support(self):self.mutate('docs/current/STATE.json',lambda o:o['claim_boundaries'].__setitem__('actual_16k_runtime_supported',True))
if __name__=='__main__':unittest.main()
