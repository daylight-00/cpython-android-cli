from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "components/upstream-thin/lib"))

from normalize import normalize_runtime_metadata  # noqa: E402
from pip_surface import install_upstream_pip  # noqa: E402


class ProductAdaptationTests(unittest.TestCase):
    def test_pip_is_installed_only_from_upstream_wheel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            install = Path(tmp) / "install"
            bundled = install / "lib/python3.14/ensurepip/_bundled"
            bundled.mkdir(parents=True)
            wheel = bundled / "pip-25.1.1-py3-none-any.whl"
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr("pip/__init__.py", "__version__='25.1.1'\n")
                archive.writestr("pip-25.1.1.dist-info/METADATA", "Name: pip\nVersion: 25.1.1\n")
            result = install_upstream_pip(install)
            self.assertEqual(result["wheel"]["version"], "25.1.1")
            self.assertFalse(result["network_acquisition"])
            self.assertTrue((install / "lib/python3.14/site-packages/pip/__init__.py").is_file())
            for name in ("pip", "pip3", "pip3.14"):
                wrapper = install / "bin" / name
                self.assertTrue(wrapper.is_file())
                text = wrapper.read_text()
                self.assertIn("python3.14\" -m pip", text)
                self.assertNotIn("/data/data/com.termux", text)

    def test_metadata_normalization_is_dynamic_and_host_neutral(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            install = Path(tmp) / "install"
            stdlib = install / "lib/python3.14"
            config = stdlib / "config-3.14-aarch64-linux-android"
            pkg = install / "lib/pkgconfig"
            config.mkdir(parents=True)
            pkg.mkdir(parents=True)
            (stdlib / "_sysconfigdata__android_aarch64-linux-android.py").write_text(
                "build_time_vars = {\n"
                " 'prefix': '/usr/local',\n"
                " 'CC': '/Users/runner/Library/Android/sdk/ndk/bin/aarch64-linux-android24-clang',\n"
                " 'CFLAGS': '-O3 -I/Users/runner/work/prefix/include',\n"
                " 'BLDLIBRARY': '-L/usr/local/lib -lpython3.14',\n"
                "}\n",
                encoding="utf-8",
            )
            (stdlib / "_sysconfig_vars__android_aarch64-linux-android.json").write_text("{}\n")
            (config / "Makefile").write_text("prefix=/usr/local\nCC=/Users/runner/ndk/clang\nLDFLAGS=-L/usr/local/lib\n")
            (config / "python-config.py").write_text("#!/usr/local/bin/python3.14\nprint('ok')\n")
            (stdlib / "build-details.json").write_text(json.dumps({
                "base_interpreter": "/usr/local/bin/python3.14", "base_prefix": "/usr/local",
                "c_api": {"headers": "/usr/local/include/python3.14", "pkgconfig_path": "/usr/local/lib/pkgconfig"},
                "suffixes": {"extensions": [".cpython-314-darwin.so"]},
                "libpython": {"dynamic": "/usr/local/lib/libpython3.14.so", "dynamic_stableabi": "/usr/local/lib/libpython3.so"},
            }) + "\n")
            (pkg / "python-3.14.pc").write_text("prefix=/usr/local\nLibs: -L/usr/local/lib -lpython3.14\n")
            result = normalize_runtime_metadata(install)
            self.assertEqual(result["normalization_kind"], "relocation-aware-runtime-and-on-device-sdk")
            sysdata = (stdlib / "_sysconfigdata__android_aarch64-linux-android.py").read_text()
            self.assertIn("BEGIN HW-T CONSUMER NORMALIZATION", sysdata)
            for marker in ("/Users/runner/", "/usr/local", "/data/data/com.termux/"):
                for path in (stdlib / "_sysconfigdata__android_aarch64-linux-android.py", stdlib / "_sysconfig_vars__android_aarch64-linux-android.json", config / "Makefile", config / "python-config.py", stdlib / "build-details.json", pkg / "python-3.14.pc"):
                    self.assertNotIn(marker, path.read_text(), f"{marker} in {path}")
            values = json.loads((stdlib / "_sysconfig_vars__android_aarch64-linux-android.json").read_text())
            self.assertEqual(values["prefix"], "${prefix}")
            self.assertEqual(values["HW_T_CROSS_BUILD_SDK"], "unavailable-without-explicit-ndk-authority")
            self.assertTrue((install / "bin/python3.14-config").is_file())


if __name__ == "__main__":
    unittest.main()
