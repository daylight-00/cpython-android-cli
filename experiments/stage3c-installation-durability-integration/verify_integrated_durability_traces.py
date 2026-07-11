#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

REQUIRED_OPERATIONS = {
    "MKDIR",
    "FSYNC_DIR",
    "FSYNC_FILE",
    "OPEN_TEMP",
    "WRITE_TEMP",
    "COPY_TEMP",
    "REPLACE",
    "SYMLINK_TEMP",
    "MOVE",
    "UNLINK",
    "RMDIR",
}
REQUIRED_LABEL_PREFIXES = {
    "installation-state",
    "installation-lock",
    "journal",
    "atomic-write",
    "prior-registry-backup",
    "install-directory-create",
    "install-regular-publish",
    "install-symlink-publish",
    "install-leaf-backup",
    "install-committed-cleanup",
    "uninstall-leaf-remove",
    "uninstall-committed-cleanup",
    "rollback-remove-path",
    "rollback-removed-restore",
    "recovery-committed-cleanup",
}


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def compact_line(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def next_rows(events: list[dict[str, Any]], index: int, count: int) -> list[dict[str, Any]]:
    return events[index + 1 : index + 1 + count]


def validate_file(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    events: list[dict[str, Any]] = []
    canonical = True
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if line != compact_line(row):
            canonical = False
        events.append(row)
    violations: list[dict[str, Any]] = []
    for index, event in enumerate(events):
        operation = event.get("op")
        label = event.get("label")
        path_text = event.get("path")
        if operation == "OPEN_TEMP":
            rows = next_rows(events, index, 4)
            expected_write = "COPY_TEMP" if label == "install-regular-publish" else "WRITE_TEMP"
            expected = [expected_write, "FSYNC_FILE", "REPLACE", "FSYNC_DIR"]
            if [row.get("op") for row in rows] != expected:
                violations.append(
                    {"kind": "atomic-sequence", "file": path.name, "index": index, "label": label}
                )
            elif not (
                all(row.get("label") == label for row in rows)
                and rows[0].get("path") == path_text
                and rows[1].get("path") == path_text
                and rows[2].get("path") == path_text
                and rows[2].get("target") == event.get("target")
                and rows[3].get("path") == str(Path(event["target"]).parent)
            ):
                violations.append(
                    {"kind": "atomic-target", "file": path.name, "index": index, "label": label}
                )
        elif operation == "SYMLINK_TEMP":
            rows = next_rows(events, index, 2)
            if [row.get("op") for row in rows] != ["REPLACE", "FSYNC_DIR"] or not (
                all(row.get("label") == label for row in rows)
                and rows[0].get("path") == path_text
                and rows[1].get("path") == str(Path(rows[0]["target"]).parent)
            ):
                violations.append(
                    {"kind": "symlink-sequence", "file": path.name, "index": index, "label": label}
                )
        elif operation == "MOVE":
            source_parent = str(Path(path_text).parent)
            destination_parent = str(Path(event["target"]).parent)
            needed = 1 if source_parent == destination_parent else 2
            rows = next_rows(events, index, needed)
            expected_paths = [source_parent] if needed == 1 else [source_parent, destination_parent]
            if [row.get("op") for row in rows] != ["FSYNC_DIR"] * needed or not (
                all(row.get("label") == label for row in rows)
                and [row.get("path") for row in rows] == expected_paths
            ):
                violations.append(
                    {"kind": "move-parent-sync", "file": path.name, "index": index, "label": label}
                )
        elif operation == "CHMOD":
            rows = next_rows(events, index, 1)
            if len(rows) != 1 or rows[0].get("op") != "FSYNC_PATH" or not (
                rows[0].get("label") == label and rows[0].get("path") == path_text
            ):
                violations.append(
                    {"kind": "chmod-sync", "file": path.name, "index": index, "label": label}
                )
        elif operation in {"UNLINK", "RMDIR"}:
            rows = next_rows(events, index, 1)
            if len(rows) != 1 or rows[0].get("op") != "FSYNC_DIR" or not (
                rows[0].get("label") == label
                and rows[0].get("path") == str(Path(path_text).parent)
            ):
                violations.append(
                    {"kind": "remove-parent-sync", "file": path.name, "index": index, "label": label}
                )
        elif operation == "MKDIR":
            rows = next_rows(events, index, 2)
            if [row.get("op") for row in rows] != ["FSYNC_DIR", "FSYNC_DIR"] or not (
                all(row.get("label") == label for row in rows)
                and [row.get("path") for row in rows]
                == [path_text, str(Path(path_text).parent)]
            ):
                violations.append(
                    {"kind": "mkdir-sync", "file": path.name, "index": index, "label": label}
                )
    return events, violations, canonical


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    trace_dir = args.trace_dir.resolve()
    trace_files = sorted(trace_dir.glob("*.jsonl"), key=lambda path: path.name)
    all_events: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    canonical_files: list[str] = []
    pid_matches: list[bool] = []
    per_file_counts: dict[str, int] = {}
    for path in trace_files:
        events, file_violations, canonical = validate_file(path)
        all_events.extend(events)
        violations.extend(file_violations)
        if canonical:
            canonical_files.append(path.name)
        per_file_counts[path.name] = len(events)
        try:
            expected_pid = int(path.stem)
        except ValueError:
            expected_pid = -1
        pid_matches.extend(event.get("pid") == expected_pid for event in events)

    operations = Counter(event.get("op") for event in all_events)
    labels = Counter(event.get("label") for event in all_events)
    label_prefixes = {
        prefix
        for prefix in REQUIRED_LABEL_PREFIXES
        if any(label == prefix or str(label).startswith(prefix + ":") for label in labels)
    }
    checks = {
        "trace_files_nonempty": len(trace_files) > 0,
        "trace_events_nonempty": len(all_events) > 0,
        "trace_files_canonical": len(canonical_files) == len(trace_files),
        "trace_pids_match_filenames": bool(pid_matches) and all(pid_matches),
        "trace_row_keys_present": all(
            {"op", "label", "path", "pid"} <= set(event)
            for event in all_events
        ),
        "required_operations_present": REQUIRED_OPERATIONS <= set(operations),
        "required_label_prefixes_present": label_prefixes == REQUIRED_LABEL_PREFIXES,
        "atomic_sequences_valid": not any(item["kind"].startswith("atomic-") for item in violations),
        "symlink_sequences_valid": not any(item["kind"] == "symlink-sequence" for item in violations),
        "move_parent_sync_valid": not any(item["kind"] == "move-parent-sync" for item in violations),
        "chmod_sync_valid_or_not_exercised": not any(item["kind"] == "chmod-sync" for item in violations),
        "remove_parent_sync_valid": not any(item["kind"] == "remove-parent-sync" for item in violations),
        "mkdir_sync_valid": not any(item["kind"] == "mkdir-sync" for item in violations),
        "violations_absent": violations == [],
        "journal_atomic_writes_present": labels["journal"] > 0
        and operations["WRITE_TEMP"] > 0,
        "payload_regular_publication_present": labels["install-regular-publish"] > 0
        and operations["COPY_TEMP"] > 0,
        "payload_symlink_publication_present": labels["install-symlink-publish"] > 0
        and operations["SYMLINK_TEMP"] > 0,
        "payload_backup_moves_present": labels["install-leaf-backup"] > 0
        and operations["MOVE"] > 0,
        "uninstall_moves_present": labels["uninstall-leaf-remove"] > 0,
        "rollback_created_removal_present": labels["rollback-remove-path"] > 0,
        "rollback_removed_restore_present": labels["rollback-removed-restore"] > 0,
        "committed_cleanup_present": any(
            str(label).startswith("recovery-committed-cleanup") for label in labels
        ),
        "transaction_journal_cleanup_present": any(
            str(label).endswith(":journal") for label in labels
        ),
        "transaction_directory_cleanup_present": any(
            str(label).endswith(":directory") for label in labels
        ),
        "file_fsync_count_positive": operations["FSYNC_FILE"] > 0,
        "directory_fsync_count_positive": operations["FSYNC_DIR"] > 0,
        "replace_count_positive": operations["REPLACE"] > 0,
        "unlink_count_positive": operations["UNLINK"] > 0,
        "rmdir_count_positive": operations["RMDIR"] > 0,
    }
    if len(checks) != 29:
        raise RuntimeError(f"unexpected check count: {len(checks)}")
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "trace_file_count": len(trace_files),
        "event_count": len(all_events),
        "operations": dict(sorted(operations.items())),
        "labels": dict(sorted(labels.items())),
        "per_file_counts": per_file_counts,
        "violations": violations,
        "claim_boundary": {
            "proved": "Observed integrated recovery operations emitted ordered file and directory sync traces for the exercised journal, registry, payload, backup, rollback, and cleanup paths.",
            "not_proved": "Trace evidence does not simulate actual sudden power loss or interruption inside a filesystem primitive.",
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 55


if __name__ == "__main__":
    raise SystemExit(main())
