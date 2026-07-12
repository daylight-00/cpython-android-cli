#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from gate3b0_preservation_support import (
    EXPECTED_CONTRACT_INDEX,
    EXPECTED_ENGINE_SHA,
    EXPECTED_OPS_SHA,
    REGULAR_CANDIDATE,
    SYMLINK_CANDIDATE,
    UNOWNED_DIR,
    UNOWNED_FILE,
    clone_seed,
    create_sentinel,
    kind,
    mutate_owned,
    owned_digest,
    read_json,
    registry,
    remaining_registered_leaves,
    snapshot,
    transactions,
    write_json,
)

EXPECTED_GATE3B0_INDEX = "7a8e982a44118dac3f232b2fefb578d22bedc0c7d32a6267ab3cd55c5e8deb27"
SUBJECTS = (
    "owned-regular",
    "owned-symlink",
    "unowned-file",
    "unowned-directory",
)
BOUNDARIES = ("prepared", "applying-late", "committed")


def snapshot_identity(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "path"}


def prepare_subject(
    root: Path,
    subject: str,
    regular: dict[str, Any],
    symlink: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any] | None]:
    if subject == "owned-regular":
        mutation = mutate_owned(root, regular, "uninstall-owned-regular")
        return regular["path"], mutation["after"], regular
    if subject == "owned-symlink":
        mutation = mutate_owned(root, symlink, "uninstall-owned-symlink")
        return symlink["path"], mutation["after"], symlink
    if subject == "unowned-file":
        relative, observed = create_sentinel(root, "uninstall-unowned-file")
        return relative, observed, None
    if subject == "unowned-directory":
        relative, observed = create_sentinel(root, "uninstall-unowned-directory")
        return relative, observed, None
    raise ValueError(subject)


def invoke_engine_process(
    *,
    runner: Path,
    engine: Path,
    contract: Path,
    root: Path,
    operation: str,
    output: Path,
    artifact: str | None = None,
    crash_flag: str | None = None,
    crash_value: int | None = None,
) -> dict[str, Any]:
    command = [
        sys.executable,
        "-I",
        "-B",
        "-S",
        str(runner),
        str(engine),
        "--installation-root",
        str(root),
        "--operation",
        operation,
        "--output",
        str(output),
    ]
    if operation == "install":
        command.extend(("--contract-results", str(contract)))
    if artifact is not None:
        command.extend(("--artifact", artifact))
    if crash_flag is not None:
        command.append(crash_flag)
        if crash_value is not None:
            command.append(str(crash_value))
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    log_path = output.with_suffix(".log")
    log_path.write_text(completed.stdout, encoding="utf-8")
    result = read_json(output) if output.is_file() else None
    process = {
        "returncode": completed.returncode,
        "result": result,
        "output_exists": output.is_file(),
        "log": log_path.name,
        "command_crash_flag": crash_flag,
        "command_crash_value": crash_value,
    }
    write_json(output.with_name(output.stem + "-process.json"), process)
    return process


def one_transaction(root: Path) -> tuple[Path, dict[str, Any]]:
    tx_root = root / ".cpython-android-cli/transactions"
    directories = sorted(path for path in tx_root.iterdir() if path.is_dir())
    if len(directories) != 1:
        raise RuntimeError(f"expected one transaction, found {len(directories)}")
    transaction = directories[0]
    return transaction, read_json(transaction / "journal.json")


def recovery_state(
    *,
    root: Path,
    rows: list[dict[str, Any]],
    subject_path: str,
) -> dict[str, Any]:
    return {
        "registry": registry(root),
        "owned_digest": owned_digest(root, rows),
        "subject": snapshot(root / "prefix" / subject_path),
        "remaining_registered_leaves": remaining_registered_leaves(root, rows),
        "remaining_registered_paths": remaining_registered_paths(root, rows),
        "transactions": transactions(root),
    }


def expected_verify_bad_paths(subject: str, subject_path: str, committed: bool) -> list[str]:
    if committed:
        return []
    if subject.startswith("owned-"):
        return [subject_path]
    return []


def expected_remaining_leaves(
    subject: str,
    subject_path: str,
    all_registered_leaves: list[str],
    committed: bool,
) -> list[str]:
    if not committed:
        return all_registered_leaves
    if subject.startswith("owned-"):
        return [subject_path]
    return []


def recovery_action(result: dict[str, Any] | None) -> tuple[int | None, str | None]:
    if not result:
        return None, None
    actions = result.get("actions", [])
    if len(actions) != 1:
        return len(actions), None
    return 1, actions[0].get("action")


def remaining_registered_paths(root: Path, rows: list[dict[str, Any]]) -> list[str]:
    return sorted(row["path"] for row in rows if kind(root / "prefix" / row["path"]) != "absent")


def expected_preserved_paths(
    subject_path: str,
    candidate: dict[str, Any] | None,
    rows: list[dict[str, Any]],
) -> list[str]:
    directory_paths = {row["path"] for row in rows if row["type"] == "directory"}
    parts = subject_path.split("/")
    ancestors = ["/".join(parts[:index]) for index in range(1, len(parts))]
    expected = {path for path in ancestors if path in directory_paths}
    if candidate is not None:
        expected.add(subject_path)
    return sorted(expected)


def registry_intent_ordinal(
    happy_uninstall: dict[str, Any],
    rows: list[dict[str, Any]],
) -> int:
    directory_paths = {row["path"] for row in rows if row["type"] == "directory"}
    failed_directory_intents = sum(
        path in directory_paths for path in happy_uninstall.get("preserved_rows", [])
    )
    mutation_count = happy_uninstall.get("uninstall", {}).get("result", {}).get("mutation_count")
    if not isinstance(mutation_count, int) or mutation_count <= 0:
        raise RuntimeError("invalid happy uninstall mutation count")
    return mutation_count + failed_directory_intents
