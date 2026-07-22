from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "components/upstream-thin/lib"))
import data_products as D


CA = b"-----BEGIN CERTIFICATE-----\nZmFrZQ==\n-----END CERTIFICATE-----\n"
TZIF = b"TZif2" + b"\0" * 64


def wheel(path: Path, distribution: str, version: str, files: dict[str, bytes], *, symlink: str | None = None) -> Path:
    dist = f"{distribution}-{version}.dist-info"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.external_attr = 0o100644 << 16
            zf.writestr(info, data)
        zf.writestr(f"{dist}/licenses/LICENSE", f"{distribution} license\n".encode())
        if symlink:
            info = zipfile.ZipInfo(symlink)
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            zf.writestr(info, "../../escape")
    return path


def inputs(root: Path, *, traversal: bool = False, symlink: bool = False) -> tuple[Path, Path]:
    cert_files = {"certifi/cacert.pem": CA}
    tz_files = {
        "tzdata/zoneinfo/tzdata.zi": b"# version 2026c\nZ Etc/UTC 0 - UTC\n",
        "tzdata/zoneinfo/UTC": TZIF,
        "tzdata/zoneinfo/Asia/Seoul": TZIF,
        "tzdata/zoneinfo/America/New_York": TZIF,
        "tzdata/zoneinfo/__init__.py": b"ignored\n",
    }
    if traversal:
        cert_files["../escape"] = b"bad"
    return (
        wheel(root / "certifi-2026.6.17-py3-none-any.whl", "certifi", "2026.6.17", cert_files, symlink="certifi/link" if symlink else None),
        wheel(root / "tzdata-2026.3-py2.py3-none-any.whl", "tzdata", "2026.3", tz_files),
    )


class DataProductTests(unittest.TestCase):
    def tmp(self) -> Path:
        return Path(tempfile.mkdtemp())

    def assemble(self, root: Path, output_name: str = "out") -> dict:
        certifi, tzdata = inputs(root)
        return D.assemble_data_product(certifi, tzdata, root / output_name, ca_version="2026.6.17", tzdata_version="2026.3")

    def test_assemble_and_verify(self) -> None:
        root = self.tmp()
        result = self.assemble(root)
        self.assertTrue(result["pass"])
        artifact = root / "out" / result["artifact"]["filename"]
        verified = D.verify_data_product(artifact)
        self.assertTrue(verified["pass"], verified)
        self.assertEqual(verified["metrics"]["iana_version"], "2026c")
        self.assertEqual(verified["metrics"]["zoneinfo_file_count"], 4)

    def test_reproducible(self) -> None:
        root = self.tmp()
        a = self.assemble(root, "a")
        b = self.assemble(root, "b")
        self.assertEqual((root / "a" / a["artifact"]["filename"]).read_bytes(), (root / "b" / b["artifact"]["filename"]).read_bytes())

    def test_install_update_rollback(self) -> None:
        root = self.tmp()
        current = self.assemble(root, "current")
        cert, tz = inputs(root / "rollback-input") if False else (None, None)
        rollback_root = root / "rollback-input"
        rollback_root.mkdir()
        cert = wheel(rollback_root / "certifi-2026.5.20-py3-none-any.whl", "certifi", "2026.5.20", {"certifi/cacert.pem": CA})
        tz = wheel(rollback_root / "tzdata-2026.2-py2.py3-none-any.whl", "tzdata", "2026.2", {
            "tzdata/zoneinfo/tzdata.zi": b"# version 2026b\nZ Etc/UTC 0 - UTC\n",
            "tzdata/zoneinfo/UTC": TZIF,
            "tzdata/zoneinfo/Asia/Seoul": TZIF,
            "tzdata/zoneinfo/America/New_York": TZIF,
        })
        old = D.assemble_data_product(cert, tz, root / "old", ca_version="2026.5.20", tzdata_version="2026.2")
        home = root / "data-home"
        old_archive = root / "old" / old["artifact"]["filename"]
        current_archive = root / "current" / current["artifact"]["filename"]
        D.install_data_product(old_archive, home)
        self.assertEqual(os.readlink(home / "current"), f"releases/{old['release_id']}")
        D.install_data_product(current_archive, home)
        self.assertEqual(os.readlink(home / "current"), f"releases/{current['release_id']}")
        D.activate_data_release(home, old["release_id"])
        self.assertEqual(os.readlink(home / "current"), f"releases/{old['release_id']}")
        D.activate_data_release(home, current["release_id"])
        self.assertTrue((home / "current/DATA.json").is_file())

    def test_immutable_release_collision_fails(self) -> None:
        root = self.tmp()
        result = self.assemble(root)
        artifact = root / "out" / result["artifact"]["filename"]
        home = root / "home"
        D.install_data_product(artifact, home)
        (home / "releases" / result["release_id"] / "ca/ca-bundle.pem").write_bytes(b"tamper")
        with self.assertRaises(ValueError):
            D.install_data_product(artifact, home)

    def test_rejects_wheel_traversal(self) -> None:
        root = self.tmp()
        certifi, tzdata = inputs(root, traversal=True)
        with self.assertRaises(ValueError):
            D.assemble_data_product(certifi, tzdata, root / "out", ca_version="2026.6.17", tzdata_version="2026.3")

    def test_rejects_wheel_symlink(self) -> None:
        root = self.tmp()
        certifi, tzdata = inputs(root, symlink=True)
        with self.assertRaises(ValueError):
            D.assemble_data_product(certifi, tzdata, root / "out", ca_version="2026.6.17", tzdata_version="2026.3")

    def test_lock_identity_mismatch_fails(self) -> None:
        root = self.tmp()
        certifi, tzdata = inputs(root)
        expected = {"filename": certifi.name, "sha256": "0" * 64, "size_bytes": certifi.stat().st_size}
        with self.assertRaises(ValueError):
            D.assemble_data_product(certifi, tzdata, root / "out", ca_version="2026.6.17", tzdata_version="2026.3", expected_certifi=expected)


if __name__ == "__main__":
    unittest.main()
