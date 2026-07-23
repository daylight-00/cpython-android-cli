from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = Path(__file__).with_name("verify_rb3_successor_technical_family_m_contract.py")
SPEC = importlib.util.spec_from_file_location("verify_successor_family_contract", MODULE)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class TechnicalFamilyContractTests(unittest.TestCase):
    def test_contract_passes(self) -> None:
        result = MOD.verify(ROOT)
        self.assertTrue(result["pass"], result)


if __name__ == "__main__":
    unittest.main()
