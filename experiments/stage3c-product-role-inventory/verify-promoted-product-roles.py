#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROLES = {
    "RUNTIME",
    "DEVELOPMENT",
    "METADATA",
    "LICENSE",
    "DEBUG_OR_OPTIONAL",
    "UNKNOWN",
}

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

REQUIRED_ANCHORS = {
    "bin/python3.14": "RUNTIME",
    "bin/python3": "RUNTIME",
    "bin/python": "RUNTIME",
    "lib/libpython3.14.so": "RUNTIME",
    "include/python3.14/Python.h": "DEVELOPMENT",
    "include/python3.14/pyconfig.h": "DEVELOPMENT",
}


def read_json(
    path: Path,
    missing: list[str],
    errors: dict[str, str],
) -> dict[str, Any]:
    if not path.is_file():
        missing.append(str(path))
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors[str(path)] = repr(exc)
        return {}
    if not isinstance(value, dict):
        errors[str(path)] = "top-level JSON value is not an object"
        return {}
    return value


def read_key_values(
    path: Path,
    missing: list[str],
    errors: dict[str, str],
) -> dict[str, str]:
    if not path.is_file():
        missing.append(str(path))
        return {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        errors[str(path)] = repr(exc)
        return {}
    result: dict[str, str] = {}
    for line in lines:
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key] = value
    return result


def read_tsv(
    path: Path,
    missing: list[str],
    errors: dict[str, str],
) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        missing.append(str(path))
        return [], []
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            fields = list(reader.fieldnames or [])
            rows = list(reader)
    except (OSError, csv.Error) as exc:
        errors[str(path)] = repr(exc)
        return [], []
    return fields, rows


def manifest_hash(rows: list[dict[str, str]]) -> str:
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


def int_value(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def parse_descendant_roles(value: str) -> set[str]:
    return {part for part in value.split(",") if part}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--expected-entry-count", required=True, type=int)
    parser.add_argument("--expected-elf-count", required=True, type=int)
    parser.add_argument("--expected-symlink-count", required=True, type=int)
    args = parser.parse_args()

    results_dir = args.results_dir.resolve()
    runtime_prefix = args.runtime_prefix.resolve()
    missing: list[str] = []
    errors: dict[str, str] = {}

    summary = read_json(
        results_dir / "role-summary.json",
        missing,
        errors,
    )
    mutation = read_key_values(
        results_dir / "mutation-check.txt",
        missing,
        errors,
    )
    inventory_fields, rows = read_tsv(
        results_dir / "product-role-inventory.tsv",
        missing,
        errors,
    )
    unknown_fields, unknown_rows = read_tsv(
        results_dir / "unknown.tsv",
        missing,
        errors,
    )
    mixed_fields, mixed_rows = read_tsv(
        results_dir / "mixed-directories.tsv",
        missing,
        errors,
    )
    rules_fields, rules_rows = read_tsv(
        results_dir / "rules.tsv",
        missing,
        errors,
    )

    paths = [row.get("path", "") for row in rows]
    unique_paths = set(paths)
    roles = Counter(row.get("role", "") for row in rows)
    types = Counter(row.get("type", "") for row in rows)
    elf_rows = [row for row in rows if row.get("elf") == "true"]
    pycache_rows = [
        row
        for row in rows
        if row.get("path", "").endswith(".pyc")
        or "/__pycache__/" in f"/{row.get('path', '')}/"
        or row.get("path", "").endswith("/__pycache__")
    ]
    special_rows = [
        row
        for row in rows
        if row.get("type") not in {"REGULAR", "DIRECTORY", "SYMLINK"}
    ]
    unknown_inventory_rows = [
        row for row in rows if row.get("role") == "UNKNOWN"
    ]
    mixed_inventory_rows = [
        row for row in rows if row.get("mixed_directory") == "true"
    ]
    directory_rows = [
        row for row in rows if row.get("type") == "DIRECTORY"
    ]
    nondirectory_rows = [
        row for row in rows if row.get("type") != "DIRECTORY"
    ]
    by_path = {row.get("path", ""): row for row in rows}
    anchor_roles = {
        path: by_path.get(path, {}).get("role")
        for path in REQUIRED_ANCHORS
    }

    declared_rule_ids = {
        row.get("rule_id", "")
        for row in rules_rows
        if row.get("rule_id")
    }
    used_rule_ids = {row.get("rule_id", "") for row in rows}
    unknown_paths = {
        row.get("path", "") for row in unknown_inventory_rows
    }
    unknown_tsv_paths = {
        row.get("path", "") for row in unknown_rows
    }
    mixed_paths = {
        row.get("path", "") for row in mixed_inventory_rows
    }
    mixed_tsv_paths = {row.get("path", "") for row in mixed_rows}

    directory_role_sets = {
        row.get("path", ""): parse_descendant_roles(
            row.get("descendant_roles", "")
        )
        for row in directory_rows
    }

    expected_role_counts = summary.get("role_counts")
    expected_type_counts = summary.get("type_counts")
    expected_entry_count = int_value(summary.get("entry_count"))
    summary_expected_entry_count = int_value(
        summary.get("expected_entry_count")
    )
    summary_unknown_count = int_value(summary.get("unknown_count"))
    summary_elf_count = int_value(summary.get("elf_count"))
    summary_pycache_count = int_value(summary.get("pycache_path_count"))
    summary_special_count = int_value(summary.get("special_file_count"))
    summary_mixed_count = int_value(summary.get("mixed_directory_count"))
    summary_unknown_paths = set(summary.get("unknown_paths", []))
    summary_mixed_paths = set(summary.get("mixed_directories", []))

    checks: dict[str, bool] = {
        "all_required_outputs_present": not missing,
        "all_required_outputs_parse": not errors,
        "inventory_schema_exact": inventory_fields
        == list(INVENTORY_FIELDS),
        "unknown_schema_exact": unknown_fields == list(INVENTORY_FIELDS),
        "mixed_schema_exact": mixed_fields == list(INVENTORY_FIELDS),
        "rules_schema_exact": rules_fields
        == ["rule_id", "role", "reason"],
        "rules_nonempty": bool(rules_rows),
        "all_used_rules_declared": used_rule_ids <= declared_rule_ids,
        "summary_schema_version": summary.get("schema_version") == 1,
        "summary_runtime_prefix_matches": summary.get("runtime_prefix")
        == str(runtime_prefix),
        "expected_entry_count_matches_contract": (
            summary_expected_entry_count == args.expected_entry_count
        ),
        "inventory_entry_count_matches": len(rows)
        == args.expected_entry_count,
        "summary_entry_count_matches": expected_entry_count == len(rows),
        "expected_elf_count_matches": len(elf_rows)
        == args.expected_elf_count,
        "summary_elf_count_matches_contract": summary_elf_count
        == args.expected_elf_count,
        "expected_symlink_count_matches": types.get("SYMLINK", 0)
        == args.expected_symlink_count,
        "paths_nonempty": all(paths),
        "paths_unique": len(unique_paths) == len(rows),
        "roles_valid": set(roles) <= ROLES,
        "role_counts_match_summary": isinstance(
            expected_role_counts,
            dict,
        )
        and dict(sorted(roles.items())) == expected_role_counts,
        "type_counts_match_summary": isinstance(
            expected_type_counts,
            dict,
        )
        and dict(sorted(types.items())) == expected_type_counts,
        "unknown_inventory_zero": not unknown_inventory_rows,
        "unknown_tsv_matches_inventory": unknown_tsv_paths
        == unknown_paths,
        "summary_unknown_zero": summary_unknown_count == 0,
        "summary_unknown_paths_match": summary_unknown_paths
        == unknown_paths,
        "all_elf_runtime": all(
            row.get("role") == "RUNTIME" for row in elf_rows
        ),
        "pycache_zero": not pycache_rows
        and summary_pycache_count == 0,
        "special_files_zero": not special_rows
        and summary_special_count == 0,
        "mixed_directories_exact": mixed_tsv_paths == mixed_paths,
        "summary_mixed_directories_match": summary_mixed_paths
        == mixed_paths,
        "mixed_directory_count_matches": len(mixed_paths)
        == summary_mixed_count,
        "directory_descendant_roles_nonempty": all(
            directory_role_sets.get(row.get("path", ""), set())
            for row in directory_rows
        ),
        "directory_descendant_roles_valid": all(
            role_set <= ROLES
            for role_set in directory_role_sets.values()
        ),
        "directory_mixed_flags_consistent": all(
            (row.get("mixed_directory") == "true")
            == (len(directory_role_sets[row.get("path", "")]) > 1)
            for row in directory_rows
        ),
        "nondirectory_role_sets_empty": all(
            not row.get("descendant_roles", "")
            and row.get("mixed_directory") == "false"
            for row in nondirectory_rows
        ),
        "manifest_sha256_matches": summary.get("manifest_sha256")
        == manifest_hash(rows),
        "mutation_runtime_prefix_matches": mutation.get("runtime_prefix")
        == str(runtime_prefix),
        "mutation_before_after_equal": bool(mutation.get("before"))
        and mutation.get("before") == mutation.get("after"),
        "mutation_summary_fingerprints_match": mutation.get("before")
        == summary.get("before_tree_sha256")
        and mutation.get("after") == summary.get("after_tree_sha256"),
        "mutation_pass": mutation.get("pass") == "true"
        and summary.get("mutation_pass") is True,
        "classifier_pass": summary.get("pass") is True,
        "anchor_paths_present": all(
            anchor_roles[path] is not None for path in REQUIRED_ANCHORS
        ),
        "anchor_roles_match": all(
            anchor_roles[path] == role
            for path, role in REQUIRED_ANCHORS.items()
        ),
    }

    failed = sorted(
        name for name, passed in checks.items() if not passed
    )
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "missing_outputs": sorted(set(missing)),
        "parse_errors": errors,
        "runtime_prefix": str(runtime_prefix),
        "expected_entry_count": args.expected_entry_count,
        "expected_elf_count": args.expected_elf_count,
        "expected_symlink_count": args.expected_symlink_count,
        "observed_entry_count": len(rows),
        "role_counts": dict(sorted(roles.items())),
        "type_counts": dict(sorted(types.items())),
        "unknown_paths": sorted(unknown_paths),
        "elf_count": len(elf_rows),
        "pycache_paths": [row.get("path") for row in pycache_rows],
        "special_file_paths": [
            row.get("path") for row in special_rows
        ],
        "mixed_directory_count": len(mixed_paths),
        "anchor_roles": anchor_roles,
        "summary": summary,
        "mutation": mutation,
    }

    output = results_dir / "verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 5


if __name__ == "__main__":
    raise SystemExit(main())
