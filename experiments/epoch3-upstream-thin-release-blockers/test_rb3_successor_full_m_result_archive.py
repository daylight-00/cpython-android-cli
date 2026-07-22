from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from verify_rb3_successor_full_m_result_archive import (
    EXPECTED_CANDIDATE,
    EXPECTED_RESULT,
    verify_index,
)


class RB3SuccessorFullResultArchiveTests(unittest.TestCase):
    def test_frozen_identities(self) -> None:
        self.assertEqual(EXPECTED_RESULT["self_index_file_count"], 77)
        self.assertEqual(EXPECTED_CANDIDATE["size_bytes"], 39414556)
        self.assertEqual(len(EXPECTED_RESULT["sha256"]), 64)
        self.assertEqual(len(EXPECTED_CANDIDATE["sha256"]), 64)

    def test_self_index_helper_detects_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = root / "payload.json"
            payload.write_text('{"pass":true}\n', encoding="utf-8")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            (root / "result-index.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "excluded_paths": ["result-index.json"],
                        "files": [
                            {
                                "path": "payload.json",
                                "sha256": digest,
                                "size_bytes": payload.stat().st_size,
                            }
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertTrue(verify_index(root)["pass"])
            payload.write_text('{"pass":false}\n', encoding="utf-8")
            self.assertFalse(verify_index(root)["pass"])


if __name__ == "__main__":
    unittest.main()
