from __future__ import annotations
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'lib'))
import owner_approval_review as m
class T(unittest.TestCase):
 def exact(self):
  b=m.binding();return {'schema_version':1,'approval_kind':'epoch3-rb1-final-notice-set-owner-approval','approved':True,'owner_id':'daylight-00','statement':b['required_statement'],**{k:b[k] for k in b if k.endswith('sha256') or k=='release_id'}}
 def test_exact_approval_valid(self):self.assertTrue(m.validate_approval(self.exact())['pass'])
 def test_execution_not_approval(self):
  x=self.exact();x['approved']=False;self.assertFalse(m.validate_approval(x)['pass'])
 def test_wrong_notice_rejected(self):
  x=self.exact();x['third_party_notices_sha256']='0'*64;self.assertFalse(m.validate_approval(x)['pass'])
 def test_wrong_statement_rejected(self):
  x=self.exact();x['statement']='approve';self.assertFalse(m.validate_approval(x)['pass'])
 def test_missing_owner_rejected(self):
  x=self.exact();x['owner_id']='';self.assertFalse(m.validate_approval(x)['pass'])
