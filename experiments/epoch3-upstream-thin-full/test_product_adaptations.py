from __future__ import annotations

import io
import json
import sys
import subprocess
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "components/upstream-thin/lib"))

from normalize import normalize_runtime_metadata  # noqa: E402
from pip_surface import install_upstream_pip  # noqa: E402
from qualify_full import _has_external_termux_prefix, _run  # noqa: E402
from verify_full import classify_host_residue  # noqa: E402
from observe_astral import observe  # noqa: E402
from archive import sha256_file  # noqa: E402


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

    def test_missing_optional_target_tool_is_recorded_not_raised(self) -> None:
        row = _run(["/definitely/not/present/hw-t-getconf"], env={})
        self.assertEqual(row["returncode"], 127)
        self.assertTrue(row["tool_unavailable"])
        self.assertIn("FileNotFoundError", row["stderr"])

    def test_astral_implied_roots_and_string_format_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tar_path = root / "golden.tar"
            with tarfile.open(tar_path, "w:") as tf:
                for name, data in (
                    ("python/PYTHON.json", json.dumps({"version": "8", "build_info": {}}).encode()),
                    ("python/build/object.o", b"object"),
                    ("python/install/bin/python3.14", b"binary"),
                ):
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    tf.addfile(info, io.BytesIO(data))
            archive = root / "golden.tar.zst"
            subprocess.run(["zstd", "-q", "-f", str(tar_path), "-o", str(archive)], check=True)
            result = observe(archive, expected_sha256=sha256_file(archive))
            self.assertTrue(result["checks"]["canonical_full_roots"])
            self.assertTrue(result["checks"]["python_json_format_8"])
            self.assertTrue(result["pass"])

    def test_candidate_nested_under_termux_prefix_is_not_external_residue(self) -> None:
        prefix = Path("/data/data/com.termux/files/usr/tmp/qualify/relocated/prefix")
        text = f"-I{prefix}/include/python3.14 -L{prefix}/lib"
        self.assertFalse(_has_external_termux_prefix(text, prefix))

    def test_external_termux_package_path_remains_rejected(self) -> None:
        prefix = Path("/data/data/com.termux/files/usr/tmp/qualify/relocated/prefix")
        text = f"-I{prefix}/include/python3.14 -I/data/data/com.termux/files/usr/include"
        self.assertTrue(_has_external_termux_prefix(text, prefix))

    def test_host_residue_classification_preserves_inert_upstream_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            python_root = Path(tmp) / "python"
            install = python_root / "install"
            stdlib = install / "lib/python3.14"
            dynload = stdlib / "lib-dynload"
            config = stdlib / "config-3.14-aarch64-linux-android"
            bin_dir = install / "bin"
            pkg = install / "lib/pkgconfig"
            for directory in (dynload, config, bin_dir, pkg):
                directory.mkdir(parents=True, exist_ok=True)
            (python_root / "PYTHON.json").write_text("{}\n", encoding="utf-8")
            (stdlib / "ctypes_util.py").write_text("# documents LD_LIBRARY_PATH\n", encoding="utf-8")
            (dynload / "upstream.so").write_bytes(b"\x7fELF\x00/home/runner/work/source.c\x00")
            (config / "Makefile").write_text("prefix=${prefix}\n", encoding="utf-8")
            (bin_dir / "pip").write_text("#!/system/bin/sh\nexec /data/data/com.termux/files/usr/bin/python -m pip\n", encoding="utf-8")
            rows = classify_host_residue(python_root, install)
            self.assertEqual(len(rows["operational"]), 1)
            self.assertIn("install/bin/pip:/data/data/com.termux/files/usr", rows["operational"][0])
            self.assertEqual(len(rows["informational_upstream_provenance"]), 2)
            self.assertTrue(any("LD_LIBRARY_PATH" in row for row in rows["informational_upstream_provenance"]))
            self.assertTrue(any("/home/runner/" in row for row in rows["informational_upstream_provenance"]))


if __name__ == "__main__":
    unittest.main()
