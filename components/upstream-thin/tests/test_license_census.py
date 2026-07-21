from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "components/upstream-thin/lib/license_census.py"
spec = importlib.util.spec_from_file_location("license_census", MODULE)
lc = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(lc)


def fake_members():
    pyjson={"build_info":{"core":{"links":[{"name":"libc.so","system":True}]},"extensions":{"zlib":[{"links":[{"name":"libz.so","system":True}]}]}}}
    base={p:b"x" for p in lc.TARGET_MEMBERS}
    base["python/PYTHON.json"]=json.dumps(pyjson).encode()
    base["python/install/lib/python3.14/build-details.json"]=b'{"implementation":{"version":{"major":3,"minor":14,"micro":6}}}'
    base["python/install/lib/pkgconfig/openssl.pc"]=b"Version: 3.5.7\n"
    base["python/install/lib/pkgconfig/sqlite3.pc"]=b"Version: 3.50.4\n"
    base["python/install/include/openssl/opensslv.h"]=b"Licensed under the Apache License 2.0"
    base["python/install/include/sqlite3.h"]=b"The author disclaims copyright to this source code"
    base["python/install/lib/python3.14/site-packages/pip-26.1.2.dist-info/METADATA"]=b"Version: 26.1.2\nLicense-Expression: MIT\n"
    base["python/install/lib/python3.14/lib-dynload/_bz2.cpython-314-aarch64-linux-android.so"]=b"version 1.0.8"
    base["python/install/lib/python3.14/lib-dynload/_lzma.cpython-314-aarch64-linux-android.so"]=b"version 5.4.6"
    base["python/install/lib/python3.14/lib-dynload/_zstd.cpython-314-aarch64-linux-android.so"]=b"version 1.5.7"
    base["python/install/lib/python3.14/lib-dynload/pyexpat.cpython-314-aarch64-linux-android.so"]=b"expat_2.8.1"
    base["python/install/lib/python3.14/lib-dynload/_decimal.cpython-314-aarch64-linux-android.so"]=b"libmpdec 2.5.1"
    return base


class LicenseCensusTests(unittest.TestCase):
    def test_bounded_component_census(self):
        with tempfile.TemporaryDirectory() as td:
            license_path=Path(td)/"LICENSE"; license_path.write_text("MIT License\n")
            licenses=[
              {"path":"python/install/lib/python3.14/LICENSE.txt","sha256":"a","size_bytes":1},
              {"path":"python/install/lib/python3.14/site-packages/pip-26.1.2.dist-info/licenses/LICENSE.txt","sha256":"b","size_bytes":1},
            ]
            components,gaps=lc.analyze_evidence(fake_members(),licenses,license_path)
        self.assertEqual([row["component_class"] for row in components],list(lc.EXPECTED_CLASSES))
        self.assertIn("libffi",{row["component_class"] for row in gaps})
        self.assertEqual(next(r for r in components if r["component_class"]=="openssl")["version"],"3.5.7")
        self.assertFalse(any(r["license_mapping"]["status"]=="complete" for r in components))

    def test_libffi_version_not_inferred_from_ambiguous_string(self):
        with tempfile.TemporaryDirectory() as td:
            license_path=Path(td)/"LICENSE"; license_path.write_text("MIT License\n")
            members=fake_members(); members["python/install/lib/python3.14/lib-dynload/_ctypes.cpython-314-aarch64-linux-android.so"]=b"1.1.0 LIBFFI_TMPDIR"
            components,_=lc.analyze_evidence(members,[],license_path)
        ffi=next(r for r in components if r["component_class"]=="libffi")
        self.assertIsNone(ffi["version"])
        self.assertEqual(ffi["version_status"],"unresolved")

    def test_repository_license_is_not_claimed_as_packaged(self):
        with tempfile.TemporaryDirectory() as td:
            license_path=Path(td)/"LICENSE"; license_path.write_text("MIT License\n")
            components,_=lc.analyze_evidence(fake_members(),[],license_path)
        launcher=next(r for r in components if r["component_class"]=="project-launcher")
        self.assertEqual(launcher["license_mapping"]["status"],"missing-from-release-family")
        self.assertEqual(launcher["license_mapping"]["evidence_paths"][0]["scope"],"repository-not-release-family")


if __name__ == "__main__":
    unittest.main()
