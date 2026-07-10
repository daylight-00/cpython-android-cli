#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import sysconfig
from collections import Counter, defaultdict
from typing import Iterable

ELF_MAGIC = b"\x7fELF"

SYSTEM_ROOTS = [
    Path("/system/lib64"),
    Path("/system/lib"),
    Path("/apex"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_type(mode: int) -> str:
    if stat.S_ISREG(mode):
        return "REGULAR"
    if stat.S_ISDIR(mode):
        return "DIRECTORY"
    if stat.S_ISLNK(mode):
        return "SYMLINK"
    if stat.S_ISCHR(mode):
        return "CHAR"
    if stat.S_ISBLK(mode):
        return "BLOCK"
    if stat.S_ISFIFO(mode):
        return "FIFO"
    if stat.S_ISSOCK(mode):
        return "SOCKET"
    return "OTHER"


def walk_entries(root: Path) -> list[Path]:
    entries: list[Path] = []
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in dirs:
            entries.append(current_path / name)
        for name in files:
            entries.append(current_path / name)
    return sorted(entries, key=lambda p: p.relative_to(root).as_posix())


def inventory_rows(root: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    for path in walk_entries(root):
        st = path.lstat()
        rel = path.relative_to(root).as_posix()
        kind = file_type(st.st_mode)
        digest = ""
        target = ""

        if kind == "REGULAR":
            digest = sha256_file(path)
        elif kind == "SYMLINK":
            target = os.readlink(path)

        rows.append(
            [
                rel,
                kind,
                f"{stat.S_IMODE(st.st_mode):04o}",
                str(st.st_size),
                digest,
                target,
            ]
        )
    return rows


def tree_fingerprint(rows: Iterable[list[str]]) -> str:
    h = hashlib.sha256()
    for row in rows:
        h.update("\t".join(row).encode("utf-8", "surrogateescape"))
        h.update(b"\n")
    return h.hexdigest()


def is_elf(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(4) == ELF_MAGIC
    except OSError:
        return False


def run_readelf(path: Path, args: list[str], errors: list[list[str]]) -> str:
    proc = subprocess.run(
        ["readelf", *args, str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        errors.append(
            [
                str(path),
                "readelf " + " ".join(args),
                str(proc.returncode),
                proc.stderr.strip().replace("\t", "\\t").replace("\n", "\\n"),
            ]
        )
        return ""
    return proc.stdout


def field_from_header(text: str, field: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(field)}:\s*(.+?)\s*$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1) if match else ""


def inspect_elf(path: Path, root: Path, errors: list[list[str]]) -> tuple[list[str], list[str]]:
    header = run_readelf(path, ["-hW"], errors)
    program = run_readelf(path, ["-lW"], errors)
    dynamic = run_readelf(path, ["-dW"], errors)
    notes = run_readelf(path, ["-nW"], errors)

    rel = path.relative_to(root).as_posix()
    elf_class = field_from_header(header, "Class")
    machine = field_from_header(header, "Machine")
    object_type = field_from_header(header, "Type")

    interpreter = ""
    match = re.search(r"Requesting program interpreter:\s*(.*?)\]", program)
    if match:
        interpreter = match.group(1).strip()

    tags: dict[str, list[str]] = defaultdict(list)
    for tag, value in re.findall(
        r"\((NEEDED|SONAME|RPATH|RUNPATH)\).*?\[(.*?)\]",
        dynamic,
    ):
        tags[tag].append(value)

    build_id = ""
    match = re.search(r"Build ID:\s*([0-9A-Fa-f]+)", notes)
    if match:
        build_id = match.group(1)

    object_row = [
        rel,
        elf_class,
        machine,
        object_type,
        interpreter,
        ";".join(tags["SONAME"]),
        ";".join(tags["RPATH"]),
        ";".join(tags["RUNPATH"]),
        build_id,
    ]

    return object_row, tags["NEEDED"]


def write_tsv(path: Path, header: list[str], rows: Iterable[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def index_library_candidates(roots: list[Path]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)

    for root in roots:
        if not root.exists():
            continue
        for current, _, files in os.walk(root, followlinks=False):
            current_path = Path(current)
            for name in files:
                if ".so" not in name:
                    continue
                result[name].append(str(current_path / name))

    return {name: sorted(paths) for name, paths in result.items()}


def python_runtime_identity() -> dict[str, object]:
    selected_config_vars = [
        "SOABI",
        "EXT_SUFFIX",
        "MULTIARCH",
        "LDLIBRARY",
        "LIBDIR",
        "LIBPL",
        "INCLUDEPY",
        "CONFINCLUDEPY",
        "ANDROID_API_LEVEL",
        "HOST_GNU_TYPE",
        "BUILD_GNU_TYPE",
    ]

    return {
        "version": sys.version,
        "version_info": list(sys.version_info),
        "implementation": {
            "name": sys.implementation.name,
            "cache_tag": sys.implementation.cache_tag,
            "version": list(sys.implementation.version),
            "hexversion": sys.implementation.hexversion,
        },
        "platform": sys.platform,
        "executable": sys.executable,
        "prefix": sys.prefix,
        "base_prefix": sys.base_prefix,
        "exec_prefix": sys.exec_prefix,
        "base_exec_prefix": sys.base_exec_prefix,
        "path": list(sys.path),
        "sysconfig_platform": sysconfig.get_platform(),
        "sysconfig_paths": sysconfig.get_paths(),
        "sysconfig_config_vars": {
            key: sysconfig.get_config_var(key) for key in selected_config_vars
        },
        "extension_suffixes": list(importlib.machinery.EXTENSION_SUFFIXES),
        "environment": {
            "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH"),
            "SSL_CERT_FILE": os.environ.get("SSL_CERT_FILE"),
            "PREFIX": os.environ.get("PREFIX"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--termux-prefix", required=True, type=Path)
    args = parser.parse_args()

    runtime_prefix = args.runtime_prefix.resolve()
    output_dir = args.output_dir.resolve()
    termux_prefix = args.termux_prefix.resolve()

    if not runtime_prefix.is_dir():
        parser.error(f"runtime prefix is not a directory: {runtime_prefix}")

    output_dir.mkdir(parents=True, exist_ok=True)

    errors: list[list[str]] = []

    before_rows = inventory_rows(runtime_prefix)
    before_fingerprint = tree_fingerprint(before_rows)

    write_tsv(
        output_dir / "files.tsv",
        ["path", "type", "mode", "size", "sha256", "symlink_target"],
        before_rows,
    )

    symlink_rows = [
        [row[0], row[5]]
        for row in before_rows
        if row[1] == "SYMLINK"
    ]
    write_tsv(
        output_dir / "symlinks.tsv",
        ["path", "target"],
        symlink_rows,
    )

    elf_object_rows: list[list[str]] = []
    needed_rows: list[list[str]] = []

    for path in walk_entries(runtime_prefix):
        try:
            if not path.is_file() or path.is_symlink() or not is_elf(path):
                continue
        except OSError:
            continue

        object_row, needed = inspect_elf(path, runtime_prefix, errors)
        elf_object_rows.append(object_row)
        for name in needed:
            needed_rows.append([object_row[0], name])

    elf_object_rows.sort(key=lambda row: row[0])
    needed_rows.sort(key=lambda row: (row[0], row[1]))

    write_tsv(
        output_dir / "elf-objects.tsv",
        [
            "path",
            "class",
            "machine",
            "object_type",
            "interpreter",
            "soname",
            "rpath",
            "runpath",
            "build_id",
        ],
        elf_object_rows,
    )

    write_tsv(
        output_dir / "elf-needed.tsv",
        ["object_path", "needed"],
        needed_rows,
    )

    with (output_dir / "python-runtime.json").open("w", encoding="utf-8") as f:
        json.dump(
            python_runtime_identity(),
            f,
            indent=2,
            sort_keys=True,
        )
        f.write("\n")

    internal_map: dict[str, list[str]] = defaultdict(list)
    for row in elf_object_rows:
        rel = row[0]
        basename = Path(rel).name
        internal_map[basename].append(rel)
        for soname in filter(None, row[5].split(";")):
            internal_map[soname].append(rel)

    for key in list(internal_map):
        internal_map[key] = sorted(set(internal_map[key]))

    system_map = index_library_candidates(SYSTEM_ROOTS)
    termux_map = index_library_candidates([termux_prefix / "lib"])

    classification_rows: list[list[str]] = []
    unresolved_rows: list[list[str]] = []
    counts: Counter[str] = Counter()

    for object_path, needed in needed_rows:
        if needed in internal_map:
            classification = "RUNTIME_INTERNAL"
            provider = ";".join(internal_map[needed])
        elif needed in system_map:
            classification = "ANDROID_SYSTEM"
            provider = ";".join(system_map[needed])
        elif needed in termux_map:
            classification = "TERMUX_HOST_INTEGRATION"
            provider = ";".join(termux_map[needed])
        else:
            classification = "UNRESOLVED"
            provider = ""

        counts[classification] += 1
        row = [object_path, needed, classification, provider]
        classification_rows.append(row)
        if classification == "UNRESOLVED":
            unresolved_rows.append(row)

    write_tsv(
        output_dir / "closure-classification.tsv",
        ["object_path", "needed", "classification", "provider"],
        classification_rows,
    )

    write_tsv(
        output_dir / "unresolved.tsv",
        ["object_path", "needed", "classification", "provider"],
        unresolved_rows,
    )

    write_tsv(
        output_dir / "errors.tsv",
        ["path", "phase", "returncode", "stderr"],
        errors,
    )

    after_rows = inventory_rows(runtime_prefix)
    after_fingerprint = tree_fingerprint(after_rows)
    mutation_pass = before_fingerprint == after_fingerprint

    with (output_dir / "mutation-check.txt").open("w", encoding="utf-8") as f:
        f.write(f"BEFORE_TREE_SHA256={before_fingerprint}\n")
        f.write(f"AFTER_TREE_SHA256={after_fingerprint}\n")
        f.write(f"MUTATION_CHECK={'PASS' if mutation_pass else 'FAIL'}\n")

    summary = {
        "runtime_prefix": str(runtime_prefix),
        "file_entry_count": len(before_rows),
        "symlink_count": len(symlink_rows),
        "elf_object_count": len(elf_object_rows),
        "needed_edge_count": len(needed_rows),
        "classification_counts": dict(sorted(counts.items())),
        "unresolved_edge_count": len(unresolved_rows),
        "inspection_error_count": len(errors),
        "mutation_check": "PASS" if mutation_pass else "FAIL",
    }

    with (output_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if mutation_pass else 3


if __name__ == "__main__":
    raise SystemExit(main())
