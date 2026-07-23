#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('verifier',HERE/'verify_rb3_successor_predecessor_supersession_m.py')
MOD=importlib.util.module_from_spec(SPEC);assert SPEC.loader is not None;SPEC.loader.exec_module(MOD)
AUTH_REL=Path('experiments/epoch3-upstream-thin-release-blockers/rb3-successor-predecessor-supersession-m-authority.json')
EXTRA=[Path('docs/current/STATE.json'),Path('docs/current/AGENT_TASK.json'),Path('experiments/epoch3-upstream-thin-release-blockers/blocker-register.json')]
def fixture(dst:Path)->None:
 authority=json.loads((MOD.ROOT/AUTH_REL).read_text())
 paths={AUTH_REL,*EXTRA}
 paths.update(Path(p) for p in authority['file_identities'])
 paths.update(Path(v['path']) for v in authority['source_authorities'].values())
 for rel in sorted(paths):
  src=MOD.ROOT/rel; out=dst/rel; out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,out)
class Tests(unittest.TestCase):
 def test_repository_passes(self):self.assertTrue(MOD.verify()['pass'])
 def test_canonical_lock_tamper_fails(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);fixture(root);p=root/'config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-canonical-family-r1.lock.json';d=json.loads(p.read_text());d['canonical_family']['release_sha256']='0'*64;p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');r=MOD.verify(root);self.assertFalse(r['pass']);self.assertIn('file_identities',r['failed_checks'])
 def test_missing_predecessor_fails_structured(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);fixture(root);(root/'experiments/epoch3-upstream-thin-artifact-family/artifact-family-authority.json').unlink();r=MOD.verify(root);self.assertFalse(r['pass']);self.assertIn('required_inputs',r['failed_checks'])
if __name__=='__main__':unittest.main()
