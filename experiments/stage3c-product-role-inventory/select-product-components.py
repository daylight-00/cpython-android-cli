#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

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
OUTPUT_FIELDS = SOURCE_FIELDS + (
    "component",
    "policy_rule",
    "policy_reason",
)
COMPONENTS = (
    "RUNTIME_BASE",
    "RUNTIME_METADATA",
    "DEVELOPMENT",
    "DEVELOPMENT_METADATA",
    "OPTIONAL_TEST_SUITE",
    "OPTIONAL_TEST_DEMO",
    "UNSUPPORTED_GUI_SOURCE",
    "LICENSE",
)
RUNTIME_METADATA_PATHS = {
    "lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py",
    "lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json",
    "lib/python3.14/build-details.json",
}
DEVELOPMENT_METADATA_NAMES = {
    "Makefile",
    "Setup",
    "Setup.local",
    "config.c",
    "python-config.py",
}
GUI_ROOTS = (
    "lib/python3.14/tkinter",
    "lib/python3.14/idlelib",
    "lib/python3.14/turtledemo",
)
GUI_RUNTIME_PATHS = {
    "lib/python3.14/turtle.py",
    "lib/python3.14/turtle.cfg",
}
TEST_ROOT = "lib/python3.14/test"
TEST_DEMO_ROOT = "lib/python3.14/__phello__"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != SOURCE_FIELDS:
            raise ValueError(f"source inventory schema mismatch: {path}")
        return list(reader)


def under(path: str, root: str) -> bool:
    return path == root or path.startswith(root + "/")


def is_config_tree(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return (
        len(parts) >= 4
        and parts[0] == "lib"
        and parts[1] == "python3.14"
        and parts[2].startswith("config-3.14-")
    )


def classify(row: dict[str, str]) -> tuple[str, str, str]:
    path = row["path"]
    role = row["role"]

    if role == "LICENSE":
        return "LICENSE", "license", "license file retained as a separately mapped product component"

    if path in RUNTIME_METADATA_PATHS:
        return (
            "RUNTIME_METADATA",
            "runtime-metadata",
            "active sysconfig/build metadata used by the promoted runtime",
        )

    if role == "METADATA" and is_config_tree(path):
        name = PurePosixPath(path).name
        if name in DEVELOPMENT_METADATA_NAMES:
            return (
                "DEVELOPMENT_METADATA",
                "development-metadata",
                "installed Makefile/config surface used for native development",
            )

    if role == "DEVELOPMENT":
        return (
            "DEVELOPMENT",
            "development-surface",
            "headers, pkg-config, static/config development ownership",
        )

    if under(path, TEST_ROOT):
        return (
            "OPTIONAL_TEST_SUITE",
            "cpython-regression-suite",
            "CPython internal regression tests and fixtures",
        )

    if under(path, TEST_DEMO_ROOT):
        return (
            "OPTIONAL_TEST_DEMO",
            "internal-test-demo",
            "CPython internal __phello__ test/demo package",
        )

    if any(under(path, root) for root in GUI_ROOTS) or path in GUI_RUNTIME_PATHS:
        return (
            "UNSUPPORTED_GUI_SOURCE",
            "unsupported-tk-stack",
            "pure-Python Tk/IDLE/turtle surface is unusable because _tkinter is absent",
        )

    if role == "RUNTIME":
        return (
            "RUNTIME_BASE",
            "runtime-base",
            "working runtime executable, libraries, extensions, and stdlib surface",
        )

    raise ValueError(f"unmapped path: role={role!r} path={path!r}")


def write_tsv(path: Path, fields: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(fields),
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def manifest_sha256(rows: list[dict[str, str]]) -> str:
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
    parser.add_argument("--role-summary", required=True, type=Path)
    parser.add_argument("--semantic-probes", required=True, type=Path)
    parser.add_argument("--semantic-verification", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expected-source-manifest", required=True)
    parser.add_argument("--expected-entry-count", type=int, default=3155)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    inventory_path = args.inventory.resolve()
    output_dir = args.output_dir.resolve()
    source_rows = read_tsv(inventory_path)
    role_summary = read_json(args.role_summary.resolve())
    semantic = read_json(args.semantic_probes.resolve())
    semantic_verification = read_json(args.semantic_verification.resolve())

    if role_summary.get("manifest_sha256") != args.expected_source_manifest:
        raise SystemExit("accepted source manifest does not match policy input")
    if len(source_rows) != args.expected_entry_count:
        raise SystemExit("accepted entry count does not match policy input")
    if semantic_verification.get("pass") is not True or semantic_verification.get("check_count") != 38:
        raise SystemExit("semantic probe evidence is not accepted 38/38 evidence")

    interpretation = semantic.get("interpretation_inputs", {})
    if interpretation.get("_tkinter_binary_importable") is not False:
        raise SystemExit("policy requires observed _tkinter absence")
    if interpretation.get("sysconfig_runtime_service_usable") is not True:
        raise SystemExit("policy requires working sysconfig runtime service")

    output_rows: list[dict[str, str]] = []
    for source in source_rows:
        component, policy_rule, policy_reason = classify(source)
        row = dict(source)
        row.update(
            {
                "component": component,
                "policy_rule": policy_rule,
                "policy_reason": policy_reason,
            }
        )
        output_rows.append(row)

    output_dir.mkdir(parents=True, exist_ok=True)
    paths_dir = output_dir / "paths"
    paths_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(output_dir / "component-inventory.tsv", OUTPUT_FIELDS, output_rows)

    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in output_rows:
        buckets[row["component"]].append(row)

    summary_rows: list[dict[str, Any]] = []
    for component in COMPONENTS:
        rows = buckets.get(component, [])
        types = Counter(row["type"] for row in rows)
        file_bytes = sum(
            int(row["size"]) for row in rows if row["type"] == "REGULAR"
        )
        summary_rows.append(
            {
                "component": component,
                "entry_count": len(rows),
                "regular_file_count": types.get("REGULAR", 0),
                "directory_count": types.get("DIRECTORY", 0),
                "symlink_count": types.get("SYMLINK", 0),
                "elf_count": sum(row["elf"] == "true" for row in rows),
                "file_bytes": file_bytes,
                "disposition": "not-distributed"
                if component == "UNSUPPORTED_GUI_SOURCE"
                else "artifact-input",
            }
        )
        (paths_dir / f"{component.lower()}.txt").write_text(
            "".join(f"{row['path']}\n" for row in sorted(rows, key=lambda item: item["path"])),
            encoding="utf-8",
        )

    write_tsv(
        output_dir / "component-summary.tsv",
        (
            "component",
            "entry_count",
            "regular_file_count",
            "directory_count",
            "symlink_count",
            "elf_count",
            "file_bytes",
            "disposition",
        ),
        summary_rows,
    )

    artifacts = {
        "runtime-base": ["RUNTIME_BASE", "RUNTIME_METADATA", "LICENSE"],
        "development-addon": ["DEVELOPMENT", "DEVELOPMENT_METADATA"],
        "test-addon": ["OPTIONAL_TEST_SUITE", "OPTIONAL_TEST_DEMO"],
        "unsupported-gui-source": ["UNSUPPORTED_GUI_SOURCE"],
    }
    artifact_disposition = {
        "runtime-base": "selected-candidate",
        "development-addon": "selected-candidate",
        "test-addon": "selected-candidate",
        "unsupported-gui-source": "not-distributed-until-tk-backend-exists",
    }

    summary_by_component = {row["component"]: row for row in summary_rows}
    artifact_rows = []
    for artifact, components in artifacts.items():
        artifact_rows.append(
            {
                "artifact": artifact,
                "components": components,
                "entry_count": sum(summary_by_component[item]["entry_count"] for item in components),
                "file_bytes": sum(summary_by_component[item]["file_bytes"] for item in components),
                "disposition": artifact_disposition[artifact],
            }
        )

    manifest = manifest_sha256(output_rows)
    checks = {
        "entry_count_matches": len(output_rows) == args.expected_entry_count,
        "all_components_known": set(buckets) <= set(COMPONENTS),
        "all_paths_unique": len({row["path"] for row in output_rows}) == len(output_rows),
        "source_manifest_matches": role_summary.get("manifest_sha256") == args.expected_source_manifest,
        "semantic_verifier_pass": semantic_verification.get("pass") is True,
        "semantic_verifier_38": semantic_verification.get("check_count") == 38,
        "source_mutation_pass": semantic.get("mutation_pass") is True,
        "sysconfig_runtime_service_usable": interpretation.get("sysconfig_runtime_service_usable") is True,
        "tkinter_backend_absent": interpretation.get("_tkinter_binary_importable") is False,
        "runtime_metadata_exact": {row["path"] for row in buckets["RUNTIME_METADATA"]} == RUNTIME_METADATA_PATHS,
        "development_metadata_exact": {PurePosixPath(row["path"]).name for row in buckets["DEVELOPMENT_METADATA"]} == DEVELOPMENT_METADATA_NAMES,
        "test_suite_nonempty": bool(buckets["OPTIONAL_TEST_SUITE"]),
        "test_demo_nonempty": bool(buckets["OPTIONAL_TEST_DEMO"]),
        "unsupported_gui_nonempty": bool(buckets["UNSUPPORTED_GUI_SOURCE"]),
        "all_elf_in_runtime_base": sum(row["elf"] == "true" for row in buckets["RUNTIME_BASE"]) == 81,
        "nonruntime_components_have_no_elf": all(
            row["elf"] != "true"
            for component in COMPONENTS
            if component != "RUNTIME_BASE"
            for row in buckets[component]
        ),
        "turtle_reassigned_to_gui": any(row["path"] == "lib/python3.14/turtle.py" for row in buckets["UNSUPPORTED_GUI_SOURCE"]),
        "license_exact": {row["path"] for row in buckets["LICENSE"]} == {"lib/python3.14/LICENSE.txt"},
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "source": {
            "inventory": str(inventory_path),
            "entry_count": len(source_rows),
            "role_manifest_sha256": role_summary.get("manifest_sha256"),
            "semantic_tree_fingerprint": semantic.get("before_tree", {}).get("fingerprint"),
        },
        "component_manifest_sha256": manifest,
        "components": summary_rows,
        "artifacts": artifact_rows,
        "selected_policy": {
            "runtime_metadata": sorted(RUNTIME_METADATA_PATHS),
            "development_metadata_names": sorted(DEVELOPMENT_METADATA_NAMES),
            "test_root": TEST_ROOT,
            "test_demo_root": TEST_DEMO_ROOT,
            "unsupported_gui_roots": list(GUI_ROOTS),
            "unsupported_gui_runtime_paths": sorted(GUI_RUNTIME_PATHS),
        },
        "claim_boundary": {
            "proved": "Every accepted source path has exactly one candidate product component.",
            "not_proved": "The selected artifact compositions pass isolated runtime, development, test, closure, and relocation validation.",
        },
    }
    (output_dir / "component-policy.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "artifact-composition.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifacts": artifact_rows,
                "component_manifest_sha256": manifest,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Component inventory: {output_dir / 'component-inventory.tsv'}")
    print(f"Component summary:   {output_dir / 'component-summary.tsv'}")
    print(f"Artifact policy:     {output_dir / 'artifact-composition.json'}")
    print(f"Policy result:       {output_dir / 'component-policy.json'}")
    print()
    print("STAGE3C_PHASE1_COMPONENT_POLICY=" + ("PASS" if result["pass"] else "FAIL"))
    if args.require_pass and not result["pass"]:
        return 9
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
