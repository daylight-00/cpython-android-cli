from __future__ import annotations

import io
import json
import subprocess
import tarfile
from pathlib import Path
import tempfile
import unittest

from verify_rb3_successor_install_only_m_acceptance import ROOT, verify


def copy_committed_tree(source: Path, destination: Path) -> None:
    archive = subprocess.run(
        ["git", "-C", str(source), "archive", "--format=tar", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as stream:
        stream.extractall(destination, filter="data")


class RB3SuccessorInstallOnlyAcceptanceTests(unittest.TestCase):
    def test_frozen_acceptance_passes(self) -> None:
        result = verify(ROOT)
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["failed_checks"], [])

    def test_boundary_rejects_stripped_start_or_family_supersession(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            copy = Path(td) / "repo"
            copy_committed_tree(ROOT, copy)
            path = copy / "experiments/epoch3-upstream-thin-release-blockers/accepted-rb3-successor-install-only-m-r2-return.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["claim_boundary"]["successor_stripped_started"] = True
            data["claim_boundary"]["artifact_family_superseded"] = True
            path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            result = verify(copy)
            self.assertFalse(result["pass"])
            self.assertIn("file_identities", result["failed_checks"])
            self.assertIn("acceptance_boundary", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
