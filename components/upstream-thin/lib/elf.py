#!/usr/bin/env python3
"""LR-3 ELF mutation and verification primitives."""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Any

DYNAMIC_RE = re.compile(r"\((NEEDED|SONAME|RPATH|RUNPATH)\).*\[(.*)\]")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_elf(path: Path) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    with path.open("rb") as stream:
        return stream.read(4) == b"\x7fELF"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def elf_surface(path: Path, readelf: str = "readelf") -> dict[str, Any]:
    header = run([readelf, "-h", str(path)])
    dynamic = run([readelf, "-d", str(path)])
    loads = run([readelf, "-lW", str(path)])
    if header.returncode or dynamic.returncode or loads.returncode:
        raise RuntimeError(f"readelf failed for {path}: {header.stderr}{dynamic.stderr}{loads.stderr}")
    kind = machine = ""
    for line in header.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Type:"):
            kind = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Machine:"):
            machine = stripped.split(":", 1)[1].strip()
    tags: dict[str, list[str]] = {key: [] for key in ("NEEDED", "SONAME", "RPATH", "RUNPATH")}
    for line in dynamic.stdout.splitlines():
        match = DYNAMIC_RE.search(line)
        if match:
            tags[match.group(1)].append(match.group(2))
    alignments: list[int] = []
    for line in loads.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("LOAD "):
            try:
                alignments.append(int(stripped.split()[-1], 0))
            except ValueError:
                pass
    return {
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
        "type": kind,
        "machine": machine,
        "needed": tags["NEEDED"],
        "soname": tags["SONAME"],
        "rpath": tags["RPATH"],
        "runpath": tags["RUNPATH"],
        "load_alignments": alignments,
    }


def relative_runpath(object_path: Path, libdir: Path) -> str:
    rel = os.path.relpath(libdir, object_path.parent)
    return "$ORIGIN" if rel == "." else "$ORIGIN/" + rel.replace(os.sep, "/")


def alignment_policy(before: list[int], after: list[int]) -> dict[str, Any]:
    before_ok = bool(before) and all(value == 0x4000 for value in before)
    after_ok = bool(after) and all(value == 0x4000 for value in after)
    count_ok = len(after) >= len(before)
    return {
        "before_load_count": len(before),
        "after_load_count": len(after),
        "before_all_16k": before_ok,
        "after_all_16k": after_ok,
        "load_count_not_reduced": count_ok,
        "preserved": before_ok and after_ok and count_ok,
    }


def patch_lr3(install: Path, patchelf: str = "patchelf", readelf: str = "readelf") -> list[dict[str, Any]]:
    libdir = install / "lib"
    rows: list[dict[str, Any]] = []
    objects = [path for path in sorted(install.rglob("*")) if is_elf(path)]
    if not objects:
        raise RuntimeError("no ELF objects found in release-mode install tree")
    help_result = run([patchelf, "--help"])
    if "--page-size" not in (help_result.stdout + help_result.stderr):
        raise RuntimeError("patchelf lacks required --page-size support")
    for path in objects:
        before = elf_surface(path, readelf)
        expected = relative_runpath(path, libdir)
        command = [patchelf, "--page-size", "16384", "--set-rpath", expected, str(path)]
        mutation = run(command)
        if mutation.returncode:
            raise RuntimeError(f"patchelf failed for {path}: {mutation.stderr.strip()}")
        after = elf_surface(path, readelf)
        alignment = alignment_policy(before["load_alignments"], after["load_alignments"])
        exact = (
            before["type"] == after["type"]
            and before["machine"] == after["machine"]
            and before["needed"] == after["needed"]
            and before["soname"] == after["soname"]
            and before["rpath"] == after["rpath"]
            and after["runpath"] == [expected]
            and alignment["preserved"]
        )
        rows.append({
            "path": path.relative_to(install).as_posix(),
            "reason": "complete-per-object-relative-native-closure",
            "command": command[:-1] + ["<install>/" + path.relative_to(install).as_posix()],
            "expected_runpath": expected,
            "before": before,
            "after": after,
            "alignment_policy": alignment,
            "exact_mutation_check": exact,
        })
        if not exact:
            raise RuntimeError(f"LR-3 exact mutation verification failed: {path}")
    return rows
