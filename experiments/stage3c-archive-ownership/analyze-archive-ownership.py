#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import posixpath
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
    "component",
    "policy_rule",
    "policy_reason",
)
OWNED_FIELDS = (
    "artifact",
    "entry_class",
    *SOURCE_FIELDS,
)
STRUCTURAL_FIELDS = (
    "artifact",
    "path",
    "entry_class",
    "owner_artifact",
    "owner_component",
    "required_by_owned_descendant_count",
    "participant_artifacts",
    "participant_count",
)
SHARED_FIELDS = (
    "path",
    "owner_artifact",
    "owner_component",
    "participant_artifacts",
    "participant_count",
    "structural_consumer_artifacts",
    "structural_consumer_count",
    "selected_descendant_count",
)
SUMMARY_FIELDS = (
    "artifact",
    "disposition",
    "standalone",
    "prerequisite_artifact",
    "owned_entry_count",
    "owned_regular_file_count",
    "owned_directory_count",
    "owned_symlink_count",
    "owned_elf_count",
    "owned_regular_file_bytes",
    "structural_parent_count",
    "shared_namespace_count",
)

ARTIFACT_COMPONENTS = {
    "runtime-base": ("RUNTIME_BASE", "RUNTIME_METADATA", "LICENSE"),
    "development-addon": ("DEVELOPMENT", "DEVELOPMENT_METADATA"),
    "test-addon": ("OPTIONAL_TEST_SUITE", "OPTIONAL_TEST_DEMO"),
}
COMPONENT_ARTIFACT = {
    component: artifact
    for artifact, components in ARTIFACT_COMPONENTS.items()
    for component in components
}
EXCLUDED_COMPONENT = "UNSUPPORTED_GUI_SOURCE"
EXPECTED_ARTIFACT_COUNTS = {
    "runtime-base": 714,
    "development-addon": 454,
    "test-addon": 1788,
}
EXPECTED_SELECTED_COUNT = 2956
EXPECTED_EXCLUDED_COUNT = 199
EXPECTED_TOTAL_COUNT = 3155
EXPECTED_SELECTED_SYMLINKS = 5
EXPECTED_SELECTED_ELF = 81
LICENSE_PATH = "lib/python3.14/LICENSE.txt"
ALLOWED_TYPES = {"REGULAR", "DIRECTORY", "SYMLINK"}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != SOURCE_FIELDS:
            raise ValueError(f"component inventory schema mismatch: {path}")
        rows = list(reader)
    return rows


def write_tsv(
    path: Path,
    fields: Iterable[str],
    rows: Iterable[dict[str, Any]],
) -> None:
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


def stable_manifest(rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> str:
    field_list = tuple(fields)
    digest = hashlib.sha256()
    for row in sorted(
        rows,
        key=lambda item: tuple(str(item.get(field, "")) for field in field_list),
    ):
        digest.update(
            "\t".join(str(row.get(field, "")) for field in field_list).encode(
                "utf-8", "surrogateescape"
            )
        )
        digest.update(b"\n")
    return digest.hexdigest()


def ancestors(path: str) -> list[str]:
    parent = PurePosixPath(path).parent
    result: list[str] = []
    while str(parent) not in {"", "."}:
        result.append(parent.as_posix())
        parent = parent.parent
    result.reverse()
    return result


def artifact_for_component(component: str) -> str | None:
    return COMPONENT_ARTIFACT.get(component)


def resolve_symlink(path: str, target: str) -> str | None:
    if not target or target.startswith("/"):
        return None
    combined = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
    if combined in {"", "."} or combined == ".." or combined.startswith("../"):
        return None
    return combined


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component-inventory", required=True, type=Path)
    parser.add_argument("--component-policy", required=True, type=Path)
    parser.add_argument("--component-verification", required=True, type=Path)
    parser.add_argument("--phase1-final-verification", required=True, type=Path)
    parser.add_argument("--canonical-fingerprint", required=True, type=Path)
    parser.add_argument("--runtime-fingerprint", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expected-component-manifest", required=True)
    parser.add_argument("--expected-canonical-fingerprint", required=True)
    parser.add_argument("--expected-runtime-fingerprint", required=True)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    inventory_path = args.component_inventory.resolve()
    output_dir = args.output_dir.resolve()
    rows = read_tsv(inventory_path)
    policy = read_json(args.component_policy.resolve())
    policy_verification = read_json(args.component_verification.resolve())
    phase1_final = read_json(args.phase1_final_verification.resolve())
    canonical_fingerprint = read_json(args.canonical_fingerprint.resolve())
    runtime_fingerprint = read_json(args.runtime_fingerprint.resolve())

    path_rows = {row["path"]: row for row in rows}
    if len(path_rows) != len(rows):
        raise SystemExit("component inventory contains duplicate paths")

    owned_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, str]] = []
    owned_by_artifact: dict[str, list[dict[str, str]]] = defaultdict(list)
    owner_by_path: dict[str, str] = {}

    for row in rows:
        component = row["component"]
        artifact = artifact_for_component(component)
        if artifact is None:
            if component != EXCLUDED_COMPONENT:
                raise SystemExit(f"unexpected component: {component}")
            excluded_rows.append(row)
            continue
        if row["path"] in owner_by_path:
            raise SystemExit(f"duplicate selected owner for path: {row['path']}")
        owner_by_path[row["path"]] = artifact
        owned_by_artifact[artifact].append(row)
        owned = {"artifact": artifact, "entry_class": "OWNED_PAYLOAD"}
        owned.update(row)
        owned_rows.append(owned)

    structural_rows: list[dict[str, Any]] = []
    structural_by_artifact: dict[str, set[str]] = defaultdict(set)
    required_counts: dict[tuple[str, str], int] = Counter()
    participants_by_directory: dict[str, set[str]] = defaultdict(set)
    descendants_by_directory: dict[str, int] = Counter()

    for artifact, artifact_rows in owned_by_artifact.items():
        for row in artifact_rows:
            for ancestor in ancestors(row["path"]):
                participants_by_directory[ancestor].add(artifact)
                descendants_by_directory[ancestor] += 1
                if owner_by_path.get(ancestor) != artifact:
                    structural_by_artifact[artifact].add(ancestor)
                    required_counts[(artifact, ancestor)] += 1

    for artifact in ARTIFACT_COMPONENTS:
        for path in sorted(structural_by_artifact[artifact]):
            directory = path_rows.get(path)
            owner_artifact = owner_by_path.get(path)
            structural_rows.append(
                {
                    "artifact": artifact,
                    "path": path,
                    "entry_class": "STRUCTURAL_PARENT",
                    "owner_artifact": owner_artifact or "",
                    "owner_component": directory["component"] if directory else "",
                    "required_by_owned_descendant_count": required_counts[(artifact, path)],
                    "participant_artifacts": ",".join(
                        sorted(participants_by_directory[path])
                    ),
                    "participant_count": len(participants_by_directory[path]),
                }
            )

    shared_paths = sorted({row["path"] for row in structural_rows})
    shared_rows: list[dict[str, Any]] = []
    for path in shared_paths:
        directory = path_rows.get(path)
        owner_artifact = owner_by_path.get(path)
        consumers = sorted(
            artifact
            for artifact in ARTIFACT_COMPONENTS
            if path in structural_by_artifact[artifact]
        )
        participants = sorted(
            participants_by_directory[path]
            | ({owner_artifact} if owner_artifact else set())
        )
        shared_rows.append(
            {
                "path": path,
                "owner_artifact": owner_artifact or "",
                "owner_component": directory["component"] if directory else "",
                "participant_artifacts": ",".join(participants),
                "participant_count": len(participants),
                "structural_consumer_artifacts": ",".join(consumers),
                "structural_consumer_count": len(consumers),
                "selected_descendant_count": descendants_by_directory[path],
            }
        )

    summary_rows: list[dict[str, Any]] = []
    for artifact in ARTIFACT_COMPONENTS:
        artifact_rows = owned_by_artifact[artifact]
        type_counts = Counter(row["type"] for row in artifact_rows)
        summary_rows.append(
            {
                "artifact": artifact,
                "disposition": (
                    "standalone-runtime"
                    if artifact == "runtime-base"
                    else "runtime-overlay-addon"
                ),
                "standalone": bool_text(artifact == "runtime-base"),
                "prerequisite_artifact": (
                    "" if artifact == "runtime-base" else "runtime-base"
                ),
                "owned_entry_count": len(artifact_rows),
                "owned_regular_file_count": type_counts["REGULAR"],
                "owned_directory_count": type_counts["DIRECTORY"],
                "owned_symlink_count": type_counts["SYMLINK"],
                "owned_elf_count": sum(
                    row["elf"] == "true" for row in artifact_rows
                ),
                "owned_regular_file_bytes": sum(
                    int(row["size"])
                    for row in artifact_rows
                    if row["type"] == "REGULAR"
                ),
                "structural_parent_count": len(structural_by_artifact[artifact]),
                "shared_namespace_count": sum(
                    artifact in row["participant_artifacts"].split(",")
                    for row in shared_rows
                ),
            }
        )

    selected_paths = set(owner_by_path)
    excluded_paths = {row["path"] for row in excluded_rows}
    symlink_rows = [row for row in owned_rows if row["type"] == "SYMLINK"]
    resolved_symlinks = {
        row["path"]: resolve_symlink(row["path"], row["symlink_target"])
        for row in symlink_rows
    }

    ownership_manifest = stable_manifest(owned_rows, OWNED_FIELDS)
    structural_manifest = stable_manifest(structural_rows, STRUCTURAL_FIELDS)
    shared_manifest = stable_manifest(shared_rows, SHARED_FIELDS)

    artifacts_model = []
    summary_by_artifact = {row["artifact"]: row for row in summary_rows}
    for artifact, components in ARTIFACT_COMPONENTS.items():
        summary = summary_by_artifact[artifact]
        artifacts_model.append(
            {
                "artifact": artifact,
                "components": list(components),
                "disposition": summary["disposition"],
                "standalone": summary["standalone"] == "true",
                "prerequisite": (
                    None
                    if artifact == "runtime-base"
                    else {
                        "artifact": "runtime-base",
                        "component_manifest_sha256": args.expected_component_manifest,
                        "runtime_fingerprint": args.expected_runtime_fingerprint,
                    }
                ),
                "owned_entry_count": summary["owned_entry_count"],
                "structural_parent_count": summary["structural_parent_count"],
            }
        )

    policy_runtime_artifact = next(
        (
            item
            for item in policy.get("artifacts", [])
            if isinstance(item, dict) and item.get("artifact") == "runtime-base"
        ),
        {},
    )
    phase1_summary = phase1_final.get("summary", {})

    checks = {
        "inventory_entry_count_3155": len(rows) == EXPECTED_TOTAL_COUNT,
        "inventory_paths_unique": len(path_rows) == EXPECTED_TOTAL_COUNT,
        "policy_schema_1": policy.get("schema_version") == 1,
        "policy_pass": policy.get("pass") is True,
        "policy_check_count_18": policy.get("check_count") == 18,
        "policy_failed_checks_empty": policy.get("failed_checks") == [],
        "policy_component_manifest_matches": policy.get(
            "component_manifest_sha256"
        )
        == args.expected_component_manifest,
        "policy_verification_schema_1": policy_verification.get("schema_version")
        == 1,
        "policy_verification_pass": policy_verification.get("pass") is True,
        "policy_verification_check_count_34": policy_verification.get(
            "check_count"
        )
        == 34,
        "policy_verification_failed_checks_empty": policy_verification.get(
            "failed_checks"
        )
        == [],
        "policy_verification_missing_outputs_empty": policy_verification.get(
            "missing_outputs"
        )
        == [],
        "policy_verification_parse_errors_empty": policy_verification.get(
            "parse_errors"
        )
        == {},
        "policy_verification_manifest_matches": policy_verification.get(
            "component_manifest_sha256"
        )
        == args.expected_component_manifest,
        "phase1_final_schema_1": phase1_final.get("schema_version") == 1,
        "phase1_final_pass": phase1_final.get("pass") is True,
        "phase1_final_check_count_47": phase1_final.get("check_count") == 47,
        "phase1_final_failed_checks_empty": phase1_final.get("failed_checks")
        == [],
        "phase1_final_missing_outputs_empty": phase1_final.get("missing_outputs")
        == [],
        "phase1_final_parse_errors_empty": phase1_final.get("parse_errors") == {},
        "phase1_final_component_manifest_matches": phase1_final.get(
            "expected", {}
        ).get("component_manifest_sha256")
        == args.expected_component_manifest,
        "phase1_final_runtime_fingerprint_matches": phase1_final.get(
            "expected", {}
        ).get("runtime_fingerprint")
        == args.expected_runtime_fingerprint,
        "phase1_final_canonical_fingerprint_matches": phase1_final.get(
            "expected", {}
        ).get("canonical_fingerprint")
        == args.expected_canonical_fingerprint,
        "phase1_final_runtime_entries_714": phase1_summary.get("runtime_entries")
        == 714,
        "phase1_final_extension_imports_67": phase1_summary.get(
            "extension_import_passes"
        )
        == 67,
        "canonical_fingerprint_schema_1": canonical_fingerprint.get(
            "schema_version"
        )
        == 1,
        "canonical_fingerprint_pass": canonical_fingerprint.get("pass") is True,
        "canonical_fingerprint_expected": canonical_fingerprint.get(
            "fingerprint"
        )
        == args.expected_canonical_fingerprint,
        "canonical_entry_count_3155": canonical_fingerprint.get("entry_count")
        == 3155,
        "runtime_fingerprint_schema_1": runtime_fingerprint.get("schema_version")
        == 1,
        "runtime_fingerprint_pass": runtime_fingerprint.get("pass") is True,
        "runtime_fingerprint_expected": runtime_fingerprint.get("fingerprint")
        == args.expected_runtime_fingerprint,
        "runtime_entry_count_714": runtime_fingerprint.get("entry_count") == 714,
        "runtime_artifact_policy_exact": policy_runtime_artifact.get("components")
        == list(ARTIFACT_COMPONENTS["runtime-base"]),
        "selected_entry_count_2956": len(owned_rows) == EXPECTED_SELECTED_COUNT,
        "excluded_entry_count_199": len(excluded_rows) == EXPECTED_EXCLUDED_COUNT,
        "selected_and_excluded_cover_inventory": selected_paths | excluded_paths
        == set(path_rows),
        "selected_and_excluded_disjoint": not (selected_paths & excluded_paths),
        "artifact_counts_exact": {
            artifact: len(owned_by_artifact[artifact])
            for artifact in ARTIFACT_COMPONENTS
        }
        == EXPECTED_ARTIFACT_COUNTS,
        "selected_path_ownership_unique": len(selected_paths) == len(owned_rows),
        "selected_types_allowed": all(
            row["type"] in ALLOWED_TYPES for row in owned_rows
        ),
        "selected_special_zero": all(
            row["type"] != "SPECIAL" for row in owned_rows
        ),
        "selected_symlink_count_5": len(symlink_rows)
        == EXPECTED_SELECTED_SYMLINKS,
        "selected_symlinks_relative_and_contained": all(
            resolved is not None for resolved in resolved_symlinks.values()
        ),
        "selected_symlink_targets_exist": all(
            resolved in path_rows
            for resolved in resolved_symlinks.values()
            if resolved is not None
        ),
        "selected_symlink_targets_same_artifact": all(
            resolved is not None
            and owner_by_path.get(resolved) == row["artifact"]
            for row in symlink_rows
            for resolved in [resolved_symlinks[row["path"]]]
        ),
        "selected_elf_count_81": sum(
            row["elf"] == "true" for row in owned_rows
        )
        == EXPECTED_SELECTED_ELF,
        "all_elf_runtime_base_owned": all(
            row["artifact"] == "runtime-base"
            for row in owned_rows
            if row["elf"] == "true"
        ),
        "license_path_selected": LICENSE_PATH in selected_paths,
        "license_path_runtime_owned": owner_by_path.get(LICENSE_PATH)
        == "runtime-base",
        "license_component_exact": path_rows.get(LICENSE_PATH, {}).get("component")
        == "LICENSE",
        "structural_parents_exist": all(
            row["path"] in path_rows for row in structural_rows
        ),
        "structural_parents_are_directories": all(
            path_rows[row["path"]]["type"] == "DIRECTORY"
            for row in structural_rows
        ),
        "structural_parent_owners_selected": all(
            row["owner_artifact"] in ARTIFACT_COMPONENTS
            for row in structural_rows
        ),
        "structural_parent_not_exactly_owned_by_consumer": all(
            row["owner_artifact"] != row["artifact"] for row in structural_rows
        ),
        "shared_namespace_nonempty": bool(shared_rows),
        "shared_namespace_participant_count_ge_2": all(
            int(row["participant_count"]) >= 2 for row in shared_rows
        ),
        "shared_namespace_structural_consumers_nonempty": all(
            int(row["structural_consumer_count"]) >= 1 for row in shared_rows
        ),
        "runtime_is_only_standalone_artifact": [
            row["artifact"]
            for row in summary_rows
            if row["standalone"] == "true"
        ]
        == ["runtime-base"],
        "addons_require_runtime_base": all(
            row["prerequisite_artifact"] == "runtime-base"
            for row in summary_rows
            if row["artifact"] != "runtime-base"
        ),
        "canonical_pycache_zero": canonical_fingerprint.get("pycache_paths")
        == [],
        "canonical_special_zero": canonical_fingerprint.get("special_paths")
        == [],
        "runtime_pycache_zero": runtime_fingerprint.get("pycache_paths") == [],
        "runtime_special_zero": runtime_fingerprint.get("special_paths") == [],
    }

    failed = sorted(name for name, passed in checks.items() if not passed)
    model = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "source": {
            "component_inventory": str(inventory_path),
            "component_manifest_sha256": args.expected_component_manifest,
            "canonical_fingerprint": args.expected_canonical_fingerprint,
            "runtime_fingerprint": args.expected_runtime_fingerprint,
            "canonical_entry_count": 3155,
            "selected_entry_count": len(owned_rows),
            "excluded_entry_count": len(excluded_rows),
        },
        "manifests": {
            "owned_paths_sha256": ownership_manifest,
            "structural_directories_sha256": structural_manifest,
            "shared_namespace_sha256": shared_manifest,
        },
        "candidate_envelope": {
            "archive_root": "<artifact-id>/",
            "metadata_root": "metadata/",
            "payload_root": "payload/",
            "extraction_semantics": "staging-not-installation",
            "payload_path_model": "prefix-relative",
            "forbidden": [
                "absolute-paths",
                "parent-traversal",
                "device-entries",
                "fifo-entries",
                "socket-entries",
                "hardlinks",
            ],
        },
        "ownership_contract": {
            "ownership_unit": "exact-manifest-path",
            "entry_classes": ["OWNED_PAYLOAD", "STRUCTURAL_PARENT"],
            "structural_parent_is_recursive_ownership": False,
            "directory_uninstall_candidate_rule": (
                "remove-owned-directory-only-when-empty"
            ),
            "unowned_descendant_policy": "preserve",
        },
        "license_contract": {
            "installed_payload_owner": "runtime-base",
            "installed_payload_path": LICENSE_PATH,
            "archive_envelope_license_material": (
                "required-for-every-distributable-artifact"
            ),
        },
        "artifacts": artifacts_model,
        "shared_namespace_directory_count": len(shared_rows),
        "claim_boundary": {
            "proved": (
                "The frozen selected components have disjoint exact payload ownership, "
                "and every external parent directory required for archive composition "
                "is explicitly represented as structural namespace rather than "
                "duplicate ownership."
            ),
            "not_proved": (
                "Archive bytes are reproducible or extraction and installation are "
                "transactionally safe."
            ),
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(
        output_dir / "artifact-owned-paths.tsv", OWNED_FIELDS, owned_rows
    )
    write_tsv(
        output_dir / "artifact-structural-directories.tsv",
        STRUCTURAL_FIELDS,
        structural_rows,
    )
    write_tsv(
        output_dir / "shared-namespace-directories.tsv",
        SHARED_FIELDS,
        shared_rows,
    )
    write_tsv(
        output_dir / "artifact-ownership-summary.tsv",
        SUMMARY_FIELDS,
        summary_rows,
    )
    (output_dir / "ownership-model.json").write_text(
        json.dumps(model, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "excluded-paths.txt").write_text(
        "".join(f"{path}\n" for path in sorted(excluded_paths)),
        encoding="utf-8",
    )

    print(json.dumps(model, indent=2, sort_keys=True))
    print()
    print(
        "STAGE3C_PHASE2_ARCHIVE_OWNERSHIP_ANALYSIS="
        + ("PASS" if model["pass"] else "FAIL")
    )
    if args.require_pass and not model["pass"]:
        return 24
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
