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
    "path", "type", "mode", "size", "mtime_ns", "sha256", "symlink_target",
    "elf", "role", "rule_id", "reason", "descendant_roles", "mixed_directory",
    "component", "policy_rule", "policy_reason",
)
OWNED_FIELDS = ("artifact", "entry_class", *SOURCE_FIELDS)
STRUCTURAL_FIELDS = (
    "artifact", "path", "entry_class", "owner_artifact", "owner_component",
    "required_by_owned_descendant_count", "participant_artifacts", "participant_count",
)
SHARED_FIELDS = (
    "path", "owner_artifact", "owner_component", "participant_artifacts",
    "participant_count", "structural_consumer_artifacts",
    "structural_consumer_count", "selected_descendant_count",
)
SUMMARY_FIELDS = (
    "artifact", "disposition", "standalone", "prerequisite_artifact",
    "owned_entry_count", "owned_regular_file_count", "owned_directory_count",
    "owned_symlink_count", "owned_elf_count", "owned_regular_file_bytes",
    "structural_parent_count", "shared_namespace_count",
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
EXPECTED_COUNTS = {
    "runtime-base": 714,
    "development-addon": 454,
    "test-addon": 1788,
}
EXPECTED_SELECTED = 2956
EXPECTED_EXCLUDED = 199
EXPECTED_TOTAL = 3155
EXPECTED_ELF = 81
EXPECTED_SYMLINKS = 5
LICENSE_PATH = "lib/python3.14/LICENSE.txt"


def read_json_safe(
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
        errors[str(path)] = "top-level JSON is not an object"
        return {}
    return value


def read_tsv_safe(
    path: Path,
    expected_fields: tuple[str, ...],
    missing: list[str],
    errors: dict[str, str],
) -> list[dict[str, str]]:
    if not path.is_file():
        missing.append(str(path))
        return []
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != expected_fields:
                errors[str(path)] = (
                    f"schema mismatch: {tuple(reader.fieldnames or ())!r}"
                )
                return []
            return list(reader)
    except OSError as exc:
        errors[str(path)] = repr(exc)
        return []


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


def artifact_for(component: str) -> str | None:
    return COMPONENT_ARTIFACT.get(component)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def normalize_rows(
    rows: list[dict[str, Any]],
    fields: tuple[str, ...],
) -> list[tuple[str, ...]]:
    return sorted(
        tuple(str(row.get(field, "")) for field in fields) for row in rows
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component-inventory", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--canonical-before", required=True, type=Path)
    parser.add_argument("--canonical-after", required=True, type=Path)
    parser.add_argument("--runtime-before", required=True, type=Path)
    parser.add_argument("--runtime-after", required=True, type=Path)
    parser.add_argument("--expected-component-manifest", required=True)
    parser.add_argument("--expected-canonical-fingerprint", required=True)
    parser.add_argument("--expected-runtime-fingerprint", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    missing: list[str] = []
    errors: dict[str, str] = {}

    source_rows = read_tsv_safe(
        args.component_inventory.resolve(), SOURCE_FIELDS, missing, errors
    )
    owned_rows = read_tsv_safe(
        output_dir / "artifact-owned-paths.tsv",
        OWNED_FIELDS,
        missing,
        errors,
    )
    structural_rows = read_tsv_safe(
        output_dir / "artifact-structural-directories.tsv",
        STRUCTURAL_FIELDS,
        missing,
        errors,
    )
    shared_rows = read_tsv_safe(
        output_dir / "shared-namespace-directories.tsv",
        SHARED_FIELDS,
        missing,
        errors,
    )
    summary_rows = read_tsv_safe(
        output_dir / "artifact-ownership-summary.tsv",
        SUMMARY_FIELDS,
        missing,
        errors,
    )
    model = read_json_safe(
        output_dir / "ownership-model.json", missing, errors
    )
    canonical_before = read_json_safe(
        args.canonical_before.resolve(), missing, errors
    )
    canonical_after = read_json_safe(
        args.canonical_after.resolve(), missing, errors
    )
    runtime_before = read_json_safe(
        args.runtime_before.resolve(), missing, errors
    )
    runtime_after = read_json_safe(
        args.runtime_after.resolve(), missing, errors
    )

    path_rows = {row["path"]: row for row in source_rows}
    expected_owned: list[dict[str, Any]] = []
    expected_excluded: set[str] = set()
    owner_by_path: dict[str, str] = {}
    owned_by_artifact: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        artifact = artifact_for(row["component"])
        if artifact is None:
            expected_excluded.add(row["path"])
            continue
        owner_by_path[row["path"]] = artifact
        owned_by_artifact[artifact].append(row)
        item = {"artifact": artifact, "entry_class": "OWNED_PAYLOAD"}
        item.update(row)
        expected_owned.append(item)

    structural_sets: dict[str, set[str]] = defaultdict(set)
    required_counts: dict[tuple[str, str], int] = Counter()
    participants: dict[str, set[str]] = defaultdict(set)
    descendant_counts: dict[str, int] = Counter()
    for artifact, rows in owned_by_artifact.items():
        for row in rows:
            for parent in ancestors(row["path"]):
                participants[parent].add(artifact)
                descendant_counts[parent] += 1
                if owner_by_path.get(parent) != artifact:
                    structural_sets[artifact].add(parent)
                    required_counts[(artifact, parent)] += 1

    expected_structural: list[dict[str, Any]] = []
    for artifact in ARTIFACT_COMPONENTS:
        for path in sorted(structural_sets[artifact]):
            source = path_rows.get(path, {})
            expected_structural.append(
                {
                    "artifact": artifact,
                    "path": path,
                    "entry_class": "STRUCTURAL_PARENT",
                    "owner_artifact": owner_by_path.get(path, ""),
                    "owner_component": source.get("component", ""),
                    "required_by_owned_descendant_count": required_counts[
                        (artifact, path)
                    ],
                    "participant_artifacts": ",".join(
                        sorted(participants[path])
                    ),
                    "participant_count": len(participants[path]),
                }
            )

    expected_shared: list[dict[str, Any]] = []
    for path in sorted({row["path"] for row in expected_structural}):
        source = path_rows.get(path, {})
        owner = owner_by_path.get(path, "")
        consumers = sorted(
            artifact
            for artifact in ARTIFACT_COMPONENTS
            if path in structural_sets[artifact]
        )
        participant_set = set(participants[path])
        if owner:
            participant_set.add(owner)
        expected_shared.append(
            {
                "path": path,
                "owner_artifact": owner,
                "owner_component": source.get("component", ""),
                "participant_artifacts": ",".join(
                    sorted(participant_set)
                ),
                "participant_count": len(participant_set),
                "structural_consumer_artifacts": ",".join(consumers),
                "structural_consumer_count": len(consumers),
                "selected_descendant_count": descendant_counts[path],
            }
        )

    expected_summary: list[dict[str, Any]] = []
    for artifact in ARTIFACT_COMPONENTS:
        rows = owned_by_artifact[artifact]
        types = Counter(row["type"] for row in rows)
        expected_summary.append(
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
                "owned_entry_count": len(rows),
                "owned_regular_file_count": types["REGULAR"],
                "owned_directory_count": types["DIRECTORY"],
                "owned_symlink_count": types["SYMLINK"],
                "owned_elf_count": sum(
                    row["elf"] == "true" for row in rows
                ),
                "owned_regular_file_bytes": sum(
                    int(row["size"])
                    for row in rows
                    if row["type"] == "REGULAR"
                ),
                "structural_parent_count": len(structural_sets[artifact]),
                "shared_namespace_count": sum(
                    artifact in row["participant_artifacts"].split(",")
                    for row in expected_shared
                ),
            }
        )

    owned_paths = [row["path"] for row in owned_rows]
    artifacts = model.get("artifacts", [])
    artifact_model = {
        item.get("artifact"): item
        for item in artifacts
        if isinstance(item, dict)
    }
    model_checks = model.get("checks", {})
    manifests = model.get("manifests", {})
    envelope = model.get("candidate_envelope", {})
    ownership_contract = model.get("ownership_contract", {})
    license_contract = model.get("license_contract", {})

    checks = {
        "all_required_outputs_present": not missing,
        "all_required_outputs_parse": not errors,
        "source_entry_count_3155": len(source_rows) == EXPECTED_TOTAL,
        "source_paths_unique": len(path_rows) == EXPECTED_TOTAL,
        "owned_schema_rows_2956": len(owned_rows) == EXPECTED_SELECTED,
        "owned_rows_exact": normalize_rows(owned_rows, OWNED_FIELDS)
        == normalize_rows(expected_owned, OWNED_FIELDS),
        "owned_paths_unique": len(set(owned_paths)) == len(owned_paths),
        "owned_path_overlap_zero": sum(
            len(rows) for rows in owned_by_artifact.values()
        )
        == len(set(owner_by_path)),
        "owned_artifact_set_exact": {
            row["artifact"] for row in owned_rows
        }
        == set(ARTIFACT_COMPONENTS),
        "artifact_counts_exact": Counter(
            row["artifact"] for row in owned_rows
        )
        == Counter(EXPECTED_COUNTS),
        "excluded_count_199": len(expected_excluded) == EXPECTED_EXCLUDED,
        "owned_plus_excluded_cover_source": set(owned_paths)
        | expected_excluded
        == set(path_rows),
        "owned_and_excluded_disjoint": not (
            set(owned_paths) & expected_excluded
        ),
        "selected_symlink_count_5": sum(
            row["type"] == "SYMLINK" for row in owned_rows
        )
        == EXPECTED_SYMLINKS,
        "selected_elf_count_81": sum(
            row["elf"] == "true" for row in owned_rows
        )
        == EXPECTED_ELF,
        "all_elf_runtime_owned": all(
            row["artifact"] == "runtime-base"
            for row in owned_rows
            if row["elf"] == "true"
        ),
        "license_runtime_owned": any(
            row["path"] == LICENSE_PATH
            and row["artifact"] == "runtime-base"
            and row["component"] == "LICENSE"
            for row in owned_rows
        ),
        "structural_rows_exact": normalize_rows(
            structural_rows, STRUCTURAL_FIELDS
        )
        == normalize_rows(expected_structural, STRUCTURAL_FIELDS),
        "structural_keys_unique": len(
            {(row["artifact"], row["path"]) for row in structural_rows}
        )
        == len(structural_rows),
        "structural_entry_class_exact": all(
            row["entry_class"] == "STRUCTURAL_PARENT"
            for row in structural_rows
        ),
        "structural_paths_are_source_directories": all(
            row["path"] in path_rows
            and path_rows[row["path"]]["type"] == "DIRECTORY"
            for row in structural_rows
        ),
        "structural_owners_selected": all(
            row["owner_artifact"] in ARTIFACT_COMPONENTS
            for row in structural_rows
        ),
        "structural_consumer_not_owner": all(
            row["artifact"] != row["owner_artifact"]
            for row in structural_rows
        ),
        "shared_rows_exact": normalize_rows(shared_rows, SHARED_FIELDS)
        == normalize_rows(expected_shared, SHARED_FIELDS),
        "shared_paths_unique": len(
            {row["path"] for row in shared_rows}
        )
        == len(shared_rows),
        "shared_participant_count_ge_2": all(
            int(row["participant_count"]) >= 2 for row in shared_rows
        ),
        "shared_consumer_count_ge_1": all(
            int(row["structural_consumer_count"]) >= 1
            for row in shared_rows
        ),
        "summary_rows_exact": normalize_rows(
            summary_rows, SUMMARY_FIELDS
        )
        == normalize_rows(expected_summary, SUMMARY_FIELDS),
        "summary_artifact_set_exact": {
            row["artifact"] for row in summary_rows
        }
        == set(ARTIFACT_COMPONENTS),
        "runtime_only_standalone": [
            row["artifact"]
            for row in summary_rows
            if row["standalone"] == "true"
        ]
        == ["runtime-base"],
        "addons_require_runtime": all(
            row["prerequisite_artifact"] == "runtime-base"
            for row in summary_rows
            if row["artifact"] != "runtime-base"
        ),
        "model_schema_1": model.get("schema_version") == 1,
        "model_pass": model.get("pass") is True,
        "model_check_count_64": model.get("check_count") == 64,
        "model_failed_checks_empty": model.get("failed_checks") == [],
        "model_checks_exact_and_true": len(model_checks) == 64
        and all(value is True for value in model_checks.values()),
        "model_component_manifest": model.get("source", {}).get(
            "component_manifest_sha256"
        )
        == args.expected_component_manifest,
        "model_canonical_fingerprint": model.get("source", {}).get(
            "canonical_fingerprint"
        )
        == args.expected_canonical_fingerprint,
        "model_runtime_fingerprint": model.get("source", {}).get(
            "runtime_fingerprint"
        )
        == args.expected_runtime_fingerprint,
        "model_selected_count_2956": model.get("source", {}).get(
            "selected_entry_count"
        )
        == EXPECTED_SELECTED,
        "model_excluded_count_199": model.get("source", {}).get(
            "excluded_entry_count"
        )
        == EXPECTED_EXCLUDED,
        "owned_manifest_matches": manifests.get("owned_paths_sha256")
        == stable_manifest(owned_rows, OWNED_FIELDS),
        "structural_manifest_matches": manifests.get(
            "structural_directories_sha256"
        )
        == stable_manifest(structural_rows, STRUCTURAL_FIELDS),
        "shared_manifest_matches": manifests.get(
            "shared_namespace_sha256"
        )
        == stable_manifest(shared_rows, SHARED_FIELDS),
        "artifact_model_set_exact": set(artifact_model)
        == set(ARTIFACT_COMPONENTS),
        "artifact_model_components_exact": all(
            artifact_model.get(artifact, {}).get("components")
            == list(components)
            for artifact, components in ARTIFACT_COMPONENTS.items()
        ),
        "artifact_model_counts_exact": all(
            artifact_model.get(artifact, {}).get("owned_entry_count")
            == count
            for artifact, count in EXPECTED_COUNTS.items()
        ),
        "runtime_model_standalone": artifact_model.get(
            "runtime-base", {}
        ).get("standalone")
        is True,
        "addon_model_prerequisites_exact": all(
            artifact_model.get(artifact, {})
            .get("prerequisite", {})
            .get("artifact")
            == "runtime-base"
            for artifact in ("development-addon", "test-addon")
        ),
        "addon_model_component_manifest_exact": all(
            artifact_model.get(artifact, {})
            .get("prerequisite", {})
            .get("component_manifest_sha256")
            == args.expected_component_manifest
            for artifact in ("development-addon", "test-addon")
        ),
        "addon_model_runtime_fingerprint_exact": all(
            artifact_model.get(artifact, {})
            .get("prerequisite", {})
            .get("runtime_fingerprint")
            == args.expected_runtime_fingerprint
            for artifact in ("development-addon", "test-addon")
        ),
        "envelope_staging_not_installation": envelope.get(
            "extraction_semantics"
        )
        == "staging-not-installation",
        "envelope_payload_prefix_relative": envelope.get(
            "payload_path_model"
        )
        == "prefix-relative",
        "envelope_roots_exact": envelope.get("metadata_root")
        == "metadata/"
        and envelope.get("payload_root") == "payload/",
        "envelope_forbidden_exact": set(envelope.get("forbidden", []))
        == {
            "absolute-paths",
            "parent-traversal",
            "device-entries",
            "fifo-entries",
            "socket-entries",
            "hardlinks",
        },
        "ownership_unit_exact_path": ownership_contract.get(
            "ownership_unit"
        )
        == "exact-manifest-path",
        "ownership_entry_classes_exact": ownership_contract.get(
            "entry_classes"
        )
        == ["OWNED_PAYLOAD", "STRUCTURAL_PARENT"],
        "structural_not_recursive_ownership": ownership_contract.get(
            "structural_parent_is_recursive_ownership"
        )
        is False,
        "unowned_descendants_preserved": ownership_contract.get(
            "unowned_descendant_policy"
        )
        == "preserve",
        "license_contract_runtime_owner": license_contract.get(
            "installed_payload_owner"
        )
        == "runtime-base",
        "license_contract_path_exact": license_contract.get(
            "installed_payload_path"
        )
        == LICENSE_PATH,
        "license_envelope_required_all": license_contract.get(
            "archive_envelope_license_material"
        )
        == "required-for-every-distributable-artifact",
        "canonical_before_pass": canonical_before.get("pass") is True,
        "canonical_after_pass": canonical_after.get("pass") is True,
        "canonical_entry_count_3155": canonical_before.get("entry_count")
        == canonical_after.get("entry_count")
        == 3155,
        "canonical_fingerprint_expected": canonical_before.get("fingerprint")
        == args.expected_canonical_fingerprint,
        "canonical_not_mutated": canonical_before.get("fingerprint")
        == canonical_after.get("fingerprint"),
        "runtime_before_pass": runtime_before.get("pass") is True,
        "runtime_after_pass": runtime_after.get("pass") is True,
        "runtime_entry_count_714": runtime_before.get("entry_count")
        == runtime_after.get("entry_count")
        == 714,
        "runtime_fingerprint_expected": runtime_before.get("fingerprint")
        == args.expected_runtime_fingerprint,
        "runtime_not_mutated": runtime_before.get("fingerprint")
        == runtime_after.get("fingerprint"),
        "canonical_pycache_special_zero": canonical_before.get(
            "pycache_paths"
        )
        == []
        and canonical_after.get("pycache_paths") == []
        and canonical_before.get("special_paths") == []
        and canonical_after.get("special_paths") == [],
        "runtime_pycache_special_zero": runtime_before.get("pycache_paths")
        == []
        and runtime_after.get("pycache_paths") == []
        and runtime_before.get("special_paths") == []
        and runtime_after.get("special_paths") == [],
    }

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "missing_outputs": sorted(set(missing)),
        "parse_errors": errors,
        "expected": {
            "component_manifest_sha256": args.expected_component_manifest,
            "canonical_fingerprint": args.expected_canonical_fingerprint,
            "runtime_fingerprint": args.expected_runtime_fingerprint,
            "selected_entries": EXPECTED_SELECTED,
            "excluded_entries": EXPECTED_EXCLUDED,
            "artifact_counts": EXPECTED_COUNTS,
        },
        "observed": {
            "owned_manifest_sha256": stable_manifest(
                owned_rows, OWNED_FIELDS
            ),
            "structural_manifest_sha256": stable_manifest(
                structural_rows, STRUCTURAL_FIELDS
            ),
            "shared_namespace_manifest_sha256": stable_manifest(
                shared_rows, SHARED_FIELDS
            ),
            "structural_row_count": len(structural_rows),
            "shared_namespace_count": len(shared_rows),
            "artifact_summary": summary_rows,
        },
        "claim_boundary": {
            "proved": (
                "Selected archive artifacts have disjoint exact payload ownership "
                "and an independently reproduced structural-directory namespace "
                "model."
            ),
            "not_proved": (
                "Archive serialization is reproducible or installation transactions "
                "are safe."
            ),
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 25


if __name__ == "__main__":
    raise SystemExit(main())
