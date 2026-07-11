from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

EXPECTED_GATE2_RESULT_INDEX = "0041f1c3c73dc7a62291b6c3b244ac885d9bad6799d4115280febc20f61384da"
EXPECTED_GATE1_CONTRACT_INDEX = "79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3"


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint(root: Path) -> str:
    rows: list[dict[str, Any]] = []
    if root.exists():
        paths: list[Path] = []
        for current_text, directories, filenames in os.walk(root, topdown=True, followlinks=False):
            current = Path(current_text)
            relative_dir = current.relative_to(root).as_posix() if current != root else ""
            if relative_dir == ".cpython-android-cli":
                directories[:] = [name for name in directories if name != "transactions"]
            for name in list(directories) + filenames:
                path = current / name
                paths.append(path)
                if path.is_symlink() and name in directories:
                    directories.remove(name)
        for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
            relative = path.relative_to(root).as_posix()
            observed = path.lstat()
            mode = f"{stat.S_IMODE(observed.st_mode):04o}"
            if path.is_symlink():
                row = {"path": relative, "type": "symlink", "mode": mode, "target": os.readlink(path)}
            elif path.is_dir():
                row = {"path": relative, "type": "directory", "mode": mode}
            elif path.is_file():
                row = {
                    "path": relative,
                    "type": "regular",
                    "mode": mode,
                    "size": observed.st_size,
                    "sha256": sha256_file(path),
                }
            else:
                row = {"path": relative, "type": "special", "mode": mode}
            rows.append(row)
    canonical = "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def transaction_dirs(root: Path) -> list[Path]:
    txroot = root / ".cpython-android-cli/transactions"
    if not txroot.is_dir():
        return []
    return sorted(path for path in txroot.iterdir() if path.is_dir())


def newest_journal(root: Path) -> tuple[Path, dict[str, Any]]:
    directories = transaction_dirs(root)
    if not directories:
        raise RuntimeError(f"no transaction directory: {root}")
    transaction = max(directories, key=lambda path: path.stat().st_mtime_ns)
    return transaction, read_json(transaction / "journal.json")


def registry(root: Path) -> dict[str, Any]:
    path = root / ".cpython-android-cli/registry.json"
    return read_json(path) if path.exists() else {
        "schema_version": 1,
        "registry_kind": "cpython-android-cli-installed-ownership-registry",
        "artifacts": [],
        "owned_paths": [],
    }


def first_regular(root: Path, artifact: str) -> str:
    return next(
        row["path"]
        for row in registry(root)["owned_paths"]
        if row["owner_artifact"] == artifact and row["type"] == "regular"
    )


def clone_installation(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, symlinks=True, copy_function=os.link)


def replace_with_bytes(path: Path, data: bytes) -> None:
    mode = stat.S_IMODE(path.lstat().st_mode)
    temporary = path.with_name(path.name + ".scenario-replacement")
    temporary.write_bytes(data)
    os.chmod(temporary, mode)
    os.replace(temporary, path)


def write_registry_snapshot(output: Path, name: str, root: Path) -> None:
    current = registry(root)
    observed_rows: list[dict[str, Any]] = []
    for row in current["owned_paths"]:
        path = root / "prefix" / row["path"]
        item = dict(row)
        kind = "absent"
        try:
            observed = path.lstat()
        except FileNotFoundError:
            observed = None
        if observed is not None:
            if path.is_symlink():
                kind = "symlink"
            elif path.is_dir():
                kind = "directory"
            elif path.is_file():
                kind = "regular"
            else:
                kind = "special"
        item["observed_type"] = kind
        item["observed_match"] = (
            kind == row["type"]
            and f"{stat.S_IMODE(observed.st_mode):04o}" == row["mode"]
            if observed is not None
            else False
        )
        if item["observed_match"] and kind == "regular":
            item["observed_match"] = path.stat().st_size == row["size"] and sha256_file(path) == row["sha256"]
            item["observed_size"] = path.stat().st_size
            item["observed_sha256"] = sha256_file(path)
        elif item["observed_match"] and kind == "symlink":
            item["observed_target"] = os.readlink(path)
            item["observed_match"] = item["observed_target"] == row["symlink_target"]
        observed_rows.append(item)
    snapshots = output / "snapshots"
    snapshots.mkdir(exist_ok=True)
    (snapshots / f"{name}-registry.json").write_bytes(canonical_json_bytes(current))
    (snapshots / f"{name}-observed-owned-paths.json").write_bytes(
        canonical_json_bytes(
            {
                "schema_version": 1,
                "owned_path_count": len(observed_rows),
                "all_match": all(item["observed_match"] for item in observed_rows),
                "rows": observed_rows,
            }
        )
    )
