from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))

from archive import sha256_file, write_tar_gz, write_tar_zst  # noqa: E402
from release_family import archive_manifest, assemble_release_family, verify_release_family  # noqa: E402


class ReleaseFamilyTests(unittest.TestCase):
    def make_archives(self, root: Path) -> tuple[dict[str, Path], dict[str, dict]]:
        full_tree = root / "full-tree"
        (full_tree / "python/build").mkdir(parents=True)
        (full_tree / "python/install/bin").mkdir(parents=True)
        (full_tree / "python/PYTHON.json").write_text('{"version":"8"}\n', encoding="utf-8")
        (full_tree / "python/build/provenance.txt").write_text("upstream\n", encoding="utf-8")
        (full_tree / "python/install/bin/python3.14").write_text("launcher\n", encoding="utf-8")
        (full_tree / "python/install/LICENSE").write_text("license\n", encoding="utf-8")

        install_tree = root / "install-tree"
        (install_tree / "python/bin").mkdir(parents=True)
        (install_tree / "python/bin/python3.14").write_text("launcher\n", encoding="utf-8")
        (install_tree / "python/LICENSE").write_text("license\n", encoding="utf-8")

        stripped_tree = root / "stripped-tree"
        (stripped_tree / "python/bin").mkdir(parents=True)
        (stripped_tree / "python/bin/python3.14").write_text("launch\n", encoding="utf-8")
        (stripped_tree / "python/LICENSE").write_text("license\n", encoding="utf-8")

        archives = {
            "full": root / "fixture-full.tar.zst",
            "install_only": root / "fixture-install_only.tar.gz",
            "install_only_stripped": root / "fixture-install_only_stripped.tar.gz",
        }
        write_tar_zst(full_tree, archives["full"])
        write_tar_gz(install_tree, archives["install_only"])
        write_tar_gz(stripped_tree, archives["install_only_stripped"])
        expected = {}
        for flavor, path in archives.items():
            expected[flavor] = {
                "filename": path.name,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "member_count": len(archive_manifest(path)),
            }
        return archives, expected

    def test_assembly_is_deterministic_and_verifies(self) -> None:
        with tempfile.TemporaryDirectory(prefix="family-test-") as temporary:
            root = Path(temporary)
            archives, expected = self.make_archives(root)
            outputs = []
            for name in ("a", "b"):
                output = root / name
                receipt = assemble_release_family(
                    archives["full"], archives["install_only"], archives["install_only_stripped"],
                    output, root=ROOT, expected=expected,
                )
                self.assertTrue(receipt["pass"])
                verification = verify_release_family(output, root=ROOT, expected=expected)
                self.assertTrue(verification["pass"], verification)
                outputs.append(output)
            names = sorted(path.name for path in outputs[0].iterdir())
            self.assertEqual(names, sorted(path.name for path in outputs[1].iterdir()))
            for name in names:
                self.assertEqual((outputs[0] / name).read_bytes(), (outputs[1] / name).read_bytes(), name)

    def test_missing_sidecar_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="family-test-") as temporary:
            root = Path(temporary)
            archives, expected = self.make_archives(root)
            output = root / "release"
            assemble_release_family(archives["full"], archives["install_only"], archives["install_only_stripped"], output, root=ROOT, expected=expected)
            sidecar = next(output.glob("*.provenance.json"))
            sidecar.unlink()
            result = verify_release_family(output, root=ROOT, expected=expected)
            self.assertFalse(result["pass"])
            self.assertIn("asset_identities", result["failed_checks"])

    def test_mutated_sha256sums_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="family-test-") as temporary:
            root = Path(temporary)
            archives, expected = self.make_archives(root)
            output = root / "release"
            assemble_release_family(archives["full"], archives["install_only"], archives["install_only_stripped"], output, root=ROOT, expected=expected)
            (output / "SHA256SUMS").write_text("0" * 64 + "  invalid\n", encoding="utf-8")
            result = verify_release_family(output, root=ROOT, expected=expected)
            self.assertFalse(result["pass"])
            self.assertIn("sha256sums_exact", result["failed_checks"])
            self.assertIn("checksum_binding", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
