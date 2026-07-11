#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_type(mode: int) -> str:
    if stat.S_ISREG(mode):
        return "REGULAR"
    if stat.S_ISDIR(mode):
        return "DIRECTORY"
    if stat.S_ISLNK(mode):
        return "SYMLINK"
    return "SPECIAL"


def entries(root: Path) -> list[Path]:
    output: list[Path] = []
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        dirs.sort()
        files.sort()
        base = Path(current)
        output.extend(base / name for name in dirs)
        output.extend(base / name for name in files)
    return sorted(output, key=lambda path: path.relative_to(root).as_posix())


def fingerprint(root: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    type_counts = {"REGULAR": 0, "DIRECTORY": 0, "SYMLINK": 0, "SPECIAL": 0}
    pycache_paths: list[str] = []
    special_paths: list[str] = []

    for path in entries(root):
        relative = path.relative_to(root).as_posix()
        st = path.lstat()
        kind = file_type(st.st_mode)
        type_counts[kind] += 1
        file_hash = sha256_file(path) if kind == "REGULAR" else ""
        target = os.readlink(path) if kind == "SYMLINK" else ""
        if kind == "SPECIAL":
            special_paths.append(relative)
        if (
            relative.endswith(".pyc")
            or relative.endswith("/__pycache__")
            or "/__pycache__/" in f"/{relative}/"
        ):
            pycache_paths.append(relative)
        digest.update(
            "\t".join(
                (
                    relative,
                    kind,
                    f"{stat.S_IMODE(st.st_mode):04o}",
                    str(st.st_size),
                    str(st.st_mtime_ns),
                    file_hash,
                    target,
                )
            ).encode("utf-8", "surrogateescape")
        )
        digest.update(b"\n")

    return {
        "schema_version": 1,
        "root": str(root),
        "fingerprint": digest.hexdigest(),
        "entry_count": sum(type_counts.values()),
        "type_counts": type_counts,
        "pycache_paths": pycache_paths,
        "special_paths": special_paths,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-entry-count", type=int, default=3155)
    args = parser.parse_args()

    root = args.runtime_prefix.resolve()
    if not root.is_dir():
        parser.error(f"runtime prefix is not a directory: {root}")
    result = fingerprint(root)
    result["expected_entry_count"] = args.expected_entry_count
    result["pass"] = (
        result["entry_count"] == args.expected_entry_count
        and result["pycache_paths"] == []
        and result["special_paths"] == []
    )
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
