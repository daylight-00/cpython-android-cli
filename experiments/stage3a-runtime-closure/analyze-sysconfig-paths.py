#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def top_prefix(path: str, depth: int = 3) -> str:
    p = PurePosixPath(path)
    parts = p.parts
    if not parts:
        return path
    if parts[0] != "/":
        return path
    return "/" + "/".join(parts[1 : 1 + depth])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    args = parser.parse_args()

    results_dir = args.results_dir.resolve()
    input_tsv = results_dir / "sysconfig-absolute-paths.tsv"

    if not input_tsv.is_file():
        parser.error(f"missing sysconfig path census: {input_tsv}")

    rows = read_tsv(input_tsv)

    by_class: Counter[str] = Counter()
    by_class_exists: Counter[tuple[str, str]] = Counter()
    by_source_key: Counter[tuple[str, str, str]] = Counter()
    by_other_prefix: Counter[str] = Counter()
    by_residue_key: Counter[tuple[str, str]] = Counter()
    unique_paths_by_class: dict[str, set[str]] = defaultdict(set)

    other_rows: list[list[str]] = []
    residue_rows: list[list[str]] = []

    for row in rows:
        classification = row["classification"]
        exists = row["exists"]
        source_type = row["source_type"]
        key = row["key"]
        path_candidate = row["path_candidate"]

        by_class[classification] += 1
        by_class_exists[(classification, exists)] += 1
        by_source_key[(classification, source_type, key)] += 1
        unique_paths_by_class[classification].add(path_candidate)

        if classification == "OTHER_ABSOLUTE":
            prefix = top_prefix(path_candidate)
            by_other_prefix[prefix] += 1
            other_rows.append(
                [
                    source_type,
                    key,
                    path_candidate,
                    exists,
                    prefix,
                    row["raw_value"],
                ]
            )

        if classification == "BUILD_PREFIX_RESIDUE":
            by_residue_key[(source_type, key)] += 1
            residue_rows.append(
                [
                    source_type,
                    key,
                    path_candidate,
                    exists,
                    row["raw_value"],
                ]
            )

    write_tsv(
        results_dir / "sysconfig-other-absolute-analysis.tsv",
        [
            "source_type",
            "key",
            "path_candidate",
            "exists",
            "top_prefix",
            "raw_value",
        ],
        sorted(other_rows, key=lambda r: (r[4], r[0], r[1], r[2])),
    )

    write_tsv(
        results_dir / "sysconfig-build-residue-analysis.tsv",
        ["source_type", "key", "path_candidate", "exists", "raw_value"],
        sorted(residue_rows, key=lambda r: (r[0], r[1], r[2])),
    )

    prefix_rows = [
        [prefix, str(count)]
        for prefix, count in sorted(
            by_other_prefix.items(), key=lambda item: (-item[1], item[0])
        )
    ]
    write_tsv(
        results_dir / "sysconfig-other-prefix-counts.tsv",
        ["top_prefix", "record_count"],
        prefix_rows,
    )

    residue_key_rows = [
        [source_type, key, str(count)]
        for (source_type, key), count in sorted(
            by_residue_key.items(), key=lambda item: (-item[1], item[0])
        )
    ]
    write_tsv(
        results_dir / "sysconfig-build-residue-key-counts.tsv",
        ["source_type", "key", "record_count"],
        residue_key_rows,
    )

    source_key_rows = [
        [classification, source_type, key, str(count)]
        for (classification, source_type, key), count in sorted(
            by_source_key.items(), key=lambda item: (item[0][0], -item[1], item[0][1], item[0][2])
        )
    ]
    write_tsv(
        results_dir / "sysconfig-path-key-counts.tsv",
        ["classification", "source_type", "key", "record_count"],
        source_key_rows,
    )

    summary = {
        "record_counts": dict(sorted(by_class.items())),
        "unique_path_counts": {
            key: len(value)
            for key, value in sorted(unique_paths_by_class.items())
        },
        "exists_counts": {
            f"{classification}:{exists}": count
            for (classification, exists), count in sorted(by_class_exists.items())
        },
        "other_absolute_top_prefix_count": len(by_other_prefix),
        "build_residue_key_count": len(by_residue_key),
    }

    with (results_dir / "sysconfig-path-analysis-summary.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
