from __future__ import annotations
import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('verify_rb7_scope',BASE/'verify_rb7_non_termux_runtime_support_scope.py')
MOD=importlib.util.module_from_spec(SPEC);assert SPEC.loader;SPEC.loader.exec_module(MOD)
class RB7ScopeTests(unittest.TestCase):
    def test_current_tree_passes(self):self.assertTrue(MOD.verify()['pass'])
    def _fixture(self)->Path:
        root=Path(tempfile.mkdtemp());auth=json.loads((MOD.ROOT/MOD.AUTH_REL).read_text())
        paths=set(auth.get('file_identities',{}))|{v['path'] for v in auth.get('source_authorities',{}).values()}|{MOD.AUTH_REL,'docs/current/STATE.json','docs/current/AGENT_TASK.json','docs/agent/TASK_CATALOG.json','docs/documentation/document-registry.json','experiments/epoch3-upstream-thin-release-blockers/blocker-register.json','docs/roadmap/EPOCH3_RELEASE_BLOCKER_RESOLUTION_PLAN.md','experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-temporal-verifier-amendment.json'}
        for rel in paths:
            src=MOD.ROOT/rel;dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        return root
    def test_non_termux_support_tamper_fails(self):
        root=self._fixture();p=root/'docs/current/STATE.json';o=json.loads(p.read_text());o['claim_boundaries']['non_termux_android_context_supported']=True;p.write_text(json.dumps(o));self.assertFalse(MOD.verify(root)['pass'])
    def test_context_guard_removal_fails(self):
        root=self._fixture();p=root/'experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-decision-contract.json';o=json.loads(p.read_text());o['runner_guard']['if_current_context_is_non_termux']='allow-scope-exclusion';p.write_text(json.dumps(o));self.assertFalse(MOD.verify(root)['pass'])
    def test_implicit_owner_approval_fails(self):
        root=self._fixture();p=root/'experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-contract.json';o=json.loads(p.read_text());o['claim_boundary']['owner_approved']=True;p.write_text(json.dumps(o));self.assertFalse(MOD.verify(root)['pass'])
if __name__=='__main__':unittest.main()
