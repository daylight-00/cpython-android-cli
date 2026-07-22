from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / "components/upstream-thin/lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from normalize import CANONICAL_HEADER, normalize_runtime_metadata  # noqa: E402
from verify_full import inspect_consumer_metadata  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MinimalConsumerMetadataTests(unittest.TestCase):
    def make_install(self, root: Path) -> Path:
        install = root / "python/install"
        stdlib = install / "lib/python3.14"
        config = stdlib / "config-3.14-aarch64-linux-android"
        pkg = install / "lib/pkgconfig"
        for path in (config, pkg, install / "bin", install / "include/python3.14", stdlib / "lib-dynload"):
            path.mkdir(parents=True, exist_ok=True)
        values = {
            "BUILD_GNU_TYPE": "aarch64-apple-darwin24.6.0",
            "HOST_GNU_TYPE": "aarch64-linux-android",
            "CONFIG_ARGS": "--with-build-python=/Users/runner/build/python.exe",
            "CC": "/Users/runner/Library/Android/sdk/ndk/toolchains/clang",
            "CXX": "/Users/runner/Library/Android/sdk/ndk/toolchains/clang++",
            "AR": "/Users/runner/Library/Android/sdk/ndk/toolchains/llvm-ar",
            "SOABI": "cpython-314-aarch64-linux-android",
            "MULTIARCH": "aarch64-linux-android",
            "EXT_SUFFIX": ".cpython-314-aarch64-linux-android.so",
            "ANDROID_API_LEVEL": 24,
            "LIBS": "-ldl -llog -lm",
        }
        (stdlib / "_sysconfigdata__android_aarch64-linux-android.py").write_text(
            CANONICAL_HEADER + "\nbuild_time_vars = " + repr(values) + "\n",
            encoding="utf-8",
        )
        sysvars = stdlib / "_sysconfig_vars__android_aarch64-linux-android.json"
        sysvars.write_text(json.dumps(values, sort_keys=True) + "\n", encoding="utf-8")
        (config / "Makefile").write_text(
            "prefix=\t\t/usr/local\n"
            "CC=\t\t/Users/runner/Library/Android/sdk/ndk/toolchains/clang\n"
            "CXX=\t\t/Users/runner/Library/Android/sdk/ndk/toolchains/clang++\n"
            "AR=\t\t/Users/runner/Library/Android/sdk/ndk/toolchains/llvm-ar\n"
            "CONFIG_ARGS=\t\t--with-build-python=/Users/runner/build/python.exe\n"
            "BUILD_GNU_TYPE=\t\taarch64-apple-darwin24.6.0\n"
            "HOST_GNU_TYPE=\t\taarch64-linux-android\n",
            encoding="utf-8",
        )
        (config / "python-config.py").write_text("#!/usr/bin/env python3\nprint('fixture')\n", encoding="utf-8")
        (stdlib / "build-details.json").write_text(
            json.dumps({
                "base_interpreter": "/usr/local/bin/python3.14",
                "base_prefix": "/usr/local",
                "c_api": {}, "suffixes": {}, "libpython": {},
            }) + "\n",
            encoding="utf-8",
        )
        for name in ("python-3.14.pc", "python-3.14-embed.pc"):
            (pkg / name).write_text(
                "prefix=/usr/local\nincludedir=${prefix}/include\nlibdir=${prefix}/lib\nCflags: -I${includedir}/python3.14\nLibs: -L${libdir} $(BLDLIBRARY)\n",
                encoding="utf-8",
            )
        return install

    def test_profile_m_preserves_producer_and_overlays_consumers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            install = self.make_install(Path(td))
            sysvars = install / "lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json"
            before_sysvars = digest(sysvars)
            result = normalize_runtime_metadata(install)
            self.assertEqual(result["normalization_kind"], "upstream-preserved-minimal-consumer-overlay")
            self.assertEqual(result["selected_profile"], "M")
            self.assertEqual(digest(sysvars), before_sysvars)
            self.assertEqual(result["sysconfig_vars_json"]["mutation"], "preserved-upstream-byte-exact")
            text = (install / "lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py").read_text()
            self.assertEqual(text.splitlines()[0], CANONICAL_HEADER)
            self.assertIn("/Users/runner/build/python.exe", text)
            self.assertNotIn("consumer-normalized-binary-derived", text)
            inspected = inspect_consumer_metadata(install)
            self.assertTrue(inspected["pass"], inspected["errors"])
            self.assertEqual(inspected["preserved_producer"]["BUILD_GNU_TYPE"], "aarch64-apple-darwin24.6.0")
            self.assertIn("/Users/runner/build/python.exe", inspected["preserved_producer"]["CONFIG_ARGS"])
            self.assertEqual(inspected["effective"]["CC"], "clang")
            self.assertEqual(inspected["effective"]["BINDIR"], str(install / "bin"))

    def test_normalization_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            roots = [Path(td) / "a", Path(td) / "b"]
            receipts = []
            hashes = []
            for root in roots:
                install = self.make_install(root)
                receipts.append(normalize_runtime_metadata(install))
                hashes.append({
                    p.relative_to(install).as_posix(): digest(p)
                    for p in install.rglob("*") if p.is_file() and not p.is_symlink()
                })
            # Install-root-dependent runtime code is textual and deterministic;
            # the output bytes do not embed the temporary roots.
            self.assertEqual(hashes[0], hashes[1])
            self.assertEqual(receipts[0], receipts[1])
            self.assertEqual(receipts[0]["effective_consumer"]["path_semantics"], "relative-to-install-root")
            self.assertEqual(receipts[0]["effective_consumer"]["paths"]["BINDIR"], "<install>/bin")
            serialized = json.dumps(receipts[0], sort_keys=True)
            self.assertNotIn(str(roots[0]), serialized)
            self.assertNotIn(str(roots[1]), serialized)


if __name__ == "__main__":
    unittest.main()
