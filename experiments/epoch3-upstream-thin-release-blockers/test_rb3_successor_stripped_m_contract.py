from __future__ import annotations
import unittest
from pathlib import Path
from verify_rb3_successor_stripped_m_contract import verify
ROOT=Path(__file__).resolve().parents[2]
class TestRB3SuccessorStrippedContract(unittest.TestCase):
 def test_transition(self):
  result=verify(ROOT);self.assertTrue(result["pass"],result);self.assertEqual(result["failed_checks"],[])
if __name__=="__main__":unittest.main()
