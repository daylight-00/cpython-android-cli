#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
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
    classification_path = results_dir / "closure-classification.tsv"

    if not classification_path.is_file():
        parser.error(f"missing closure classification: {classification_path}")

    rows = read_tsv(classification_path)

    by_needed: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_object: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in rows:
        by_needed[row["needed"]].append(row)
        by_object[row["object_path"]].append(row)

    needed_rows: list[list[str]] = []
    ambiguous_rows: list[list[str]] = []

    for needed in sorted(by_needed):
        group = by_needed[needed]
        classifications = sorted({row["classification"] for row in group})
        objects = sorted({row["object_path"] for row in group})
        providers = sorted(
            {
                provider
                for row in group
                for provider in row["provider"].split(";")
                if provider
            }
        )

        needed_row = [
            needed,
            ";".join(classifications),
            str(len(group)),
            str(len(objects)),
            str(len(providers)),
            ";".join(providers),
        ]
        needed_rows.append(needed_row)

        if len(classifications) != 1 or len(providers) > 1:
            ambiguous_rows.append(needed_row)

    object_rows: list[list[str]] = []
    for object_path in sorted(by_object):
        group = by_object[object_path]
        classifications: dict[str, int] = defaultdict(int)
        for row in group:
            classifications[row["classification"]] += 1

        object_rows.append(
            [
                object_path,
                str(len(group)),
                json.dumps(dict(sorted(classifications.items())), sort_keys=True),
            ]
        )

    write_tsv(
        results_dir / "needed-sonames.tsv",
        [
            "needed",
            "classifications",
            "edge_count",
            "object_count",
            "provider_count",
            "providers",
        ],
        needed_rows,
    )

    write_tsv(
        results_dir / "provider-ambiguity.tsv",
        [
            "needed",
            "classifications",
            "edge_count",
            "object_count",
            "provider_count",
            "providers",
        ],
        ambiguous_rows,
    )

    write_tsv(
        results_dir / "object-dependency-counts.tsv",
        ["object_path", "needed_edge_count", "classification_counts_json"],
        object_rows,
    )

    classification_counts: dict[str, int] = defaultdict(int)
    unique_by_classification: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        classification_counts[row["classification"]] += 1
        unique_by_classification[row["classification"]].add(row["needed"])

    summary = {
        "needed_edge_count": len(rows),
        "unique_needed_soname_count": len(by_needed),
        "classification_edge_counts": dict(sorted(classification_counts.items())),
        "classification_unique_soname_counts": {
            key: len(value)
            for key, value in sorted(unique_by_classification.items())
        },
        "ambiguous_provider_soname_count": len(ambiguous_rows),
        "object_count_with_needed_edges": len(by_object),
    }

    with (results_dir / "closure-analysis-summary.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
