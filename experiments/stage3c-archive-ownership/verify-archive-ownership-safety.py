#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import posixpath
from pathlib import Path
from typing import Any

SOURCE_FIELDS = (
    "path", "type", "mode", "size", "mtime_ns", "sha256", "symlink_target",
    "elf", "role", "rule_id", "reason", "descendant_roles", "mixed_directory",
    "component", "policy_rule", "policy_reason",
)
OWNED_FIELDS = ("artifact", "entry_class", *SOURCE_FIELDS)
SELECTED_COMPONENTS = {
    "RUNTIME_BASE", "RUNTIME_METADATA", "LICENSE", "DEVELOPMENT",
    "DEVELOPMENT_METADATA", "OPTIONAL_TEST_SUITE", "OPTIONAL_TEST_DEMO",
}
EXCLUDED_COMPONENT = "UNSUPPORTED_GUI_SOURCE"
ALLOWED_TYPES = {"REGULAR", "DIRECTORY", "SYMLINK"}


def read_tsv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"schema mismatch: {path}")
        return list(reader)


def resolve(path: str, target: str) -> str | None:
    if not target or target.startswith("/"):
        return None
    value = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
    if value in {"", "."} or value == ".." or value.startswith("../"):
        return None
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component-inventory", required=True, type=Path)
    parser.add_argument("--owned-paths", required=True, type=Path)
    parser.add_argument("--excluded-paths", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source = read_tsv(args.component_inventory.resolve(), SOURCE_FIELDS)
    owned = read_tsv(args.owned_paths.resolve(), OWNED_FIELDS)
    excluded_output = args.excluded_paths.resolve().read_text(
        encoding="utf-8"
    ).splitlines()

    source_by_path = {row["path"]: row for row in source}
    owner_by_path = {row["path"]: row["artifact"] for row in owned}
    expected_excluded = sorted(
        row["path"] for row in source if row["component"] == EXCLUDED_COMPONENT
    )
    unknown_components = {
        row["component"]
        for row in source
        if row["component"] not in SELECTED_COMPONENTS | {EXCLUDED_COMPONENT}
    }
    symlinks = [row for row in owned if row["type"] == "SYMLINK"]
    resolved = {
        row["path"]: resolve(row["path"], row["symlink_target"])
        for row in symlinks
    }

    checks = {
        "unknown_components_zero": not unknown_components,
        "excluded_component_count_199": len(expected_excluded) == 199,
        "excluded_paths_exact": excluded_output == expected_excluded,
        "selected_types_allowed": all(
            row["type"] in ALLOWED_TYPES for row in owned
        ),
        "selected_special_zero": all(
            row["type"] != "SPECIAL" for row in owned
        ),
        "selected_symlink_count_5": len(symlinks) == 5,
        "selected_symlinks_relative_and_contained": all(
            value is not None for value in resolved.values()
        ),
        "selected_symlink_targets_exist": all(
            value in source_by_path
            for value in resolved.values()
            if value is not None
        ),
        "selected_symlink_targets_same_artifact": all(
            target is not None and owner_by_path.get(target) == row["artifact"]
            for row in symlinks
            for target in [resolved[row["path"]]]
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    result: dict[str, Any] = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "observed": {
            "selected_entry_count": len(owned),
            "selected_symlink_count": len(symlinks),
            "excluded_entry_count": len(expected_excluded),
            "unknown_components": sorted(unknown_components),
            "symlinks": [
                {
                    "artifact": row["artifact"],
                    "path": row["path"],
                    "target": row["symlink_target"],
                    "resolved_target": resolved[row["path"]],
                }
                for row in symlinks
            ],
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 27


if __name__ == "__main__":
    raise SystemExit(main())
