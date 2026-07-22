from __future__ import annotations
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[2]
BASE = Path("experiments/epoch3-upstream-thin-release-blockers")
spec = importlib.util.spec_from_file_location(
    "v", ROOT / BASE / "verify_rb1_source_provenance_acceptance.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def copy_authority_fixture(destination: Path) -> Path:
    """Copy only the authority subtree required by the verifier.

    Copying the whole repository followed historical work/result symlinks and made
    the negative fixture depend on stale external targets in the owner checkout.
    The verifier reads only BASE, so a bounded subtree copy is both sufficient and
    independent of unrelated repository state.
    """
    root = destination / "repo"
    target = root / BASE
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / BASE, target, symlinks=True)
    return root


class T(unittest.TestCase):
    def test_real(self):
        self.assertTrue(m.verify(ROOT)["pass"])

    def test_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            x = copy_authority_fixture(Path(d))
            p = x / BASE / "rb1-source-provenance-authority-evidence/source-provenance.json"
            p.write_text("{}\n")
            self.assertFalse(m.verify(x)["pass"])

    def test_claim_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            x = copy_authority_fixture(Path(d))
            p = x / BASE / "accepted-rb1-source-provenance-r1-return.json"
            q = json.loads(p.read_text())
            q["claim_boundary"]["selectable"] = True
            p.write_text(json.dumps(q))
            self.assertFalse(m.verify(x)["pass"])


if __name__ == "__main__":
    unittest.main()
