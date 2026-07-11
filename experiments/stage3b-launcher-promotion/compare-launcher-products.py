#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

DYNAMIC_RE = re.compile(
    r"\((NEEDED|SONAME|RPATH|RUNPATH)\).*?\[(.*?)\]"
)
HEADER_KEYS = {"Class", "Data", "Type", "Machine", "Flags"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def readelf(readelf_bin: str, *args: str, path: Path) -> str:
    return subprocess.run(
        [readelf_bin, *args, str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def surface(readelf_bin: str, path: Path) -> dict:
    header_out = readelf(readelf_bin, "-hW", path=path)
    dynamic_out = readelf(readelf_bin, "-dW", path=path)
    symbols_out = readelf(
        readelf_bin, "--dyn-syms", "-W", path=path
    )

    header = {}
    for line in header_out.splitlines():
        if ":" not in line:
            continue
        key, value = line.strip().split(":", 1)
        if key in HEADER_KEYS:
            header[key] = value.strip()

    dynamic = {"NEEDED": [], "SONAME": [], "RPATH": [], "RUNPATH": []}
    for line in dynamic_out.splitlines():
        match = DYNAMIC_RE.search(line)
        if match:
            dynamic[match.group(1)].append(match.group(2))
    dynamic = {key: sorted(value) for key, value in dynamic.items()}

    symbols = set()
    for line in symbols_out.splitlines():
        fields = line.split(None, 7)
        if len(fields) != 8 or not fields[0].rstrip(":").isdigit():
            continue
        _, _, _, symbol_type, bind, visibility, ndx, name = fields
        if bind not in {"GLOBAL", "WEAK", "UNIQUE"}:
            continue
        name = re.sub(r"\s+\(\d+\)$", "", name)
        symbols.add((
            name, symbol_type, bind, visibility,
            "UND" if ndx == "UND" else "DEF",
        ))

    return {
        "header": header,
        "dynamic": dynamic,
        "dynamic_symbols": [list(value) for value in sorted(symbols)],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical", required=True, type=Path)
    parser.add_argument("--promoted", required=True, type=Path)
    parser.add_argument("--historical-build-info", required=True, type=Path)
    parser.add_argument("--promoted-build-info", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--readelf", default="readelf")
    args = parser.parse_args()

    old_surface = surface(args.readelf, args.historical)
    new_surface = surface(args.readelf, args.promoted)
    checks = {
        "header": old_surface["header"] == new_surface["header"],
        "dynamic": old_surface["dynamic"] == new_surface["dynamic"],
        "dynamic_symbols": (
            old_surface["dynamic_symbols"]
            == new_surface["dynamic_symbols"]
        ),
    }
    result = {
        "schema_version": 1,
        "historical": {
            "path": str(args.historical.resolve()),
            "size_bytes": args.historical.stat().st_size,
            "sha256": sha256(args.historical),
            "build_info": str(args.historical_build_info.resolve()),
        },
        "promoted": {
            "path": str(args.promoted.resolve()),
            "size_bytes": args.promoted.stat().st_size,
            "sha256": sha256(args.promoted),
            "build_info": str(args.promoted_build_info.resolve()),
        },
        "exact_byte_match": sha256(args.historical) == sha256(args.promoted),
        "semantic_checks": checks,
        "pass": all(checks.values()),
    }
    if not result["pass"]:
        result["historical_surface"] = old_surface
        result["promoted_surface"] = new_surface

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Result: {args.output}")
    print(
        "STAGE3B_PROMOTED_LAUNCHER_COMPARE="
        + ("PASS" if result["pass"] else "FAIL")
    )
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
