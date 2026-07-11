#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

SOURCE_FIELDS = (
    "path", "type", "mode", "size", "mtime_ns", "sha256",
    "symlink_target", "elf", "role", "rule_id", "reason",
    "descendant_roles", "mixed_directory",
)
OUTPUT_FIELDS = SOURCE_FIELDS + ("component", "policy_rule", "policy_reason")
COMPONENTS = {
    "RUNTIME_BASE", "RUNTIME_METADATA", "DEVELOPMENT",
    "DEVELOPMENT_METADATA", "OPTIONAL_TEST_SUITE",
    "OPTIONAL_TEST_DEMO", "UNSUPPORTED_GUI_SOURCE", "LICENSE",
}
RUNTIME_METADATA = {
    "lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py",
    "lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json",
    "lib/python3.14/build-details.json",
}
DEVELOPMENT_METADATA = {
    "lib/python3.14/config-3.14-aarch64-linux-android/Makefile",
    "lib/python3.14/config-3.14-aarch64-linux-android/Setup",
    "lib/python3.14/config-3.14-aarch64-linux-android/Setup.local",
    "lib/python3.14/config-3.14-aarch64-linux-android/config.c",
    "lib/python3.14/config-3.14-aarch64-linux-android/python-config.py",
}
GUI_ROOTS = (
    "lib/python3.14/tkinter",
    "lib/python3.14/idlelib",
    "lib/python3.14/turtledemo",
)
GUI_FILES = {"lib/python3.14/turtle.py", "lib/python3.14/turtle.cfg"}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def read_tsv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"TSV schema mismatch: {path}")
        return list(reader)


def under(path: str, root: str) -> bool:
    return path == root or path.startswith(root + "/")


def expected_component(row: dict[str, str]) -> str:
    path = row["path"]
    role = row["role"]
    if role == "LICENSE":
        return "LICENSE"
    if path in RUNTIME_METADATA:
        return "RUNTIME_METADATA"
    if path in DEVELOPMENT_METADATA:
        return "DEVELOPMENT_METADATA"
    if role == "DEVELOPMENT":
        return "DEVELOPMENT"
    if under(path, "lib/python3.14/test"):
        return "OPTIONAL_TEST_SUITE"
    if under(path, "lib/python3.14/__phello__"):
        return "OPTIONAL_TEST_DEMO"
    if any(under(path, root) for root in GUI_ROOTS) or path in GUI_FILES:
        return "UNSUPPORTED_GUI_SOURCE"
    if role == "RUNTIME":
        return "RUNTIME_BASE"
    raise ValueError(f"unmapped source path: {path}")


def manifest_hash(rows: list[dict[str, str]]) -> str:
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item["path"]):
        digest.update(
            "\t".join(row[field] for field in OUTPUT_FIELDS).encode(
                "utf-8", "surrogateescape"
            )
        )
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--semantic-verification", required=True, type=Path)
    parser.add_argument("--expected-entry-count", type=int, default=3155)
    parser.add_argument("--expected-elf-count", type=int, default=81)
    parser.add_argument("--expected-symlink-count", type=int, default=5)
    args = parser.parse_args()

    missing: list[str] = []
    errors: dict[str, str] = {}
    output_dir = args.output_dir.resolve()
    required = {
        "source": args.inventory.resolve(),
        "inventory": output_dir / "component-inventory.tsv",
        "summary": output_dir / "component-summary.tsv",
        "policy": output_dir / "component-policy.json",
        "artifacts": output_dir / "artifact-composition.json",
        "semantic": args.semantic_verification.resolve(),
    }
    for path in required.values():
        if not path.is_file():
            missing.append(str(path))

    source_rows: list[dict[str, str]] = []
    rows: list[dict[str, str]] = []
    summary_rows: list[dict[str, str]] = []
    policy: dict[str, Any] = {}
    artifacts: dict[str, Any] = {}
    semantic: dict[str, Any] = {}
    if not missing:
        try:
            source_rows = read_tsv(required["source"], SOURCE_FIELDS)
            rows = read_tsv(required["inventory"], OUTPUT_FIELDS)
            summary_rows = read_tsv(
                required["summary"],
                (
                    "component", "entry_count", "regular_file_count",
                    "directory_count", "symlink_count", "elf_count",
                    "file_bytes", "disposition",
                ),
            )
            policy = read_json(required["policy"])
            artifacts = read_json(required["artifacts"])
            semantic = read_json(required["semantic"])
        except (OSError, csv.Error, json.JSONDecodeError, ValueError) as exc:
            errors["parse"] = repr(exc)

    source_by_path = {row["path"]: row for row in source_rows}
    rows_by_path = {row["path"]: row for row in rows}
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        buckets[row.get("component", "")].append(row)

    expected_mapping_ok = True
    source_fields_match = True
    for path, row in rows_by_path.items():
        source = source_by_path.get(path)
        if source is None:
            source_fields_match = False
            expected_mapping_ok = False
            continue
        if any(row[field] != source[field] for field in SOURCE_FIELDS):
            source_fields_match = False
        try:
            if row["component"] != expected_component(source):
                expected_mapping_ok = False
        except ValueError:
            expected_mapping_ok = False

    observed_summary: dict[str, dict[str, int]] = {}
    for component in COMPONENTS:
        component_rows = buckets.get(component, [])
        types = Counter(row["type"] for row in component_rows)
        observed_summary[component] = {
            "entry_count": len(component_rows),
            "regular_file_count": types.get("REGULAR", 0),
            "directory_count": types.get("DIRECTORY", 0),
            "symlink_count": types.get("SYMLINK", 0),
            "elf_count": sum(row["elf"] == "true" for row in component_rows),
            "file_bytes": sum(
                int(row["size"])
                for row in component_rows
                if row["type"] == "REGULAR"
            ),
        }
    summary_by_component = {row.get("component", ""): row for row in summary_rows}
    summary_matches = set(summary_by_component) == COMPONENTS
    if summary_matches:
        for component, expected in observed_summary.items():
            row = summary_by_component[component]
            if any(int(row[key]) != value for key, value in expected.items()):
                summary_matches = False
                break

    path_lists_match = True
    for component in COMPONENTS:
        path_file = output_dir / "paths" / f"{component.lower()}.txt"
        if not path_file.is_file():
            path_lists_match = False
            continue
        observed = path_file.read_text(encoding="utf-8").splitlines()
        expected = sorted(row["path"] for row in buckets.get(component, []))
        if observed != expected:
            path_lists_match = False

    manifest = manifest_hash(rows) if rows else ""
    artifact_rows = artifacts.get("artifacts", [])
    artifact_names = {
        row.get("artifact") for row in artifact_rows if isinstance(row, dict)
    }
    runtime_components = None
    gui_disposition = None
    for row in artifact_rows:
        if not isinstance(row, dict):
            continue
        if row.get("artifact") == "runtime-base":
            runtime_components = row.get("components")
        if row.get("artifact") == "unsupported-gui-source":
            gui_disposition = row.get("disposition")

    checks = {
        "all_required_outputs_present": not missing,
        "all_required_outputs_parse": not errors,
        "source_entry_count": len(source_rows) == args.expected_entry_count,
        "output_entry_count": len(rows) == args.expected_entry_count,
        "source_paths_unique": len(source_by_path) == len(source_rows),
        "output_paths_unique": len(rows_by_path) == len(rows),
        "path_sets_equal": set(source_by_path) == set(rows_by_path),
        "source_fields_preserved": source_fields_match,
        "component_set_exact": set(buckets) == COMPONENTS,
        "expected_mapping_exact": expected_mapping_ok,
        "policy_schema": policy.get("schema_version") == 1,
        "policy_pass": policy.get("pass") is True,
        "policy_failed_checks_empty": policy.get("failed_checks") == [],
        "component_manifest_hash_matches": manifest == policy.get("component_manifest_sha256"),
        "artifact_manifest_hash_matches": manifest == artifacts.get("component_manifest_sha256"),
        "component_summary_exact": summary_matches,
        "component_path_lists_exact": path_lists_match,
        "semantic_verifier_pass": semantic.get("pass") is True,
        "semantic_verifier_38": semantic.get("check_count") == 38,
        "all_elf_runtime_base": observed_summary.get("RUNTIME_BASE", {}).get("elf_count") == args.expected_elf_count,
        "total_elf_count": sum(value["elf_count"] for value in observed_summary.values()) == args.expected_elf_count,
        "total_symlink_count": sum(value["symlink_count"] for value in observed_summary.values()) == args.expected_symlink_count,
        "runtime_metadata_exact": {row["path"] for row in buckets["RUNTIME_METADATA"]} == RUNTIME_METADATA,
        "development_metadata_exact": {row["path"] for row in buckets["DEVELOPMENT_METADATA"]} == DEVELOPMENT_METADATA,
        "test_suite_root_exact": all(under(row["path"], "lib/python3.14/test") for row in buckets["OPTIONAL_TEST_SUITE"]),
        "test_demo_root_exact": all(under(row["path"], "lib/python3.14/__phello__") for row in buckets["OPTIONAL_TEST_DEMO"]),
        "gui_component_contains_turtle": any(row["path"] == "lib/python3.14/turtle.py" for row in buckets["UNSUPPORTED_GUI_SOURCE"]),
        "gui_component_has_no_elf": observed_summary.get("UNSUPPORTED_GUI_SOURCE", {}).get("elf_count") == 0,
        "license_exact": {row["path"] for row in buckets["LICENSE"]} == {"lib/python3.14/LICENSE.txt"},
        "runtime_anchors_present": all(rows_by_path.get(path, {}).get("component") == "RUNTIME_BASE" for path in ("bin/python", "bin/python3", "bin/python3.14", "lib/libpython3.14.so")),
        "development_anchors_present": all(rows_by_path.get(path, {}).get("component") == "DEVELOPMENT" for path in ("include/python3.14/Python.h", "include/python3.14/pyconfig.h")),
        "artifact_names_exact": artifact_names == {"runtime-base", "development-addon", "test-addon", "unsupported-gui-source"},
        "runtime_artifact_components_exact": runtime_components == ["RUNTIME_BASE", "RUNTIME_METADATA", "LICENSE"],
        "unsupported_gui_not_distributed": gui_disposition == "not-distributed-until-tk-backend-exists",
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "missing_outputs": missing,
        "parse_errors": errors,
        "component_manifest_sha256": manifest,
        "components": observed_summary,
        "artifact_names": sorted(name for name in artifact_names if name),
    }
    output = output_dir / "component-policy-verification.json"
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 10


if __name__ == "__main__":
    raise SystemExit(main())
