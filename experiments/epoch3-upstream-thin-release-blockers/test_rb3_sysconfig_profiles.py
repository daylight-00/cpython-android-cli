#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("rb3_sysconfig_profiles.py")
spec = importlib.util.spec_from_file_location("profiles", SCRIPT)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def write_sysdata(path: Path, header: str = mod.CANONICAL_HEADER):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "\nbuild_time_vars = {'CONFIG_ARGS':'truth','BUILD_GNU_TYPE':'darwin','SOABI':'cpython-314-aarch64-linux-android','CC':'absolute-clang'}\n")


class ProfileTests(unittest.TestCase):
    def test_header_profile_changes_only_first_line(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.py"; write_sysdata(p,"# custom")
            mod.replace_header(p)
            lines=p.read_text().splitlines()
            self.assertEqual(lines[0],mod.CANONICAL_HEADER)
            self.assertIn("CONFIG_ARGS",lines[1])

    def test_minimal_overlay_preserves_provenance_and_identity_literals(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.py"; write_sysdata(p)
            mod.apply_minimal_sysconfig_overlay(p)
            text=p.read_text()
            self.assertIn("'CONFIG_ARGS':'truth'",text)
            self.assertIn("'BUILD_GNU_TYPE':'darwin'",text)
            self.assertNotIn('"CONFIG_ARGS":',text)
            self.assertNotIn('"BUILD_GNU_TYPE":',text)
            self.assertNotIn('"SOABI":',text)
            self.assertIn('"CC": "clang"',text)

    def test_minimal_makefile_preserves_producer_fields(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"Makefile"
            p.write_text("prefix=/usr/local\nBUILD_GNU_TYPE=aarch64-apple-darwin\nCONFIG_ARGS=truth\nCC=absolute\n")
            mod.patch_makefile_minimal(p); text=p.read_text()
            self.assertIn("BUILD_GNU_TYPE=aarch64-apple-darwin",text)
            self.assertIn("CONFIG_ARGS=truth",text)
            self.assertIn("CC=\t\tclang",text)
            self.assertIn("prefix :=",text)

    def test_build_details_corrects_consumer_surface(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"build-details.json"
            p.write_text(json.dumps({'c_api':{},'suffixes':{},'libpython':{}}))
            mod.patch_build_details(p); d=json.loads(p.read_text())
            self.assertEqual(d['base_interpreter'],'bin/python3.14')
            self.assertEqual(d['suffixes']['extensions'][0],'.cpython-314-aarch64-linux-android.so')

if __name__ == '__main__': unittest.main()
