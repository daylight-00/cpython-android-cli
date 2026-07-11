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
    read_tsv,
    safe_relative,
    sha256_file,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase3-results", required=True, type=Path)
    parser.add_argument("--contract-results", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    phase3 = args.phase3_results.resolve()
    results = args.contract_results.resolve()
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
    phase3_verification = read_json(phase3 / "archive-verification.json")
    phase3_workflow = read_json(phase3 / "workflow-status.json")
    build_a = read_json(phase3 / "build-a-index.json")
    build_b = read_json(phase3 / "build-b-index.json")
    derivation = read_json(results / "derivation.json")
    contract = read_json(results / "installation-contract.json")
    index = read_json(results / "contract-index.json")
    registry = read_json(results / "registry-template.json")
    owned = read_tsv(results / "installed-owned-paths.tsv", OWNED_FIELDS)
    structural = read_tsv(results / "structural-paths.tsv", STRUCTURAL_FIELDS)
    policies = read_tsv(results / "collision-policy.tsv", POLICY_FIELDS)
    order = read_tsv(results / "operation-order.tsv", ORDER_FIELDS)
    summary = read_tsv(results / "contract-summary.tsv", SUMMARY_FIELDS)

    a_by = {item["artifact"]: item for item in build_a["artifacts"]}
    b_by = {item["artifact"]: item for item in build_b["artifacts"]}
    expected_owned: list[dict[str, str]] = []
    expected_structural: list[dict[str, str]] = []
    expected_registry_paths: list[dict[str, Any]] = []
    expected_registry_artifacts: list[dict[str, Any]] = []
    expected_summary: list[dict[str, str]] = []

    for artifact in ARTIFACTS:
        manifest = manifests[artifact]
        aid = manifest["artifact"]["artifact_id"]
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
                row = {
                    "path": entry["payload_path"],
                    "owner_artifact": artifact,
                    "artifact_id": aid,
                    "component": entry.get("component", ""),
                    "type": entry["type"],
                    "mode": entry["mode"],
                    "size": str(entry.get("size", "")),
                    "sha256": entry.get("sha256", ""),
                    "symlink_target": entry.get("symlink_target", ""),
                    "elf": "true" if entry.get("elf") is True else "false",
                    "install_action": (
                        "CREATE_OR_VALIDATE_DIRECTORY"
                        if entry["type"] == "directory"
                        else "CREATE_OR_REPLACE_REGISTERED"
                    ),
                    "uninstall_action": (
                        "REMOVE_IF_EMPTY"
                        if entry["type"] == "directory"
                        else "REMOVE_IF_REGISTERED_MATCH_ELSE_PRESERVE"
                    ),
                }
                expected_owned.append(row)
                expected_registry_paths.append(
                    {
                        "path": row["path"],
                        "owner_artifact": artifact,
                        "type": row["type"],
                        "mode": row["mode"],
                        "size": int(row["size"]) if row["size"] else None,
                        "sha256": row["sha256"] or None,
                        "symlink_target": row["symlink_target"] or None,
                        "component": row["component"],
                        "elf": row["elf"] == "true",
                    }
                )
            else:
                expected_structural.append(
                    {
                        "path": entry["payload_path"],
                        "consumer_artifact": artifact,
                        "owner_artifact": entry["owner_artifact"],
                        "type": entry["type"],
                        "mode": entry["mode"],
                        "install_action": "CREATE_OR_REUSE_DIRECTORY_NONOWNING",
                        "uninstall_action": "PRESERVE_NAMESPACE",
                    }
                )
        expected_registry_artifacts.append(
            {
                "artifact": artifact,
                "artifact_id": aid,
                "archive_filename": a_by[artifact]["filename"],
                "archive_sha256": a_by[artifact]["sha256"],
                "archive_size": a_by[artifact]["size"],
                "manifest_sha256": sha256_file(manifest_paths[artifact]),
                "owned_entry_count": manifest["ownership"]["owned_entry_count"],
                "structural_parent_count": manifest["ownership"][
                    "structural_parent_count"
                ],
                "prerequisite": manifest["compatibility"]["prerequisite"],
            }
        )
        expected_summary.append(
            {
                "artifact": artifact,
                "owned_entry_count": str(
                    manifest["ownership"]["owned_entry_count"]
                ),
                "structural_parent_count": str(
                    manifest["ownership"]["structural_parent_count"]
                ),
                "regular_count": str(counts["regular"]),
                "directory_count": str(counts["directory"]),
                "symlink_count": str(counts["symlink"]),
                "elf_count": str(elf_count),
                "regular_bytes": str(regular_bytes),
                "archive_size": str(a_by[artifact]["size"]),
                "archive_sha256": a_by[artifact]["sha256"],
                "manifest_sha256": sha256_file(manifest_paths[artifact]),
            }
        )

    expected_owned.sort(key=lambda row: row["path"])
    expected_registry_paths.sort(key=lambda row: row["path"])
    expected_structural.sort(
        key=lambda row: (row["path"], row["consumer_artifact"])
    )
    expected_registry_artifacts.sort(
        key=lambda row: ARTIFACTS.index(row["artifact"])
    )
    expected_summary.sort(key=lambda row: ARTIFACTS.index(row["artifact"]))
    expected_policies = [dict(zip(POLICY_FIELDS, row)) for row in COLLISION_POLICY]
    expected_order = [
        {
            "operation": operation,
            "sequence": str(sequence),
            "step": step,
            "mutation": mutation,
            "rollback_required": rollback,
        }
        for operation, sequence, step, mutation, rollback in OPERATION_ORDER
    ]
    expected_layout = {
        "installation_root": "selected-at-transaction-time",
        "payload_prefix": "prefix/",
        "state_root": ".cpython-android-cli/",
        "registry_path": ".cpython-android-cli/registry.json",
        "lock_path": ".cpython-android-cli/lock",
        "transactions_root": ".cpython-android-cli/transactions/",
    }

    workflow_codes = phase3_workflow.get("returncodes", {})
    index_files = index.get("files", {})
    owned_counts = Counter(row["owner_artifact"] for row in owned)
    structural_counts = Counter(row["consumer_artifact"] for row in structural)
    path_counts = Counter(row["path"] for row in owned)

    checks: dict[str, bool] = {
        "phase3_reproducibility_pass_31": reproducibility.get("pass") is True
        and reproducibility.get("check_count") == 31
        and reproducibility.get("failed_checks") == [],
        "phase3_preflight_pass_28": preflight.get("pass") is True
        and preflight.get("check_count") == 28
        and preflight.get("failed_checks") == [],
        "phase3_verification_pass_76": phase3_verification.get("pass") is True
        and phase3_verification.get("check_count") == 76
        and phase3_verification.get("failed_checks") == [],
        "phase3_workflow_pass": phase3_workflow.get("pass") is True,
        "phase3_workflow_returncodes_zero": bool(workflow_codes)
        and all(value == 0 for value in workflow_codes.values()),
        "manifest_index_hash_exact": sha256_file(
            manifest_root / "manifest-index.json"
        )
        == EXPECTED_MANIFEST_INDEX,
        "product_lock_hash_exact": sha256_file(
            manifest_root / "input/product-lock.json"
        )
        == EXPECTED_PRODUCT_LOCK,
        "manifest_hashes_exact": {
            name: sha256_file(manifest_paths[name]) for name in ARTIFACTS
        }
        == EXPECTED_MANIFEST_HASHES,
        "archive_build_a_exact": all(
            a_by[name]["sha256"] == EXPECTED_ARCHIVES[name]["sha256"]
            and a_by[name]["size"] == EXPECTED_ARCHIVES[name]["size"]
            and a_by[name]["member_count"] == EXPECTED_ARCHIVES[name]["members"]
            for name in ARTIFACTS
        ),
        "archive_build_b_exact": all(
            b_by[name]["sha256"] == EXPECTED_ARCHIVES[name]["sha256"]
            and b_by[name]["size"] == EXPECTED_ARCHIVES[name]["size"]
            and b_by[name]["member_count"] == EXPECTED_ARCHIVES[name]["members"]
            for name in ARTIFACTS
        ),
        "retained_archives_exact": all(
            sha256_file(phase3 / "archives" / a_by[name]["filename"])
            == EXPECTED_ARCHIVES[name]["sha256"]
            for name in ARTIFACTS
        ),
        "derivation_pass_54": derivation.get("pass") is True
        and derivation.get("check_count") == 54
        and derivation.get("failed_checks") == [],
        "contract_schema_kind_exact": contract.get("schema_version") == 1
        and contract.get("contract_kind")
        == "cpython-android-cli-installation-contract"
        and contract.get("status") == "model-only-no-target-mutation",
        "contract_input_exact": contract.get("input")
        == {
            "manifest_index_sha256": EXPECTED_MANIFEST_INDEX,
            "product_lock_sha256": EXPECTED_PRODUCT_LOCK,
            "manifest_sha256": EXPECTED_MANIFEST_HASHES,
            "archives": EXPECTED_ARCHIVES,
        },
        "contract_layout_exact": contract.get("installation_layout")
        == expected_layout,
        "contract_artifact_order_exact": contract.get("artifact_order")
        == list(ARTIFACTS),
        "contract_ownership_counts_exact": contract.get("ownership", {}).get(
            "owned_path_count"
        )
        == 2956
        and contract.get("ownership", {}).get("structural_reference_count") == 4,
        "contract_shared_namespace_exact": contract.get("ownership", {}).get(
            "shared_namespace_paths"
        )
        == list(EXPECTED_SHARED_NAMESPACE),
        "contract_metadata_not_installed": contract.get("ownership", {}).get(
            "metadata_envelope_installed"
        )
        is False,
        "contract_registry_semantics_exact": contract.get("registry")
        == {
            "schema_version": 1,
            "registry_template_file": "registry-template.json",
            "registry_write": "atomic-replace-after-payload-mutation",
            "path_records": "OWNED_PAYLOAD-only",
            "structural_records": "non-owning-reference-only",
            "local_modification_uninstall_policy": "preserve-and-report",
        },
        "contract_transaction_states_exact": contract.get("transaction", {}).get(
            "states"
        )
        == [
            "PREPARED",
            "APPLYING",
            "COMMITTED",
            "ROLLING_BACK",
            "ROLLED_BACK",
            "FAILED",
        ],
        "contract_transaction_guards_true": all(
            contract.get("transaction", {}).get(key) is True
            for key in [
                "preflight_before_mutation",
                "exclusive_lock_required",
                "same_filesystem_staging_required",
                "backup_before_replace_or_remove",
                "prior_registry_backup_required",
                "rollback_required_after_first_mutation",
            ]
        ),
        "contract_reinstall_exact": contract.get("reinstall")
        == {
            "exact_match": "NOOP",
            "registered_same_artifact_mismatch": "REPLACE_WITH_BACKUP",
            "unregistered_existing": "CONFLICT",
            "other_artifact_owner": "CONFLICT",
        },
        "contract_uninstall_exact": contract.get("uninstall")
        == {
            "matching_regular_or_symlink": "REMOVE_EXACT",
            "modified_regular_or_symlink": "PRESERVE_AND_REPORT",
            "owned_directory": "REMOVE_ONLY_WHEN_EMPTY",
            "structural_parent": "PRESERVE_NAMESPACE",
            "unowned_descendant": "PRESERVE",
        },
        "owned_rows_exact": owned == expected_owned,
        "structural_rows_exact": structural == expected_structural,
        "collision_policy_exact": policies == expected_policies,
        "operation_order_exact": order == expected_order,
        "summary_rows_exact": summary == expected_summary,
        "registry_schema_kind_exact": registry.get("schema_version") == 1
        and registry.get("registry_kind")
        == "cpython-android-cli-installed-ownership-registry",
        "registry_layout_exact": registry.get("installation_layout")
        == expected_layout,
        "registry_artifacts_exact": registry.get("artifacts")
        == expected_registry_artifacts,
        "registry_paths_exact": registry.get("owned_paths")
        == expected_registry_paths,
        "registry_structural_exact": registry.get("structural_namespace")
        == expected_structural,
        "registry_shared_namespace_exact": registry.get("shared_namespace_paths")
        == list(EXPECTED_SHARED_NAMESPACE),
        "owned_counts_exact": {name: owned_counts[name] for name in ARTIFACTS}
        == {name: EXPECTED_COUNTS[name]["owned"] for name in ARTIFACTS},
        "structural_counts_exact": {
            name: structural_counts[name] for name in ARTIFACTS
        }
        == {name: EXPECTED_COUNTS[name]["structural"] for name in ARTIFACTS},
        "owned_overlap_zero": all(count == 1 for count in path_counts.values()),
        "owned_paths_safe": all(safe_relative(row["path"]) for row in owned),
        "structural_paths_safe": all(
            safe_relative(row["path"]) for row in structural
        ),
        "structural_directory_only": all(
            row["type"] == "directory" for row in structural
        ),
        "metadata_envelope_absent_from_registry": all(
            not row["path"].startswith("metadata/") for row in owned
        ),
        "collision_policy_count_17": len(policies) == 17,
        "operation_order_count_22": len(order) == 22,
        "operation_install_sequence_contiguous": [
            int(row["sequence"])
            for row in order
            if row["operation"] == "install"
        ]
        == list(range(1, 13)),
        "operation_uninstall_sequence_contiguous": [
            int(row["sequence"])
            for row in order
            if row["operation"] == "uninstall"
        ]
        == list(range(1, 11)),
        "preflight_before_first_mutation": min(
            int(row["sequence"])
            for row in order
            if row["operation"] == "install" and row["mutation"] == "true"
        )
        == 7,
        "modified_uninstall_preserved": any(
            row["observed_state"] == "REGISTERED_MISMATCH"
            and row["action"] == "PRESERVE_AND_REPORT"
            for row in policies
        ),
        "unowned_adoption_forbidden": any(
            row["observed_state"] == "EXISTING_UNOWNED"
            and row["action"] == "CONFLICT"
            and row["allowed"] == "false"
            for row in policies
        ),
        "structural_uninstall_preserved": any(
            row["path_class"] == "STRUCTURAL_PARENT"
            and row["action"] == "PRESERVE_NAMESPACE"
            for row in policies
        ),
        "contract_json_canonical": (
            results / "installation-contract.json"
        ).read_bytes()
        == canonical_json_bytes(contract),
        "registry_json_canonical": (
            results / "registry-template.json"
        ).read_bytes()
        == canonical_json_bytes(registry),
        "index_json_canonical": (results / "contract-index.json").read_bytes()
        == canonical_json_bytes(index),
        "index_schema_kind_exact": index.get("schema_version") == 1
        and index.get("index_kind")
        == "cpython-android-cli-installation-contract-index",
        "index_file_set_exact": set(index_files)
        == {
            "installed_owned_paths",
            "structural_paths",
            "collision_policy",
            "operation_order",
            "contract_summary",
            "registry_template",
            "installation_contract",
        },
        "index_hashes_match": all(
            sha256_file(results / item["filename"]) == item["sha256"]
            for item in index_files.values()
        ),
        "index_sizes_match": all(
            (results / item["filename"]).stat().st_size == item["size"]
            for item in index_files.values()
        ),
        "derivation_observed_counts_exact": derivation.get("observed", {}).get(
            "owned_path_count"
        )
        == 2956
        and derivation.get("observed", {}).get("structural_reference_count") == 4
        and derivation.get("observed", {}).get("collision_policy_count") == 17
        and derivation.get("observed", {}).get("operation_step_count") == 22,
        "derivation_contract_index_hash_exact": derivation.get("observed", {}).get(
            "contract_index_sha256"
        )
        == sha256_file(results / "contract-index.json"),
    }

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "observed": {
            "owned_path_count": len(owned),
            "structural_reference_count": len(structural),
            "collision_policy_count": len(policies),
            "operation_step_count": len(order),
            "contract_index_sha256": sha256_file(
                results / "contract-index.json"
            ),
        },
        "claim_boundary": contract["claim_boundary"],
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 36


if __name__ == "__main__":
    raise SystemExit(main())
