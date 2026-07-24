from __future__ import annotations
import importlib.util, json, shutil, tempfile, unittest
from pathlib import Path
BASE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('verify_rb5_scope', BASE / 'verify_rb5_api24_support_scope.py')
MOD = importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(MOD)

class RB5ScopeTests(unittest.TestCase):
    def test_current_tree_passes(self):
        self.assertTrue(MOD.verify()['pass'])

    def _fixture(self) -> Path:
        root = Path(tempfile.mkdtemp())
        auth = json.loads((MOD.ROOT / MOD.AUTH_REL).read_text())
        paths = set(auth.get('file_identities', {})) | {v['path'] for v in auth.get('source_authorities', {}).values()} | {
            MOD.AUTH_REL, 'docs/current/STATE.json', 'docs/current/AGENT_TASK.json',
            'experiments/epoch3-upstream-thin-release-blockers/blocker-register.json',
            'experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-disposition-contract.json',
            'docs/roadmap/EPOCH3_RELEASE_BLOCKER_RESOLUTION_PLAN.md'}
        for rel in paths:
            src = MOD.ROOT / rel; dst = root / rel; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)
        return root

    def test_api24_support_tamper_fails(self):
        root = self._fixture()
        p = root / 'docs/current/STATE.json'; obj = json.loads(p.read_text()); obj['claim_boundaries']['api24_runtime_supported'] = True; p.write_text(json.dumps(obj))
        self.assertFalse(MOD.verify(root)['pass'])

    def test_minimum_api_inference_fails(self):
        root = self._fixture()
        p = root / 'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-support-scope-authority.json'; obj = json.loads(p.read_text()); obj['support_policy']['minimum_supported_android_api_declared'] = True; p.write_text(json.dumps(obj))
        self.assertFalse(MOD.verify(root)['pass'])

if __name__ == '__main__': unittest.main()
