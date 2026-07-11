#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def read_tsv(path: Path) -> list[dict]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def index_inventory(path: Path) -> dict[str, dict]:
    return {row["relative_path"]: row for row in read_tsv(path)}


def top_level(path: str) -> str:
    return path.split("/", 1)[0]


def suffix(path: str) -> str:
    name = Path(path).name
    if ".so." in name:
        return ".so.*"
    return Path(name).suffix or "<none>"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-inventory", required=True, type=Path)
    parser.add_argument("--package-inventory", required=True, type=Path)
    parser.add_argument("--diff", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    historical = index_inventory(args.historical_inventory)
    package = index_inventory(args.package_inventory)
    differences = [
        row for row in read_tsv(args.diff)
        if row["status"] != "common_exact"
    ]

    classes = Counter()
    levels = Counter()
    changed_suffixes = Counter()
    only_historical = []
    only_package = []
    changed_elf_paths = []
    changed_symlink_paths = []
    kind_change_paths = []

    for row in differences:
        path = row["relative_path"]
        status = row["status"]
        old = historical.get(path)
        new = package.get(path)
        levels[top_level(path)] += 1

        if status == "only_historical":
            cls = "ONLY_HISTORICAL"
            only_historical.append(path)
        elif status == "only_package":
            cls = "ONLY_PACKAGE"
            only_package.append(path)
        elif old["kind"] != new["kind"]:
            cls = "KIND_CHANGE"
            kind_change_paths.append(path)
        elif old["kind"] == "file":
            changed_suffixes[suffix(path)] += 1
            if old["elf"] == "true" or new["elf"] == "true":
                cls = "ELF_CONTENT_DIFFERENCE"
                changed_elf_paths.append(path)
            else:
                cls = "FILE_CONTENT_DIFFERENCE"
        elif old["kind"] == "symlink":
            cls = "SYMLINK_TARGET_DIFFERENCE"
            changed_symlink_paths.append(path)
        else:
            cls = "NON_FILE_IDENTITY_DIFFERENCE"
        classes[cls] += 1

    result = {
        "schema_version": 1,
        "difference_count": len(differences),
        "mechanical_class_counts": dict(sorted(classes.items())),
        "top_level_counts": dict(sorted(levels.items())),
        "changed_file_suffix_counts": dict(sorted(changed_suffixes.items())),
        "only_historical_paths": sorted(only_historical),
        "only_package_paths": sorted(only_package),
        "changed_elf_count": len(changed_elf_paths),
        "changed_elf_paths": sorted(changed_elf_paths),
        "changed_symlink_paths": sorted(changed_symlink_paths),
        "kind_change_paths": sorted(kind_change_paths),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Result: {args.output}")
    print("STAGE3B_PACKAGE_DIFF_REVIEW=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
