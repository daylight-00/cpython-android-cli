from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from verify_rb3_successor_install_only_m_acceptance_result_archive import EXPECTED_RESULT, verify_index


class InstallOnlyAcceptanceResultArchiveTests(unittest.TestCase):
    def test_frozen_result_identity(self) -> None:
        self.assertEqual(EXPECTED_RESULT["size_bytes"], 9973)
        self.assertEqual(EXPECTED_RESULT["self_index_file_count"], 21)
        self.assertEqual(len(EXPECTED_RESULT["sha256"]), 64)

    def test_index_detects_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = root / "summary.json"
            payload.write_text('{"pass":true}\n', encoding="utf-8")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            (root / "result-index.json").write_text(json.dumps({"excluded_paths": ["result-index.json"], "files": [{"path": "summary.json", "sha256": digest, "size_bytes": payload.stat().st_size}]}, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(verify_index(root)["pass"])
            payload.write_text('{"pass":false}\n', encoding="utf-8")
            self.assertFalse(verify_index(root)["pass"])


if __name__ == "__main__":
    unittest.main()
