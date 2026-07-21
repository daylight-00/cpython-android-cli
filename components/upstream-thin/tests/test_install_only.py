from __future__ import annotations

import gzip
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "components/upstream-thin/bin/cpython-android-upstream-thin"
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))

from archive import safe_extract_tar, write_tar_gz  # noqa: E402


def add_file(tf: tarfile.TarFile, name: str, data: bytes, mode: int = 0o644) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = mode
    info.mtime = 0
    tf.addfile(info, io.BytesIO(data))


def add_directory(tf: tarfile.TarFile, name: str, mode: int = 0o755) -> None:
    info = tarfile.TarInfo(name)
    info.type = tarfile.DIRTYPE
    info.mode = mode
    info.mtime = 0
    tf.addfile(info)


def add_symlink(tf: tarfile.TarFile, name: str, target: str, mode: int = 0o777) -> None:
    info = tarfile.TarInfo(name)
    info.type = tarfile.SYMTYPE
    info.linkname = target
    info.mode = mode
    info.mtime = 0
    tf.addfile(info)


class InstallOnlyTests(unittest.TestCase):
    _class_tmp: tempfile.TemporaryDirectory[str]
    full_fixture: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._class_tmp = tempfile.TemporaryDirectory(prefix="install-only-tests-")
        root = Path(cls._class_tmp.name)
        upstream, launcher = cls.make_upstream_fixture(root)
        output = root / "full-output"
        proc = subprocess.run(
            [
                str(CLI), "assemble-full", "--fixture-mode",
                "--upstream-archive", str(upstream),
                "--launcher", str(launcher),
                "--output-dir", str(output),
                "--release-id", "fixture",
            ],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stdout + proc.stderr)
        cls.full_fixture = next(output.glob("*-full.tar.zst"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._class_tmp.cleanup()

    @staticmethod
    def make_upstream_fixture(root: Path) -> tuple[Path, Path]:
        archive = root / "fixture-upstream.tar.gz"
        build_details = {
            "implementation": {
                "name": "cpython",
                "cache_tag": "cpython-314",
                "hexversion": 0x30E06F0,
                "version": {
                    "major": 3,
                    "minor": 14,
                    "micro": 6,
                    "releaselevel": "final",
                    "serial": 0,
                },
            }
        }
        with tarfile.open(archive, "w:gz") as tf:
            add_directory(tf, ".")
            for directory in (
                "prefix",
                "prefix/bin",
                "prefix/lib",
                "prefix/lib/python3.14",
                "prefix/lib/python3.14/site-packages",
                "prefix/include",
                "prefix/include/python3.14",
            ):
                add_directory(tf, directory)
            add_file(tf, "prefix/lib/python3.14/build-details.json", (json.dumps(build_details) + "\n").encode())
            add_file(tf, "prefix/lib/python3.14/LICENSE.txt", b"fixture license\n")
            add_file(tf, "prefix/lib/python3.14/os.py", b"# fixture\n")
            add_file(tf, "prefix/include/python3.14/Python.h", b"/* fixture */\n")
            for name in ("pip", "pip3", "pip3.14"):
                add_file(tf, f"prefix/bin/{name}", b"#!/system/bin/sh\nexit 0\n", 0o755)
            add_symlink(tf, "prefix/lib/libfixture.so", "python3.14/LICENSE.txt")
        launcher = root / "python3.14"
        launcher.write_text("#!/system/bin/sh\nexit 0\n", encoding="utf-8")
        launcher.chmod(0o755)
        return archive, launcher

    def assemble_install(self, full: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(CLI),
                "assemble-install-only",
                "--fixture-mode",
                "--full-archive",
                str(full),
                "--output-dir",
                str(output),
                "--release-id",
                "fixture",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def verify_install(self, install: Path, full: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(CLI),
                "verify-install-only",
                "--fixture-mode",
                str(install),
                "--full-archive",
                str(full),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_exact_projection_and_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            full = self.full_fixture
            output = root / "install"
            proc = self.assemble_install(full, output)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            install = next(output.glob("*-install_only.tar.gz"))
            verify = self.verify_install(install, full)
            self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
            result = json.loads(verify.stdout)
            self.assertTrue(result["pass"])
            self.assertTrue(result["checks"]["exact_projection"])
            self.assertTrue(result["checks"]["full_metadata_absent"])

    def test_projection_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            full = self.full_fixture
            artifacts = []
            for name in ("a", "b"):
                output = root / name
                proc = self.assemble_install(full, output)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                artifacts.append(next(output.glob("*-install_only.tar.gz")))
            self.assertEqual(artifacts[0].read_bytes(), artifacts[1].read_bytes())

    def test_non_fixture_rejects_unaccepted_full_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            full = self.full_fixture
            proc = subprocess.run(
                [
                    str(CLI),
                    "assemble-install-only",
                    "--full-archive",
                    str(full),
                    "--output-dir",
                    str(root / "out"),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("accepted full mismatch", proc.stderr)

    def test_verifier_rejects_extra_projected_member(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            full = self.full_fixture
            output = root / "install"
            proc = self.assemble_install(full, output)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            install = next(output.glob("*-install_only.tar.gz"))

            tar_path = root / "install.tar"
            with gzip.open(install, "rb") as source, tar_path.open("wb") as target:
                target.write(source.read())
            tree = root / "tree"
            safe_extract_tar(tar_path, tree, "r:")
            (tree / "python/EXTRA.txt").write_text("not in full\n", encoding="utf-8")
            mutated = root / "mutated.tar.gz"
            write_tar_gz(tree / "python", mutated)

            verify = self.verify_install(mutated, full)
            self.assertNotEqual(verify.returncode, 0)
            result = json.loads(verify.stdout)
            self.assertFalse(result["checks"]["exact_projection"])

    def test_rejects_full_without_install_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_tree = root / "bad/python"
            (bad_tree / "build").mkdir(parents=True)
            (bad_tree / "PYTHON.json").write_text("{}\n", encoding="utf-8")
            bad_tar = root / "bad.tar"
            with tarfile.open(bad_tar, "w") as tf:
                tf.add(bad_tree.parent / "python", arcname="python")
            full = root / "bad-full.tar.zst"
            zstd = subprocess.run(["zstd", "-q", "-f", str(bad_tar), "-o", str(full)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(zstd.returncode, 0, zstd.stderr)
            proc = self.assemble_install(full, root / "out")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("lacks python/install", proc.stderr)

    def test_projection_contains_only_python_root_and_preserves_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            full = self.full_fixture
            output = root / "install"
            proc = self.assemble_install(full, output)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            install = next(output.glob("*-install_only.tar.gz"))
            with tarfile.open(install, "r:gz") as tf:
                names = [member.name for member in tf.getmembers()]
                self.assertTrue(all(name == "python" or name.startswith("python/") for name in names))
                self.assertNotIn("python/PYTHON.json", names)
                self.assertFalse(any(name == "python/build" or name.startswith("python/build/") for name in names))
                link = tf.getmember("python/lib/libfixture.so")
                self.assertTrue(link.issym())
                self.assertEqual(link.linkname, "python3.14/LICENSE.txt")


if __name__ == "__main__":
    unittest.main()
