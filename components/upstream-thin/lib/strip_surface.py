#!/usr/bin/env python3
"""ELF section census and recorded safe strip primitives."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Any

from elf import elf_surface

REMOVABLE_SECTION_NAMES = {".symtab", ".strtab"}
REMOVABLE_SECTION_PREFIXES = (".debug", ".zdebug")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def resolve_tool(tool: str) -> Path:
    """Return an absolute invocation path without dereferencing tool aliases.

    LLVM multi-call tools select their interface from argv[0]. In particular,
    Termux exposes ``readelf`` as a symlink to ``llvm-readobj`` and
    ``llvm-strip`` as a symlink to ``llvm-objcopy``. Dereferencing those
    symlinks before execution silently changes command-line and output
    semantics. Identity recording may inspect the canonical target, but the
    executable path used for subprocess invocation must preserve the alias.
    """
    candidate = Path(tool).expanduser()
    if candidate.parent != Path(".") or candidate.is_absolute():
        invocation = candidate if candidate.is_absolute() else Path.cwd() / candidate
        invocation = invocation.absolute()
        if not invocation.is_file():
            raise FileNotFoundError(f"tool not found: {tool}")
        return invocation
    found = shutil.which(tool)
    if not found:
        raise FileNotFoundError(f"tool not found on PATH: {tool}")
    return Path(found).absolute()


def section_names(path: Path, readelf: str = "readelf") -> list[str]:
    readelf_path = resolve_tool(readelf)
    proc = run([str(readelf_path), "-SW", str(path)])
    if proc.returncode:
        raise RuntimeError(f"readelf section census failed for {path}: {proc.stderr.strip()}")
    names: list[str] = []
    for line in proc.stdout.splitlines():
        stripped = line.lstrip()
        if not stripped.startswith("[") or "]" not in stripped:
            continue
        fields = stripped.split("]", 1)[1].strip().split()
        if fields and fields[0].startswith("."):
            names.append(fields[0])
    return names


def is_removable_section(name: str) -> bool:
    return name in REMOVABLE_SECTION_NAMES or name.startswith(REMOVABLE_SECTION_PREFIXES)


def section_census(path: Path, readelf: str = "readelf") -> dict[str, Any]:
    sections = section_names(path, readelf)
    removable = [name for name in sections if is_removable_section(name)]
    return {
        "sections": sections,
        "removable_sections": removable,
        "has_symtab": ".symtab" in sections,
        "has_strtab": ".strtab" in sections,
        "debug_sections": [name for name in sections if name.startswith(REMOVABLE_SECTION_PREFIXES)],
        "eligible": bool(removable),
    }


def tool_identity(tool: str) -> dict[str, Any]:
    invocation_path = resolve_tool(tool)
    canonical_path = invocation_path.resolve()
    proc = run([str(invocation_path), "--version"])
    return {
        "requested": tool,
        "path": str(invocation_path),
        "canonical_path": str(canonical_path),
        "is_symlink": invocation_path.is_symlink(),
        "sha256": sha256_file(invocation_path),
        "size_bytes": invocation_path.stat().st_size,
        "version_returncode": proc.returncode,
        "version_stdout": proc.stdout,
        "version_stderr": proc.stderr,
    }


def strip_one(
    path: Path,
    *,
    strip_tool: str,
    readelf: str = "readelf",
    display_path: str | None = None,
) -> dict[str, Any]:
    strip_path = resolve_tool(strip_tool)
    before_surface = elf_surface(path, readelf)
    before_sections = section_census(path, readelf)
    before_hash = sha256_file(path)
    command = [str(strip_path), "--strip-unneeded", str(path)]
    proc = run(command)
    if proc.returncode:
        raise RuntimeError(f"strip failed for {path}: {proc.stderr.strip()}")
    after_surface = elf_surface(path, readelf)
    after_sections = section_census(path, readelf)
    after_hash = sha256_file(path)
    preserved_keys = ("type", "machine", "needed", "soname", "rpath", "runpath", "load_alignments")
    dynamic_preserved = all(before_surface[key] == after_surface[key] for key in preserved_keys)
    sections_removed = not after_sections["eligible"]
    recorded = display_path or path.name
    return {
        "command": [str(strip_path), "--strip-unneeded", f"<install>/{recorded}"],
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "before": {
            "sha256": before_hash,
            "size_bytes": before_surface["size"],
            "surface": before_surface,
            "section_census": before_sections,
        },
        "after": {
            "sha256": after_hash,
            "size_bytes": after_surface["size"],
            "surface": after_surface,
            "section_census": after_sections,
        },
        "changed": before_hash != after_hash,
        "dynamic_and_alignment_surface_preserved": dynamic_preserved,
        "removable_sections_removed": sections_removed,
    }
