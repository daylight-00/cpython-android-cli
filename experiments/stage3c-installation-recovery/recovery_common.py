#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import shutil
import stat
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

from recovery_durability import (
    durable_atomic_write,
    durable_copy_file,
    durable_ensure_directory,
    durable_open_lock,
)

ARTIFACTS = ("runtime-base", "development-addon", "test-addon")
REGISTRY_KIND = "cpython-android-cli-installed-ownership-registry"


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


def atomic_write(path: Path, data: bytes) -> None:
    durable_atomic_write(path, data, mode=0o600, label="atomic-write")


def empty_registry() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "registry_kind": REGISTRY_KIND,
        "artifacts": [],
        "owned_paths": [],
    }


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_registry()
    value = read_json(path)
    if value.get("schema_version") != 1 or value.get("registry_kind") != REGISTRY_KIND:
        raise RuntimeError("invalid registry")
    return value


def actual_kind(path: Path) -> str:
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return "absent"
    if stat.S_ISLNK(observed.st_mode):
        return "symlink"
    if stat.S_ISDIR(observed.st_mode):
        return "directory"
    if stat.S_ISREG(observed.st_mode):
        return "regular"
    return "special"


def record_from_entry(entry: dict[str, Any], artifact: str) -> dict[str, Any]:
    return {
        "path": entry["payload_path"],
        "owner_artifact": artifact,
        "type": entry["type"],
        "mode": entry["mode"],
        "size": entry.get("size"),
        "sha256": entry.get("sha256"),
        "symlink_target": entry.get("symlink_target"),
        "component": entry.get("component", ""),
        "elf": entry.get("elf") is True,
    }


def matches(path: Path, record: dict[str, Any]) -> bool:
    kind = actual_kind(path)
    if kind != record["type"]:
        return False
    if f"{stat.S_IMODE(path.lstat().st_mode):04o}" != record["mode"]:
        return False
    if kind == "regular":
        return path.stat().st_size == record["size"] and sha256_file(path) == record["sha256"]
    if kind == "symlink":
        return os.readlink(path) == record["symlink_target"]
    return True


def ensure_no_symlink_parent(prefix: Path, relative: str) -> None:
    current = prefix
    for part in PurePosixPath(relative).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(f"symlink parent: {current}")
        if current.exists() and not current.is_dir():
            raise RuntimeError(f"non-directory parent: {current}")


def artifact_metadata(manifest: dict[str, Any], archive: Path, archive_info: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact": manifest["artifact"]["name"],
        "artifact_id": manifest["artifact"]["artifact_id"],
        "archive_filename": archive.name,
        "archive_sha256": archive_info["sha256"],
        "archive_size": archive_info["size"],
        "manifest_sha256": hashlib.sha256(canonical_json_bytes(manifest)).hexdigest(),
    }


def load_inputs(contract_results: Path, artifact: str) -> tuple[dict[str, Any], Path, dict[str, Any]]:
    phase3 = contract_results / "input/phase3"
    manifest_path = phase3 / "input/manifest-schema/manifests" / f"{artifact}.manifest.json"
    manifest = read_json(manifest_path)
    archive_info = read_json(contract_results / "installation-contract.json")["input"]["archives"][artifact]
    matches_archives = list((phase3 / "archives").glob(f"*{artifact}.tar.gz"))
    if len(matches_archives) != 1:
        raise RuntimeError(f"archive selection mismatch for {artifact}")
    archive = matches_archives[0]
    if sha256_file(archive) != archive_info["sha256"] or archive.stat().st_size != archive_info["size"]:
        raise RuntimeError("archive identity mismatch")
    with tarfile.open(archive, "r:gz") as container:
        root = manifest["artifact"]["artifact_id"]
        member = container.getmember(f"{root}/metadata/manifest.json")
        stream = container.extractfile(member)
        if stream is None or stream.read() != manifest_path.read_bytes():
            raise RuntimeError("embedded manifest mismatch")
    return manifest, archive, archive_info


def stage_archive(archive: Path, manifest: dict[str, Any], staging: Path) -> Path:
    payload = staging / "payload"
    payload.mkdir(parents=True)
    root = manifest["artifact"]["artifact_id"]
    expected = {
        f"{root}/{entry['archive_path']}": entry
        for entry in manifest["entries"]
        if entry["entry_class"] == "OWNED_PAYLOAD"
    }
    with tarfile.open(archive, "r:gz") as container:
        members = {member.name: member for member in container.getmembers()}
        for name, entry in expected.items():
            member = members.get(name)
            if member is None:
                raise RuntimeError(f"missing member {name}")
            destination = payload / entry["payload_path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            if entry["type"] == "directory":
                destination.mkdir(exist_ok=True)
                os.chmod(destination, int(entry["mode"], 8))
            elif entry["type"] == "regular":
                source = container.extractfile(member)
                if source is None:
                    raise RuntimeError(f"missing member bytes {name}")
                with destination.open("wb") as output:
                    shutil.copyfileobj(source, output)
                os.chmod(destination, int(entry["mode"], 8))
            elif entry["type"] == "symlink":
                if member.linkname != entry["symlink_target"]:
                    raise RuntimeError(f"staged symlink target mismatch {entry['payload_path']}")
                os.symlink(entry["symlink_target"], destination)
            else:
                raise RuntimeError("unsupported entry type")
            if not matches(destination, record_from_entry(entry, manifest["artifact"]["name"])):
                raise RuntimeError(f"staged payload mismatch {entry['payload_path']}")
    return payload


@contextlib.contextmanager
def installation_lock(root: Path, *, nonblocking: bool = False):
    state = root / ".cpython-android-cli"
    durable_ensure_directory(state, label="installation-state")
    lock_path = state / "lock"
    descriptor = durable_open_lock(lock_path, label="installation-lock")
    try:
        flags = fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblocking else 0)
        try:
            fcntl.flock(descriptor, flags)
        except BlockingIOError as exc:
            raise RuntimeError("installation lock busy") from exc
        yield state
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def persist_journal(transaction: Path, journal: dict[str, Any]) -> None:
    durable_atomic_write(
        transaction / "journal.json",
        canonical_json_bytes(journal),
        mode=0o600,
        label="journal",
    )


class CrashController:
    def __init__(
        self,
        *,
        after_prepared: bool = False,
        after_intents: int | None = None,
        after_mutations: int | None = None,
        after_commit: bool = False,
        persist_each_checkpoint: bool = True,
    ):
        self.after_prepared = after_prepared
        self.after_intents = after_intents
        self.after_mutations = after_mutations
        self.after_commit = after_commit
        self.persist_each_checkpoint = persist_each_checkpoint
        self.recorded_intents = 0
        self.applied_mutations = 0

    def crash_prepared(self) -> None:
        if self.after_prepared:
            os._exit(90)

    def intent_recorded(self) -> None:
        self.recorded_intents += 1
        if self.after_intents is not None and self.recorded_intents >= self.after_intents:
            os._exit(93)

    def mutation_applied(self) -> None:
        self.applied_mutations += 1
        if self.after_mutations is not None and self.applied_mutations >= self.after_mutations:
            os._exit(91)

    def crash_committed(self) -> None:
        if self.after_commit:
            os._exit(92)


def add_intent(
    transaction: Path,
    journal: dict[str, Any],
    record: dict[str, Any],
    crash: CrashController,
) -> int:
    item = dict(record)
    item["status"] = "INTENT"
    journal["mutations"].append(item)
    if crash.persist_each_checkpoint:
        persist_journal(transaction, journal)
    crash.intent_recorded()
    return len(journal["mutations"]) - 1


def mark_applied(transaction: Path, journal: dict[str, Any], index: int, crash: CrashController) -> None:
    journal["mutations"][index]["status"] = "APPLIED"
    if crash.persist_each_checkpoint:
        persist_journal(transaction, journal)
    crash.mutation_applied()


def save_prior_registry(transaction: Path, registry_path: Path) -> bool:
    backup = transaction / "backup/prior-registry.json"
    if registry_path.exists():
        durable_copy_file(registry_path, backup, mode=0o600, label="prior-registry-backup")
        return True
    return False
