#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).with_name('run_rb3_sysconfig_boundary_probe.py')
spec=importlib.util.spec_from_file_location('probe',SCRIPT); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

class ProbeTests(unittest.TestCase):
    def test_catalog_preserves_exact_local_archive(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x.tar.gz'; p.write_bytes(b'x')
            row=mod.catalog_row(p,'H')
            self.assertEqual(row['url'],p.resolve().as_uri())
            self.assertEqual(row['os'],'linux'); self.assertEqual(row['libc'],'none')
            self.assertIn('profile-h',row['build'])

    def test_android_identity(self):
        row={'returncode':0,'stdout':json.dumps({'implementation':'CPython','version':'3.14.6','soabi':'cpython-314-aarch64-linux-android','multiarch':'aarch64-linux-android','platform':'android-24-arm64_v8a'})}
        self.assertTrue(mod.android_identity(row))
        row['stdout']=row['stdout'].replace('android-24-arm64_v8a','linux-aarch64')
        self.assertFalse(mod.android_identity(row))


    def test_expected_profile_identities_are_complete(self):
        rows=mod.expected_profile_identities()
        self.assertEqual(set(rows),{'C','H','U','M'})
        self.assertEqual(rows['C']['sha256'],'84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76')

    def test_clean_env_removes_caller_toolchain_and_uv_state(self):
        old={k:os.environ.get(k) for k in ('CC','CFLAGS','LDFLAGS','UV_PYTHON_INSTALL_DIR','LD_LIBRARY_PATH')}
        try:
            os.environ.update({'CC':'bad','CFLAGS':'bad','LDFLAGS':'bad','UV_PYTHON_INSTALL_DIR':'bad','LD_LIBRARY_PATH':'bad'})
            with tempfile.TemporaryDirectory() as td:
                env=mod.clean_env(Path(td))
            for key in ('CC','CFLAGS','LDFLAGS','UV_PYTHON_INSTALL_DIR','LD_LIBRARY_PATH'):
                self.assertNotIn(key,env)
        finally:
            for key,value in old.items():
                if value is None: os.environ.pop(key,None)
                else: os.environ[key]=value

    def test_wheel_probe_creates_its_work_directory(self):
        text=SCRIPT.read_text()
        self.assertIn('work.mkdir(parents=True, exist_ok=True)',text)
        self.assertIn('raw_native_wheel_import',text)
        self.assertIn('explicit_normalized_extension_import',text)

    def test_claim_boundary_is_not_closed_in_source(self):
        text=SCRIPT.read_text()
        self.assertIn('"rb3_closed": False',text)
        self.assertIn('"selected": False',text)

if __name__=='__main__': unittest.main()
