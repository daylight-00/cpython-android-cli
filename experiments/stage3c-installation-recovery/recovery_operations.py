#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any
import os
import shutil
import stat
import uuid

from recovery_common import (
    ARTIFACTS,
    REGISTRY_KIND,
    CrashController,
    actual_kind,
    add_intent,
    artifact_metadata,
    atomic_write,
    canonical_json_bytes,
    ensure_no_symlink_parent,
    installation_lock,
    load_inputs,
    load_registry,
    mark_applied,
    matches,
    persist_journal,
    record_from_entry,
    save_prior_registry,
    stage_archive,
)


def install(
    contract_results: Path,
    root: Path,
    artifact: str,
    *,
    nonblocking_lock: bool = False,
    crash_after_prepared: bool = False,
    crash_after_intents: int | None = None,
    crash_after_mutations: int | None = None,
    crash_after_commit: bool = False,
    fast_success: bool = False,
) -> dict[str, Any]:
    manifest, archive, archive_info = load_inputs(contract_results, artifact)
    prefix = root / "prefix"
    prefix.mkdir(parents=True, exist_ok=True)
    crash = CrashController(
        after_prepared=crash_after_prepared,
        after_intents=crash_after_intents,
        after_mutations=crash_after_mutations,
        after_commit=crash_after_commit,
        persist_each_checkpoint=not fast_success,
    )
    with installation_lock(root, nonblocking=nonblocking_lock) as state:
        registry_path = state / "registry.json"
        current_registry = load_registry(registry_path)
        path_map = {item["path"]: item for item in current_registry["owned_paths"]}
        artifact_map = {item["artifact"]: item for item in current_registry["artifacts"]}
        prerequisite = manifest["compatibility"]["prerequisite"]
        if prerequisite and (
            prerequisite["artifact"] not in artifact_map
            or artifact_map[prerequisite["artifact"]]["artifact_id"] != prerequisite["artifact_id"]
        ):
            raise RuntimeError("prerequisite not installed")

        owned = [entry for entry in manifest["entries"] if entry["entry_class"] == "OWNED_PAYLOAD"]
        structural = [entry for entry in manifest["entries"] if entry["entry_class"] == "STRUCTURAL_PARENT"]
        plan: list[tuple[str, dict[str, Any]]] = []
        for entry in structural:
            relative = entry["payload_path"]
            ensure_no_symlink_parent(prefix, relative)
            path = prefix / relative
            kind = actual_kind(path)
            if kind not in ("absent", "directory"):
                raise RuntimeError(f"structural collision {relative}")
            if kind == "directory" and f"{stat.S_IMODE(path.lstat().st_mode):04o}" != entry["mode"]:
                raise RuntimeError(f"structural mode mismatch {relative}")
            if kind == "absent":
                plan.append(("mkdir-structural", entry))

        for entry in owned:
            relative = entry["payload_path"]
            ensure_no_symlink_parent(prefix, relative)
            path = prefix / relative
            kind = actual_kind(path)
            old = path_map.get(relative)
            desired = record_from_entry(entry, artifact)
            if old and old["owner_artifact"] != artifact:
                raise RuntimeError(f"other owner {relative}")
            if old:
                if matches(path, desired):
                    plan.append(("noop", entry))
                elif entry["type"] == "directory":
                    plan.append(("repair-dir", entry))
                else:
                    plan.append(("repair", entry))
            elif kind == "absent":
                plan.append(("create", entry))
            elif (
                entry["type"] == "directory"
                and kind == "directory"
                and f"{stat.S_IMODE(path.lstat().st_mode):04o}" == entry["mode"]
            ):
                plan.append(("reuse-dir", entry))
            else:
                raise RuntimeError(f"unowned collision {relative}")

        actionable = [item for item in plan if item[0] not in ("noop", "reuse-dir")]
        if not actionable and artifact in artifact_map:
            return {
                "operation": "install",
                "artifact": artifact,
                "pass": True,
                "noop": True,
                "action_counts": dict(Counter(action for action, _ in plan)),
                "mutation_count": 0,
            }

        transaction_id = "install-" + artifact + "-" + uuid.uuid4().hex
        transaction = state / "transactions" / transaction_id
        transaction.mkdir(parents=True)
        staging = stage_archive(archive, manifest, transaction / "staging")
        (transaction / "backup").mkdir()
        prior_registry_exists = save_prior_registry(transaction, registry_path)
        journal: dict[str, Any] = {
            "schema_version": 2,
            "journal_kind": "cpython-android-cli-crash-recoverable-transaction",
            "id": transaction_id,
            "operation": "install",
            "artifact": artifact,
            "state": "PREPARED",
            "prior_registry_exists": prior_registry_exists,
            "plan": [{"action": action, "path": entry["payload_path"]} for action, entry in plan],
            "mutations": [],
        }
        persist_journal(transaction, journal)
        crash.crash_prepared()
        journal["state"] = "APPLYING"
        persist_journal(transaction, journal)

        directories = [
            (action, entry)
            for action, entry in plan
            if entry["type"] == "directory" and action in ("mkdir-structural", "create", "repair-dir")
        ]
        directories.sort(key=lambda item: len(PurePosixPath(item[1]["payload_path"]).parts))
        for action, entry in directories:
            relative = entry["payload_path"]
            path = prefix / relative
            if action in ("mkdir-structural", "create"):
                index = add_intent(transaction, journal, {"kind": "created", "path": relative}, crash)
                path.mkdir(parents=True, exist_ok=False)
                os.chmod(path, int(entry["mode"], 8))
                mark_applied(transaction, journal, index, crash)
            else:
                kind = actual_kind(path)
                if kind == "absent":
                    index = add_intent(transaction, journal, {"kind": "created", "path": relative}, crash)
                    path.mkdir(parents=True, exist_ok=False)
                    os.chmod(path, int(entry["mode"], 8))
                    mark_applied(transaction, journal, index, crash)
                elif kind == "directory":
                    old_mode = f"{stat.S_IMODE(path.lstat().st_mode):04o}"
                    index = add_intent(
                        transaction,
                        journal,
                        {"kind": "chmod", "path": relative, "old_mode": old_mode},
                        crash,
                    )
                    os.chmod(path, int(entry["mode"], 8))
                    mark_applied(transaction, journal, index, crash)
                else:
                    backup_path = transaction / "backup" / relative
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    index = add_intent(
                        transaction,
                        journal,
                        {
                            "kind": "replaced",
                            "path": relative,
                            "backup": str(backup_path.relative_to(transaction)),
                        },
                        crash,
                    )
                    os.replace(path, backup_path)
                    path.mkdir(parents=True, exist_ok=False)
                    os.chmod(path, int(entry["mode"], 8))
                    mark_applied(transaction, journal, index, crash)

        for action, entry in plan:
            if entry["type"] == "directory" or action in ("noop", "reuse-dir"):
                continue
            relative = entry["payload_path"]
            path = prefix / relative
            source = staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if action == "repair":
                backup_path = transaction / "backup" / relative
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                record = {
                    "kind": "replaced",
                    "path": relative,
                    "backup": str(backup_path.relative_to(transaction)),
                }
            else:
                backup_path = None
                record = {"kind": "created", "path": relative}
            index = add_intent(transaction, journal, record, crash)
            if backup_path is not None:
                os.replace(path, backup_path)
            temporary = path.with_name(path.name + ".new-" + uuid.uuid4().hex)
            if entry["type"] == "regular":
                shutil.copyfile(source, temporary, follow_symlinks=False)
                os.chmod(temporary, int(entry["mode"], 8))
            else:
                os.symlink(os.readlink(source), temporary)
            os.replace(temporary, path)
            mark_applied(transaction, journal, index, crash)

        new_paths = {key: value for key, value in path_map.items() if value["owner_artifact"] != artifact}
        for entry in owned:
            new_paths[entry["payload_path"]] = record_from_entry(entry, artifact)
        new_artifacts = {key: value for key, value in artifact_map.items() if key != artifact}
        new_artifacts[artifact] = artifact_metadata(manifest, archive, archive_info)
        new_registry = {
            "schema_version": 1,
            "registry_kind": REGISTRY_KIND,
            "artifacts": [new_artifacts[name] for name in ARTIFACTS if name in new_artifacts],
            "owned_paths": [new_paths[name] for name in sorted(new_paths)],
        }
        index = add_intent(
            transaction,
            journal,
            {"kind": "registry", "prior_exists": prior_registry_exists},
            crash,
        )
        atomic_write(registry_path, canonical_json_bytes(new_registry))
        mark_applied(transaction, journal, index, crash)
        journal["state"] = "COMMITTED"
        persist_journal(transaction, journal)
        crash.crash_committed()
        shutil.rmtree(transaction)

        return {
            "operation": "install",
            "artifact": artifact,
            "pass": True,
            "noop": False,
            "action_counts": dict(Counter(action for action, _ in plan)),
            "mutation_count": crash.applied_mutations,
        }


def uninstall(
    contract_results: Path,
    root: Path,
    artifact: str,
    *,
    nonblocking_lock: bool = False,
    crash_after_prepared: bool = False,
    crash_after_intents: int | None = None,
    crash_after_mutations: int | None = None,
    crash_after_commit: bool = False,
    fast_success: bool = False,
) -> dict[str, Any]:
    del contract_results
    prefix = root / "prefix"
    crash = CrashController(
        after_prepared=crash_after_prepared,
        after_intents=crash_after_intents,
        after_mutations=crash_after_mutations,
        after_commit=crash_after_commit,
        persist_each_checkpoint=not fast_success,
    )
    with installation_lock(root, nonblocking=nonblocking_lock) as state:
        registry_path = state / "registry.json"
        current_registry = load_registry(registry_path)
        artifact_map = {item["artifact"]: item for item in current_registry["artifacts"]}
        rows = [item for item in current_registry["owned_paths"] if item["owner_artifact"] == artifact]
        if artifact not in artifact_map:
            raise RuntimeError("artifact not installed")
        if artifact == "runtime-base":
            dependents = [item["artifact"] for item in current_registry["artifacts"] if item["artifact"] != artifact]
            if dependents:
                raise RuntimeError("dependent addons installed")

        transaction_id = "uninstall-" + artifact + "-" + uuid.uuid4().hex
        transaction = state / "transactions" / transaction_id
        transaction.mkdir(parents=True)
        (transaction / "backup").mkdir()
        prior_registry_exists = save_prior_registry(transaction, registry_path)
        journal: dict[str, Any] = {
            "schema_version": 2,
            "journal_kind": "cpython-android-cli-crash-recoverable-transaction",
            "id": transaction_id,
            "operation": "uninstall",
            "artifact": artifact,
            "state": "PREPARED",
            "prior_registry_exists": prior_registry_exists,
            "mutations": [],
            "preserved": [],
        }
        persist_journal(transaction, journal)
        crash.crash_prepared()
        journal["state"] = "APPLYING"
        persist_journal(transaction, journal)

        leaves = [row for row in rows if row["type"] != "directory"]
        leaves.sort(key=lambda row: row["path"], reverse=True)
        for row in leaves:
            path = prefix / row["path"]
            if matches(path, row):
                backup_path = transaction / "backup" / row["path"]
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                index = add_intent(
                    transaction,
                    journal,
                    {
                        "kind": "removed",
                        "path": row["path"],
                        "backup": str(backup_path.relative_to(transaction)),
                    },
                    crash,
                )
                os.replace(path, backup_path)
                mark_applied(transaction, journal, index, crash)
            else:
                journal["preserved"].append(row["path"])
                persist_journal(transaction, journal)

        directories = [row for row in rows if row["type"] == "directory"]
        directories.sort(
            key=lambda row: (len(PurePosixPath(row["path"]).parts), row["path"]),
            reverse=True,
        )
        for row in directories:
            path = prefix / row["path"]
            if path.is_dir() and not path.is_symlink():
                index = add_intent(
                    transaction,
                    journal,
                    {"kind": "removed-dir", "path": row["path"], "mode": row["mode"]},
                    crash,
                )
                try:
                    path.rmdir()
                except OSError:
                    journal["mutations"].pop(index)
                    journal["preserved"].append(row["path"])
                    persist_journal(transaction, journal)
                else:
                    mark_applied(transaction, journal, index, crash)
            elif actual_kind(path) != "absent":
                journal["preserved"].append(row["path"])
                persist_journal(transaction, journal)

        new_registry = {
            "schema_version": 1,
            "registry_kind": REGISTRY_KIND,
            "artifacts": [item for item in current_registry["artifacts"] if item["artifact"] != artifact],
            "owned_paths": [item for item in current_registry["owned_paths"] if item["owner_artifact"] != artifact],
        }
        index = add_intent(
            transaction,
            journal,
            {"kind": "registry", "prior_exists": prior_registry_exists},
            crash,
        )
        atomic_write(registry_path, canonical_json_bytes(new_registry))
        mark_applied(transaction, journal, index, crash)
        journal["state"] = "COMMITTED"
        persist_journal(transaction, journal)
        crash.crash_committed()
        preserved = sorted(set(journal["preserved"]))
        shutil.rmtree(transaction)
        return {
            "operation": "uninstall",
            "artifact": artifact,
            "pass": True,
            "preserved": preserved,
            "mutation_count": crash.applied_mutations,
        }
