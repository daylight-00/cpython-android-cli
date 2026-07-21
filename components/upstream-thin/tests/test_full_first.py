from __future__ import annotations

import io
import json
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "components/upstream-thin/bin/cpython-android-upstream-thin"


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


class FullFirstTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> tuple[Path, Path]:
        archive = root / "fixture.tar.gz"
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
            # The official Python.org Android archive begins with this normal
            # POSIX tar root marker. Product extraction must accept it without
            # weakening parent-traversal or link safety.
            add_directory(tf, ".")
            for directory in (
                "prefix",
                "prefix/lib",
                "prefix/lib/python3.14",
                "prefix/include",
                "prefix/include/python3.14",
                "prefix/lib/python3.14/site-packages",
            ):
                add_directory(tf, directory)
            add_file(
                tf,
                "prefix/lib/python3.14/build-details.json",
                (json.dumps(build_details) + "\n").encode(),
            )
            add_file(tf, "prefix/lib/python3.14/LICENSE.txt", b"fixture license\n")
            add_file(tf, "prefix/lib/python3.14/os.py", b"# fixture\n")
            add_file(tf, "prefix/include/python3.14/Python.h", b"/* fixture */\n")
        launcher = root / "python3.14"
        launcher.write_text("#!/system/bin/sh\nexit 0\n", encoding="utf-8")
        launcher.chmod(0o755)
        return archive, launcher

    def assemble_fixture(self, archive: Path, launcher: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(CLI),
                "assemble-full",
                "--fixture-mode",
                "--upstream-archive",
                str(archive),
                "--launcher",
                str(launcher),
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

    def test_full_fixture_and_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, launcher = self.make_fixture(root)
            output = root / "out"
            proc = self.assemble_fixture(archive, launcher, output)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            full = next(output.glob("*-full.tar.zst"))
            verify = subprocess.run(
                [str(CLI), "verify-full", "--fixture-mode", str(full)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
            self.assertTrue(json.loads(verify.stdout)["pass"])

    def test_full_fixture_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, launcher = self.make_fixture(root)
            outputs = [root / "out-a", root / "out-b"]
            for output in outputs:
                proc = self.assemble_fixture(archive, launcher, output)
                self.assertEqual(proc.returncode, 0, proc.stderr)
            artifacts = [next(output.glob("*-full.tar.zst")) for output in outputs]
            self.assertEqual(artifacts[0].read_bytes(), artifacts[1].read_bytes())


    def test_rejects_parent_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "unsafe.tar.gz"
            with tarfile.open(archive, "w:gz") as tf:
                add_file(tf, "../escape", b"bad")
            launcher = root / "launcher"
            launcher.write_text("x")
            launcher.chmod(0o755)
            proc = self.assemble_fixture(archive, launcher, root / "out")
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse((root / "escape").exists())

    def test_rejects_escaping_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "unsafe-symlink.tar.gz"
            with tarfile.open(archive, "w:gz") as tf:
                add_directory(tf, "prefix")
                add_directory(tf, "prefix/lib")
                add_symlink(tf, "prefix/lib/escape", "../../../outside")
            launcher = root / "launcher"
            launcher.write_text("x")
            launcher.chmod(0o755)
            proc = self.assemble_fixture(archive, launcher, root / "out")
            self.assertNotEqual(proc.returncode, 0)

    def test_rejects_duplicate_member(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "duplicate.tar.gz"
            with tarfile.open(archive, "w:gz") as tf:
                add_directory(tf, "prefix")
                add_file(tf, "prefix/value", b"first")
                add_file(tf, "prefix/value", b"second")
            launcher = root / "launcher"
            launcher.write_text("x")
            launcher.chmod(0o755)
            proc = self.assemble_fixture(archive, launcher, root / "out")
            self.assertNotEqual(proc.returncode, 0)

    def test_rejects_incomplete_input_without_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            launcher = root / "launcher"
            launcher.write_text("x")
            launcher.chmod(0o755)

            archive = root / "incomplete.tar.gz"
            with tarfile.open(archive, "w:gz") as tf:
                add_file(tf, "README.txt", b"no prefix\n")
            proc = self.assemble_fixture(archive, launcher, root / "out-incomplete")
            self.assertNotEqual(proc.returncode, 0)

            invalid_root = root / "invalid-root-marker.tar.gz"
            with tarfile.open(invalid_root, "w:gz") as tf:
                add_file(tf, ".", b"not a directory")
            proc = self.assemble_fixture(invalid_root, launcher, root / "out-invalid-root")
            self.assertNotEqual(proc.returncode, 0)

    def test_contract_is_full_first(self) -> None:
        contract = json.loads(
            (ROOT / "components/upstream-thin/contracts/product-v1.json").read_text()
        )
        self.assertEqual(
            contract["artifact_order"],
            ["full", "install_only", "install_only_stripped"],
        )
        self.assertIn("verified full", contract["artifacts"]["install_only"]["derivation"])
        self.assertIn(
            "verified install_only",
            contract["artifacts"]["install_only_stripped"]["derivation"],
        )


if __name__ == "__main__":
    unittest.main()
