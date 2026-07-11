from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

import recovery_engine as engine

EXPECTED_GATE2_RESULT_INDEX = "0041f1c3c73dc7a62291b6c3b244ac885d9bad6799d4115280febc20f61384da"
EXPECTED_GATE1_CONTRACT_INDEX = "79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3"
EXPECTED_LOGS = [
    "01-runtime-seed-install.json",
    "02-runtime-seed-verify.json",
    "03-runtime-development-seed-install.json",
    "04-runtime-development-seed-verify.json",
    "05-prepared-crash.json",
    "06-prepared-journal-before-recovery.json",
    "07-prepared-recovery.json",
    "08-prepared-journal-after-recovery.json",
    "09-prepared-verify.json",
    "10-intent-crash.json",
    "11-intent-journal-before-recovery.json",
    "12-intent-recovery.json",
    "13-intent-journal-after-recovery.json",
    "14-intent-verify.json",
    "15-applying-install-crash.json",
    "16-applying-install-journal-before-recovery.json",
    "17-applying-install-recovery.json",
    "18-applying-install-journal-after-recovery.json",
    "19-applying-install-verify.json",
    "20-applying-uninstall-crash.json",
    "21-applying-uninstall-journal-before-recovery.json",
    "22-applying-uninstall-recovery.json",
    "23-applying-uninstall-journal-after-recovery.json",
    "24-applying-uninstall-verify.json",
    "25-registry-crash-repair.json",
    "26-registry-crash-journal-before-recovery.json",
    "27-registry-crash-recovery.json",
    "28-registry-crash-journal-after-recovery.json",
    "29-registry-crash-verify-restored-corruption.json",
    "30-registry-crash-normal-repair.json",
    "31-registry-crash-repaired-verify.json",
    "32-committed-repair-crash.json",
    "33-committed-journal-before-recovery.json",
    "34-committed-recovery.json",
    "35-committed-verify.json",
    "36-lock-contender.json",
    "37-lock-holder.json",
    "38-lock-post-release-install.json",
    "39-lock-post-release-verify.json",
    "40-idempotent-second-recovery.json",
]
EXPECTED_SNAPSHOTS = {
    "prepared-final": 714,
    "intent-final": 714,
    "applying-install-final": 1168,
    "applying-uninstall-final": 1168,
    "registry-crash-final": 1168,
}


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
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


def journals(root: Path) -> list[dict[str, Any]]:
    txroot = root / ".cpython-android-cli/transactions"
    if not txroot.is_dir():
        return []
    return [read_json(path) for path in sorted(txroot.glob("*/journal.json"))]
