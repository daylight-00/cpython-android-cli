#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from gate3c_addon_lifecycle_support import (
    EXPECTED_ARTIFACTS,
    EXPECTED_CONTRACT_INDEX_SHA,
    EXPECTED_ENGINE_SHA,
    EXPECTED_GATE3B_ARCHIVE_SHA,
    EXPECTED_GATE3B_INDEX_SHA,
    EXPECTED_MANIFEST_INDEX_SHA,
    EXPECTED_OPS_SHA,
    EXPECTED_STATES,
    cjson,
    exact_match,
    kind,
    path_snapshot,
    read_json,
    registry_value,
    sha256_file,
    transaction_inventory,
    tree_rows,
    verify_result_index,
    write_json,
)

EXPECTED_GATE3C_ARCHIVE_SHA = "43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a"
EXPECTED_GATE3C_INDEX_SHA = "fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c"
EXPECTED_GATE3C_SAFETY_SHA = "ab338579025da63dec1750e3a7649c9a5f260cd4556f60ab3b3ade6140187bb9"
EXPECTED_GATE3D_MATRIX_SHA = "a36f86d82ad04b71dfa0afb4ab4fd2da764354402cb8db3fdd73d1903606797f"
EXPECTED_GATE3C_MATRIX_SHA = "52c622450e9664c6738a75fbc947b809cf1f4766e61b04a68a1a8dcc24b6c14a"

RUNTIME_REGULAR = "lib/python3.14/LICENSE.txt"
RUNTIME_SYMLINK = "bin/python"
UNOWNED_FILE = "lib/python3.14/site-packages/gate3d-user-file.txt"
UNOWNED_DIR = "lib/python3.14/site-packages/gate3d-user-dir"
UNOWNED_DESCENDANT = "lib/python3.14/site-packages/gate3d-user-dir/nested.txt"
SHARED_UNOWNED_FILE = "lib/python3.14/gate3d-shared-user.txt"


def snapshot_identity(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "path"}


def rows_by_path(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["path"]: row for row in rows}


def directory_ancestors(relative: str, runtime_rows: list[dict[str, Any]]) -> list[str]:
    directories = {row["path"] for row in runtime_rows if row["type"] == "directory"}
    parts = relative.split("/")
    return sorted({"/".join(parts[:index]) for index in range(1, len(parts)) if "/".join(parts[:index]) in directories})


def mutate_modified_regular(root: Path, row: dict[str, Any], marker: bytes = b"gate3d-user-modified-regular\n") -> dict[str, Any]:
    path = root / "prefix" / row["path"]
    before = path_snapshot(path)
    path.write_bytes(marker)
    os.chmod(path, int(row["mode"], 8))
    return {"path": row["path"], "before": before, "after": path_snapshot(path)}


def mutate_modified_symlink(root: Path, row: dict[str, Any], target: str = "gate3d-user-modified-target") -> dict[str, Any]:
    path = root / "prefix" / row["path"]
    before = path_snapshot(path)
    path.unlink()
    os.symlink(target, path)
    return {"path": row["path"], "before": before, "after": path_snapshot(path)}


def create_unowned_file(root: Path, relative: str = UNOWNED_FILE, payload: bytes = b"gate3d-unowned-file\n") -> dict[str, Any]:
    path = root / "prefix" / relative
    before = path_snapshot(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    os.chmod(path, 0o600)
    return {"path": relative, "before": before, "after": path_snapshot(path)}


def create_unowned_directory(root: Path, relative: str = UNOWNED_DIR) -> dict[str, Any]:
    path = root / "prefix" / relative
    before = path_snapshot(path, recursive=True)
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    payload = path / "payload.txt"
    payload.write_bytes(b"gate3d-unowned-directory\n")
    os.chmod(payload, 0o600)
    return {"path": relative, "before": before, "after": path_snapshot(path, recursive=True)}


def create_unowned_descendant(root: Path, relative: str = UNOWNED_DESCENDANT) -> dict[str, Any]:
    return create_unowned_file(root, relative, b"gate3d-unowned-descendant\n")


def prepare_subject(
    root: Path,
    subject: str,
    runtime_rows: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    by_path = rows_by_path(runtime_rows)
    mutations: list[dict[str, Any]] = []
    subject_paths: list[str] = []
    snapshots: list[dict[str, Any]] = []
    if subject == "exact-owned":
        return subject_paths, mutations, snapshots
    if subject == "modified-owned-regular":
        mutation = mutate_modified_regular(root, by_path[RUNTIME_REGULAR])
    elif subject == "modified-owned-symlink":
        mutation = mutate_modified_symlink(root, by_path[RUNTIME_SYMLINK])
    elif subject == "unowned-file":
        mutation = create_unowned_file(root)
    elif subject == "unowned-directory":
        mutation = create_unowned_directory(root)
    elif subject == "unowned-descendant-under-owned-directory":
        mutation = create_unowned_descendant(root)
    elif subject == "unowned-file-under-shared-namespace":
        mutation = create_unowned_file(root, SHARED_UNOWNED_FILE, b"gate3d-shared-unowned\n")
    elif subject == "mixed":
        first = mutate_modified_regular(root, by_path[RUNTIME_REGULAR], b"gate3d-mixed-modified\n")
        second = create_unowned_file(root, UNOWNED_FILE, b"gate3d-mixed-unowned\n")
        for item in (first, second):
            mutations.append(item)
            subject_paths.append(item["path"])
            snapshots.append(item["after"])
        return subject_paths, mutations, snapshots
    else:
        raise ValueError(subject)
    mutations.append(mutation)
    subject_paths.append(mutation["path"])
    snapshots.append(mutation["after"])
    return subject_paths, mutations, snapshots


def expected_residual_paths(subject_paths: Iterable[str], root: Path, runtime_rows: list[dict[str, Any]]) -> list[str]:
    expected: set[str] = set()
    for relative in subject_paths:
        expected.update(directory_ancestors(relative, runtime_rows))
        parts = relative.split("/")
        for index in range(1, len(parts)):
            ancestor = "/".join(parts[:index])
            if kind(root / "prefix" / ancestor) == "directory":
                expected.add(ancestor)
        path = root / "prefix" / relative
        if kind(path) == "directory":
            expected.add(relative)
            for row in tree_rows(path):
                expected.add(relative + "/" + row["path"])
        elif kind(path) != "absent":
            expected.add(relative)
    return sorted(expected)


def remaining_manifest_paths(root: Path, runtime_rows: list[dict[str, Any]]) -> list[str]:
    return sorted(row["path"] for row in runtime_rows if kind(root / "prefix" / row["path"]) != "absent")


def exact_owned_leaves(root: Path, runtime_rows: list[dict[str, Any]]) -> list[str]:
    return sorted(
        row["path"]
        for row in runtime_rows
        if row["type"] != "directory" and exact_match(root / "prefix" / row["path"], row)
    )


def final_state_audit(
    *,
    root: Path,
    runtime_rows: list[dict[str, Any]],
    final_class: str,
    subject_paths: Iterable[str] = (),
    subject_snapshots: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    registry = registry_value(root)
    transactions = transaction_inventory(root)
    prefix = root / "prefix"
    rows = tree_rows(prefix)
    observed_paths = [row["path"] for row in rows]
    expected_paths = expected_residual_paths(subject_paths, root, runtime_rows)
    current_subjects = [path_snapshot(prefix / relative, recursive=True) for relative in subject_paths]
    expected_subjects = [snapshot_identity(item) for item in subject_snapshots]
    observed_subjects = [snapshot_identity(item) for item in current_subjects]
    exact_leaves = exact_owned_leaves(root, runtime_rows)
    base_checks = {
        "registry_empty": registry["artifact_count"] == 0 and registry["owned_path_count"] == 0,
        "transactions_empty": transactions == [],
        "owned_payload_absent": exact_leaves == [],
        "residual_membership_exact": observed_paths == expected_paths,
        "subjects_unchanged": observed_subjects == expected_subjects,
    }
    if final_class == "exact-owned-teardown":
        class_checks = {
            "approved_residuals_empty": expected_paths == [] and observed_paths == [],
            "prefix_root_physically_empty": prefix.is_dir() and not any(prefix.iterdir()),
        }
    elif final_class == "modified-owned-residual":
        class_checks = {
            "modified_subject_present": bool(expected_paths) and all(kind(prefix / relative) in {"regular", "symlink"} for relative in subject_paths),
            "prefix_root_not_empty": prefix.is_dir() and any(prefix.iterdir()),
        }
    elif final_class == "unowned-sentinel-residual":
        class_checks = {
            "unowned_subject_present": bool(expected_paths) and all(kind(prefix / relative) != "absent" for relative in subject_paths),
            "prefix_root_not_empty": prefix.is_dir() and any(prefix.iterdir()),
        }
    elif final_class == "mixed-approved-residual":
        class_checks = {
            "mixed_subjects_present": len(list(subject_paths)) >= 2 and all(kind(prefix / relative) != "absent" for relative in subject_paths),
            "prefix_root_not_empty": prefix.is_dir() and any(prefix.iterdir()),
        }
    else:
        raise ValueError(final_class)
    checks = {**base_checks, **class_checks}
    return {
        "schema_version": 1,
        "final_state_class": final_class,
        "registry": registry,
        "transactions": transactions,
        "prefix_rows": rows,
        "observed_paths": observed_paths,
        "expected_residual_paths": expected_paths,
        "exact_owned_leaves": exact_leaves,
        "subject_paths": list(subject_paths),
        "subject_snapshots": current_subjects,
        "checks": checks,
        "pass": all(checks.values()),
    }


def registry_intent_ordinal(uninstall_result: dict[str, Any], runtime_rows: list[dict[str, Any]]) -> int:
    preserved = uninstall_result.get("preserved", [])
    directories = {row["path"] for row in runtime_rows if row["type"] == "directory"}
    failed_directory_intents = sum(path in directories for path in preserved)
    mutation_count = uninstall_result.get("mutation_count")
    if not isinstance(mutation_count, int) or mutation_count <= 0:
        raise RuntimeError("invalid uninstall mutation count")
    return mutation_count + failed_directory_intents


def verify_authorities(
    *,
    gate3b_archive: Path,
    gate3b_results: Path,
    gate3c_archive: Path,
    gate3c_results: Path,
    contract: Path,
    matrix: Path,
    engine: Path,
    operations: Path,
    output: Path,
) -> dict[str, Any]:
    manifest_root = contract / "input/phase3/input/manifest-schema"
    gate3b_verification = read_json(gate3b_results / "verification.json")
    gate3b_scenarios = read_json(gate3b_results / "scenario-summary.json")
    gate3c_verification = read_json(gate3c_results / "verification.json")
    gate3c_scenarios = read_json(gate3c_results / "scenario-summary.json")
    gate3c_safety = gate3c_results / "result-tree-safety.json"
    checks = {
        "gate3b_archive": sha256_file(gate3b_archive) == EXPECTED_GATE3B_ARCHIVE_SHA,
        "gate3b_index": sha256_file(gate3b_results / "result-index.json") == EXPECTED_GATE3B_INDEX_SHA,
        "gate3b_index_contents": verify_result_index(gate3b_results, gate3b_results / "result-index.json")["pass"],
        "gate3b_verifier_62": gate3b_verification.get("pass") is True and gate3b_verification.get("check_count") == 62,
        "gate3b_scenarios_29": gate3b_scenarios.get("pass") is True and gate3b_scenarios.get("check_count") == 29,
        "gate3c_archive": sha256_file(gate3c_archive) == EXPECTED_GATE3C_ARCHIVE_SHA,
        "gate3c_index": sha256_file(gate3c_results / "result-index.json") == EXPECTED_GATE3C_INDEX_SHA,
        "gate3c_index_contents": verify_result_index(gate3c_results, gate3c_results / "result-index.json")["pass"],
        "gate3c_safety": sha256_file(gate3c_safety) == EXPECTED_GATE3C_SAFETY_SHA and read_json(gate3c_safety).get("pass") is True,
        "gate3c_verifier_103": gate3c_verification.get("pass") is True and gate3c_verification.get("check_count") == 103,
        "gate3c_scenarios_50": gate3c_scenarios.get("pass") is True and gate3c_scenarios.get("pass_count") == 50,
        "contract_index": sha256_file(contract / "contract-index.json") == EXPECTED_CONTRACT_INDEX_SHA,
        "manifest_index": sha256_file(manifest_root / "manifest-index.json") == EXPECTED_MANIFEST_INDEX_SHA,
        "gate3d_matrix": sha256_file(matrix) == EXPECTED_GATE3D_MATRIX_SHA,
        "engine": sha256_file(engine) == EXPECTED_ENGINE_SHA,
        "operations": sha256_file(operations) == EXPECTED_OPS_SHA,
    }
    for artifact, expected in EXPECTED_ARTIFACTS.items():
        manifest = manifest_root / "manifests" / f"{artifact}.manifest.json"
        archives = list((contract / "input/phase3/archives").glob(f"*{artifact}.tar.gz"))
        checks[f"{artifact}_manifest"] = sha256_file(manifest) == expected["manifest_sha256"]
        checks[f"{artifact}_archive"] = len(archives) == 1 and sha256_file(archives[0]) == expected["archive_sha256"]
    result = {
        "schema_version": 1,
        "verification_kind": "stage3c-phase5-gate3d-accepted-authorities",
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": sorted(key for key, value in checks.items() if not value),
        "pass": all(checks.values()),
        "claim_boundary": "Authority validation only; target Gate 3D acceptance still requires complete scenario execution and independent archive inspection.",
    }
    write_json(output, result)
    return result
