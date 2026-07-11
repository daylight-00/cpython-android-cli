#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory

DYNAMIC_RE = re.compile(
    r"\((NEEDED|SONAME|RPATH|RUNPATH)\).*?\[(.*?)\]"
)
HEADER_KEYS = {"Class", "Data", "Type", "Machine", "Flags"}


def run_readelf(readelf: str, *args: str, path: Path) -> str:
    return subprocess.run(
        [readelf, *args, str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def elf_surface(readelf: str, path: Path) -> dict:
    header_out = run_readelf(readelf, "-hW", path=path)
    dynamic_out = run_readelf(readelf, "-dW", path=path)
    symbols_out = run_readelf(readelf, "--dyn-syms", "-W", path=path)

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
    dynamic = {key: sorted(values) for key, values in dynamic.items()}

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
            name,
            symbol_type,
            bind,
            visibility,
            "UND" if ndx == "UND" else "DEF",
        ))

    return {
        "header": header,
        "dynamic": dynamic,
        "dynamic_symbols": [list(item) for item in sorted(symbols)],
    }


def read_tsv(path: Path) -> list[dict]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-prefix", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--diff", required=True, type=Path)
    parser.add_argument("--historical-inventory", required=True, type=Path)
    parser.add_argument("--package-inventory", required=True, type=Path)
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    historical_prefix = args.historical_prefix.resolve()
    package = args.package.resolve()
    review = json.loads(args.review.read_text())
    changed_elf_paths = review["changed_elf_paths"]

    historical_inventory = {
        row["relative_path"]: row for row in read_tsv(
            args.historical_inventory
        )
    }
    package_inventory = {
        row["relative_path"]: row for row in read_tsv(args.package_inventory)
    }
    diff_rows = [
        row for row in read_tsv(args.diff)
        if row["status"] == "common_different"
    ]

    non_elf_differences = []
    for row in diff_rows:
        path = row["relative_path"]
        old = historical_inventory[path]
        new = package_inventory[path]
        if old["elf"] != "true" and new["elf"] != "true":
            non_elf_differences.append({
                "relative_path": path,
                "historical_kind": old["kind"],
                "package_kind": new["kind"],
                "historical_size_bytes": int(old["size_bytes"]),
                "package_size_bytes": int(new["size_bytes"]),
                "historical_sha256": old["sha256"],
                "package_sha256": new["sha256"],
            })

    comparisons = {}
    with tarfile.open(package, "r:*") as archive, TemporaryDirectory(
        prefix="stage3b-elf-"
    ) as temp:
        members = {
            member.name.lstrip("./").rstrip("/"): member
            for member in archive.getmembers()
        }
        temp_root = Path(temp)

        for index, rel in enumerate(changed_elf_paths):
            historical_path = historical_prefix / rel
            member_name = f"prefix/{rel}"
            member = members.get(member_name)
            if member is None or not member.isfile():
                raise SystemExit(f"missing package ELF member: {member_name}")
            stream = archive.extractfile(member)
            if stream is None:
                raise SystemExit(f"cannot read package ELF member: {member_name}")
            package_path = temp_root / f"{index}.so"
            with stream, package_path.open("wb") as output:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    output.write(chunk)

            old = elf_surface(args.readelf, historical_path)
            new = elf_surface(args.readelf, package_path)
            checks = {
                "header": old["header"] == new["header"],
                "dynamic": old["dynamic"] == new["dynamic"],
                "dynamic_symbols": (
                    old["dynamic_symbols"] == new["dynamic_symbols"]
                ),
            }
            item = {"checks": checks, "pass": all(checks.values())}
            if not item["pass"]:
                item["historical"] = old
                item["package"] = new
            comparisons[rel] = item

    failed = sorted(
        path for path, item in comparisons.items() if not item["pass"]
    )
    result = {
        "schema_version": 1,
        "changed_elf_count": len(changed_elf_paths),
        "semantic_match_count": len(comparisons) - len(failed),
        "semantic_mismatch_count": len(failed),
        "semantic_mismatch_paths": failed,
        "comparisons": comparisons,
        "non_elf_difference_count": len(non_elf_differences),
        "non_elf_differences": non_elf_differences,
        "pass": len(failed) == 0,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "regenerated-surface-comparison.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Result: {output}")
    print(
        "STAGE3B_REGENERATED_SURFACE_COMPARE="
        + ("PASS" if result["pass"] else "FAIL")
    )
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
