from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Trace:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(
        self,
        operation: str,
        *,
        label: str,
        path: Path,
        **extra: Any,
    ) -> None:
        row: dict[str, Any] = {
            "seq": len(self.events) + 1,
            "op": operation,
            "label": label,
            "path": str(path),
        }
        row.update(extra)
        self.events.append(row)

    def document(self, kind: str) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "trace_kind": kind,
            "event_count": len(self.events),
            "events": self.events,
        }


def fsync_directory(path: Path, trace: Trace, label: str) -> None:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    trace.record("FSYNC_DIR", label=label, path=path)


def atomic_replace_bytes(
    target: Path,
    data: bytes,
    mode: int,
    trace: Trace,
    label: str,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / f".{target.name}.tmp-{uuid.uuid4().hex}"
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(temporary, flags, mode)
    trace.record(
        "OPEN_TEMP",
        label=label,
        path=temporary,
        target=str(target),
        mode=f"{mode:04o}",
    )
    try:
        view = memoryview(data)
        total = 0
        while total < len(view):
            total += os.write(descriptor, view[total:])
        trace.record(
            "WRITE_TEMP",
            label=label,
            path=temporary,
            size=len(data),
            sha256=sha256_bytes(data),
        )
        os.fsync(descriptor)
        trace.record("FSYNC_FILE", label=label, path=temporary)
    finally:
        os.close(descriptor)

    os.replace(temporary, target)
    trace.record(
        "REPLACE",
        label=label,
        path=temporary,
        target=str(target),
    )
    fsync_directory(target.parent, trace, label)


def durable_mkdir(path: Path, mode: int, trace: Trace, label: str) -> None:
    os.mkdir(path, mode)
    os.chmod(path, mode)
    trace.record("MKDIR", label=label, path=path, mode=f"{mode:04o}")
    fsync_directory(path, trace, label)
    fsync_directory(path.parent, trace, label)


def durable_move(
    source: Path,
    destination: Path,
    trace: Trace,
    label: str,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)
    trace.record(
        "MOVE",
        label=label,
        path=source,
        target=str(destination),
    )
    fsync_directory(source.parent, trace, label)
    if destination.parent != source.parent:
        fsync_directory(destination.parent, trace, label)


def durable_unlink(path: Path, trace: Trace, label: str) -> None:
    os.unlink(path)
    trace.record("UNLINK", label=label, path=path)
    fsync_directory(path.parent, trace, label)


def durable_rmdir(path: Path, trace: Trace, label: str) -> None:
    os.rmdir(path)
    trace.record("RMDIR", label=label, path=path)
    fsync_directory(path.parent, trace, label)


def audit_atomic(
    events: list[dict[str, Any]],
    label: str,
    target: Path,
) -> tuple[bool, list[str]]:
    rows = [event for event in events if event.get("label") == label]
    reasons: list[str] = []
    expected = [
        "OPEN_TEMP",
        "WRITE_TEMP",
        "FSYNC_FILE",
        "REPLACE",
        "FSYNC_DIR",
    ]
    if [event.get("op") for event in rows] != expected:
        reasons.append("operation-sequence")
    if rows:
        if rows[-1].get("path") != str(target.parent):
            reasons.append("parent-fsync-path")
        if len(rows) >= 2 and rows[-2].get("target") != str(target):
            reasons.append("replace-target")
        if len(rows) == 5 and not all(
            rows[index]["seq"] < rows[index + 1]["seq"]
            for index in range(4)
        ):
            reasons.append("sequence-order")
    return not reasons, reasons
