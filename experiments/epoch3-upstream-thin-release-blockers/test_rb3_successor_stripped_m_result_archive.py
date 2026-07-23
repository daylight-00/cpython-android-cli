from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from verify_rb3_successor_stripped_m_result_archive import EXPECTED_CANDIDATE_FILENAME, EXPECTED_CHANGED_PATHS, verify_index


class SuccessorStrippedResultArchiveTests(unittest.TestCase):
    def test_frozen_surface(self) -> None:
        self.assertTrue(EXPECTED_CANDIDATE_FILENAME.endswith("_stripped.tar.gz"))
        self.assertEqual(EXPECTED_CHANGED_PATHS, ["bin/python3.14"])

    def test_index_detects_extra_and_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = root / "payload.json"
            payload.write_text('{"pass":true}\n', encoding="utf-8")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            (root / "result-index.json").write_text(json.dumps({"excluded_paths": ["result-index.json"], "files": [{"path": "payload.json", "sha256": digest, "size_bytes": payload.stat().st_size}]}, indent=2) + "\n", encoding="utf-8")
            self.assertTrue(verify_index(root)["pass"])
            (root / "extra.txt").write_text("unexpected\n", encoding="utf-8")
            self.assertFalse(verify_index(root)["pass"])


if __name__ == "__main__":
    unittest.main()
