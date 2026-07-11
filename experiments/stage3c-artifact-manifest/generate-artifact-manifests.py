#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
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
    read_json,
    read_tsv,
    safe_relative,
    sha256_file,
)


def owned_entry(row: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "archive_path": f"payload/{row['path']}",
        "component": row["component"],
        "elf": row["elf"] == "true",
        "entry_class": "OWNED_PAYLOAD",
        "mode": row["mode"],
        "payload_path": row["path"],
        "type": row["type"].lower(),
    }
    if row["type"] == "REGULAR":
        result.update(sha256=row["sha256"], size=int(row["size"]))
    elif row["type"] == "SYMLINK":
        result["symlink_target"] = row["symlink_target"]
    elif row["type"] != "DIRECTORY":
        raise ValueError(f"unsupported type: {row['type']}")
    return result


def structural_entry(
    row: dict[str, str], source_by_path: dict[str, dict[str, str]]
) -> dict[str, Any]:
    source = source_by_path[row["path"]]
    if source["type"] != "DIRECTORY":
        raise ValueError(f"structural path is not a directory: {row['path']}")
    return {
        "archive_path": f"payload/{row['path']}",
        "entry_class": "STRUCTURAL_PARENT",
        "mode": source["mode"],
        "owner_artifact": row["owner_artifact"],
        "owner_component": row["owner_component"],
        "payload_path": row["path"],
        "type": "directory",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ownership-dir", required=True, type=Path)
    parser.add_argument("--product-lock", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expected-component-manifest", required=True)
    parser.add_argument("--expected-canonical-fingerprint", required=True)
    parser.add_argument("--expected-runtime-fingerprint", required=True)
    parser.add_argument("--expected-owned-manifest", required=True)
    parser.add_argument("--expected-structural-manifest", required=True)
    parser.add_argument("--expected-shared-manifest", required=True)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    ownership = args.ownership_dir.resolve()
    output = args.output_dir.resolve()
    manifests_dir = output / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)

    model = read_json(ownership / "ownership-model.json")
    verification = read_json(ownership / "verification.json")
    safety = read_json(ownership / "safety-verification.json")
    workflow = read_json(ownership / "workflow-status.json")
    canonical_before = read_json(ownership / "canonical-before.json")
    canonical_after = read_json(ownership / "canonical-after.json")
    runtime_before = read_json(ownership / "runtime-before.json")
    runtime_after = read_json(ownership / "runtime-after.json")
    product_lock_path = args.product_lock.resolve()
    product_lock = read_json(product_lock_path)
    owned_rows = read_tsv(ownership / "artifact-owned-paths.tsv", OWNED_FIELDS)
    structural_rows = read_tsv(
        ownership / "artifact-structural-directories.tsv", STRUCTURAL_FIELDS
    )
    source_rows = read_tsv(
        ownership / "input/component-inventory.tsv", SOURCE_FIELDS
    )

    source_by_path = {row["path"]: row for row in source_rows}
    owned_by_artifact: dict[str, list[dict[str, str]]] = defaultdict(list)
    structural_by_artifact: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in owned_rows:
        owned_by_artifact[row["artifact"]].append(row)
    for row in structural_rows:
        structural_by_artifact[row["artifact"]].append(row)

    model_hashes = model.get("manifests", {})
    returncodes = workflow.get("returncodes", {})
    lock_sha = sha256_file(product_lock_path)
    license_row = next(row for row in owned_rows if row["path"] == LICENSE_PATH)

    checks: dict[str, bool] = {
        "ownership_model_pass_64": model.get("pass") is True
        and model.get("check_count") == 64
        and model.get("failed_checks") == [],
        "ownership_verification_pass_74": verification.get("pass") is True
        and verification.get("check_count") == 74
        and verification.get("failed_checks") == []
        and verification.get("missing_outputs") == []
        and verification.get("parse_errors") == {},
        "ownership_safety_pass_9": safety.get("pass") is True
        and safety.get("check_count") == 9
        and safety.get("failed_checks") == [],
        "ownership_workflow_pass": workflow.get("pass") is True,
        "ownership_workflow_keys_exact": set(returncodes) == {
            "ownership_analysis",
            "source_mutation",
            "independent_verification",
            "safety_verification",
        },
        "ownership_workflow_returncodes_zero": bool(returncodes)
        and all(value == 0 for value in returncodes.values()),
        "component_manifest_exact": model.get("source", {}).get(
            "component_manifest_sha256"
        )
        == args.expected_component_manifest,
        "canonical_fingerprint_exact": model.get("source", {}).get(
            "canonical_fingerprint"
        )
        == args.expected_canonical_fingerprint,
        "runtime_fingerprint_exact": model.get("source", {}).get(
            "runtime_fingerprint"
        )
        == args.expected_runtime_fingerprint,
        "owned_manifest_exact": model_hashes.get("owned_paths_sha256")
        == args.expected_owned_manifest,
        "structural_manifest_exact": model_hashes.get(
            "structural_directories_sha256"
        )
        == args.expected_structural_manifest,
        "shared_manifest_exact": model_hashes.get("shared_namespace_sha256")
        == args.expected_shared_manifest,
        "canonical_unchanged": canonical_before.get("fingerprint")
        == canonical_after.get("fingerprint")
        == args.expected_canonical_fingerprint,
        "runtime_unchanged": runtime_before.get("fingerprint")
        == runtime_after.get("fingerprint")
        == args.expected_runtime_fingerprint,
        "product_lock_schema_1": product_lock.get("schema_version") == 1,
        "product_lock_identity_exact": product_lock.get("product_kind")
        == PRODUCT["product_kind"]
        and product_lock.get("python_version") == PRODUCT["python_version"]
        and product_lock.get("source_head") == PRODUCT["source_head"]
        and product_lock.get("target_host") == PRODUCT["target_host"]
        and product_lock.get("android_api") == PRODUCT["android_api"]
        and product_lock.get("ndk_version") == PRODUCT["ndk_version"],
        "product_lock_source_archive_exact": product_lock.get("archive")
        == PRODUCT["source_archive"],
        "product_lock_prefix_root_exact": product_lock.get("package_prefix_root")
        == "prefix",
        "owned_entry_count_2956": len(owned_rows) == 2956,
        "structural_entry_count_4": len(structural_rows) == 4,
        "source_entry_count_3155": len(source_rows) == 3155,
        "artifact_owned_counts_exact": {
            name: len(owned_by_artifact[name]) for name in ARTIFACTS
        }
        == {name: EXPECTED_COUNTS[name]["owned"] for name in ARTIFACTS},
        "artifact_structural_counts_exact": {
            name: len(structural_by_artifact[name]) for name in ARTIFACTS
        }
        == {name: EXPECTED_COUNTS[name]["structural"] for name in ARTIFACTS},
        "license_row_exact": license_row["artifact"] == "runtime-base"
        and license_row["component"] == "LICENSE"
        and license_row["type"] == "REGULAR"
        and len(license_row["sha256"]) == 64,
    }

    manifest_objects: dict[str, dict[str, Any]] = {}
    index_items: list[dict[str, Any]] = []
    for name in ARTIFACTS:
        owned = [owned_entry(row) for row in owned_by_artifact[name]]
        structural = [
            structural_entry(row, source_by_path)
            for row in structural_by_artifact[name]
        ]
        entries = sorted(
            owned + structural,
            key=lambda item: (item["payload_path"], item["entry_class"]),
        )
        standalone = name == "runtime-base"
        prerequisite = None if standalone else {
            "artifact": "runtime-base",
            "artifact_id": artifact_id("runtime-base"),
            "android_api": PRODUCT["android_api"],
            "component_manifest_sha256": args.expected_component_manifest,
            "python_version": PRODUCT["python_version"],
            "runtime_fingerprint": args.expected_runtime_fingerprint,
            "target_host": PRODUCT["target_host"],
        }
        manifest: dict[str, Any] = {
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
                "canonical_product_fingerprint": args.expected_canonical_fingerprint,
                "component_manifest_sha256": args.expected_component_manifest,
                "ownership_manifests": {
                    "owned_paths_sha256": args.expected_owned_manifest,
                    "shared_namespace_sha256": args.expected_shared_manifest,
                    "structural_directories_sha256": args.expected_structural_manifest,
                },
                "prerequisite": prerequisite,
                "runtime_base_fingerprint": args.expected_runtime_fingerprint,
            },
            "layout": {
                "archive_root": f"{artifact_id(name)}/",
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
        manifest_objects[name] = manifest
        path = manifests_dir / f"{name}.manifest.json"
        data = canonical_json_bytes(manifest)
        path.write_bytes(data)
        index_items.append(
            {
                "artifact": name,
                "artifact_id": artifact_id(name),
                "filename": f"manifests/{path.name}",
                "manifest_entry_count": len(entries),
                "owned_entry_count": len(owned),
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
                "structural_parent_count": len(structural),
            }
        )

    index = {
        "schema_version": 1,
        "index_kind": "cpython-android-cli-artifact-manifest-index",
        "artifacts": index_items,
        "component_manifest_sha256": args.expected_component_manifest,
        "owned_paths_manifest_sha256": args.expected_owned_manifest,
        "product": {
            "android_api": PRODUCT["android_api"],
            "python_version": PRODUCT["python_version"],
            "target_host": PRODUCT["target_host"],
        },
    }
    index_data = canonical_json_bytes(index)
    (output / "manifest-index.json").write_bytes(index_data)

    checks.update(
        {
            "artifact_set_exact": set(manifest_objects) == set(ARTIFACTS),
            "artifact_ids_unique": len(
                {value["artifact"]["artifact_id"] for value in manifest_objects.values()}
            )
            == 3,
            "archive_roots_unique": len(
                {value["layout"]["archive_root"] for value in manifest_objects.values()}
            )
            == 3,
            "manifest_counts_exact": {
                name: len(manifest_objects[name]["entries"]) for name in ARTIFACTS
            }
            == {name: EXPECTED_COUNTS[name]["total"] for name in ARTIFACTS},
            "archive_paths_safe": all(
                safe_relative(entry["archive_path"])
                and entry["archive_path"].startswith("payload/")
                for manifest in manifest_objects.values()
                for entry in manifest["entries"]
            ),
            "payload_paths_safe": all(
                safe_relative(entry["payload_path"])
                for manifest in manifest_objects.values()
                for entry in manifest["entries"]
            ),
            "archive_paths_unique_per_artifact": all(
                len({entry["archive_path"] for entry in manifest["entries"]})
                == len(manifest["entries"])
                for manifest in manifest_objects.values()
            ),
            "regular_fields_exact": all(
                isinstance(entry.get("size"), int)
                and len(entry.get("sha256", "")) == 64
                and "symlink_target" not in entry
                for manifest in manifest_objects.values()
                for entry in manifest["entries"]
                if entry["type"] == "regular"
            ),
            "directory_fields_exact": all(
                "size" not in entry
                and "sha256" not in entry
                and "symlink_target" not in entry
                for manifest in manifest_objects.values()
                for entry in manifest["entries"]
                if entry["type"] == "directory"
            ),
            "symlink_fields_exact": all(
                bool(entry.get("symlink_target"))
                and "size" not in entry
                and "sha256" not in entry
                for manifest in manifest_objects.values()
                for entry in manifest["entries"]
                if entry["type"] == "symlink"
            ),
            "structural_entries_directory_only": all(
                entry["type"] == "directory"
                for manifest in manifest_objects.values()
                for entry in manifest["entries"]
                if entry["entry_class"] == "STRUCTURAL_PARENT"
            ),
            "runtime_prerequisite_null": manifest_objects["runtime-base"][
                "compatibility"
            ]["prerequisite"]
            is None,
            "addon_prerequisites_exact": all(
                manifest_objects[name]["compatibility"]["prerequisite"][
                    "runtime_fingerprint"
                ]
                == args.expected_runtime_fingerprint
                for name in ("development-addon", "test-addon")
            ),
            "license_metadata_equal_all": len(
                {
                    (
                        value["license"]["archive_metadata_path"],
                        value["license"]["sha256"],
                        value["license"]["size"],
                    )
                    for value in manifest_objects.values()
                }
            )
            == 1,
            "license_installed_path_runtime_only": manifest_objects[
                "runtime-base"
            ]["license"]["installed_payload_path"]
            == LICENSE_PATH
            and all(
                manifest_objects[name]["license"]["installed_payload_path"] is None
                for name in ("development-addon", "test-addon")
            ),
            "index_artifact_count_3": len(index_items) == 3,
            "index_hashes_match": all(
                sha256_file(output / item["filename"]) == item["sha256"]
                for item in index_items
            ),
            "index_sizes_match": all(
                (output / item["filename"]).stat().st_size == item["size"]
                for item in index_items
            ),
        }
    )

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "manifest_index": index,
        "manifest_index_sha256": hashlib.sha256(index_data).hexdigest(),
        "product_lock_sha256": lock_sha,
        "claim_boundary": {
            "proved": (
                "Three deterministic schema-v1 manifests encode exact payload, "
                "structural namespace, compatibility, license, and provenance metadata."
            ),
            "not_proved": (
                "Archive bytes, extraction safety, and installation transactions are valid."
            ),
        },
    }
    (output / "generation.json").write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(
        "STAGE3C_PHASE2_ARTIFACT_MANIFEST_GENERATION="
        + ("PASS" if result["pass"] else "FAIL")
    )
    if args.require_pass and not result["pass"]:
        return 28
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
