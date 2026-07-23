#!/usr/bin/env python3
from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'components/upstream-thin/lib'))
import successor_legal_family as m
class Tests(unittest.TestCase):
 def test_claim_boundary(self):
  b=m.candidate_claim_boundary();self.assertTrue(b['successor_legal_family_candidate']);self.assertFalse(b['successor_legal_family_accepted']);self.assertFalse(b['rb2_rebound']);self.assertFalse(b['predecessor_family_superseded'])
 def test_contract_identity(self):
  d=json.loads((ROOT/m.CONTRACT).read_text());self.assertEqual(d['proposed_output']['release_id'],m.LEGAL_RELEASE_ID);self.assertEqual(d['accepted_technical_family']['file_count'],23)
 def test_constants(self):
  self.assertEqual(m.EXPECTED_FILE_COUNT,128);self.assertEqual(m.EXPECTED_LEGAL_FILE_COUNT,102);self.assertEqual(m.NOTICE_SHA256,'80cf82a6b6957fd830701e2559755d1eecdf01c61cbcb4f8f8843b9735eaf613')

 def test_host_assembly_identity(self):
  h=json.loads((ROOT/'experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-family-m-host-assembly.json').read_text())
  self.assertEqual(h['output']['release_id'],m.LEGAL_RELEASE_ID)
  self.assertEqual(h['output']['file_count'],128)
  self.assertTrue(h['checks']['all_128_files_byte_identical_between_assemblies'])
  self.assertTrue(h['checks']['independent_audit_pass'])
  self.assertFalse(h['claim_boundary']['successor_legal_family_accepted'])
if __name__=='__main__':unittest.main()
