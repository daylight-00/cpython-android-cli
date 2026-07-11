#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from install_contract_common import (
    ARTIFACTS,
    COLLISION_POLICY,
    EXPECTED_ARCHIVES,
    EXPECTED_COUNTS,
    EXPECTED_MANIFEST_HASHES,
    EXPECTED_MANIFEST_INDEX,
    EXPECTED_PRODUCT_LOCK,
    EXPECTED_SHARED_NAMESPACE,
    OPERATION_ORDER,
    ORDER_FIELDS,
    OWNED_FIELDS,
    POLICY_FIELDS,
    STRUCTURAL_FIELDS,
    SUMMARY_FIELDS,
    canonical_json_bytes,
    read_json,
    safe_relative,
    sha256_file,
    write_tsv,
)


def archive_by_artifact(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["artifact"]: item for item in index.get("artifacts", [])}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase3-results", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    phase3 = args.phase3_results.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest_root = phase3 / "input/manifest-schema"
    manifests = {
        name: read_json(manifest_root / "manifests" / f"{name}.manifest.json")
        for name in ARTIFACTS
    }
    manifest_paths = {
        name: manifest_root / "manifests" / f"{name}.manifest.json"
        for name in ARTIFACTS
    }
    reproducibility = read_json(phase3 / "reproducibility.json")
    preflight = read_json(phase3 / "preflight-verification.json")
    verification = read_json(phase3 / "archive-verification.json")
    workflow = read_json(phase3 / "workflow-status.json")
    build_a = read_json(phase3 / "build-a-index.json")
    build_b = read_json(phase3 / "build-b-index.json")
    manifest_index_path = manifest_root / "manifest-index.json"
    product_lock_path = manifest_root / "input/product-lock.json"
    a_by = archive_by_artifact(build_a)
    b_by = archive_by_artifact(build_b)

    owned_rows: list[dict[str, Any]] = []
    structural_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    registry_artifacts: list[dict[str, Any]] = []
    registry_paths: list[dict[str, Any]] = []
    namespace_refs: list[dict[str, Any]] = []

    for artifact in ARTIFACTS:
        manifest = manifests[artifact]
        artifact_id = manifest["artifact"]["artifact_id"]
        counts = Counter(
            entry["type"]
            for entry in manifest["entries"]
            if entry["entry_class"] == "OWNED_PAYLOAD"
        )
        regular_bytes = sum(
            entry.get("size", 0)
            for entry in manifest["entries"]
            if entry["entry_class"] == "OWNED_PAYLOAD"
            and entry["type"] == "regular"
        )
        elf_count = sum(
            entry.get("elf") is True
            for entry in manifest["entries"]
            if entry["entry_class"] == "OWNED_PAYLOAD"
        )
        for entry in manifest["entries"]:
            if entry["entry_class"] == "OWNED_PAYLOAD":
                install_action = (
                    "CREATE_OR_VALIDATE_DIRECTORY"
                    if entry["type"] == "directory"
                    else "CREATE_OR_REPLACE_REGISTERED"
                )
                uninstall_action = (
                    "REMOVE_IF_EMPTY"
                    if entry["type"] == "directory"
                    else "REMOVE_IF_REGISTERED_MATCH_ELSE_PRESERVE"
                )
                row = {
                    "path": entry["payload_path"],
                    "owner_artifact": artifact,
                    "artifact_id": artifact_id,
                    "component": entry.get("component", ""),
                    "type": entry["type"],
                    "mode": entry["mode"],
                    "size": entry.get("size", ""),
                    "sha256": entry.get("sha256", ""),
                    "symlink_target": entry.get("symlink_target", ""),
                    "elf": "true" if entry.get("elf") is True else "false",
                    "install_action": install_action,
                    "uninstall_action": uninstall_action,
                }
                owned_rows.append(row)
                registry_paths.append(
                    {
                        "path": row["path"],
                        "owner_artifact": artifact,
                        "type": row["type"],
                        "mode": row["mode"],
                        "size": row["size"] if row["size"] != "" else None,
                        "sha256": row["sha256"] or None,
                        "symlink_target": row["symlink_target"] or None,
                        "component": row["component"],
                        "elf": row["elf"] == "true",
                    }
                )
            else:
                row = {
                    "path": entry["payload_path"],
                    "consumer_artifact": artifact,
                    "owner_artifact": entry["owner_artifact"],
                    "type": entry["type"],
                    "mode": entry["mode"],
                    "install_action": "CREATE_OR_REUSE_DIRECTORY_NONOWNING",
                    "uninstall_action": "PRESERVE_NAMESPACE",
                }
                structural_rows.append(row)
                namespace_refs.append(row.copy())
        archive = a_by[artifact]
        summary_rows.append(
            {
                "artifact": artifact,
                "owned_entry_count": manifest["ownership"]["owned_entry_count"],
                "structural_parent_count": manifest["ownership"]["structural_parent_count"],
                "regular_count": counts["regular"],
                "directory_count": counts["directory"],
                "symlink_count": counts["symlink"],
                "elf_count": elf_count,
                "regular_bytes": regular_bytes,
                "archive_size": archive["size"],
                "archive_sha256": archive["sha256"],
                "manifest_sha256": sha256_file(manifest_paths[artifact]),
            }
        )
        registry_artifacts.append(
            {
                "artifact": artifact,
                "artifact_id": artifact_id,
                "archive_filename": archive["filename"],
                "archive_sha256": archive["sha256"],
                "archive_size": archive["size"],
                "manifest_sha256": sha256_file(manifest_paths[artifact]),
                "owned_entry_count": manifest["ownership"]["owned_entry_count"],
                "structural_parent_count": manifest["ownership"]["structural_parent_count"],
                "prerequisite": manifest["compatibility"]["prerequisite"],
            }
        )

    owned_rows.sort(key=lambda row: row["path"])
    registry_paths.sort(key=lambda row: row["path"])
    structural_rows.sort(key=lambda row: (row["path"], row["consumer_artifact"]))
    namespace_refs.sort(key=lambda row: (row["path"], row["consumer_artifact"]))
    summary_rows.sort(key=lambda row: ARTIFACTS.index(row["artifact"]))
    registry_artifacts.sort(key=lambda row: ARTIFACTS.index(row["artifact"]))

    collision_rows = [dict(zip(POLICY_FIELDS, row)) for row in COLLISION_POLICY]
    order_rows = [
        {
            "operation": operation,
            "sequence": sequence,
            "step": step,
            "mutation": mutation,
            "rollback_required": rollback,
        }
        for operation, sequence, step, mutation, rollback in OPERATION_ORDER
    ]
    write_tsv(output / "installed-owned-paths.tsv", OWNED_FIELDS, owned_rows)
    write_tsv(output / "structural-paths.tsv", STRUCTURAL_FIELDS, structural_rows)
    write_tsv(output / "collision-policy.tsv", POLICY_FIELDS, collision_rows)
    write_tsv(output / "operation-order.tsv", ORDER_FIELDS, order_rows)
    write_tsv(output / "contract-summary.tsv", SUMMARY_FIELDS, summary_rows)

    registry_template = {
        "schema_version": 1,
        "registry_kind": "cpython-android-cli-installed-ownership-registry",
        "installation_layout": {
            "installation_root": "selected-at-transaction-time",
            "payload_prefix": "prefix/",
            "state_root": ".cpython-android-cli/",
            "registry_path": ".cpython-android-cli/registry.json",
            "lock_path": ".cpython-android-cli/lock",
            "transactions_root": ".cpython-android-cli/transactions/",
        },
        "artifacts": registry_artifacts,
        "owned_paths": registry_paths,
        "structural_namespace": namespace_refs,
        "shared_namespace_paths": list(EXPECTED_SHARED_NAMESPACE),
    }
    (output / "registry-template.json").write_bytes(
        canonical_json_bytes(registry_template)
    )

    generated = {
        "installed_owned_paths": output / "installed-owned-paths.tsv",
        "structural_paths": output / "structural-paths.tsv",
        "collision_policy": output / "collision-policy.tsv",
        "operation_order": output / "operation-order.tsv",
        "contract_summary": output / "contract-summary.tsv",
        "registry_template": output / "registry-template.json",
    }
    output_index = {
        name: {
            "filename": path.name,
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
        for name, path in generated.items()
    }

    workflow_codes = workflow.get("returncodes", {})
    owned_counts = Counter(row["owner_artifact"] for row in owned_rows)
    structural_counts = Counter(row["consumer_artifact"] for row in structural_rows)
    type_counts = Counter(row["type"] for row in owned_rows)
    path_counts = Counter(row["path"] for row in owned_rows)
    build_a_hashes = {name: a_by[name]["sha256"] for name in ARTIFACTS}
    build_b_hashes = {name: b_by[name]["sha256"] for name in ARTIFACTS}
    checks: dict[str, bool] = {
        "phase3_reproducibility_pass_31": reproducibility.get("pass") is True
        and reproducibility.get("check_count") == 31
        and reproducibility.get("failed_checks") == []
        and reproducibility.get("source_errors") == [],
        "phase3_preflight_pass_28": preflight.get("pass") is True
        and preflight.get("check_count") == 28
        and preflight.get("failed_checks") == [],
        "phase3_verification_pass_76": verification.get("pass") is True
        and verification.get("check_count") == 76
        and verification.get("failed_checks") == [],
        "phase3_workflow_pass": workflow.get("pass") is True,
        "phase3_workflow_keys_exact": set(workflow_codes)
        == {
            "archive_build",
            "archive_preflight",
            "archive_verification",
            "source_mutation",
        },
        "phase3_workflow_returncodes_zero": bool(workflow_codes)
        and all(value == 0 for value in workflow_codes.values()),
        "manifest_index_hash_exact": sha256_file(manifest_index_path)
        == EXPECTED_MANIFEST_INDEX,
        "product_lock_hash_exact": sha256_file(product_lock_path)
        == EXPECTED_PRODUCT_LOCK,
        "manifest_hashes_exact": {
            name: sha256_file(manifest_paths[name]) for name in ARTIFACTS
        }
        == EXPECTED_MANIFEST_HASHES,
        "archive_artifact_sets_exact": set(a_by) == set(b_by) == set(ARTIFACTS),
        "archive_build_a_hashes_exact": build_a_hashes
        == {name: EXPECTED_ARCHIVES[name]["sha256"] for name in ARTIFACTS},
        "archive_build_b_hashes_exact": build_b_hashes == build_a_hashes,
        "archive_sizes_exact": all(
            a_by[name]["size"] == EXPECTED_ARCHIVES[name]["size"]
            for name in ARTIFACTS
        ),
        "archive_member_counts_exact": all(
            a_by[name]["member_count"] == EXPECTED_ARCHIVES[name]["members"]
            for name in ARTIFACTS
        ),
        "retained_archives_exist": all(
            (phase3 / "archives" / a_by[name]["filename"]).is_file()
            for name in ARTIFACTS
        ),
        "retained_archive_hashes_exact": all(
            sha256_file(phase3 / "archives" / a_by[name]["filename"])
            == EXPECTED_ARCHIVES[name]["sha256"]
            for name in ARTIFACTS
        ),
        "retained_archive_sizes_exact": all(
            (phase3 / "archives" / a_by[name]["filename"]).stat().st_size
            == EXPECTED_ARCHIVES[name]["size"]
            for name in ARTIFACTS
        ),
        "artifact_manifest_counts_exact": all(
            len(manifests[name]["entries"]) == EXPECTED_COUNTS[name]["manifest"]
            for name in ARTIFACTS
        ),
        "owned_counts_exact": {name: owned_counts[name] for name in ARTIFACTS}
        == {name: EXPECTED_COUNTS[name]["owned"] for name in ARTIFACTS},
        "structural_counts_exact": {
            name: structural_counts[name] for name in ARTIFACTS
        }
        == {name: EXPECTED_COUNTS[name]["structural"] for name in ARTIFACTS},
        "owned_total_2956": len(owned_rows) == 2956,
        "structural_total_4": len(structural_rows) == 4,
        "owned_path_overlap_zero": all(count == 1 for count in path_counts.values()),
        "owned_paths_safe": all(safe_relative(row["path"]) for row in owned_rows),
        "structural_paths_safe": all(
            safe_relative(row["path"]) for row in structural_rows
        ),
        "shared_namespace_exact": tuple(
            sorted({row["path"] for row in structural_rows})
        )
        == EXPECTED_SHARED_NAMESPACE,
        "structural_directory_only": all(
            row["type"] == "directory" for row in structural_rows
        ),
        "structural_nonowning_actions_exact": all(
            row["install_action"] == "CREATE_OR_REUSE_DIRECTORY_NONOWNING"
            and row["uninstall_action"] == "PRESERVE_NAMESPACE"
            for row in structural_rows
        ),
        "owned_type_set_exact": set(type_counts)
        == {"regular", "directory", "symlink"},
        "runtime_elf_count_81": next(
            int(row["elf_count"])
            for row in summary_rows
            if row["artifact"] == "runtime-base"
        )
        == 81,
        "addon_elf_count_zero": all(
            int(row["elf_count"]) == 0
            for row in summary_rows
            if row["artifact"] != "runtime-base"
        ),
        "runtime_prerequisite_null": registry_artifacts[0]["prerequisite"] is None,
        "addon_prerequisites_present": all(
            item["prerequisite"] is not None for item in registry_artifacts[1:]
        ),
        "registry_artifact_order_exact": [
            item["artifact"] for item in registry_artifacts
        ]
        == list(ARTIFACTS),
        "registry_path_count_2956": len(registry_paths) == 2956,
        "registry_paths_sorted": [row["path"] for row in registry_paths]
        == sorted(row["path"] for row in registry_paths),
        "registry_path_owner_exact": all(
            row["owner_artifact"] in ARTIFACTS for row in registry_paths
        ),
        "metadata_envelope_not_registered": all(
            not row["path"].startswith("metadata/") for row in registry_paths
        ),
        "collision_policy_count_17": len(collision_rows) == 17,
        "collision_policy_has_no_unowned_adoption": any(
            row["observed_state"] == "EXISTING_UNOWNED"
            and row["action"] == "CONFLICT"
            and row["allowed"] == "false"
            for row in collision_rows
        ),
        "collision_policy_preserves_modified_uninstall": any(
            row["observed_state"] == "REGISTERED_MISMATCH"
            and row["action"] == "PRESERVE_AND_REPORT"
            for row in collision_rows
        ),
        "collision_policy_preserves_structural": any(
            row["path_class"] == "STRUCTURAL_PARENT"
            and row["operation"] == "uninstall"
            and row["action"] == "PRESERVE_NAMESPACE"
            for row in collision_rows
        ),
        "operation_order_install_12": sum(
            row["operation"] == "install" for row in order_rows
        )
        == 12,
        "operation_order_uninstall_10": sum(
            row["operation"] == "uninstall" for row in order_rows
        )
        == 10,
        "mutation_steps_require_prior_journal": all(
            int(row["sequence"]) >= 7
            for row in order_rows
            if row["operation"] == "install" and row["mutation"] == "true"
        ),
        "rollback_required_for_mutating_core": all(
            row["rollback_required"] == "true"
            for row in order_rows
            if row["mutation"] == "true"
            and "remove transaction" not in row["step"]
            and "mark transaction COMMITTED" not in row["step"]
        ),
        "output_files_exist": all(path.is_file() for path in generated.values()),
        "output_hashes_unique": len(
            {item["sha256"] for item in output_index.values()}
        )
        == len(output_index),
        "registry_template_canonical_json": (
            output / "registry-template.json"
        ).read_bytes()
        == canonical_json_bytes(registry_template),
    }

    contract = {
        "schema_version": 1,
        "contract_kind": "cpython-android-cli-installation-contract",
        "status": "model-only-no-target-mutation",
        "input": {
            "manifest_index_sha256": EXPECTED_MANIFEST_INDEX,
            "product_lock_sha256": EXPECTED_PRODUCT_LOCK,
            "manifest_sha256": EXPECTED_MANIFEST_HASHES,
            "archives": EXPECTED_ARCHIVES,
        },
        "installation_layout": registry_template["installation_layout"],
        "artifact_order": list(ARTIFACTS),
        "ownership": {
            "unit": "exact-registry-path",
            "owned_path_count": len(owned_rows),
            "structural_reference_count": len(structural_rows),
            "shared_namespace_paths": list(EXPECTED_SHARED_NAMESPACE),
            "metadata_envelope_installed": False,
        },
        "registry": {
            "schema_version": 1,
            "registry_template_file": "registry-template.json",
            "registry_write": "atomic-replace-after-payload-mutation",
            "path_records": "OWNED_PAYLOAD-only",
            "structural_records": "non-owning-reference-only",
            "local_modification_uninstall_policy": "preserve-and-report",
        },
        "transaction": {
            "states": [
                "PREPARED",
                "APPLYING",
                "COMMITTED",
                "ROLLING_BACK",
                "ROLLED_BACK",
                "FAILED",
            ],
            "preflight_before_mutation": True,
            "exclusive_lock_required": True,
            "same_filesystem_staging_required": True,
            "backup_before_replace_or_remove": True,
            "prior_registry_backup_required": True,
            "rollback_required_after_first_mutation": True,
        },
        "reinstall": {
            "exact_match": "NOOP",
            "registered_same_artifact_mismatch": "REPLACE_WITH_BACKUP",
            "unregistered_existing": "CONFLICT",
            "other_artifact_owner": "CONFLICT",
        },
        "uninstall": {
            "matching_regular_or_symlink": "REMOVE_EXACT",
            "modified_regular_or_symlink": "PRESERVE_AND_REPORT",
            "owned_directory": "REMOVE_ONLY_WHEN_EMPTY",
            "structural_parent": "PRESERVE_NAMESPACE",
            "unowned_descendant": "PRESERVE",
        },
        "generated": dict(output_index),
        "claim_boundary": {
            "proved": (
                "Deterministic installed ownership, registry, collision, reinstall, "
                "transaction-order, and uninstall policy is derivable from frozen "
                "archives and manifests."
            ),
            "not_proved": (
                "Filesystem mutation, rollback execution, crash recovery, concurrency, "
                "upgrade, downgrade, or runtime behavior after installation."
            ),
        },
    }
    (output / "installation-contract.json").write_bytes(
        canonical_json_bytes(contract)
    )
    output_index["installation_contract"] = {
        "filename": "installation-contract.json",
        "sha256": sha256_file(output / "installation-contract.json"),
        "size": (output / "installation-contract.json").stat().st_size,
    }
    index = {
        "schema_version": 1,
        "index_kind": "cpython-android-cli-installation-contract-index",
        "files": output_index,
    }
    (output / "contract-index.json").write_bytes(canonical_json_bytes(index))
    checks.update(
        {
            "installation_contract_canonical_json": (
                output / "installation-contract.json"
            ).read_bytes()
            == canonical_json_bytes(contract),
            "contract_index_canonical_json": (
                output / "contract-index.json"
            ).read_bytes()
            == canonical_json_bytes(index),
            "contract_index_file_count_7": len(output_index) == 7,
            "contract_index_hashes_match": all(
                sha256_file(output / item["filename"]) == item["sha256"]
                for item in output_index.values()
            ),
            "contract_index_sizes_match": all(
                (output / item["filename"]).stat().st_size == item["size"]
                for item in output_index.values()
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
        "observed": {
            "owned_path_count": len(owned_rows),
            "structural_reference_count": len(structural_rows),
            "collision_policy_count": len(collision_rows),
            "operation_step_count": len(order_rows),
            "contract_index_sha256": sha256_file(output / "contract-index.json"),
        },
        "claim_boundary": contract["claim_boundary"],
    }
    (output / "derivation.json").write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(
        "STAGE3C_PHASE4_INSTALLATION_CONTRACT_DERIVATION="
        + ("PASS" if result["pass"] else "FAIL")
    )
    if args.require_pass and not result["pass"]:
        return 35
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
