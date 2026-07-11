#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import stat
from collections import Counter
from pathlib import Path, PurePosixPath
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
    "component",
    "policy_rule",
    "policy_reason",
)
VARIANTS = {
    "runtime-base": (
        "RUNTIME_BASE",
        "RUNTIME_METADATA",
        "LICENSE",
    ),
    "runtime-development": (
        "RUNTIME_BASE",
        "RUNTIME_METADATA",
        "LICENSE",
        "DEVELOPMENT",
        "DEVELOPMENT_METADATA",
    ),
    "runtime-test": (
        "RUNTIME_BASE",
        "RUNTIME_METADATA",
        "LICENSE",
        "OPTIONAL_TEST_SUITE",
        "OPTIONAL_TEST_DEMO",
    ),
    "runtime-supported": (
        "RUNTIME_BASE",
        "RUNTIME_METADATA",
        "LICENSE",
        "DEVELOPMENT",
        "DEVELOPMENT_METADATA",
        "OPTIONAL_TEST_SUITE",
        "OPTIONAL_TEST_DEMO",
    ),
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def read_inventory(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != SOURCE_FIELDS:
            raise ValueError(f"component inventory schema mismatch: {path}")
        return list(reader)


def depth(path: str) -> int:
    return len(PurePosixPath(path).parts)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_ancestor_closed(rows: list[dict[str, str]]) -> list[str]:
    selected = {row["path"] for row in rows}
    missing: list[str] = []
    for row in rows:
        parent = PurePosixPath(row["path"]).parent
        while str(parent) not in {".", ""}:
            parent_text = parent.as_posix()
            if parent_text not in selected:
                missing.append(f"{row['path']} -> {parent_text}")
            parent = parent.parent
    return sorted(set(missing))


def set_metadata(source: Path, destination: Path, kind: str) -> None:
    st = source.lstat()
    if kind != "SYMLINK":
        os.chmod(destination, stat.S_IMODE(st.st_mode), follow_symlinks=False)
    os.utime(
        destination,
        ns=(st.st_atime_ns, st.st_mtime_ns),
        follow_symlinks=False,
    )


def copy_variant(
    source_prefix: Path,
    destination_prefix: Path,
    rows: list[dict[str, str]],
) -> None:
    destination_prefix.mkdir(parents=True, exist_ok=True)
    directories = sorted(
        (row for row in rows if row["type"] == "DIRECTORY"),
        key=lambda row: (depth(row["path"]), row["path"]),
    )
    nondirectories = sorted(
        (row for row in rows if row["type"] != "DIRECTORY"),
        key=lambda row: row["path"],
    )

    for row in directories:
        destination = destination_prefix / row["path"]
        destination.mkdir(parents=False, exist_ok=False)

    for row in nondirectories:
        source = source_prefix / row["path"]
        destination = destination_prefix / row["path"]
        if row["type"] == "REGULAR":
            shutil.copyfile(source, destination, follow_symlinks=False)
            set_metadata(source, destination, "REGULAR")
        elif row["type"] == "SYMLINK":
            os.symlink(os.readlink(source), destination)
            set_metadata(source, destination, "SYMLINK")
        else:
            raise ValueError(
                f"unsupported materialization type={row['type']} path={row['path']}"
            )

    for row in sorted(directories, key=lambda item: (-depth(item["path"]), item["path"])):
        set_metadata(
            source_prefix / row["path"],
            destination_prefix / row["path"],
            "DIRECTORY",
        )


def component_manifest_sha256(rows: list[dict[str, str]]) -> str:
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
    parser.add_argument("--source-prefix", required=True, type=Path)
    parser.add_argument("--component-inventory", required=True, type=Path)
    parser.add_argument("--component-policy", required=True, type=Path)
    parser.add_argument("--component-verification", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-component-manifest", required=True)
    args = parser.parse_args()

    source_prefix = args.source_prefix.resolve()
    inventory_path = args.component_inventory.resolve()
    output_root = args.output_root.resolve()
    output_path = args.output.resolve()

    rows = read_inventory(inventory_path)
    policy = read_json(args.component_policy.resolve())
    verification = read_json(args.component_verification.resolve())
    observed_manifest = component_manifest_sha256(rows)

    if not source_prefix.is_dir():
        raise SystemExit(f"source prefix is missing: {source_prefix}")
    if observed_manifest != args.expected_component_manifest:
        raise SystemExit("component inventory manifest does not match expected input")
    if policy.get("pass") is not True:
        raise SystemExit("component policy is not accepted")
    if verification.get("pass") is not True or verification.get("check_count") != 34:
        raise SystemExit("component policy verification is not accepted 34/34 evidence")
    if verification.get("component_manifest_sha256") != observed_manifest:
        raise SystemExit("component policy verification manifest mismatch")

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    variant_results: list[dict[str, Any]] = []
    all_components = {row["component"] for row in rows}
    expected_components = {
        component
        for components in VARIANTS.values()
        for component in components
    } | {"UNSUPPORTED_GUI_SOURCE"}
    if all_components != expected_components:
        raise SystemExit(
            f"component set mismatch: observed={sorted(all_components)} "
            f"expected={sorted(expected_components)}"
        )

    for variant, components in VARIANTS.items():
        selected = [row for row in rows if row["component"] in components]
        missing_ancestors = ensure_ancestor_closed(selected)
        if missing_ancestors:
            raise SystemExit(
                f"variant is not ancestor-closed: {variant}: {missing_ancestors[:20]}"
            )
        destination_prefix = output_root / variant / "prefix"
        copy_variant(source_prefix, destination_prefix, selected)
        types = Counter(row["type"] for row in selected)
        variant_results.append(
            {
                "variant": variant,
                "components": list(components),
                "prefix": str(destination_prefix),
                "entry_count": len(selected),
                "regular_file_count": types.get("REGULAR", 0),
                "directory_count": types.get("DIRECTORY", 0),
                "symlink_count": types.get("SYMLINK", 0),
                "elf_count": sum(row["elf"] == "true" for row in selected),
                "file_bytes": sum(
                    int(row["size"])
                    for row in selected
                    if row["type"] == "REGULAR"
                ),
                "python_executable": str(destination_prefix / "bin" / "python"),
                "python_executable_exists": (destination_prefix / "bin" / "python").is_symlink()
                or os.access(destination_prefix / "bin" / "python", os.X_OK),
            }
        )

    checks = {
        "component_manifest_matches": observed_manifest
        == args.expected_component_manifest,
        "component_policy_pass": policy.get("pass") is True,
        "component_verification_34": verification.get("pass") is True
        and verification.get("check_count") == 34,
        "variant_set_exact": {row["variant"] for row in variant_results}
        == set(VARIANTS),
        "all_variants_have_python": all(
            row["python_executable_exists"] for row in variant_results
        ),
        "all_variants_retain_all_elf": all(
            row["elf_count"] == 81 for row in variant_results
        ),
        "unsupported_gui_not_materialized": all(
            "UNSUPPORTED_GUI_SOURCE" not in row["components"]
            for row in variant_results
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "source_prefix": str(source_prefix),
        "component_inventory": str(inventory_path),
        "component_manifest_sha256": observed_manifest,
        "output_root": str(output_root),
        "variants": variant_results,
        "claim_boundary": {
            "proved": "Selected component rows were copied into four ancestor-closed isolated variant trees.",
            "not_proved": "The copied trees match every selected source path and pass runtime behavior validation.",
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print("STAGE3C_PHASE1_VARIANT_MATERIALIZATION=" + ("PASS" if result["pass"] else "FAIL"))
    return 0 if result["pass"] else 14


if __name__ == "__main__":
    raise SystemExit(main())
