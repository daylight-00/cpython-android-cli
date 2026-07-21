from __future__ import annotations

import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "components/upstream-thin/bin/cpython-android-upstream-thin"
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))

from archive import safe_extract_tar, write_tar_gz  # noqa: E402
from strip_surface import section_census, tool_identity  # noqa: E402


class StrippedTests(unittest.TestCase):
    def compile_elf(self, root: Path, *, already_stripped: bool = False) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        source = root / "launcher.c"
        source.write_text("int main(void) { return 0; }\n", encoding="utf-8")
        output = root / "python/bin/python3.14"
        output.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            ["cc", "-g", "-Wl,-rpath,$ORIGIN/../lib", str(source), "-o", str(output)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        output.chmod(0o755)
        if already_stripped:
            proc = subprocess.run(
                ["strip", "--strip-unneeded", str(output)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
        return output

    def make_install_only(self, root: Path, *, already_stripped: bool = False) -> Path:
        tree = root / "tree/python"
        launcher = self.compile_elf(root / "tree", already_stripped=already_stripped)
        self.assertEqual(launcher, tree / "bin/python3.14")
        os.symlink("python3.14", tree / "bin/python3")
        os.symlink("python3.14", tree / "bin/python")
        (tree / "lib").mkdir(parents=True)
        (tree / "lib/marker.txt").write_text("unchanged payload\n", encoding="utf-8")
        archive = root / "fixture-install_only.tar.gz"
        write_tar_gz(tree, archive)
        return archive

    def assemble(self, source: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(CLI),
                "assemble-stripped",
                "--fixture-mode",
                "--install-only-archive",
                str(source),
                "--output-dir",
                str(output),
                "--strip-tool",
                "strip",
                "--readelf",
                "readelf",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def verify(self, stripped: Path, source: Path, receipt: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(CLI),
                "verify-stripped",
                "--fixture-mode",
                str(stripped),
                "--install-only-archive",
                str(source),
                "--mutation-receipt",
                str(receipt),
                "--readelf",
                "readelf",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_distinct_archive_and_verifier(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stripped-test-") as temporary:
            root = Path(temporary)
            source = self.make_install_only(root)
            output = root / "output"
            proc = self.assemble(source, output)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            receipt_data = json.loads(proc.stdout)
            self.assertEqual(receipt_data["decision"], "distinct-archive")
            self.assertEqual(receipt_data["regular_elf_count"], 1)
            self.assertEqual(receipt_data["eligible_paths"], ["bin/python3.14"])
            self.assertEqual(receipt_data["changed_paths"], ["bin/python3.14"])
            stripped = next(output.glob("*-install_only_stripped.tar.gz"))
            receipt = output / f"{stripped.name}.receipt.json"
            verify = self.verify(stripped, source, receipt)
            self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
            result = json.loads(verify.stdout)
            self.assertTrue(result["pass"])
            self.assertTrue(result["checks"]["all_and_only_eligible_elf_changed"])
            self.assertTrue(result["checks"]["non_elf_bytes_unchanged"])
            self.assertTrue(result["checks"]["elf_dynamic_alignment_preserved"])

    def test_distinct_derivation_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stripped-test-") as temporary:
            root = Path(temporary)
            source = self.make_install_only(root)
            artifacts: list[Path] = []
            receipts: list[dict] = []
            for name in ("a", "b"):
                output = root / name
                proc = self.assemble(source, output)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                artifacts.append(next(output.glob("*-install_only_stripped.tar.gz")))
                receipts.append(json.loads(proc.stdout))
            self.assertEqual(artifacts[0].read_bytes(), artifacts[1].read_bytes())
            self.assertEqual(receipts[0]["artifact"], receipts[1]["artifact"])
            self.assertEqual(receipts[0]["changed_paths"], receipts[1]["changed_paths"])

    def test_non_elf_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stripped-test-") as temporary:
            root = Path(temporary)
            source = self.make_install_only(root)
            output = root / "output"
            proc = self.assemble(source, output)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            stripped = next(output.glob("*-install_only_stripped.tar.gz"))
            receipt = output / f"{stripped.name}.receipt.json"

            tar_path = root / "stripped.tar"
            with gzip.open(stripped, "rb") as input_stream, tar_path.open("wb") as output_stream:
                shutil.copyfileobj(input_stream, output_stream)
            tree = root / "mutated"
            safe_extract_tar(tar_path, tree, "r:")
            (tree / "python/lib/marker.txt").write_text("mutated\n", encoding="utf-8")
            mutated = root / "mutated-install_only_stripped.tar.gz"
            write_tar_gz(tree / "python", mutated)

            verify = self.verify(mutated, source, receipt)
            self.assertNotEqual(verify.returncode, 0)
            result = json.loads(verify.stdout)
            self.assertFalse(result["checks"]["non_elf_bytes_unchanged"])

    def test_already_stripped_input_returns_alias_decision_without_archive(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stripped-test-") as temporary:
            root = Path(temporary)
            source = self.make_install_only(root, already_stripped=True)
            output = root / "output"
            proc = self.assemble(source, output)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            result = json.loads(proc.stdout)
            self.assertEqual(result["decision"], "producer-already-stripped-alias")
            self.assertEqual(result["eligible_elf_count"], 0)
            self.assertEqual(result["changed_elf_count"], 0)
            self.assertIsNone(result["artifact"])
            self.assertFalse(list(output.glob("*.tar.gz")))
            self.assertEqual(len(list(output.glob("*.receipt.json"))), 1)

    def test_non_fixture_rejects_unaccepted_install_only_identity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stripped-test-") as temporary:
            root = Path(temporary)
            source = self.make_install_only(root)
            proc = subprocess.run(
                [
                    str(CLI),
                    "assemble-stripped",
                    "--install-only-archive",
                    str(source),
                    "--output-dir",
                    str(root / "output"),
                    "--strip-tool",
                    "strip",
                    "--readelf",
                    "readelf",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("accepted install-only mismatch", proc.stderr)

    def test_tool_identity_resolves_path_name_and_census_detects_sections(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stripped-test-") as temporary:
            root = Path(temporary)
            launcher = self.compile_elf(root)
            identity = tool_identity("strip")
            self.assertTrue(Path(identity["path"]).is_file())
            self.assertEqual(len(identity["sha256"]), 64)
            census = section_census(launcher, "readelf")
            self.assertTrue(census["eligible"])
            self.assertIn(".symtab", census["removable_sections"])

    def test_multicall_tool_alias_is_preserved_for_invocation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stripped-test-") as temporary:
            root = Path(temporary)
            target = root / "llvm-readobj"
            target.write_text(
                "#!/bin/sh\n"
                "case \"$(basename \"$0\")\" in\n"
                "  readelf)\n"
                "    cat <<'EOF'\n"
                "  [ 1] .symtab SYMTAB 00000000 000000 000018 18 0 0 8\n"
                "  [ 2] .strtab STRTAB 00000000 000018 000010 00 0 0 1\n"
                "EOF\n"
                "    ;;\n"
                "  *)\n"
                "    cat <<'EOF'\n"
                "Sections [\n"
                "  Section { Name: .symtab }\n"
                "]\n"
                "EOF\n"
                "    ;;\n"
                "esac\n",
                encoding="utf-8",
            )
            target.chmod(0o755)
            alias = root / "readelf"
            alias.symlink_to(target.name)
            dummy = root / "dummy.elf"
            dummy.write_bytes(b"not inspected by fake tool")

            identity = tool_identity(str(alias))
            self.assertEqual(Path(identity["path"]), alias.absolute())
            self.assertEqual(Path(identity["canonical_path"]), target.resolve())
            self.assertTrue(identity["is_symlink"])
            census = section_census(dummy, str(alias))
            self.assertEqual(census["removable_sections"], [".symtab", ".strtab"])
            self.assertTrue(census["eligible"])


if __name__ == "__main__":
    unittest.main()
