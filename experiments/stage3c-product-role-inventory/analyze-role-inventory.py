#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

INVENTORY_FIELDS = (
    "path",
    "type",
    "mode",
    "size",
    "mtime_ns",
    "sha256",
    "symlink_target",
    "elf",
    "role",
    "rule_id",
    "reason",
    "descendant_roles",
    "mixed_directory",
)

ROLES = (
    "RUNTIME",
    "DEVELOPMENT",
    "METADATA",
    "LICENSE",
    "DEBUG_OR_OPTIONAL",
    "UNKNOWN",
)

OPTIONAL_COMPONENTS = {
    "test",
    "tests",
    "idlelib",
    "turtledemo",
    "tkinter",
    "__phello__",
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON value is not an object: {path}")
    return value


def read_inventory(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        fields = tuple(reader.fieldnames or ())
        if fields != INVENTORY_FIELDS:
            raise ValueError(
                f"inventory schema mismatch: expected={INVENTORY_FIELDS!r} observed={fields!r}"
            )
        return list(reader)


def write_tsv(path: Path, fields: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    field_list = list(fields)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=field_list,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def integer(row: dict[str, str], key: str) -> int:
    return int(row[key])


def regular_file_bytes(rows: Iterable[dict[str, str]]) -> int:
    return sum(
        integer(row, "size")
        for row in rows
        if row["type"] == "REGULAR"
    )


def count_types(rows: Iterable[dict[str, str]]) -> Counter[str]:
    return Counter(row["type"] for row in rows)


def aggregate(
    rows: list[dict[str, str]],
    keys: tuple[str, ...],
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        buckets[tuple(row[key] for key in keys)].append(row)

    output: list[dict[str, Any]] = []
    for key_values, bucket in sorted(buckets.items()):
        types = count_types(bucket)
        item: dict[str, Any] = dict(zip(keys, key_values))
        item.update(
            {
                "entry_count": len(bucket),
                "regular_file_count": types.get("REGULAR", 0),
                "directory_count": types.get("DIRECTORY", 0),
                "symlink_count": types.get("SYMLINK", 0),
                "file_bytes": regular_file_bytes(bucket),
            }
        )
        output.append(item)
    return output


def top_level(path: str) -> str:
    parts = PurePosixPath(path).parts
    return parts[0] if parts else "<root>"


def python_subtree(path: str) -> str:
    parts = PurePosixPath(path).parts
    if len(parts) < 2 or parts[:2] != ("lib", "python3.14"):
        return "<outside-python-tree>"
    if len(parts) == 2:
        return "<python-root>"
    return parts[2]


def optional_root(path: str, rule_id: str) -> tuple[str, str]:
    parts = PurePosixPath(path).parts
    lower_parts = tuple(part.lower() for part in parts)
    if rule_id == "debug-surface":
        for index, part in enumerate(lower_parts):
            if part in {"debug", "symbols", ".debug"}:
                return part, "/".join(parts[: index + 1])
        return "debug-file", path
    for index, part in enumerate(lower_parts):
        if part in OPTIONAL_COMPONENTS:
            return part, "/".join(parts[: index + 1])
    return "unmatched-optional", path


def development_surface(path: str, rule_id: str) -> str:
    parts = PurePosixPath(path).parts
    name = PurePosixPath(path).name.lower()
    if parts and parts[0] == "include":
        return "include"
    if len(parts) >= 2 and parts[:2] == ("lib", "pkgconfig"):
        return "lib/pkgconfig"
    if len(parts) >= 3 and parts[0] == "lib" and parts[1] == "python3.14" and parts[2].startswith("config-"):
        return "lib/python3.14/config-*"
    if name.endswith((".a", ".la")):
        return "static-or-libtool-library"
    return f"other:{rule_id}"


def runtime_surface(path: str, rule_id: str) -> str:
    parts = PurePosixPath(path).parts
    name = PurePosixPath(path).name
    if parts and parts[0] == "bin":
        return "bin"
    if path == "lib/libpython3.14.so" or name.startswith("libpython3.14.so"):
        return "libpython"
    if len(parts) >= 3 and parts[:3] == ("lib", "python3.14", "lib-dynload"):
        return "lib-dynload"
    if len(parts) >= 2 and parts[:2] == ("lib", "python3.14"):
        return "stdlib-and-runtime-data"
    if parts and parts[0] == "lib":
        return "lib-runtime"
    return f"other:{rule_id}"


def inventory_hash(rows: list[dict[str, str]]) -> str:
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item["path"]):
        digest.update(
            "\t".join(row[field] for field in INVENTORY_FIELDS).encode(
                "utf-8",
                "surrogateescape",
            )
        )
        digest.update(b"\n")
    return digest.hexdigest()


def percent(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return round(part * 100.0 / whole, 4)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--expected-entry-count", required=True, type=int)
    parser.add_argument("--expected-elf-count", required=True, type=int)
    parser.add_argument("--expected-symlink-count", required=True, type=int)
    args = parser.parse_args()

    results_dir = args.results_dir.resolve()
    inventory_path = results_dir / "product-role-inventory.tsv"
    summary_path = results_dir / "role-summary.json"

    if not inventory_path.is_file():
        raise SystemExit(f"missing inventory: {inventory_path}")
    if not summary_path.is_file():
        raise SystemExit(f"missing summary: {summary_path}")

    rows = read_inventory(inventory_path)
    summary = read_json(summary_path)

    observed_manifest = inventory_hash(rows)
    role_counts = Counter(row["role"] for row in rows)
    type_counts = Counter(row["type"] for row in rows)
    role_bytes: Counter[str] = Counter()
    role_regular_counts: Counter[str] = Counter()
    elf_count = 0
    for row in rows:
        if row["type"] == "REGULAR":
            role_bytes[row["role"]] += integer(row, "size")
            role_regular_counts[row["role"]] += 1
        if row["elf"] == "true":
            elf_count += 1

    total_file_bytes = sum(role_bytes.values())
    role_overview = []
    for role in ROLES:
        role_overview.append(
            {
                "role": role,
                "entry_count": role_counts.get(role, 0),
                "regular_file_count": role_regular_counts.get(role, 0),
                "file_bytes": role_bytes.get(role, 0),
                "entry_percent": percent(role_counts.get(role, 0), len(rows)),
                "file_byte_percent": percent(role_bytes.get(role, 0), total_file_bytes),
            }
        )

    rule_rows = aggregate(rows, ("role", "rule_id"))
    type_rows = aggregate(rows, ("role", "type"))

    top_rows_input = [dict(row, top_level=top_level(row["path"])) for row in rows]
    top_rows = aggregate(top_rows_input, ("role", "top_level"))

    python_rows_input = [
        dict(row, python_subtree=python_subtree(row["path"]))
        for row in rows
    ]
    python_rows = aggregate(python_rows_input, ("role", "python_subtree"))

    optional_input = []
    for row in rows:
        if row["role"] != "DEBUG_OR_OPTIONAL":
            continue
        component, root = optional_root(row["path"], row["rule_id"])
        optional_input.append(
            dict(row, optional_component=component, optional_root=root)
        )
    optional_component_rows = aggregate(
        optional_input,
        ("optional_component",),
    )
    optional_root_rows = aggregate(
        optional_input,
        ("optional_component", "optional_root"),
    )

    development_input = [
        dict(
            row,
            development_surface=development_surface(
                row["path"],
                row["rule_id"],
            ),
        )
        for row in rows
        if row["role"] == "DEVELOPMENT"
    ]
    development_rows = aggregate(
        development_input,
        ("development_surface",),
    )

    runtime_input = [
        dict(
            row,
            runtime_surface=runtime_surface(row["path"], row["rule_id"]),
        )
        for row in rows
        if row["role"] == "RUNTIME"
    ]
    runtime_rows = aggregate(runtime_input, ("runtime_surface",))

    boundary_rows = [
        row
        for row in rows
        if row["role"] in {"LICENSE", "METADATA"}
        or row["type"] == "SYMLINK"
    ]
    largest_rows = sorted(
        (row for row in rows if row["type"] == "REGULAR"),
        key=lambda row: (-integer(row, "size"), row["path"]),
    )[:100]

    aggregate_fields = (
        "entry_count",
        "regular_file_count",
        "directory_count",
        "symlink_count",
        "file_bytes",
    )
    write_tsv(
        results_dir / "role-overview.tsv",
        (
            "role",
            "entry_count",
            "regular_file_count",
            "file_bytes",
            "entry_percent",
            "file_byte_percent",
        ),
        role_overview,
    )
    write_tsv(
        results_dir / "role-by-rule.tsv",
        ("role", "rule_id", *aggregate_fields),
        rule_rows,
    )
    write_tsv(
        results_dir / "role-by-type.tsv",
        ("role", "type", *aggregate_fields),
        type_rows,
    )
    write_tsv(
        results_dir / "role-by-top-level.tsv",
        ("role", "top_level", *aggregate_fields),
        top_rows,
    )
    write_tsv(
        results_dir / "python-subtree-summary.tsv",
        ("role", "python_subtree", *aggregate_fields),
        python_rows,
    )
    write_tsv(
        results_dir / "optional-component-summary.tsv",
        ("optional_component", *aggregate_fields),
        optional_component_rows,
    )
    write_tsv(
        results_dir / "optional-root-summary.tsv",
        ("optional_component", "optional_root", *aggregate_fields),
        optional_root_rows,
    )
    write_tsv(
        results_dir / "development-surface-summary.tsv",
        ("development_surface", *aggregate_fields),
        development_rows,
    )
    write_tsv(
        results_dir / "runtime-surface-summary.tsv",
        ("runtime_surface", *aggregate_fields),
        runtime_rows,
    )
    write_tsv(
        results_dir / "selected-boundary-rows.tsv",
        INVENTORY_FIELDS,
        boundary_rows,
    )
    write_tsv(
        results_dir / "largest-regular-files.tsv",
        INVENTORY_FIELDS,
        largest_rows,
    )

    summary_role_counts = summary.get("role_counts", {})
    summary_type_counts = summary.get("type_counts", {})
    summary_role_bytes = summary.get("file_bytes_by_role", {})

    checks = {
        "manifest_matches_expected": observed_manifest
        == args.expected_manifest_sha256,
        "manifest_matches_summary": observed_manifest
        == summary.get("manifest_sha256"),
        "entry_count_matches_expected": len(rows)
        == args.expected_entry_count,
        "entry_count_matches_summary": len(rows)
        == summary.get("entry_count"),
        "elf_count_matches_expected": elf_count == args.expected_elf_count,
        "elf_count_matches_summary": elf_count == summary.get("elf_count"),
        "symlink_count_matches_expected": type_counts.get("SYMLINK", 0)
        == args.expected_symlink_count,
        "role_counts_match_summary": dict(sorted(role_counts.items()))
        == summary_role_counts,
        "type_counts_match_summary": dict(sorted(type_counts.items()))
        == summary_type_counts,
        "role_bytes_match_summary": dict(sorted(role_bytes.items()))
        == summary_role_bytes,
        "unknown_zero": role_counts.get("UNKNOWN", 0) == 0,
        "optional_decomposition_complete": sum(
            row["entry_count"] for row in optional_component_rows
        )
        == role_counts.get("DEBUG_OR_OPTIONAL", 0),
        "optional_byte_decomposition_complete": sum(
            row["file_bytes"] for row in optional_component_rows
        )
        == role_bytes.get("DEBUG_OR_OPTIONAL", 0),
        "development_decomposition_complete": sum(
            row["entry_count"] for row in development_rows
        )
        == role_counts.get("DEVELOPMENT", 0),
        "development_byte_decomposition_complete": sum(
            row["file_bytes"] for row in development_rows
        )
        == role_bytes.get("DEVELOPMENT", 0),
        "runtime_decomposition_complete": sum(
            row["entry_count"] for row in runtime_rows
        )
        == role_counts.get("RUNTIME", 0),
        "runtime_byte_decomposition_complete": sum(
            row["file_bytes"] for row in runtime_rows
        )
        == role_bytes.get("RUNTIME", 0),
        "no_unmatched_optional_bucket": not any(
            row["optional_component"] == "unmatched-optional"
            for row in optional_component_rows
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)

    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "input": {
            "results_dir": str(results_dir),
            "inventory": str(inventory_path),
            "summary": str(summary_path),
            "expected_manifest_sha256": args.expected_manifest_sha256,
            "observed_manifest_sha256": observed_manifest,
            "expected_entry_count": args.expected_entry_count,
            "expected_elf_count": args.expected_elf_count,
            "expected_symlink_count": args.expected_symlink_count,
        },
        "totals": {
            "entry_count": len(rows),
            "regular_file_count": type_counts.get("REGULAR", 0),
            "directory_count": type_counts.get("DIRECTORY", 0),
            "symlink_count": type_counts.get("SYMLINK", 0),
            "elf_count": elf_count,
            "file_bytes": total_file_bytes,
        },
        "role_overview": role_overview,
        "optional_components": optional_component_rows,
        "development_surfaces": development_rows,
        "runtime_surfaces": runtime_rows,
        "policy_review_required": [
            "Review CPython regression-test and package-local test roots separately.",
            "Review Tkinter as a consumer-facing optional component rather than assuming it is equivalent to tests or demos.",
            "Review IDLE and turtledemo as separately omittable components.",
            "Select shared-directory ownership only after runtime/development/optional archive split is chosen.",
            "Map the exact LICENSE row to every archive that redistributes covered payloads.",
            "Decide whether installed sysconfig/config metadata belongs in runtime, development, or a shared metadata layer.",
        ],
        "claim_boundary": {
            "proved": "The accepted role inventory is exactly and completely decomposed by rule and path surface.",
            "not_proved": "DEBUG_OR_OPTIONAL may be removed wholesale from the default runtime archive.",
        },
    }

    output = results_dir / "role-review.json"
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Role overview:       {results_dir / 'role-overview.tsv'}")
    print(f"Role by rule:        {results_dir / 'role-by-rule.tsv'}")
    print(f"Optional components: {results_dir / 'optional-component-summary.tsv'}")
    print(f"Optional roots:      {results_dir / 'optional-root-summary.tsv'}")
    print(f"Development:         {results_dir / 'development-surface-summary.tsv'}")
    print(f"Runtime:             {results_dir / 'runtime-surface-summary.tsv'}")
    print(f"Boundary rows:       {results_dir / 'selected-boundary-rows.tsv'}")
    print(f"Largest files:       {results_dir / 'largest-regular-files.tsv'}")
    print(f"Review:              {output}")
    print()
    print(
        "STAGE3C_PHASE1_ROLE_DECOMPOSITION="
        + ("PASS" if result["pass"] else "FAIL")
    )
    return 0 if result["pass"] else 6


if __name__ == "__main__":
    raise SystemExit(main())
