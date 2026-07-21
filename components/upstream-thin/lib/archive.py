#!/usr/bin/env python3
"""Safe extraction and deterministic archive primitives for upstream-thin."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import posixpath
import shutil
import stat
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_member_name(name: str) -> str:
    if not name or name.startswith("/") or "\\" in name or "\x00" in name:
        raise ValueError(f"unsafe archive path: {name!r}")
    normalized = posixpath.normpath(name)
    if normalized in {".", ".."} or normalized.startswith("../"):
        raise ValueError(f"unsafe archive path: {name!r}")
    if any(part in {"", ".", ".."} for part in PurePosixPath(normalized).parts):
        raise ValueError(f"unsafe archive component: {name!r}")
    return normalized


def safe_link_target(member: str, target: str) -> bool:
    if not target or target.startswith("/") or "\\" in target or "\x00" in target:
        return False
    resolved = list(PurePosixPath(member).parent.parts)
    root = PurePosixPath(member).parts[0]
    for part in PurePosixPath(target).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not resolved:
                return False
            resolved.pop()
        else:
            resolved.append(part)
    return bool(resolved) and resolved[0] == root


def safe_extract_tar(archive: Path, destination: Path, mode: str = "r:*") -> list[dict[str, Any]]:
    destination.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    names: set[str] = set()
    with tarfile.open(archive, mode) as tf:
        members: list[tuple[tarfile.TarInfo, str]] = []
        for member in tf.getmembers():
            name = normalize_member_name(member.name)
            if name in names:
                raise ValueError(f"duplicate archive member: {name}")
            names.add(name)
            if member.islnk() or member.isdev() or member.isfifo():
                raise ValueError(f"forbidden archive member type: {name}")
            if not (member.isdir() or member.isfile() or member.issym()):
                raise ValueError(f"unsupported archive member type: {name}")
            if member.issym() and not safe_link_target(name, member.linkname):
                raise ValueError(f"unsafe symlink: {name} -> {member.linkname}")
            members.append((member, name))
        for member, name in members:
            target = destination / name
            permission = stat.S_IMODE(member.mode)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                os.chmod(target, permission)
                kind, digest = "directory", None
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                source = tf.extractfile(member)
                if source is None:
                    raise ValueError(f"cannot read archive member: {name}")
                with target.open("wb") as output:
                    shutil.copyfileobj(source, output)
                os.chmod(target, permission)
                kind, digest = "file", sha256_file(target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(member.linkname, target)
                kind, digest = "symlink", None
            rows.append({
                "path": name,
                "type": kind,
                "mode": f"{permission:04o}",
                "size": member.size,
                "sha256": digest,
                "linkname": member.linkname if member.issym() else None,
            })
    return rows


def copy_entry(source: Path, target: Path) -> None:
    metadata = source.lstat()
    permission = stat.S_IMODE(metadata.st_mode)
    if stat.S_ISDIR(metadata.st_mode):
        target.mkdir(parents=True, exist_ok=True)
        for child in sorted(source.iterdir(), key=lambda item: item.name):
            copy_entry(child, target / child.name)
        os.chmod(target, permission)
    elif stat.S_ISREG(metadata.st_mode):
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target, follow_symlinks=False)
        os.chmod(target, permission)
    elif stat.S_ISLNK(metadata.st_mode):
        linkname = os.readlink(source)
        if not safe_link_target("python/" + target.name, linkname):
            # The final archive walk performs the authoritative root-aware check.
            if linkname.startswith("/"):
                raise ValueError(f"absolute symlink forbidden: {source} -> {linkname}")
        target.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(linkname, target)
    else:
        raise ValueError(f"unsupported filesystem entry: {source}")


def copy_tree_contents(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for child in sorted(source.iterdir(), key=lambda item: item.name):
        copy_entry(child, target / child.name)
    os.chmod(target, stat.S_IMODE(source.lstat().st_mode))


def tree_manifest(root: Path, *, exclude: Iterable[str] = ()) -> list[dict[str, Any]]:
    excluded = set(exclude)
    rows: list[dict[str, Any]] = []
    for path in sorted([root, *root.rglob("*")], key=lambda item: item.relative_to(root.parent).as_posix()):
        rel = path.relative_to(root.parent).as_posix()
        if rel in excluded:
            continue
        metadata = path.lstat()
        permission = stat.S_IMODE(metadata.st_mode)
        if stat.S_ISDIR(metadata.st_mode):
            kind, size, digest, linkname = "directory", 0, None, None
        elif stat.S_ISREG(metadata.st_mode):
            kind, size, digest, linkname = "file", metadata.st_size, sha256_file(path), None
        elif stat.S_ISLNK(metadata.st_mode):
            linkname = os.readlink(path)
            if not safe_link_target(rel, linkname):
                raise ValueError(f"unsafe symlink in tree: {rel} -> {linkname}")
            kind, size, digest = "symlink", 0, None
        else:
            raise ValueError(f"unsupported tree entry: {path}")
        rows.append({"path": rel, "type": kind, "mode": f"{permission:04o}", "size": size, "sha256": digest, "linkname": linkname})
    paths = [row["path"] for row in rows]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate tree member")
    return rows


def _tar_info(row: dict[str, Any]) -> tarfile.TarInfo:
    info = tarfile.TarInfo(row["path"])
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mtime = 0
    info.mode = int(row["mode"], 8)
    if row["type"] == "directory":
        info.type = tarfile.DIRTYPE
        info.size = 0
    elif row["type"] == "symlink":
        info.type = tarfile.SYMTYPE
        info.linkname = row["linkname"]
        info.size = 0
    else:
        info.type = tarfile.REGTYPE
        info.size = row["size"]
    return info


def write_uncompressed_tar(tree_root: Path, output: Path, rows: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows = rows or tree_manifest(tree_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w", format=tarfile.PAX_FORMAT) as tf:
        for row in rows:
            info = _tar_info(row)
            source = tree_root.parent / row["path"]
            if row["type"] == "file":
                with source.open("rb") as stream:
                    tf.addfile(info, stream)
            else:
                tf.addfile(info)
    return rows


def write_tar_zst(tree_root: Path, output: Path, zstd: str = "zstd") -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="upstream-thin-tar-") as tmp:
        tar_path = Path(tmp) / "artifact.tar"
        rows = write_uncompressed_tar(tree_root, tar_path)
        proc = subprocess.run([zstd, "-q", "-19", "-T1", "-f", str(tar_path), "-o", str(output)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            raise RuntimeError(f"zstd failed: {proc.stderr.strip()}")
    return rows


def write_tar_gz(tree_root: Path, output: Path) -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="upstream-thin-tar-") as tmp:
        tar_path = Path(tmp) / "artifact.tar"
        rows = write_uncompressed_tar(tree_root, tar_path)
        with tar_path.open("rb") as source, output.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as compressed:
                shutil.copyfileobj(source, compressed)
    return rows
