#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

FIELDS = (
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
    "component",
    "policy_rule",
    "policy_reason",
)
VARIANTS = {
    "runtime-base": {
        "RUNTIME_BASE",
        "RUNTIME_METADATA",
        "LICENSE",
    },
    "runtime-development": {
        "RUNTIME_BASE",
        "RUNTIME_METADATA",
        "LICENSE",
        "DEVELOPMENT",
        "DEVELOPMENT_METADATA",
    },
    "runtime-test": {
        "RUNTIME_BASE",
        "RUNTIME_METADATA",
        "LICENSE",
        "OPTIONAL_TEST_SUITE",
        "OPTIONAL_TEST_DEMO",
    },
    "runtime-supported": {
        "RUNTIME_BASE",
        "RUNTIME_METADATA",
        "LICENSE",
        "DEVELOPMENT",
        "DEVELOPMENT_METADATA",
        "OPTIONAL_TEST_SUITE",
        "OPTIONAL_TEST_DEMO",
    },
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def read_inventory(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"component inventory schema mismatch: {path}")
        return list(reader)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def kind(mode: int) -> str:
    if stat.S_ISREG(mode):
        return "REGULAR"
    if stat.S_ISDIR(mode):
        return "DIRECTORY"
    if stat.S_ISLNK(mode):
        return "SYMLINK"
    return "SPECIAL"


def walk(root: Path) -> list[Path]:
    output: list[Path] = []
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        dirs.sort()
        files.sort()
        base = Path(current)
        output.extend(base / name for name in dirs)
        output.extend(base / name for name in files)
    return sorted(output, key=lambda path: path.relative_to(root).as_posix())


def inspect_variant(root: Path) -> dict[str, dict[str, Any]]:
    observed: dict[str, dict[str, Any]] = {}
    for path in walk(root):
        relative = path.relative_to(root).as_posix()
        st = path.lstat()
        item_kind = kind(st.st_mode)
        observed[relative] = {
            "type": item_kind,
            "mode": f"{stat.S_IMODE(st.st_mode):04o}",
            "size": st.st_size,
            "mtime_ns": st.st_mtime_ns,
            "sha256": sha256_file(path) if item_kind == "REGULAR" else "",
            "symlink_target": os.readlink(path) if item_kind == "SYMLINK" else "",
        }
    return observed


def portable_manifest(rows: list[dict[str, str]]) -> str:
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item["path"]):
        parts = [
            row["path"],
            row["type"],
            row["mode"],
            row["mtime_ns"],
            row["size"] if row["type"] == "REGULAR" else "",
            row["sha256"] if row["type"] == "REGULAR" else "",
            row["symlink_target"] if row["type"] == "SYMLINK" else "",
        ]
        digest.update("\t".join(parts).encode("utf-8", "surrogateescape"))
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component-inventory", required=True, type=Path)
    parser.add_argument("--materialization", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-component-manifest", required=True)
    args = parser.parse_args()

    inventory_path = args.component_inventory.resolve()
    materialization_path = args.materialization.resolve()
    output_root = args.output_root.resolve()
    output_path = args.output.resolve()

    rows = read_inventory(inventory_path)
    materialization = read_json(materialization_path)
    by_variant = {
        item.get("variant"): item
        for item in materialization.get("variants", [])
        if isinstance(item, dict)
    }

    variant_results: dict[str, Any] = {}
    global_checks: dict[str, bool] = {
        "materialization_pass": materialization.get("pass") is True,
        "component_manifest_matches": materialization.get(
            "component_manifest_sha256"
        )
        == args.expected_component_manifest,
        "variant_set_exact": set(by_variant) == set(VARIANTS),
    }

    for variant, components in VARIANTS.items():
        selected = [row for row in rows if row["component"] in components]
        expected = {row["path"]: row for row in selected}
        root = output_root / variant / "prefix"
        observed = inspect_variant(root) if root.is_dir() else {}
        added = sorted(set(observed) - set(expected))
        removed = sorted(set(expected) - set(observed))
        changed: list[dict[str, Any]] = []
        pycache = sorted(
            path
            for path in observed
            if path.endswith(".pyc")
            or path.endswith("/__pycache__")
            or "/__pycache__/" in f"/{path}/"
        )
        special = sorted(
            path for path, item in observed.items() if item["type"] == "SPECIAL"
        )

        for path in sorted(set(expected) & set(observed)):
            source = expected[path]
            target = observed[path]
            differences: dict[str, Any] = {}
            for key in ("type", "mode", "mtime_ns"):
                source_value: Any = source[key]
                target_value: Any = target[key]
                if key == "mtime_ns":
                    source_value = int(source_value)
                if source_value != target_value:
                    differences[key] = {
                        "expected": source_value,
                        "observed": target_value,
                    }
            if source["type"] == "REGULAR":
                for key in ("size", "sha256"):
                    source_value = int(source[key]) if key == "size" else source[key]
                    if source_value != target[key]:
                        differences[key] = {
                            "expected": source_value,
                            "observed": target[key],
                        }
            if source["type"] == "SYMLINK" and source["symlink_target"] != target[
                "symlink_target"
            ]:
                differences["symlink_target"] = {
                    "expected": source["symlink_target"],
                    "observed": target["symlink_target"],
                }
            if differences:
                changed.append({"path": path, "differences": differences})

        counts = {
            "entry_count": len(selected),
            "regular_file_count": sum(row["type"] == "REGULAR" for row in selected),
            "directory_count": sum(row["type"] == "DIRECTORY" for row in selected),
            "symlink_count": sum(row["type"] == "SYMLINK" for row in selected),
            "elf_count": sum(row["elf"] == "true" for row in selected),
            "file_bytes": sum(
                int(row["size"])
                for row in selected
                if row["type"] == "REGULAR"
            ),
        }
        materialized_item = by_variant.get(variant, {})
        checks = {
            "prefix_present": root.is_dir(),
            "path_set_exact": not added and not removed,
            "portable_metadata_exact": not changed,
            "pycache_zero": not pycache,
            "special_zero": not special,
            "entry_count_matches_materializer": materialized_item.get("entry_count")
            == counts["entry_count"],
            "file_bytes_match_materializer": materialized_item.get("file_bytes")
            == counts["file_bytes"],
            "elf_count_81": counts["elf_count"] == 81,
            "python_present": (root / "bin" / "python").exists(),
            "unsupported_gui_absent": not any(
                row["component"] == "UNSUPPORTED_GUI_SOURCE" for row in selected
            ),
        }
        variant_results[variant] = {
            "pass": all(checks.values()),
            "checks": checks,
            "components": sorted(components),
            "prefix": str(root),
            "counts": counts,
            "added_paths": added,
            "removed_paths": removed,
            "changed_paths": changed,
            "pycache_paths": pycache,
            "special_paths": special,
            "portable_manifest_sha256": portable_manifest(selected),
        }
        global_checks[f"{variant}_pass"] = variant_results[variant]["pass"]

    expected_counts = {
        "runtime-base": (714, 38_759_749),
        "runtime-development": (1168, 43_733_124),
        "runtime-test": (2502, 72_236_539),
        "runtime-supported": (2956, 77_209_914),
    }
    for variant, (entry_count, file_bytes) in expected_counts.items():
        counts = variant_results.get(variant, {}).get("counts", {})
        global_checks[f"{variant}_expected_entry_count"] = (
            counts.get("entry_count") == entry_count
        )
        global_checks[f"{variant}_expected_file_bytes"] = (
            counts.get("file_bytes") == file_bytes
        )

    failed = sorted(name for name, passed in global_checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(global_checks),
        "checks": global_checks,
        "failed_checks": failed,
        "component_manifest_sha256": args.expected_component_manifest,
        "output_root": str(output_root),
        "variants": variant_results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print("STAGE3C_PHASE1_VARIANT_FIDELITY=" + ("PASS" if result["pass"] else "FAIL"))
    return 0 if result["pass"] else 15


if __name__ == "__main__":
    raise SystemExit(main())
