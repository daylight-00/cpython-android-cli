#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from recovery_common import (
    ARTIFACTS,
    actual_kind,
    atomic_write,
    canonical_json_bytes,
    installation_lock,
    load_registry,
    matches,
    persist_journal,
    read_json,
    sha256_file,
)
from recovery_durability import (
    durable_chmod,
    durable_cleanup_transaction,
    durable_ensure_directory,
    durable_mkdir,
    durable_move,
    durable_tree_remove,
    durable_unlink,
)
from recovery_operations import install, uninstall


def remove_path(path: Path) -> None:
    durable_tree_remove(path, label="rollback-remove-path")


def rollback_transaction(root: Path, transaction: Path, journal: dict[str, Any]) -> dict[str, Any]:
    prefix = root / "prefix"
    state = root / ".cpython-android-cli"
    registry_path = state / "registry.json"
    journal["state"] = "ROLLING_BACK"
    persist_journal(transaction, journal)
    restored = 0
    for mutation in reversed(journal.get("mutations", [])):
        kind = mutation["kind"]
        relative = mutation.get("path")
        if kind == "registry":
            backup = transaction / "backup/prior-registry.json"
            if mutation.get("prior_exists"):
                if not backup.is_file():
                    raise RuntimeError("missing prior registry backup")
                atomic_write(registry_path, backup.read_bytes())
            else:
                durable_unlink(
                    registry_path,
                    missing_ok=True,
                    label="rollback-registry-remove",
                )
            restored += 1
        elif kind == "created":
            path = prefix / relative
            if actual_kind(path) != "absent":
                remove_path(path)
                restored += 1
        elif kind == "replaced":
            path = prefix / relative
            backup = transaction / mutation["backup"]
            if backup.exists() or backup.is_symlink():
                if actual_kind(path) != "absent":
                    remove_path(path)
                durable_ensure_directory(path.parent, label="rollback-replaced-parent")
                durable_move(backup, path, label="rollback-replaced-restore")
                restored += 1
        elif kind == "chmod":
            path = prefix / relative
            if path.is_dir() and not path.is_symlink():
                durable_chmod(
                    path,
                    int(mutation["old_mode"], 8),
                    label="rollback-chmod-restore",
                )
                restored += 1
        elif kind == "removed":
            path = prefix / relative
            backup = transaction / mutation["backup"]
            if backup.exists() or backup.is_symlink():
                if actual_kind(path) != "absent":
                    remove_path(path)
                durable_ensure_directory(path.parent, label="rollback-removed-parent")
                durable_move(backup, path, label="rollback-removed-restore")
                restored += 1
        elif kind == "removed-dir":
            path = prefix / relative
            if actual_kind(path) == "absent":
                durable_mkdir(
                    path,
                    mode=int(mutation["mode"], 8),
                    parents=True,
                    label="rollback-directory-restore",
                )
                restored += 1
        else:
            raise RuntimeError(f"unknown mutation kind: {kind}")
    journal["state"] = "ROLLED_BACK"
    journal["recovery"] = {"action": "rollback", "restored_count": restored}
    persist_journal(transaction, journal)
    return {
        "transaction": transaction.name,
        "prior_state": "APPLYING_OR_PREPARED",
        "action": "ROLLED_BACK",
        "restored_count": restored,
    }


def recover(root: Path, *, nonblocking_lock: bool = False) -> dict[str, Any]:
    with installation_lock(root, nonblocking=nonblocking_lock) as state:
        transactions_root = state / "transactions"
        durable_ensure_directory(transactions_root, label="recovery-transactions-root")
        actions: list[dict[str, Any]] = []
        for transaction in sorted(path for path in transactions_root.iterdir() if path.is_dir()):
            journal_path = transaction / "journal.json"
            if not journal_path.is_file():
                durable_cleanup_transaction(transaction, label="recovery-unjournaled-prepare")
                actions.append(
                    {
                        "transaction": transaction.name,
                        "prior_state": "UNJOURNALED_PREPARE",
                        "action": "DISCARDED_PREPARE",
                        "restored_count": 0,
                    }
                )
                continue
            journal = read_json(journal_path)
            current_state = journal.get("state")
            if current_state in {"PREPARED", "APPLYING", "ROLLING_BACK"}:
                actions.append(rollback_transaction(root, transaction, journal))
            elif current_state == "COMMITTED":
                actions.append(
                    {
                        "transaction": transaction.name,
                        "prior_state": "COMMITTED",
                        "action": "FINALIZED_COMMIT",
                        "restored_count": 0,
                    }
                )
                durable_cleanup_transaction(transaction, label="recovery-committed-cleanup")
            elif current_state == "ROLLED_BACK":
                actions.append(
                    {
                        "transaction": transaction.name,
                        "prior_state": "ROLLED_BACK",
                        "action": "NOOP_ROLLED_BACK",
                        "restored_count": 0,
                    }
                )
            else:
                raise RuntimeError(f"unknown transaction state: {current_state}")
        return {
            "operation": "recover",
            "pass": True,
            "transaction_count": len(actions),
            "actions": actions,
        }


def verify(root: Path) -> dict[str, Any]:
    registry_path = root / ".cpython-android-cli/registry.json"
    current_registry = load_registry(registry_path)
    prefix = root / "prefix"
    bad_paths = [
        row["path"]
        for row in current_registry["owned_paths"]
        if not matches(prefix / row["path"], row)
    ]
    return {
        "operation": "verify",
        "pass": not bad_paths,
        "artifact_count": len(current_registry["artifacts"]),
        "owned_path_count": len(current_registry["owned_paths"]),
        "bad_paths": bad_paths,
        "registry_sha256": sha256_file(registry_path) if registry_path.exists() else None,
    }


def hold_lock(root: Path, seconds: float, ready_file: Path | None) -> dict[str, Any]:
    with installation_lock(root):
        if ready_file is not None:
            ready_file.parent.mkdir(parents=True, exist_ok=True)
            ready_file.write_text("ready\n", encoding="utf-8")
        time.sleep(seconds)
    return {"operation": "hold-lock", "pass": True, "seconds": seconds}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-results", type=Path)
    parser.add_argument("--installation-root", required=True, type=Path)
    parser.add_argument(
        "--operation",
        required=True,
        choices=("install", "uninstall", "verify", "recover", "hold-lock"),
    )
    parser.add_argument("--artifact", choices=ARTIFACTS)
    parser.add_argument("--nonblocking-lock", action="store_true")
    parser.add_argument("--crash-after-prepared", action="store_true")
    parser.add_argument("--crash-after-intents", type=int)
    parser.add_argument("--crash-after-mutations", type=int)
    parser.add_argument("--crash-after-commit", action="store_true")
    parser.add_argument("--fast-success", action="store_true")
    parser.add_argument("--hold-seconds", type=float, default=1.0)
    parser.add_argument("--ready-file", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.fast_success and (
        args.crash_after_prepared
        or args.crash_after_intents is not None
        or args.crash_after_mutations is not None
        or args.crash_after_commit
    ):
        parser.error("--fast-success cannot be combined with crash injection")

    try:
        if args.operation == "install":
            if args.contract_results is None or args.artifact is None:
                raise RuntimeError("install requires contract results and artifact")
            result = install(
                args.contract_results.resolve(),
                args.installation_root.resolve(),
                args.artifact,
                nonblocking_lock=args.nonblocking_lock,
                crash_after_prepared=args.crash_after_prepared,
                crash_after_intents=args.crash_after_intents,
                crash_after_mutations=args.crash_after_mutations,
                crash_after_commit=args.crash_after_commit,
                fast_success=args.fast_success,
            )
        elif args.operation == "uninstall":
            if args.artifact is None:
                raise RuntimeError("uninstall requires artifact")
            result = uninstall(
                (args.contract_results or Path(".")).resolve(),
                args.installation_root.resolve(),
                args.artifact,
                nonblocking_lock=args.nonblocking_lock,
                crash_after_prepared=args.crash_after_prepared,
                crash_after_intents=args.crash_after_intents,
                crash_after_mutations=args.crash_after_mutations,
                crash_after_commit=args.crash_after_commit,
                fast_success=args.fast_success,
            )
        elif args.operation == "verify":
            result = verify(args.installation_root.resolve())
        elif args.operation == "recover":
            result = recover(args.installation_root.resolve(), nonblocking_lock=args.nonblocking_lock)
        else:
            result = hold_lock(
                args.installation_root.resolve(),
                args.hold_seconds,
                args.ready_file.resolve() if args.ready_file else None,
            )
    except Exception as exc:
        result = {
            "operation": args.operation,
            "artifact": args.artifact,
            "pass": False,
            "error": repr(exc),
        }

    if args.output is not None:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") else 44


if __name__ == "__main__":
    raise SystemExit(main())
