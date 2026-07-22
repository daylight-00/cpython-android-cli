#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("run_rb3_successor_full_m.py")
spec = importlib.util.spec_from_file_location("rb3_successor_full", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SuccessorFullTests(unittest.TestCase):
    def test_catalog_binds_exact_local_projection(self):
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / "install.tar.gz"
            archive.write_bytes(b"candidate")
            row = mod.catalog_row(archive)
            self.assertEqual(row["url"], archive.resolve().as_uri())
            self.assertEqual(row["sha256"], mod.sha256_file(archive))
            self.assertEqual(row["os"], "linux")
            self.assertEqual(row["libc"], "none")

    def test_profile_m_identity_requires_preserved_producer_truth(self):
        value = {
            "implementation": "CPython", "version": "3.14.6",
            "soabi": "cpython-314-aarch64-linux-android", "multiarch": "aarch64-linux-android",
            "platform": "android-24-arm64_v8a", "metadata_profile": mod.EXPECTED_PROFILE,
            "cc": "clang", "cxx": "clang++", "ar": "llvm-ar",
            "host_gnu_type": "aarch64-unknown-linux-android", "build_gnu_type": "aarch64-apple-darwin24.6.0",
            "config_args": "--host=aarch64-linux-android --build=aarch64-apple-darwin24.6.0",
            "cflags": "-D__BIONIC_NO_PAGE_SIZE_MACRO",
            "ldflags": "-Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384",
            "ldshared": "clang -shared -Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384",
        }
        row = {"returncode": 0, "stdout": json.dumps(value)}
        self.assertTrue(mod.profile_m_identity(row))
        value["build_gnu_type"] = "aarch64-unknown-linux-android"
        row["stdout"] = json.dumps(value)
        self.assertFalse(mod.profile_m_identity(row))


    def test_profile_m_identity_accepts_uv_managed_tool_names(self):
        value = {
            "implementation": "CPython", "version": "3.14.6",
            "soabi": "cpython-314-aarch64-linux-android", "multiarch": "aarch64-linux-android",
            "platform": "android-24-arm64_v8a", "metadata_profile": mod.EXPECTED_PROFILE,
            "cc": "cc", "cxx": "c++", "ar": "ar",
            "host_gnu_type": "aarch64-unknown-linux-android", "build_gnu_type": "aarch64-apple-darwin24.6.0",
            "config_args": "--host=aarch64-linux-android",
            "cflags": "-D__BIONIC_NO_PAGE_SIZE_MACRO",
            "ldflags": "-Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384",
            "ldshared": "cc -shared -Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384",
        }
        row = {"returncode": 0, "stdout": json.dumps(value)}
        self.assertTrue(mod.profile_m_identity(row, managed=True))
        self.assertFalse(mod.profile_m_identity(row, managed=False))

    def test_claim_boundaries_remain_open_in_source(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"successor_full_accepted": False', text)
        self.assertIn('"predecessor_family_superseded": False', text)
        self.assertIn('"rb3_closed": False', text)
        self.assertIn('"portable_raw_wheel_claim": False', text)
        self.assertIn('"user_built_wheel_postprocessing": "out-of-scope-external-tool-responsibility"', text)
        self.assertIn('"native_wheel_16k_alignment"', text)
        self.assertIn('"managed_native_wheel_16k_alignment"', text)
        self.assertNotIn('"explicit_wheel_normalization_import"', text)


if __name__ == "__main__":
    unittest.main()
