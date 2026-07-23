#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('v',HERE/'verify_rb4_release_operations.py');MOD=importlib.util.module_from_spec(SPEC);assert SPEC.loader;SPEC.loader.exec_module(MOD)
AUTH_REL=Path('experiments/epoch3-upstream-thin-release-blockers/rb4-release-operations-authority.json')
EXTRA=[Path('docs/current/STATE.json'),Path('docs/current/AGENT_TASK.json'),Path('experiments/epoch3-upstream-thin-release-blockers/blocker-register.json'),Path('experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-contract.json')]
def fixture(dst:Path)->None:
 a=json.loads((MOD.ROOT/AUTH_REL).read_text());paths={AUTH_REL,*EXTRA};paths.update(Path(p) for p in a['file_identities']);paths.update(Path(v['path']) for v in a['source_authorities'].values())
 for rel in sorted(paths):
  src=MOD.ROOT/rel;out=dst/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,out)
class Tests(unittest.TestCase):
 def test_repository_passes(self):self.assertTrue(MOD.verify()['pass'])
 def test_revocation_tamper_fails(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);fixture(root);p=root/'experiments/epoch3-upstream-thin-release-blockers/rb4-release-operations-authority-evidence/revocation-readback.json';d=json.loads(p.read_text());d['checks']['revoked_selection_denied']=False;p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');r=MOD.verify(root);self.assertFalse(r['pass']);self.assertIn('file_identities',r['failed_checks'])
 def test_missing_source_fails_structured(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);fixture(root);(root/'experiments/epoch2-upstream-thin-upstream-evolution/upstream-evolution-authority.json').unlink();r=MOD.verify(root);self.assertFalse(r['pass']);self.assertIn('required_inputs',r['failed_checks'])
if __name__=='__main__':unittest.main()
