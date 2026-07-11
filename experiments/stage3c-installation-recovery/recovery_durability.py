#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

TRACE_DIR_ENV = "CPYTHON_ANDROID_CLI_DURABILITY_TRACE_DIR"


def _trace(operation: str, *, label: str, path: Path, **extra: Any) -> None:
    trace_dir_text = os.environ.get(TRACE_DIR_ENV)
    if not trace_dir_text:
        return
    trace_dir = Path(trace_dir_text)
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_path = trace_dir / f"{os.getpid()}.jsonl"
    row: dict[str, Any] = {
        "op": operation,
        "label": label,
        "path": str(path),
        "pid": os.getpid(),
    }
    row.update(extra)
    data = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    descriptor = os.open(
        trace_path,
        os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_CLOEXEC", 0),
        0o600,
    )
    try:
        view = memoryview(data)
        total = 0
        while total < len(view):
            total += os.write(descriptor, view[total:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def fsync_directory(path: Path, *, label: str) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _trace("FSYNC_DIR", label=label, path=path)


def fsync_path(path: Path, *, label: str) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if path.is_dir() and not path.is_symlink():
        flags |= getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _trace("FSYNC_PATH", label=label, path=path)


def durable_ensure_directory(path: Path, *, mode: int = 0o755, label: str) -> None:
    missing: list[Path] = []
    current = path
    while not current.exists():
        missing.append(current)
        parent = current.parent
        if parent == current:
            raise RuntimeError(f"cannot find existing directory ancestor for {path}")
        current = parent
    if current.is_symlink() or not current.is_dir():
        raise RuntimeError(f"directory ancestor is not a directory: {current}")
    for directory in reversed(missing):
        os.mkdir(directory, mode)
        os.chmod(directory, mode)
        _trace("MKDIR", label=label, path=directory, mode=f"{mode:04o}")
        fsync_directory(directory, label=label)
        fsync_directory(directory.parent, label=label)


def durable_mkdir(
    path: Path,
    *,
    mode: int = 0o755,
    parents: bool = False,
    exist_ok: bool = False,
    label: str,
) -> bool:
    if path.exists():
        if exist_ok and path.is_dir() and not path.is_symlink():
            return False
        raise FileExistsError(path)
    if parents:
        durable_ensure_directory(path.parent, mode=0o755, label=label + ":parents")
    elif not path.parent.is_dir() or path.parent.is_symlink():
        raise FileNotFoundError(path.parent)
    os.mkdir(path, mode)
    os.chmod(path, mode)
    _trace("MKDIR", label=label, path=path, mode=f"{mode:04o}")
    fsync_directory(path, label=label)
    fsync_directory(path.parent, label=label)
    return True


def durable_chmod(path: Path, mode: int, *, label: str) -> None:
    os.chmod(path, mode)
    _trace("CHMOD", label=label, path=path, mode=f"{mode:04o}")
    fsync_path(path, label=label)


def _write_all(descriptor: int, data: bytes) -> None:
    view = memoryview(data)
    total = 0
    while total < len(view):
        total += os.write(descriptor, view[total:])


def durable_atomic_write(path: Path, data: bytes, *, mode: int = 0o600, label: str) -> None:
    durable_ensure_directory(path.parent, label=label + ":parent")
    temporary = path.parent / f".{path.name}.tmp-{uuid.uuid4().hex}"
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
        mode,
    )
    _trace("OPEN_TEMP", label=label, path=temporary, target=str(path), mode=f"{mode:04o}")
    try:
        _write_all(descriptor, data)
        os.fchmod(descriptor, mode)
        _trace("WRITE_TEMP", label=label, path=temporary, target=str(path), size=len(data))
        os.fsync(descriptor)
        _trace("FSYNC_FILE", label=label, path=temporary, target=str(path))
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    _trace("REPLACE", label=label, path=temporary, target=str(path))
    fsync_directory(path.parent, label=label)


def durable_copy_file(source: Path, destination: Path, *, mode: int = 0o600, label: str) -> None:
    durable_atomic_write(destination, source.read_bytes(), mode=mode, label=label)


def durable_move(source: Path, destination: Path, *, label: str) -> None:
    durable_ensure_directory(destination.parent, label=label + ":destination-parent")
    source_parent = source.parent
    destination_parent = destination.parent
    os.replace(source, destination)
    _trace("MOVE", label=label, path=source, target=str(destination))
    fsync_directory(source_parent, label=label)
    if destination_parent != source_parent:
        fsync_directory(destination_parent, label=label)


def durable_publish_regular(source: Path, destination: Path, mode: int, *, label: str) -> None:
    durable_ensure_directory(destination.parent, label=label + ":parent")
    temporary = destination.parent / f".{destination.name}.new-{uuid.uuid4().hex}"
    source_descriptor = os.open(source, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
    target_descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
        mode,
    )
    _trace("OPEN_TEMP", label=label, path=temporary, target=str(destination), mode=f"{mode:04o}")
    try:
        while True:
            block = os.read(source_descriptor, 1024 * 1024)
            if not block:
                break
            _write_all(target_descriptor, block)
        os.fchmod(target_descriptor, mode)
        _trace("COPY_TEMP", label=label, path=temporary, target=str(destination))
        os.fsync(target_descriptor)
        _trace("FSYNC_FILE", label=label, path=temporary, target=str(destination))
    finally:
        os.close(target_descriptor)
        os.close(source_descriptor)
    os.replace(temporary, destination)
    _trace("REPLACE", label=label, path=temporary, target=str(destination))
    fsync_directory(destination.parent, label=label)


def durable_publish_symlink(target: str, destination: Path, *, label: str) -> None:
    durable_ensure_directory(destination.parent, label=label + ":parent")
    temporary = destination.parent / f".{destination.name}.new-{uuid.uuid4().hex}"
    os.symlink(target, temporary)
    _trace("SYMLINK_TEMP", label=label, path=temporary, target=target)
    os.replace(temporary, destination)
    _trace("REPLACE", label=label, path=temporary, target=str(destination))
    fsync_directory(destination.parent, label=label)


def durable_unlink(path: Path, *, missing_ok: bool = False, label: str) -> bool:
    try:
        os.unlink(path)
    except FileNotFoundError:
        if missing_ok:
            return False
        raise
    _trace("UNLINK", label=label, path=path)
    fsync_directory(path.parent, label=label)
    return True


def durable_rmdir(path: Path, *, label: str) -> None:
    os.rmdir(path)
    _trace("RMDIR", label=label, path=path)
    fsync_directory(path.parent, label=label)


def durable_tree_remove(path: Path, *, label: str) -> None:
    if path.is_symlink() or path.is_file():
        durable_unlink(path, label=label)
        return
    if not path.exists():
        return
    for child in sorted(path.iterdir(), key=lambda item: item.name, reverse=True):
        durable_tree_remove(child, label=label)
    durable_rmdir(path, label=label)


def durable_cleanup_transaction(transaction: Path, *, label: str) -> None:
    if not transaction.exists():
        return
    journal = transaction / "journal.json"
    for child in sorted(transaction.iterdir(), key=lambda item: item.name, reverse=True):
        if child == journal:
            continue
        durable_tree_remove(child, label=label + ":content")
    if journal.exists() or journal.is_symlink():
        durable_unlink(journal, label=label + ":journal")
    if transaction.exists():
        durable_rmdir(transaction, label=label + ":directory")


def durable_open_lock(path: Path, *, label: str) -> int:
    durable_ensure_directory(path.parent, label=label + ":state")
    flags = os.O_RDWR | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        descriptor = os.open(path, flags)
    else:
        os.fchmod(descriptor, 0o600)
        os.fsync(descriptor)
        _trace("FSYNC_FILE", label=label, path=path)
        fsync_directory(path.parent, label=label)
    return descriptor
