#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    args = parser.parse_args()

    results_dir = args.results_dir.resolve()
    input_tsv = results_dir / "sysconfig-absolute-paths.tsv"

    if not input_tsv.is_file():
        parser.error(f"missing sysconfig path census: {input_tsv}")

    rows = read_tsv(input_tsv)

    existing_other: list[list[str]] = []
    missing_other: list[list[str]] = []
    missing_runtime: list[list[str]] = []

    missing_other_prefix_counts: Counter[str] = Counter()
    missing_other_key_counts: Counter[tuple[str, str]] = Counter()
    existing_other_key_counts: Counter[tuple[str, str]] = Counter()
    missing_runtime_key_counts: Counter[tuple[str, str]] = Counter()

    unique_other_paths: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "exists": "no",
            "keys": set(),
            "source_types": set(),
            "record_count": 0,
        }
    )

    for row in rows:
        classification = row["classification"]
        exists = row["exists"]
        source_type = row["source_type"]
        key = row["key"]
        path = row["path_candidate"]
        raw_value = row["raw_value"]

        if classification == "OTHER_ABSOLUTE":
            entry = unique_other_paths[path]
            entry["record_count"] = int(entry["record_count"]) + 1
            entry["keys"].add(key)
            entry["source_types"].add(source_type)
            if exists == "yes":
                entry["exists"] = "yes"

            out_row = [source_type, key, path, raw_value]
            if exists == "yes":
                existing_other.append(out_row)
                existing_other_key_counts[(source_type, key)] += 1
            else:
                missing_other.append(out_row)
                missing_other_key_counts[(source_type, key)] += 1
                parts = Path(path).parts
                prefix = "/" + "/".join(parts[1:4]) if len(parts) > 1 else path
                missing_other_prefix_counts[prefix] += 1

        if classification == "RUNTIME_PREFIX" and exists == "no":
            missing_runtime.append([source_type, key, path, raw_value])
            missing_runtime_key_counts[(source_type, key)] += 1

    write_tsv(
        results_dir / "sysconfig-existing-other-absolute.tsv",
        ["source_type", "key", "path_candidate", "raw_value"],
        sorted(existing_other, key=lambda r: (r[2], r[0], r[1])),
    )

    write_tsv(
        results_dir / "sysconfig-missing-other-absolute.tsv",
        ["source_type", "key", "path_candidate", "raw_value"],
        sorted(missing_other, key=lambda r: (r[2], r[0], r[1])),
    )

    write_tsv(
        results_dir / "sysconfig-missing-runtime-prefix.tsv",
        ["source_type", "key", "path_candidate", "raw_value"],
        sorted(missing_runtime, key=lambda r: (r[2], r[0], r[1])),
    )

    write_tsv(
        results_dir / "sysconfig-missing-other-prefix-counts.tsv",
        ["prefix", "record_count"],
        [
            [prefix, str(count)]
            for prefix, count in sorted(
                missing_other_prefix_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    )

    write_tsv(
        results_dir / "sysconfig-missing-other-key-counts.tsv",
        ["source_type", "key", "record_count"],
        [
            [source_type, key, str(count)]
            for (source_type, key), count in sorted(
                missing_other_key_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    )

    write_tsv(
        results_dir / "sysconfig-existing-other-key-counts.tsv",
        ["source_type", "key", "record_count"],
        [
            [source_type, key, str(count)]
            for (source_type, key), count in sorted(
                existing_other_key_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    )

    write_tsv(
        results_dir / "sysconfig-missing-runtime-key-counts.tsv",
        ["source_type", "key", "record_count"],
        [
            [source_type, key, str(count)]
            for (source_type, key), count in sorted(
                missing_runtime_key_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    )

    unique_rows: list[list[str]] = []
    for path, data in sorted(unique_other_paths.items()):
        unique_rows.append(
            [
                path,
                str(data["exists"]),
                str(data["record_count"]),
                ";".join(sorted(data["source_types"])),
                ";".join(sorted(data["keys"])),
            ]
        )

    write_tsv(
        results_dir / "sysconfig-unique-other-paths.tsv",
        ["path_candidate", "exists", "record_count", "source_types", "keys"],
        unique_rows,
    )

    summary = {
        "existing_other_record_count": len(existing_other),
        "missing_other_record_count": len(missing_other),
        "unique_other_path_count": len(unique_other_paths),
        "unique_existing_other_path_count": sum(
            1 for data in unique_other_paths.values() if data["exists"] == "yes"
        ),
        "unique_missing_other_path_count": sum(
            1 for data in unique_other_paths.values() if data["exists"] == "no"
        ),
        "missing_runtime_prefix_record_count": len(missing_runtime),
        "missing_other_prefix_group_count": len(missing_other_prefix_counts),
    }

    with (results_dir / "sysconfig-path-triage-summary.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
