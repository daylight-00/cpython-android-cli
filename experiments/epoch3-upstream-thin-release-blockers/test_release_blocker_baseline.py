from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
import importlib.util

MOD=Path(__file__).with_name('audit_release_blocker_baseline.py')
spec=importlib.util.spec_from_file_location('rb_audit',MOD); rb=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(rb)

class BaselineAuditTests(unittest.TestCase):
    def fixture(self,root:Path):
        components=[]
        for c in rb.EXPECTED_CLASSES:
            components.append({'component_class':c,'license_mapping':{'status':'unmapped'}})
        census={'family':{'fingerprint_sha256':rb.EXPECTED_FINGERPRINT},'subject':{'sha256':rb.EXPECTED_FULL_SHA},'components':components,'summary':{'component_to_license_mapping_complete':False},'claim_boundary':{'component_license_mapping_complete':False,'selectable':False,'publication':False,'artifact_bytes_mutated':False}}
        gaps={'blocking_gap_count':3,'closure_status':'incomplete','gaps':[{'component_class':'libffi','code':'libffi-version-unresolved'},{'component_class':'libffi','code':'libffi-license-evidence-not-packaged'},{'component_class':'project-launcher','code':'project-license-not-in-release-family'}]}
        result={'pass':True,'full_artifact_identity_preserved':True}
        for name,data in [('component-census.json',census),('license-gap-register.json',gaps),('baseline-result.json',result)]: (root/name).write_text(json.dumps(data))
    def test_success(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self.fixture(root); self.assertTrue(rb.audit(root)['pass'])
    def test_reject_complete_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self.fixture(root); d=json.loads((root/'component-census.json').read_text()); d['claim_boundary']['selectable']=True; (root/'component-census.json').write_text(json.dumps(d)); self.assertFalse(rb.audit(root)['pass'])
    def test_reject_missing_libffi_gap(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self.fixture(root); d=json.loads((root/'license-gap-register.json').read_text()); d['gaps']=[r for r in d['gaps'] if r['component_class']!='libffi']; (root/'license-gap-register.json').write_text(json.dumps(d)); self.assertFalse(rb.audit(root)['pass'])

if __name__=='__main__': unittest.main()
