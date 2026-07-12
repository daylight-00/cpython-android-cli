#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

FINGERPRINT_KIND = "stage3c-installed-payload-portable-v1"
EXPECTED_TYPES = {"directory": 57, "regular": 654, "symlink": 3}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def paths(root: Path) -> list[Path]:
    output: list[Path] = []
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        dirs.sort()
        files.sort()
        base = Path(current)
        output.extend(base / name for name in dirs)
        output.extend(base / name for name in files)
    return sorted(output, key=lambda path: path.relative_to(root).as_posix())


def portable_record(path: Path, root: Path) -> tuple[str, str, str, str, str, str]:
    observed = path.lstat()
    relative = path.relative_to(root).as_posix()
    mode = f"{stat.S_IMODE(observed.st_mode):04o}"
    if stat.S_ISREG(observed.st_mode):
        return relative, "regular", mode, str(observed.st_size), sha256_file(path), ""
    if stat.S_ISDIR(observed.st_mode):
        return relative, "directory", mode, "", "", ""
    if stat.S_ISLNK(observed.st_mode):
        return relative, "symlink", mode, "", "", os.readlink(path)
    return relative, "special", mode, "", "", ""


def fingerprint(root: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    type_counts = {kind: 0 for kind in (*EXPECTED_TYPES, "special")}
    pycache_paths: list[str] = []
    special_paths: list[str] = []

    for path in paths(root):
        record = portable_record(path, root)
        relative, kind = record[:2]
        type_counts[kind] += 1
        if kind == "special":
            special_paths.append(relative)
        if (
            relative.endswith(".pyc")
            or relative.endswith("/__pycache__")
            or "/__pycache__/" in f"/{relative}/"
        ):
            pycache_paths.append(relative)
        digest.update("\t".join(record).encode("utf-8", "surrogateescape"))
        digest.update(b"\n")

    result = {
        "schema_version": 1,
        "fingerprint_kind": FINGERPRINT_KIND,
        "root": str(root),
        "fingerprint": digest.hexdigest(),
        "entry_count": sum(type_counts.values()),
        "type_counts": type_counts,
        "pycache_paths": pycache_paths,
        "special_paths": special_paths,
    }
    result["pass"] = (
        result["entry_count"] == 714
        and {kind: type_counts[kind] for kind in EXPECTED_TYPES} == EXPECTED_TYPES
        and type_counts["special"] == 0
        and pycache_paths == []
        and special_paths == []
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--installed-prefix", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    root = args.installed_prefix.resolve()
    if not root.is_dir():
        parser.error(f"installed prefix is not a directory: {root}")
    result = fingerprint(root)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 11


if __name__ == "__main__":
    raise SystemExit(main())
