#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import stat
from pathlib import Path
from typing import Any


def cjson(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def walk_entries(root: Path, *, exclude: set[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def visit(directory: Path) -> None:
        for entry in sorted(os.scandir(directory), key=lambda row: row.name):
            path = Path(entry.path)
            resolved_identity = path.absolute()
            if resolved_identity in exclude:
                continue
            rel = path.relative_to(root).as_posix()
            st = path.lstat()
            mode = f"{stat.S_IMODE(st.st_mode):04o}"
            if stat.S_ISLNK(st.st_mode):
                target = os.readlink(path)
                normalized = None
                safe = False
                if not posixpath.isabs(target):
                    normalized = posixpath.normpath(posixpath.join(posixpath.dirname(rel), target))
                    safe = normalized not in ("..", ".") and not normalized.startswith("../")
                rows.append({"path": rel, "type": "symlink", "mode": mode, "target": target, "resolved_target": normalized, "safe_target": safe})
            elif stat.S_ISDIR(st.st_mode):
                rows.append({"path": rel, "type": "directory", "mode": mode})
                visit(path)
            elif stat.S_ISREG(st.st_mode):
                rows.append({"path": rel, "type": "regular", "mode": mode, "size": st.st_size, "sha256": sha256_file(path)})
            else:
                rows.append({"path": rel, "type": "special", "mode": mode, "stat_mode": st.st_mode})

    visit(root)
    return rows


def write_safety(root: Path, safety_output: Path, index_output: Path) -> int:
    safety_output.unlink(missing_ok=True)
    index_output.unlink(missing_ok=True)
    rows = walk_entries(root, exclude={safety_output.absolute(), index_output.absolute()})
    counts = {kind: sum(row["type"] == kind for row in rows) for kind in ("regular", "directory", "symlink", "special")}
    unsafe_links = [
        {key: row[key] for key in ("path", "target", "resolved_target")}
        for row in rows
        if row["type"] == "symlink" and row.get("safe_target") is not True
    ]
    special_entries = [{key: row[key] for key in ("path", "mode", "stat_mode")} for row in rows if row["type"] == "special"]
    result = {
        "schema_version": 1,
        "verification_kind": "stage3c-phase5-gate3c-result-tree-safety",
        "counts": counts,
        "unsafe_links": unsafe_links,
        "special_entries": special_entries,
        "pass": not unsafe_links and not special_entries,
        "claim_boundary": "Pre-archive filesystem safety only; final Gate 3C acceptance still requires independent archive and root-index inspection.",
    }
    safety_output.write_bytes(cjson(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 2


def write_index(root: Path, safety_output: Path, index_output: Path) -> int:
    if write_safety(root, safety_output, index_output) != 0:
        raise SystemExit("result-tree safety did not pass")
    index_output.unlink(missing_ok=True)
    rows = walk_entries(root, exclude={index_output.absolute()})
    unsupported = [row for row in rows if row["type"] == "special"]
    if unsupported:
        raise SystemExit(f"unsupported result entries: {unsupported}")
    files = []
    for row in rows:
        if row["type"] == "directory":
            continue
        if row["type"] == "regular":
            files.append({key: row[key] for key in ("path", "type", "mode", "size", "sha256")})
        elif row["type"] == "symlink":
            if row.get("safe_target") is not True:
                raise SystemExit(f"unsafe symlink in result index: {row['path']} -> {row['target']}")
            files.append({key: row[key] for key in ("path", "type", "mode", "target")})
    result = {
        "schema_version": 1,
        "index_kind": "stage3c-phase5-gate3c-addon-lifecycle-result-index",
        "file_count": len(files),
        "files": files,
    }
    index_output.write_bytes(cjson(result))
    print(json.dumps({"file_count": len(files), "symlink_count": sum(row["type"] == "symlink" for row in files)}, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--phase", required=True, choices=("audit", "index"))
    parser.add_argument("--safety-output", type=Path)
    parser.add_argument("--index-output", type=Path)
    args = parser.parse_args()
    root = args.results_dir.resolve()
    safety_output = (args.safety_output or root / "result-tree-safety.json").resolve()
    index_output = (args.index_output or root / "result-index.json").resolve()
    if root not in safety_output.parents or root not in index_output.parents:
        raise SystemExit("outputs must be inside results-dir")
    if args.phase == "audit":
        return write_safety(root, safety_output, index_output)
    return write_index(root, safety_output, index_output)


if __name__ == "__main__":
    raise SystemExit(main())
