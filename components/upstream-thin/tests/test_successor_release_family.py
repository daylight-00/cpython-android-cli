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
from release_family import archive_manifest  # noqa: E402
from successor_release_family import (  # noqa: E402
    RELEASE_ID,
    assemble_successor_release_family,
    verify_successor_release_family,
)


class SuccessorReleaseFamilyTests(unittest.TestCase):
    def make_archives(self, root: Path) -> tuple[dict[str, Path], dict[str, dict]]:
        full_tree = root / "full-tree"
        (full_tree / "python/build").mkdir(parents=True)
        (full_tree / "python/install/bin").mkdir(parents=True)
        (full_tree / "python/PYTHON.json").write_text('{"version":"3.14.6"}\n', encoding="utf-8")
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
        expected = {
            flavor: {
                "filename": path.name,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "member_count": len(archive_manifest(path)),
            }
            for flavor, path in archives.items()
        }
        return archives, expected

    def test_successor_family_is_deterministic_and_verifies(self) -> None:
        with tempfile.TemporaryDirectory(prefix="successor-family-test-") as temporary:
            root = Path(temporary)
            archives, expected = self.make_archives(root)
            outputs = []
            for name in ("a", "b"):
                output = root / name
                receipt = assemble_successor_release_family(
                    archives["full"], archives["install_only"], archives["install_only_stripped"],
                    output, root=ROOT, expected=expected,
                )
                self.assertTrue(receipt["pass"])
                self.assertEqual(receipt["release_id"], RELEASE_ID)
                verification = verify_successor_release_family(output, root=ROOT, expected=expected)
                self.assertTrue(verification["pass"], verification)
                self.assertEqual(verification["file_count"], 23)
                outputs.append(output)
            names = sorted(path.name for path in outputs[0].iterdir())
            self.assertEqual(names, sorted(path.name for path in outputs[1].iterdir()))
            for name in names:
                self.assertEqual((outputs[0] / name).read_bytes(), (outputs[1] / name).read_bytes(), name)

    def test_mutated_candidate_boundary_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="successor-family-test-") as temporary:
            root = Path(temporary)
            archives, expected = self.make_archives(root)
            output = root / "release"
            assemble_successor_release_family(
                archives["full"], archives["install_only"], archives["install_only_stripped"],
                output, root=ROOT, expected=expected,
            )
            index_path = output / "release-index.json"
            index = json.loads(index_path.read_text())
            index["release"]["claim_boundary"]["selectable"] = True
            index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
            result = verify_successor_release_family(output, root=ROOT, expected=expected)
            self.assertFalse(result["pass"])
            self.assertIn("claims_bounded", result["failed_checks"])

    def test_predecessor_artifact_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="successor-family-test-") as temporary:
            root = Path(temporary)
            archives, expected = self.make_archives(root)
            output = root / "release"
            assemble_successor_release_family(
                archives["full"], archives["install_only"], archives["install_only_stripped"],
                output, root=ROOT, expected=expected,
            )
            (output / "cpython-3.14.6+e3-full-r4-aarch64-linux-android-full.tar.zst").write_bytes(b"old")
            result = verify_successor_release_family(output, root=ROOT, expected=expected)
            self.assertFalse(result["pass"])
            self.assertIn("exact_file_set", result["failed_checks"])
            self.assertIn("predecessor_artifacts_absent", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
