#!/usr/bin/env python3
"""Verify exact full-to-install-only projection and deterministic archive metadata."""
from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from archive import safe_extract_tar, sha256_file, tree_manifest

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-full-r4.lock.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def extract_full(archive: Path, destination: Path, zstd: str) -> Path:
    tar_path = destination / "full.tar"
    proc = subprocess.run([zstd, "-q", "-d", "-f", str(archive), "-o", str(tar_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise RuntimeError(proc.stderr)
    tree = destination / "full"
    safe_extract_tar(tar_path, tree, "r:")
    return tree


def extract_install(archive: Path, destination: Path) -> Path:
    tar_path = destination / "install-only.tar"
    with gzip.open(archive, "rb") as source, tar_path.open("wb") as target:
        while block := source.read(1024 * 1024):
            target.write(block)
    tree = destination / "install-only"
    safe_extract_tar(tar_path, tree, "r:")
    return tree


def mapped_source_manifest(source: Path) -> list[dict[str, Any]]:
    rows = []
    for row in tree_manifest(source):
        item = dict(row)
        path = item["path"]
        if path == "install":
            item["path"] = "python"
        elif path.startswith("install/"):
            item["path"] = "python/" + path[len("install/"):]
        else:
            raise ValueError(f"unexpected source path: {path}")
        rows.append(item)
    return rows


def tar_metadata(archive: Path) -> dict[str, Any]:
    duplicate = False
    names: list[str] = []
    normalized = True
    with tarfile.open(archive, "r:gz") as tf:
        for member in tf.getmembers():
            names.append(member.name)
            normalized = normalized and member.uid == 0 and member.gid == 0 and member.mtime == 0 and member.uname == "" and member.gname == ""
    duplicate = len(names) != len(set(names))
    header = archive.read_bytes()[:10]
    gzip_mtime = int.from_bytes(header[4:8], "little") if len(header) >= 8 else -1
    return {"member_count": len(names), "duplicate": duplicate, "tar_normalized": normalized, "gzip_mtime": gzip_mtime}


def verify(install_archive: Path, full_archive: Path, *, zstd: str = "zstd", full_lock: Path = DEFAULT_LOCK, fixture_mode: bool = False) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    lock = load(full_lock)
    observed_full = {"filename": full_archive.name, "sha256": sha256_file(full_archive), "size_bytes": full_archive.stat().st_size}
    expected = lock["artifact"]
    checks["accepted_full_identity"] = fixture_mode or all(observed_full[key] == expected[key] for key in ("filename", "sha256", "size_bytes"))
    try:
        with tempfile.TemporaryDirectory(prefix="verify-install-only-") as tmp:
            root = Path(tmp)
            full_tree = extract_full(full_archive, root, zstd)
            install_tree = extract_install(install_archive, root)
            source = full_tree / "python/install"
            projected = install_tree / "python"
            checks["source_root"] = source.is_dir()
            checks["one_python_root"] = projected.is_dir() and sorted(path.name for path in install_tree.iterdir()) == ["python"]
            checks["full_metadata_absent"] = not (projected / "PYTHON.json").exists() and not (projected / "build").exists()
            expected_rows = mapped_source_manifest(source) if source.is_dir() else []
            actual_rows = tree_manifest(projected) if projected.is_dir() else []
            checks["exact_projection"] = actual_rows == expected_rows
            checks["payload_bytes_unchanged"] = actual_rows == expected_rows
            checks["launcher_surface"] = all((projected / f"bin/{name}").exists() for name in ("python", "python3", "python3.14"))
            checks["pip_surface"] = all((projected / f"bin/{name}").exists() for name in ("pip", "pip3", "pip3.14"))
            meta = tar_metadata(install_archive)
            checks["no_duplicate_members"] = meta["duplicate"] is False
            checks["deterministic_tar_metadata"] = meta["tar_normalized"] is True
            checks["deterministic_gzip_header"] = meta["gzip_mtime"] == 0
            checks["archive_member_count_matches_projection"] = meta["member_count"] == len(actual_rows)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{type(exc).__name__}: {exc}")
    failed = sorted(key for key, value in checks.items() if value is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-upstream-thin-install-only-exact-projection",
        "pass": not failed and not errors,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "source_full": observed_full,
        "artifact": {"path": str(install_archive), "sha256": sha256_file(install_archive), "size_bytes": install_archive.stat().st_size, "member_count": meta["member_count"] if "meta" in locals() else None},
        "claim_boundary": {"install_only_candidate": not failed and not errors, "install_only_authority_frozen": False, "stripped_started": False, "selectable": False, "publication": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("install_archive")
    parser.add_argument("--full-archive", required=True)
    parser.add_argument("--full-lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--zstd", default="zstd")
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args()
    result = verify(Path(args.install_archive).resolve(), Path(args.full_archive).resolve(), zstd=args.zstd, full_lock=Path(args.full_lock).resolve(), fixture_mode=args.fixture_mode)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
