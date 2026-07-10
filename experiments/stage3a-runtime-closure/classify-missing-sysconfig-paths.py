#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def classify(path: str, key: str) -> str:
    if path.startswith("/Users/runner/work/release-tools/"):
        return "BUILD_WORKSPACE_RESIDUE"
    if path.startswith("/Users/runner/Library/Android/sdk/ndk/"):
        return "TOOLCHAIN_RESIDUE"
    if path.startswith("/data/data/com.termux/files/home/.local/"):
        return "USER_SCHEME_DESTINATION"
    if path == "/usr/bin/install":
        return "HOST_BUILD_TOOL_RESIDUE"
    if key == "TZPATH" and path in {
        "/usr/share/zoneinfo",
        "/usr/lib/zoneinfo",
        "/usr/share/lib/zoneinfo",
        "/etc/zoneinfo",
    }:
        return "TZDATA_SEARCH_PATH_METADATA"
    return "UNKNOWN"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    args = parser.parse_args()

    results_dir = args.results_dir.resolve()
    input_tsv = results_dir / "sysconfig-missing-other-absolute.tsv"
    if not input_tsv.is_file():
        parser.error(f"missing triage input: {input_tsv}")

    rows = read_tsv(input_tsv)
    classified_rows: list[list[str]] = []
    record_counts: Counter[str] = Counter()
    unique_paths: dict[str, set[str]] = {}

    for row in rows:
        path = row["path_candidate"]
        key = row["key"]
        category = classify(path, key)
        record_counts[category] += 1
        unique_paths.setdefault(category, set()).add(path)
        classified_rows.append(
            [
                row["source_type"],
                key,
                path,
                category,
                row["raw_value"],
            ]
        )

    classified_rows.sort(key=lambda r: (r[3], r[2], r[1]))

    write_tsv(
        results_dir / "sysconfig-missing-other-classified.tsv",
        ["source_type", "key", "path_candidate", "category", "raw_value"],
        classified_rows,
    )

    category_rows = [
        [category, str(record_counts[category]), str(len(unique_paths[category]))]
        for category in sorted(record_counts)
    ]
    write_tsv(
        results_dir / "sysconfig-missing-other-category-counts.tsv",
        ["category", "record_count", "unique_path_count"],
        category_rows,
    )

    summary = {
        "record_count": len(rows),
        "unique_path_count": len({row["path_candidate"] for row in rows}),
        "category_record_counts": dict(sorted(record_counts.items())),
        "category_unique_path_counts": {
            category: len(paths)
            for category, paths in sorted(unique_paths.items())
        },
        "unknown_record_count": record_counts.get("UNKNOWN", 0),
        "unknown_unique_path_count": len(unique_paths.get("UNKNOWN", set())),
    }

    with (results_dir / "sysconfig-missing-other-classification-summary.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["unknown_record_count"] == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())
