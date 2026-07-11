#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from artifact_manifest_contract import (
    ARTIFACTS,
    ARTIFACT_COMPONENTS,
    EXPECTED_COUNTS,
    LICENSE_PATH,
    OWNED_FIELDS,
    PRODUCT,
    SOURCE_FIELDS,
    STRUCTURAL_FIELDS,
    artifact_id,
    canonical_json_bytes,
    read_json_safe,
    read_tsv_safe,
    safe_relative,
    sha256_file,
)


def owned_entry(row: dict[str, str]) -> dict[str, Any]:
    item: dict[str, Any] = {
        "archive_path": "payload/" + row["path"],
        "component": row["component"],
        "elf": row["elf"] == "true",
        "entry_class": "OWNED_PAYLOAD",
        "mode": row["mode"],
        "payload_path": row["path"],
        "type": row["type"].lower(),
    }
    if row["type"] == "REGULAR":
        item["sha256"] = row["sha256"]
        item["size"] = int(row["size"])
    elif row["type"] == "SYMLINK":
        item["symlink_target"] = row["symlink_target"]
    return item


def structural_entry(
    row: dict[str, str], source_by_path: dict[str, dict[str, str]]
) -> dict[str, Any]:
    return {
        "archive_path": "payload/" + row["path"],
        "entry_class": "STRUCTURAL_PARENT",
        "mode": source_by_path[row["path"]]["mode"],
        "owner_artifact": row["owner_artifact"],
        "owner_component": row["owner_component"],
        "payload_path": row["path"],
        "type": "directory",
    }


def expected_manifest(
    name: str,
    owned: list[dict[str, str]],
    structural: list[dict[str, str]],
    source_by_path: dict[str, dict[str, str]],
    license_row: dict[str, str],
    lock_sha: str,
    component_manifest: str,
    canonical_fingerprint: str,
    runtime_fingerprint: str,
    owned_manifest: str,
    structural_manifest: str,
    shared_manifest: str,
) -> dict[str, Any]:
    standalone = name == "runtime-base"
    entries = sorted(
        [owned_entry(row) for row in owned]
        + [structural_entry(row, source_by_path) for row in structural],
        key=lambda item: (item["payload_path"], item["entry_class"]),
    )
    prerequisite = None if standalone else {
        "artifact": "runtime-base",
        "artifact_id": artifact_id("runtime-base"),
        "android_api": PRODUCT["android_api"],
        "component_manifest_sha256": component_manifest,
        "python_version": PRODUCT["python_version"],
        "runtime_fingerprint": runtime_fingerprint,
        "target_host": PRODUCT["target_host"],
    }
    return {
        "schema_version": 1,
        "manifest_kind": "cpython-android-cli-artifact-manifest",
        "artifact": {
            "artifact_id": artifact_id(name),
            "components": ARTIFACT_COMPONENTS[name],
            "disposition": (
                "standalone-runtime" if standalone else "runtime-overlay-addon"
            ),
            "name": name,
            "standalone": standalone,
        },
        "product": {
            "product_kind": PRODUCT["product_kind"],
            "python_implementation": "CPython",
            "python_version": PRODUCT["python_version"],
            "source_head": PRODUCT["source_head"],
            "target": {
                "android_api": PRODUCT["android_api"],
                "architecture": PRODUCT["architecture"],
                "host": PRODUCT["target_host"],
                "multiarch": PRODUCT["multiarch"],
                "ndk_version": PRODUCT["ndk_version"],
                "platform": PRODUCT["platform"],
                "soabi": PRODUCT["soabi"],
            },
        },
        "compatibility": {
            "canonical_product_fingerprint": canonical_fingerprint,
            "component_manifest_sha256": component_manifest,
            "ownership_manifests": {
                "owned_paths_sha256": owned_manifest,
                "shared_namespace_sha256": shared_manifest,
                "structural_directories_sha256": structural_manifest,
            },
            "prerequisite": prerequisite,
            "runtime_base_fingerprint": runtime_fingerprint,
        },
        "layout": {
            "archive_root": artifact_id(name) + "/",
            "extraction_semantics": "staging-not-installation",
            "metadata_root": "metadata/",
            "payload_paths": "prefix-relative",
            "payload_root": "payload/",
        },
        "ownership": {
            "directory_removal_rule": "remove-owned-directory-only-when-empty",
            "manifest_entry_count": len(entries),
            "non_owning_entry_classes": ["STRUCTURAL_PARENT"],
            "owned_entry_count": len(owned),
            "ownership_unit": "exact-manifest-path",
            "register_entry_classes": ["OWNED_PAYLOAD"],
            "structural_parent_count": len(structural),
            "unowned_descendant_policy": "preserve",
        },
        "license": {
            "archive_metadata_path": "metadata/licenses/CPython-LICENSE.txt",
            "installed_payload_owner": "runtime-base",
            "installed_payload_path": LICENSE_PATH if standalone else None,
            "sha256": license_row["sha256"],
            "size": int(license_row["size"]),
            "source_payload_path": LICENSE_PATH,
        },
        "provenance": {
            "phase1_final_verification": "input/phase1-final-verification.json",
            "phase2_ownership_model": "input/ownership-model.json",
            "phase2_ownership_verification": "input/ownership-verification.json",
            "phase2_safety_verification": "input/ownership-safety-verification.json",
            "product_lock_path": (
                "config/products/cpython-3.14.6-aarch64-linux-android.lock.json"
            ),
            "product_lock_sha256": lock_sha,
            "source_archive": PRODUCT["source_archive"],
        },
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ownership-dir", required=True, type=Path)
    parser.add_argument("--manifest-output-dir", required=True, type=Path)
    parser.add_argument("--product-lock", required=True, type=Path)
    parser.add_argument("--canonical-before", required=True, type=Path)
    parser.add_argument("--canonical-after", required=True, type=Path)
    parser.add_argument("--runtime-before", required=True, type=Path)
    parser.add_argument("--runtime-after", required=True, type=Path)
    parser.add_argument("--expected-component-manifest", required=True)
    parser.add_argument("--expected-canonical-fingerprint", required=True)
    parser.add_argument("--expected-runtime-fingerprint", required=True)
    parser.add_argument("--expected-owned-manifest", required=True)
    parser.add_argument("--expected-structural-manifest", required=True)
    parser.add_argument("--expected-shared-manifest", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    ownership = args.ownership_dir.resolve()
    manifest_output = args.manifest_output_dir.resolve()
    missing: list[str] = []
    errors: dict[str, str] = {}

    product_lock_path = args.product_lock.resolve()
    product_lock = read_json_safe(product_lock_path, missing, errors)
    generation = read_json_safe(manifest_output / "generation.json", missing, errors)
    index = read_json_safe(manifest_output / "manifest-index.json", missing, errors)
    manifests = {
        name: read_json_safe(
            manifest_output / "manifests" / f"{name}.manifest.json",
            missing,
            errors,
        )
        for name in ARTIFACTS
    }
    owned_rows = read_tsv_safe(
        ownership / "artifact-owned-paths.tsv", OWNED_FIELDS, missing, errors
    )
    structural_rows = read_tsv_safe(
        ownership / "artifact-structural-directories.tsv",
        STRUCTURAL_FIELDS,
        missing,
        errors,
    )
    source_rows = read_tsv_safe(
        ownership / "input/component-inventory.tsv", SOURCE_FIELDS, missing, errors
    )
    ownership_model = read_json_safe(
        ownership / "ownership-model.json", missing, errors
    )
    ownership_verification = read_json_safe(
        ownership / "verification.json", missing, errors
    )
    safety_verification = read_json_safe(
        ownership / "safety-verification.json", missing, errors
    )
    canonical_before = read_json_safe(args.canonical_before.resolve(), missing, errors)
    canonical_after = read_json_safe(args.canonical_after.resolve(), missing, errors)
    runtime_before = read_json_safe(args.runtime_before.resolve(), missing, errors)
    runtime_after = read_json_safe(args.runtime_after.resolve(), missing, errors)

    source_by_path = {row["path"]: row for row in source_rows}
    owned_by_artifact: dict[str, list[dict[str, str]]] = defaultdict(list)
    structural_by_artifact: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in owned_rows:
        owned_by_artifact[row["artifact"]].append(row)
    for row in structural_rows:
        structural_by_artifact[row["artifact"]].append(row)
    license_row = next(
        (row for row in owned_rows if row["path"] == LICENSE_PATH), {}
    )
    lock_sha = sha256_file(product_lock_path) if product_lock_path.is_file() else ""

    expected = {
        name: expected_manifest(
            name,
            owned_by_artifact[name],
            structural_by_artifact[name],
            source_by_path,
            license_row,
            lock_sha,
            args.expected_component_manifest,
            args.expected_canonical_fingerprint,
            args.expected_runtime_fingerprint,
            args.expected_owned_manifest,
            args.expected_structural_manifest,
            args.expected_shared_manifest,
        )
        for name in ARTIFACTS
    }
    index_items = index.get("artifacts", [])
    index_by_name = {
        item.get("artifact"): item
        for item in index_items
        if isinstance(item, dict)
    }
    all_entries = [
        entry for manifest in manifests.values() for entry in manifest.get("entries", [])
    ]
    owned_paths = {
        name: {
            entry.get("payload_path")
            for entry in manifests[name].get("entries", [])
            if entry.get("entry_class") == "OWNED_PAYLOAD"
        }
        for name in ARTIFACTS
    }
    overlap_counts = Counter(path for paths in owned_paths.values() for path in paths)

    checks: dict[str, bool] = {
        "all_required_outputs_present": not missing,
        "all_required_outputs_parse": not errors,
        "generation_pass_42": generation.get("pass") is True
        and generation.get("check_count") == 42
        and generation.get("failed_checks") == [],
        "ownership_inputs_pass": ownership_model.get("pass") is True
        and ownership_model.get("check_count") == 64
        and ownership_verification.get("pass") is True
        and ownership_verification.get("check_count") == 74
        and safety_verification.get("pass") is True
        and safety_verification.get("check_count") == 9,
        "product_lock_exact": product_lock.get("schema_version") == 1
        and product_lock.get("product_kind") == PRODUCT["product_kind"]
        and product_lock.get("python_version") == PRODUCT["python_version"]
        and product_lock.get("source_head") == PRODUCT["source_head"]
        and product_lock.get("target_host") == PRODUCT["target_host"]
        and product_lock.get("android_api") == PRODUCT["android_api"]
        and product_lock.get("ndk_version") == PRODUCT["ndk_version"]
        and product_lock.get("archive") == PRODUCT["source_archive"]
        and product_lock.get("package_prefix_root") == "prefix",
        "product_lock_hash_matches": generation.get("product_lock_sha256")
        == lock_sha,
        "index_schema_exact": index.get("schema_version") == 1
        and index.get("index_kind")
        == "cpython-android-cli-artifact-manifest-index",
        "index_product_exact": index.get("product")
        == {
            "android_api": PRODUCT["android_api"],
            "python_version": PRODUCT["python_version"],
            "target_host": PRODUCT["target_host"],
        },
        "index_identity_exact": index.get("component_manifest_sha256")
        == args.expected_component_manifest
        and index.get("owned_paths_manifest_sha256")
        == args.expected_owned_manifest,
        "index_artifact_set_exact": set(index_by_name) == set(ARTIFACTS)
        and len(index_items) == 3,
        "generation_index_exact": generation.get("manifest_index") == index,
        "generation_index_hash_exact": generation.get("manifest_index_sha256")
        == sha256_file(manifest_output / "manifest-index.json"),
        "manifest_objects_exact": all(manifests[name] == expected[name] for name in ARTIFACTS),
        "manifest_schema_kind_exact": all(
            manifests[name].get("schema_version") == 1
            and manifests[name].get("manifest_kind")
            == "cpython-android-cli-artifact-manifest"
            for name in ARTIFACTS
        ),
        "artifact_identity_exact": all(
            manifests[name].get("artifact") == expected[name]["artifact"]
            for name in ARTIFACTS
        ),
        "product_identity_exact": all(
            manifests[name].get("product") == expected[name]["product"]
            for name in ARTIFACTS
        ),
        "compatibility_exact": all(
            manifests[name].get("compatibility") == expected[name]["compatibility"]
            for name in ARTIFACTS
        ),
        "layout_exact": all(
            manifests[name].get("layout") == expected[name]["layout"]
            for name in ARTIFACTS
        ),
        "ownership_contract_exact": all(
            manifests[name].get("ownership") == expected[name]["ownership"]
            for name in ARTIFACTS
        ),
        "license_contract_exact": all(
            manifests[name].get("license") == expected[name]["license"]
            for name in ARTIFACTS
        ),
        "provenance_exact": all(
            manifests[name].get("provenance") == expected[name]["provenance"]
            for name in ARTIFACTS
        ),
        "entries_exact": all(
            manifests[name].get("entries") == expected[name]["entries"]
            for name in ARTIFACTS
        ),
        "owned_counts_exact": {
            name: len(owned_paths[name]) for name in ARTIFACTS
        }
        == {name: EXPECTED_COUNTS[name]["owned"] for name in ARTIFACTS},
        "structural_counts_exact": {
            name: sum(
                entry.get("entry_class") == "STRUCTURAL_PARENT"
                for entry in manifests[name].get("entries", [])
            )
            for name in ARTIFACTS
        }
        == {name: EXPECTED_COUNTS[name]["structural"] for name in ARTIFACTS},
        "manifest_counts_exact": {
            name: len(manifests[name].get("entries", [])) for name in ARTIFACTS
        }
        == {name: EXPECTED_COUNTS[name]["total"] for name in ARTIFACTS},
        "combined_counts_exact": sum(len(paths) for paths in owned_paths.values())
        == 2956
        and sum(
            entry.get("entry_class") == "STRUCTURAL_PARENT" for entry in all_entries
        )
        == 4
        and len(all_entries) == 2960,
        "cross_artifact_owned_overlap_zero": all(
            count == 1 for count in overlap_counts.values()
        ),
        "paths_safe": all(
            safe_relative(entry.get("archive_path"))
            and str(entry.get("archive_path")).startswith("payload/")
            and safe_relative(entry.get("payload_path"))
            for entry in all_entries
        ),
        "archive_paths_unique_per_artifact": all(
            len({entry.get("archive_path") for entry in manifests[name]["entries"]})
            == len(manifests[name]["entries"])
            for name in ARTIFACTS
        ),
        "entry_classes_exact": {entry.get("entry_class") for entry in all_entries}
        == {"OWNED_PAYLOAD", "STRUCTURAL_PARENT"},
        "entry_types_allowed": {entry.get("type") for entry in all_entries}
        <= {"regular", "directory", "symlink"},
        "regular_fields_exact": all(
            isinstance(entry.get("size"), int)
            and len(entry.get("sha256", "")) == 64
            and "symlink_target" not in entry
            for entry in all_entries
            if entry.get("type") == "regular"
        ),
        "directory_fields_exact": all(
            "size" not in entry
            and "sha256" not in entry
            and "symlink_target" not in entry
            for entry in all_entries
            if entry.get("type") == "directory"
        ),
        "symlink_fields_exact": all(
            bool(entry.get("symlink_target"))
            and "size" not in entry
            and "sha256" not in entry
            for entry in all_entries
            if entry.get("type") == "symlink"
        ),
        "structural_directory_only": all(
            entry.get("type") == "directory"
            for entry in all_entries
            if entry.get("entry_class") == "STRUCTURAL_PARENT"
        ),
        "structural_paths_exact": {
            name: {
                entry.get("payload_path")
                for entry in manifests[name]["entries"]
                if entry.get("entry_class") == "STRUCTURAL_PARENT"
            }
            for name in ARTIFACTS
        }
        == {
            "runtime-base": set(),
            "development-addon": {"lib", "lib/python3.14"},
            "test-addon": {"lib", "lib/python3.14"},
        },
        "all_elf_runtime_owned": sum(
            entry.get("elf") is True
            for entry in manifests["runtime-base"]["entries"]
        )
        == 81
        and all(
            entry.get("elf") is False
            for name in ("development-addon", "test-addon")
            for entry in manifests[name]["entries"]
            if entry.get("entry_class") == "OWNED_PAYLOAD"
        ),
        "runtime_standalone_only": manifests["runtime-base"]["artifact"][
            "standalone"
        ]
        is True
        and all(
            manifests[name]["artifact"]["standalone"] is False
            for name in ("development-addon", "test-addon")
        ),
        "prerequisites_exact": manifests["runtime-base"]["compatibility"][
            "prerequisite"
        ]
        is None
        and all(
            manifests[name]["compatibility"]["prerequisite"]
            == expected[name]["compatibility"]["prerequisite"]
            for name in ("development-addon", "test-addon")
        ),
        "license_hash_equal_all": len(
            {manifests[name]["license"]["sha256"] for name in ARTIFACTS}
        )
        == 1,
        "license_installed_path_runtime_only": manifests["runtime-base"][
            "license"
        ]["installed_payload_path"]
        == LICENSE_PATH
        and all(
            manifests[name]["license"]["installed_payload_path"] is None
            for name in ("development-addon", "test-addon")
        ),
        "manifest_files_canonical_json": all(
            (manifest_output / "manifests" / f"{name}.manifest.json").read_bytes()
            == canonical_json_bytes(manifests[name])
            for name in ARTIFACTS
        ),
        "index_file_canonical_json": (
            manifest_output / "manifest-index.json"
        ).read_bytes()
        == canonical_json_bytes(index),
        "index_hashes_sizes_match": all(
            sha256_file(manifest_output / item["filename"]) == item.get("sha256")
            and (manifest_output / item["filename"]).stat().st_size == item.get("size")
            for item in index_items
        ),
        "index_counts_match": all(
            item.get("owned_entry_count")
            == EXPECTED_COUNTS[item["artifact"]]["owned"]
            and item.get("structural_parent_count")
            == EXPECTED_COUNTS[item["artifact"]]["structural"]
            and item.get("manifest_entry_count")
            == EXPECTED_COUNTS[item["artifact"]]["total"]
            for item in index_items
        ),
        "canonical_identity_unchanged": canonical_before.get("pass") is True
        and canonical_after.get("pass") is True
        and canonical_before.get("entry_count") == canonical_after.get("entry_count") == 3155
        and canonical_before.get("fingerprint")
        == canonical_after.get("fingerprint")
        == args.expected_canonical_fingerprint,
        "runtime_identity_unchanged": runtime_before.get("pass") is True
        and runtime_after.get("pass") is True
        and runtime_before.get("entry_count") == runtime_after.get("entry_count") == 714
        and runtime_before.get("fingerprint")
        == runtime_after.get("fingerprint")
        == args.expected_runtime_fingerprint,
        "pycache_special_zero": canonical_before.get("pycache_paths") == []
        and canonical_after.get("pycache_paths") == []
        and canonical_before.get("special_paths") == []
        and canonical_after.get("special_paths") == []
        and runtime_before.get("pycache_paths") == []
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
        "observed": {
            "manifest_index_sha256": (
                sha256_file(manifest_output / "manifest-index.json")
                if (manifest_output / "manifest-index.json").is_file()
                else None
            ),
            "product_lock_sha256": lock_sha,
            "manifests": {
                name: {
                    "entry_count": len(manifests[name].get("entries", [])),
                    "sha256": (
                        sha256_file(
                            manifest_output / "manifests" / f"{name}.manifest.json"
                        )
                        if (
                            manifest_output / "manifests" / f"{name}.manifest.json"
                        ).is_file()
                        else None
                    ),
                }
                for name in ARTIFACTS
            },
        },
        "claim_boundary": {
            "proved": (
                "Schema-v1 manifests and index are exactly reproduced from accepted "
                "ownership rows and product identity with canonical JSON bytes."
            ),
            "not_proved": (
                "Archive container bytes, extraction safety, or installation transactions."
            ),
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(__import__("json").dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 29


if __name__ == "__main__":
    raise SystemExit(main())
