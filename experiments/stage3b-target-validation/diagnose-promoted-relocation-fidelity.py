#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ENTRY_FIELDS = (
    "type",
    "mode",
    "size",
    "mtime_ns",
    "target",
    "sha256",
)


def file_type(mode: int) -> str:
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISCHR(mode):
        return "char-device"
    if stat.S_ISBLK(mode):
        return "block-device"
    if stat.S_ISFIFO(mode):
        return "fifo"
    if stat.S_ISSOCK(mode):
        return "socket"
    return "other"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_paths(root: Path) -> Iterable[Path]:
    stack = [root]
    while stack:
        current = stack.pop()
        entries = sorted(os.scandir(current), key=lambda entry: entry.name, reverse=True)
        for entry in entries:
            path = Path(entry.path)
            yield path
            try:
                is_directory = entry.is_dir(follow_symlinks=False)
            except OSError:
                is_directory = False
            if is_directory:
                stack.append(path)


def collect_manifest(root: Path) -> dict[str, dict[str, Any]]:
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"runtime tree is missing: {root}")

    manifest: dict[str, dict[str, Any]] = {}
    for path in iter_paths(root):
        relative = path.relative_to(root).as_posix()
        st = path.lstat()
        kind = file_type(st.st_mode)
        target: str | None = None
        content_hash: str | None = None

        if kind == "symlink":
            target = os.readlink(path)
        elif kind == "file":
            content_hash = sha256_file(path)

        manifest[relative] = {
            "path": relative,
            "type": kind,
            "mode": stat.S_IMODE(st.st_mode),
            "size": st.st_size,
            "mtime_ns": st.st_mtime_ns,
            "target": target,
            "sha256": content_hash,
        }

    return manifest


def strict_fields(entry: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(entry[field] for field in ENTRY_FIELDS)


def portable_fields(entry: dict[str, Any]) -> dict[str, Any]:
    result = {
        "type": entry["type"],
        "mode": entry["mode"],
        "mtime_ns": entry["mtime_ns"],
    }

    if entry["type"] == "file":
        result["size"] = entry["size"]
        result["sha256"] = entry["sha256"]
    elif entry["type"] == "symlink":
        result["target"] = entry["target"]
    elif entry["type"] not in {"directory"}:
        result["size"] = entry["size"]

    return result


def changed_fields(
    source: dict[str, Any],
    relocated: dict[str, Any],
    fields: Iterable[str],
) -> list[str]:
    return [field for field in fields if source.get(field) != relocated.get(field)]


def manifest_rows(manifest: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [manifest[path] for path in sorted(manifest)]


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            json.dump(row, f, sort_keys=True)
            f.write("\n")


def write_tsv(
    path: Path,
    added: list[str],
    removed: list[str],
    changed: list[dict[str, Any]],
) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write("status\tpath\tfields\tsource_type\trelocated_type\n")
        for item in added:
            f.write(f"ADDED\t{item}\t\t\t\n")
        for item in removed:
            f.write(f"REMOVED\t{item}\t\t\t\n")
        for item in changed:
            f.write(
                "CHANGED\t{path}\t{fields}\t{source_type}\t{relocated_type}\n".format(
                    path=item["path"],
                    fields=",".join(item["portable_changed_fields"]),
                    source_type=item["source"]["type"],
                    relocated_type=item["relocated"]["type"],
                )
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--relocated", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    source_root = args.source.resolve()
    relocated_root = args.relocated.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_manifest = collect_manifest(source_root)
    relocated_manifest = collect_manifest(relocated_root)

    source_paths = set(source_manifest)
    relocated_paths = set(relocated_manifest)
    added = sorted(relocated_paths - source_paths)
    removed = sorted(source_paths - relocated_paths)

    strict_changed: list[dict[str, Any]] = []
    portable_changed: list[dict[str, Any]] = []
    strict_field_counts: Counter[str] = Counter()
    portable_field_counts: Counter[str] = Counter()
    strict_type_counts: Counter[str] = Counter()
    portable_type_counts: Counter[str] = Counter()

    for path in sorted(source_paths & relocated_paths):
        source = source_manifest[path]
        relocated = relocated_manifest[path]

        strict_delta = changed_fields(source, relocated, ENTRY_FIELDS)
        source_portable = portable_fields(source)
        relocated_portable = portable_fields(relocated)
        portable_delta = changed_fields(
            source_portable,
            relocated_portable,
            sorted(set(source_portable) | set(relocated_portable)),
        )

        if strict_delta:
            item = {
                "path": path,
                "strict_changed_fields": strict_delta,
                "portable_changed_fields": portable_delta,
                "source": source,
                "relocated": relocated,
            }
            strict_changed.append(item)
            strict_field_counts.update(strict_delta)
            strict_type_counts.update([source["type"]])

        if portable_delta:
            item = {
                "path": path,
                "strict_changed_fields": strict_delta,
                "portable_changed_fields": portable_delta,
                "source": source,
                "relocated": relocated,
            }
            portable_changed.append(item)
            portable_field_counts.update(portable_delta)
            portable_type_counts.update([source["type"]])

    pycache_paths = sorted(
        path
        for path in relocated_paths
        if path.endswith(".pyc") or "/__pycache__/" in f"/{path}/" or path.endswith("/__pycache__")
    )

    added_type_counts = Counter(
        relocated_manifest[path]["type"] for path in added
    )
    removed_type_counts = Counter(source_manifest[path]["type"] for path in removed)

    summary = {
        "schema_version": 1,
        "source_root": str(source_root),
        "relocated_root": str(relocated_root),
        "source_entry_count": len(source_manifest),
        "relocated_entry_count": len(relocated_manifest),
        "added_count": len(added),
        "removed_count": len(removed),
        "strict_changed_count": len(strict_changed),
        "portable_changed_count": len(portable_changed),
        "strict_pass": not added and not removed and not strict_changed,
        "portable_pass": not added and not removed and not portable_changed,
        "interpretation": {
            "strict": "Replicates the prior metadata-sensitive comparison and includes directory st_size.",
            "portable": "Ignores directory st_size, but requires path/type/mode/mtime equality, regular-file size and content equality, and symlink-target equality.",
        },
        "added_type_counts": dict(sorted(added_type_counts.items())),
        "removed_type_counts": dict(sorted(removed_type_counts.items())),
        "strict_changed_field_counts": dict(sorted(strict_field_counts.items())),
        "portable_changed_field_counts": dict(sorted(portable_field_counts.items())),
        "strict_changed_type_counts": dict(sorted(strict_type_counts.items())),
        "portable_changed_type_counts": dict(sorted(portable_type_counts.items())),
        "pycache_path_count": len(pycache_paths),
        "pycache_paths": pycache_paths,
        "added_paths": added,
        "removed_paths": removed,
        "strict_changed": strict_changed,
        "portable_changed": portable_changed,
    }

    write_jsonl(output_dir / "source-manifest.jsonl", manifest_rows(source_manifest))
    write_jsonl(
        output_dir / "relocated-manifest.jsonl", manifest_rows(relocated_manifest)
    )
    write_json(output_dir / "tree-delta.json", summary)
    write_tsv(output_dir / "tree-delta.tsv", added, removed, portable_changed)

    print(json.dumps(summary, indent=2, sort_keys=True))
    print()
    print(f"Source manifest:    {output_dir / 'source-manifest.jsonl'}")
    print(f"Relocated manifest: {output_dir / 'relocated-manifest.jsonl'}")
    print(f"Delta JSON:         {output_dir / 'tree-delta.json'}")
    print(f"Delta TSV:          {output_dir / 'tree-delta.tsv'}")
    print()
    print(
        "PROMOTED_RELOCATION_PORTABLE_FIDELITY="
        + ("PASS" if summary["portable_pass"] else "FAIL")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
