#!/usr/bin/env python3
"""Derive the canonical install-only archive from the accepted full archive."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from archive import copy_tree_contents, safe_extract_tar, sha256_file, tree_manifest, write_json, write_tar_gz

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-full-r4.lock.json"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON must be object: {path}")
    return value


def extract_full(archive: Path, destination: Path, zstd: str) -> Path:
    tar_path = destination / "full.tar"
    proc = subprocess.run([zstd, "-q", "-d", "-f", str(archive), "-o", str(tar_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise RuntimeError(f"zstd failed: {proc.stderr.strip()}")
    tree = destination / "full-tree"
    safe_extract_tar(tar_path, tree, "r:")
    return tree


def verify_full_identity(archive: Path, lock: dict[str, Any], fixture_mode: bool) -> dict[str, Any]:
    observed = {"filename": archive.name, "sha256": sha256_file(archive), "size_bytes": archive.stat().st_size}
    if not fixture_mode:
        expected = lock["artifact"]
        for key in ("filename", "sha256", "size_bytes"):
            if observed[key] != expected[key]:
                raise RuntimeError(f"accepted full mismatch for {key}: expected={expected[key]!r} observed={observed[key]!r}")
    return observed


def assemble(args: argparse.Namespace) -> dict[str, Any]:
    full = Path(args.full_archive).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    lock = load_json(Path(args.full_lock).resolve())
    identity = verify_full_identity(full, lock, args.fixture_mode)
    release_id = args.release_id or lock.get("release_id", "e3-full-r4")
    target = lock.get("target_triple", "aarch64-linux-android")
    python_version = lock.get("python_version", "3.14.6")
    artifact = output_dir / f"cpython-{python_version}+{release_id}-{target}-install_only.tar.gz"

    with tempfile.TemporaryDirectory(prefix="e3-install-only-") as tmp:
        workspace = Path(tmp)
        full_tree = extract_full(full, workspace, args.zstd)
        source = full_tree / "python/install"
        if not source.is_dir():
            raise RuntimeError("accepted full lacks python/install/")
        if not (full_tree / "python/PYTHON.json").is_file() or not (full_tree / "python/build").is_dir():
            raise RuntimeError("accepted full lacks required full-only roots")

        projection_parent = workspace / "projection"
        python_root = projection_parent / "python"
        copy_tree_contents(source, python_root)
        if (python_root / "PYTHON.json").exists() or (python_root / "build").exists():
            raise RuntimeError("full-only metadata leaked into install-only projection")

        source_rows = tree_manifest(source)
        projected_rows = tree_manifest(python_root)
        rows = write_tar_gz(python_root, artifact)
        receipt = {
            "schema_version": 1,
            "receipt_kind": "epoch3-upstream-thin-install-only-local-projection",
            "status": "passed-structural-fixture" if args.fixture_mode else "passed-local-install-only-projection",
            "source_full": identity,
            "projection": {
                "source_prefix": "python/install/",
                "target_prefix": "python/",
                "payload_bytes_changed": False,
                "filtering": "none-preserve-all-install-members",
                "source_member_count": len(source_rows),
                "projected_member_count": len(projected_rows),
                "archive_member_count": len(rows),
            },
            "artifact": {
                "path": str(artifact),
                "filename": artifact.name,
                "sha256": sha256_file(artifact),
                "size_bytes": artifact.stat().st_size,
                "member_count": len(rows),
            },
            "selectable": False,
            "publication": False,
        }
        write_json(output_dir / f"{artifact.name.removesuffix('.tar.gz')}.receipt.json", receipt)
        return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-archive", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--full-lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--release-id")
    parser.add_argument("--zstd", default="zstd")
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args()
    print(json.dumps(assemble(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
