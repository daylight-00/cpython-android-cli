from __future__ import annotations
import importlib.util,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SCRIPT=ROOT/'experiments/epoch3-upstream-thin-release-blockers/run_rb3_consumer_compatibility.py'
spec=importlib.util.spec_from_file_location('rb3',SCRIPT); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
class TestRB3(unittest.TestCase):
 def test_catalog_row_is_uv_custom_download_shape(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'x.tar.gz'; p.write_bytes(b'x'); r=mod.catalog_row(p)
   self.assertEqual(r['name'],'cpython'); self.assertEqual(r['os'],'linux'); self.assertEqual(r['libc'],'none'); self.assertEqual(r['arch']['family'],'aarch64'); self.assertEqual((r['major'],r['minor'],r['patch']),(3,14,6)); self.assertTrue(r['url'].startswith('file://'))
 def test_identity_rejects_non_android(self):
  row={'returncode':0,'stdout':'{"implementation":"CPython","version":"3.14.6","soabi":"cpython-314-x86_64-linux-gnu","multiarch":"x86_64-linux-gnu","platform":"linux-x86_64","real_executable":"/x"}'}
  self.assertFalse(mod.identity_ok(row))
 def test_contract_keeps_claims_bounded(self):
  import json
  c=json.loads((ROOT/'experiments/epoch3-upstream-thin-release-blockers/rb3-consumer-compatibility-contract.json').read_text())
  self.assertFalse(c['claim_boundary']['rb3_closed']); self.assertFalse(c['claim_boundary']['built_in_uv_android_catalog']); self.assertFalse(c['claim_boundary']['publication'])
if __name__=='__main__': unittest.main()
