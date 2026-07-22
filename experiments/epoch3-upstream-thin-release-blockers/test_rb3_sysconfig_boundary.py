#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_rb3_sysconfig_boundary import (
    CANONICAL_HEADER,
    category,
    dynamic_override_nodes,
    parse_build_time_vars,
    recursive_absolute_strings,
)


class BoundaryReviewTests(unittest.TestCase):
    def test_parse_build_time_vars(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "data.py"
            p.write_text(CANONICAL_HEADER + "\nbuild_time_vars = {'CC': 'clang', 'SOABI': 'x'}\n")
            self.assertEqual(parse_build_time_vars(p)["CC"], "clang")

    def test_dynamic_override_parser_preserves_expressions(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "normalizer.py"
            p.write_text("def _dynamic_normalizer():\n    return '''build_time_vars.update({\"CC\": \"clang\", \"LIBDIR\": root + \"/lib\"})'''\n")
            result = dynamic_override_nodes(p)
            self.assertEqual(result["CC"], {"kind": "literal", "value": "clang"})
            self.assertEqual(result["LIBDIR"]["kind"], "expression")

    def test_categories_separate_provenance_and_sdk(self):
        self.assertEqual(category("BUILD_GNU_TYPE"), "producer-provenance-or-build-only")
        self.assertEqual(category("CC"), "on-device-sdk-toolchain")
        self.assertEqual(category("INCLUDEPY"), "consumer-path")
        self.assertEqual(category("SOABI"), "target-identity")

    def test_absolute_path_collection(self):
        rows = recursive_absolute_strings({"a": "/build/x -I/install/include", "b": ["relative", "/tools/y"]})
        values = {row["value"] for row in rows}
        self.assertEqual(values, {"/build/x", "/tools/y"})


if __name__ == "__main__":
    unittest.main()
