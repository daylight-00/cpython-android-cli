from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODULE_PATH = HERE / "verify_rb3_successor_install_only_m_contract.py"
spec = importlib.util.spec_from_file_location("verify_successor_install_contract", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class SuccessorInstallOnlyContractTests(unittest.TestCase):
    def test_current_contract_passes(self) -> None:
        self.assertTrue(module.verify(ROOT)["pass"])

    def make_copy(self, root: Path) -> None:
        required = [
            module.CONTRACT,
            module.CORRECTION,
            module.R1_INSPECTION,
            module.INSPECTION,
            module.LOCK,
            module.AUTHORITY,
            "docs/current/STATE.json",
            "docs/agent/TASK_CATALOG.json",
            "docs/documentation/document-registry.json",
        ]
        for relative in required:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)

    def test_rejects_premature_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            copy = Path(td) / "repo"
            self.make_copy(copy)
            path = copy / module.CORRECTION
            value = json.loads(path.read_text())
            value["success_boundary"]["successor_install_only_accepted"] = True
            path.write_text(json.dumps(value))
            self.assertFalse(module.verify(copy)["pass"])

    def test_rejects_product_byte_change_scope(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            copy = Path(td) / "repo"
            self.make_copy(copy)
            path = copy / module.CORRECTION
            value = json.loads(path.read_text())
            value["correction_scope"]["product_bytes_changed"] = True
            path.write_text(json.dumps(value))
            self.assertFalse(module.verify(copy)["pass"])


if __name__ == "__main__":
    unittest.main()
