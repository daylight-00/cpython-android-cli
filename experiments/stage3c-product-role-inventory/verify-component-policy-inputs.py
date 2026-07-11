#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

SOURCE_FIELDS = (
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


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def read_inventory(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != SOURCE_FIELDS:
            raise ValueError(f"inventory schema mismatch: {path}")
        return list(reader)


def inventory_hash(rows: list[dict[str, str]]) -> str:
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item["path"]):
        digest.update(
            "\t".join(row[field] for field in SOURCE_FIELDS).encode(
                "utf-8", "surrogateescape"
            )
        )
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--role-summary", required=True, type=Path)
    parser.add_argument("--semantic-probes", required=True, type=Path)
    parser.add_argument("--semantic-verification", required=True, type=Path)
    parser.add_argument("--tree-fingerprint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-source-manifest", required=True)
    parser.add_argument("--expected-entry-count", type=int, default=3155)
    args = parser.parse_args()

    missing: list[str] = []
    errors: dict[str, str] = {}
    paths = (
        args.inventory.resolve(),
        args.role_summary.resolve(),
        args.semantic_probes.resolve(),
        args.semantic_verification.resolve(),
        args.tree_fingerprint.resolve(),
    )
    for path in paths:
        if not path.is_file():
            missing.append(str(path))

    rows: list[dict[str, str]] = []
    role_summary: dict[str, Any] = {}
    semantic: dict[str, Any] = {}
    semantic_verification: dict[str, Any] = {}
    tree: dict[str, Any] = {}
    if not missing:
        try:
            rows = read_inventory(paths[0])
            role_summary = read_json(paths[1])
            semantic = read_json(paths[2])
            semantic_verification = read_json(paths[3])
            tree = read_json(paths[4])
        except (OSError, csv.Error, json.JSONDecodeError, ValueError) as exc:
            errors["parse"] = repr(exc)

    observed_manifest = inventory_hash(rows) if rows else ""
    semantic_before = semantic.get("before_tree", {})
    interpretation = semantic.get("interpretation_inputs", {})
    checks = {
        "all_inputs_present": not missing,
        "all_inputs_parse": not errors,
        "inventory_entry_count": len(rows) == args.expected_entry_count,
        "inventory_paths_unique": len({row["path"] for row in rows}) == len(rows),
        "inventory_manifest_expected": observed_manifest == args.expected_source_manifest,
        "inventory_manifest_summary": observed_manifest == role_summary.get("manifest_sha256"),
        "role_summary_pass": role_summary.get("pass") is True,
        "role_summary_unknown_zero": role_summary.get("unknown_count") == 0,
        "semantic_probe_pass": semantic.get("pass") is True,
        "semantic_mutation_pass": semantic.get("mutation_pass") is True,
        "semantic_verification_pass": semantic_verification.get("pass") is True,
        "semantic_verification_38": semantic_verification.get("check_count") == 38,
        "semantic_failed_checks_empty": semantic_verification.get("failed_checks") == [],
        "semantic_missing_outputs_empty": semantic_verification.get("missing_outputs") == [],
        "semantic_parse_errors_empty": semantic_verification.get("parse_errors") == {},
        "tkinter_backend_absent": interpretation.get("_tkinter_binary_importable") is False,
        "sysconfig_runtime_service_usable": interpretation.get("sysconfig_runtime_service_usable") is True,
        "tree_probe_pass": tree.get("pass") is True,
        "tree_entry_count": tree.get("entry_count") == args.expected_entry_count,
        "tree_matches_semantic_fingerprint": tree.get("fingerprint") == semantic_before.get("fingerprint"),
        "tree_pycache_zero": tree.get("pycache_paths") == [],
        "tree_special_zero": tree.get("special_paths") == [],
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "missing_inputs": missing,
        "parse_errors": errors,
        "inventory_manifest_sha256": observed_manifest,
        "tree_fingerprint": tree.get("fingerprint"),
        "entry_count": len(rows),
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 12


if __name__ == "__main__":
    raise SystemExit(main())
