#!/usr/bin/env python3
"""Acquire and materialize the frozen Termux-native CPython 3.14.6 producer."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"top-level JSON is not an object: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(value: str) -> bool:
    if not value or value.startswith("/") or "\\" in value or "\x00" in value:
        return False
    return all(part not in {"", ".", ".."} for part in PurePosixPath(value).parts)


def safe_symlink(member_name: str, target: str, artifact_root: str) -> bool:
    if not target or target.startswith("/") or "\\" in target or "\x00" in target:
        return False
    resolved = list(PurePosixPath(member_name).parent.parts)
    for part in PurePosixPath(target).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not resolved:
                return False
            resolved.pop()
        else:
            resolved.append(part)
    return bool(resolved) and resolved[0] == artifact_root


def ensure_exact(path: Path, row: dict[str, Any]) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"authority file is missing: {path}")
    observed_size = path.stat().st_size
    observed_sha = sha256_file(path)
    if observed_size != row["size"] or observed_sha != row["sha256"]:
        raise RuntimeError(
            f"authority file identity mismatch: {path}: "
            f"size {observed_size}/{row['size']} sha256 {observed_sha}/{row['sha256']}"
        )


def acquire(binding: dict[str, Any], authority_root: Path, no_acquire: bool) -> dict[str, Any]:
    authority = binding["authority"]
    remote = authority["remote"].rstrip("/")
    index_rel = authority["index"]["path"]
    index_row = authority["index"]
    required = [index_rel, *sorted(authority["files"])]
    authority_root.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []

    def copy_one(rel: str) -> None:
        destination = authority_root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            ["rclone", "copyto", f"{remote}/{rel}", str(destination)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"rclone acquisition failed for {rel}: {proc.stderr.strip()}")
        copied.append(rel)

    if not no_acquire:
        index_path = authority_root / index_rel
        if not index_path.is_file() or index_path.stat().st_size != index_row["size"] or sha256_file(index_path) != index_row["sha256"]:
            copy_one(index_rel)
        ensure_exact(index_path, index_row)
        for rel, row in sorted(authority["files"].items()):
            path = authority_root / rel
            if not path.is_file() or path.stat().st_size != row["size"] or sha256_file(path) != row["sha256"]:
                copy_one(rel)
    index_path = authority_root / index_rel
    ensure_exact(index_path, index_row)
    index = read_json(index_path)
    if index.get("schema_version") != 1 or index.get("authority_kind") != authority["kind"] or index.get("status") != "frozen-pass":
        raise RuntimeError("authority index identity fields are invalid")
    indexed_files = index.get("files")
    if indexed_files != authority["files"]:
        raise RuntimeError("authority index file set does not match the binding contract")
    for rel, row in sorted(authority["files"].items()):
        ensure_exact(authority_root / rel, row)
    return {"copied": copied, "file_count": len(required), "index": index_rel}


def read_manifest(path: Path, artifact_name: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest = read_json(path)
    artifact = manifest.get("artifact", {})
    if manifest.get("schema_version") != 1 or manifest.get("manifest_kind") not in {"artifact-manifest", "cpython-android-cli-artifact-manifest"}:
        raise RuntimeError(f"invalid artifact manifest: {path}")
    if artifact.get("name") != artifact_name:
        raise RuntimeError(f"manifest artifact mismatch: {path}")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise RuntimeError(f"manifest has no entries: {path}")
    by_archive: dict[str, dict[str, Any]] = {}
    for row in entries:
        if not isinstance(row, dict):
            raise RuntimeError(f"manifest entry is not an object: {path}")
        archive_path = row.get("archive_path")
        payload_path = row.get("payload_path")
        if not isinstance(archive_path, str) or not safe_relative(archive_path):
            raise RuntimeError(f"unsafe archive path in manifest: {archive_path!r}")
        if not isinstance(payload_path, str) or not safe_relative(payload_path):
            raise RuntimeError(f"unsafe payload path in manifest: {payload_path!r}")
        if archive_path != f"payload/{payload_path}":
            raise RuntimeError(f"manifest payload/archive path mismatch: {archive_path}")
        if archive_path in by_archive:
            raise RuntimeError(f"duplicate manifest entry: {archive_path}")
        by_archive[archive_path] = row
    return manifest, by_archive


def member_kind(member: tarfile.TarInfo) -> str:
    if member.isdir():
        return "directory"
    if member.isreg():
        return "regular"
    if member.issym():
        return "symlink"
    if member.islnk():
        return "hardlink"
    return "special"


def verify_regular(stream: BinaryIO, row: dict[str, Any], member_name: str) -> bytes:
    data = stream.read()
    observed = hashlib.sha256(data).hexdigest()
    if len(data) != row.get("size") or observed != row.get("sha256"):
        raise RuntimeError(f"regular-file identity mismatch in artifact: {member_name}")
    return data


def apply_owned(prefix: Path, row: dict[str, Any], data: bytes | None, owned: set[str]) -> None:
    rel = row["payload_path"]
    if rel in owned:
        raise RuntimeError(f"duplicate selected ownership: {rel}")
    destination = prefix / rel
    kind = row["type"]
    mode = int(row["mode"], 8)
    if destination.exists() or destination.is_symlink():
        raise RuntimeError(f"selected artifact collision: {rel}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if kind == "directory":
        destination.mkdir()
        os.chmod(destination, mode, follow_symlinks=False)
    elif kind == "regular":
        if data is None:
            raise RuntimeError(f"missing data for regular payload: {rel}")
        destination.write_bytes(data)
        os.chmod(destination, mode, follow_symlinks=False)
    elif kind == "symlink":
        target = row.get("symlink_target")
        if not isinstance(target, str):
            raise RuntimeError(f"missing symlink target: {rel}")
        os.symlink(target, destination)
    else:
        raise RuntimeError(f"unsupported manifest type: {kind}")
    owned.add(rel)


def materialize_artifact(
    archive: Path,
    manifest_path: Path,
    artifact_name: str,
    prefix: Path,
    owned: set[str],
) -> dict[str, Any]:
    manifest, expected = read_manifest(manifest_path, artifact_name)
    artifact_id = manifest["artifact"]["artifact_id"]
    seen_payload: set[str] = set()
    process = subprocess.Popen(["zstd", "-q", "-dc", str(archive)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.stdout is None or process.stderr is None:
        raise RuntimeError("failed to open zstd stream")
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|") as tar:
            seen_members: set[str] = set()
            for member in tar:
                name = member.name.rstrip("/")
                if not safe_relative(name) or name in seen_members:
                    raise RuntimeError(f"unsafe or duplicate archive member: {member.name!r}")
                seen_members.add(name)
                parts = PurePosixPath(name).parts
                if not parts or parts[0] != artifact_id:
                    raise RuntimeError(f"archive root mismatch: {name}")
                kind = member_kind(member)
                if kind in {"hardlink", "special"}:
                    raise RuntimeError(f"forbidden archive member type: {name}: {kind}")
                if kind == "symlink" and not safe_symlink(name, member.linkname, artifact_id):
                    raise RuntimeError(f"unsafe archive symlink: {name} -> {member.linkname}")
                if len(parts) == 1:
                    if kind != "directory":
                        raise RuntimeError("artifact root is not a directory")
                    continue
                section = parts[1]
                if section not in {"metadata", "payload"}:
                    raise RuntimeError(f"unexpected artifact section: {name}")
                if section == "metadata":
                    continue
                if len(parts) == 2:
                    if kind != "directory":
                        raise RuntimeError("payload root is not a directory")
                    continue
                archive_rel = PurePosixPath(*parts[1:]).as_posix()
                row = expected.get(archive_rel)
                if row is None:
                    raise RuntimeError(f"payload archive member is absent from manifest: {archive_rel}")
                if kind != row.get("type") or f"{member.mode & 0o7777:04o}" != row.get("mode"):
                    raise RuntimeError(f"payload type/mode mismatch: {archive_rel}")
                if kind == "symlink" and member.linkname != row.get("symlink_target"):
                    raise RuntimeError(f"payload symlink target mismatch: {archive_rel}")
                data: bytes | None = None
                if kind == "regular":
                    stream = tar.extractfile(member)
                    if stream is None:
                        raise RuntimeError(f"cannot read archive member: {archive_rel}")
                    data = verify_regular(stream, row, archive_rel)
                entry_class = row.get("entry_class")
                if entry_class == "STRUCTURAL_PARENT":
                    destination = prefix / row["payload_path"]
                    if kind != "directory" or not destination.is_dir() or destination.is_symlink():
                        raise RuntimeError(f"structural parent is not provided by an earlier artifact: {row['payload_path']}")
                    if f"{stat.S_IMODE(destination.stat().st_mode):04o}" != row.get("mode"):
                        raise RuntimeError(f"structural parent mode mismatch: {row['payload_path']}")
                elif entry_class == "OWNED_PAYLOAD":
                    apply_owned(prefix, row, data, owned)
                else:
                    raise RuntimeError(f"unknown manifest entry class: {entry_class!r}")
                seen_payload.add(archive_rel)
        stderr = process.stderr.read().decode("utf-8", errors="replace")
        returncode = process.wait()
        if returncode != 0:
            raise RuntimeError(f"zstd failed for {archive}: {stderr.strip()}")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    if seen_payload != set(expected):
        missing = sorted(set(expected) - seen_payload)
        extra = sorted(seen_payload - set(expected))
        raise RuntimeError(f"artifact/manifest coverage mismatch: missing={missing[:5]} extra={extra[:5]}")
    return {
        "artifact": artifact_name,
        "manifest_entries": len(expected),
        "owned_entries": sum(row.get("entry_class") == "OWNED_PAYLOAD" for row in expected.values()),
        "structural_entries": sum(row.get("entry_class") == "STRUCTURAL_PARENT" for row in expected.values()),
    }


def observed_paths(prefix: Path) -> set[str]:
    return {
        path.relative_to(prefix).as_posix()
        for path in prefix.rglob("*")
    }


def verify_prefix(prefix: Path, manifests: list[dict[str, Any]], owned: set[str]) -> dict[str, Any]:
    expected_owned: dict[str, dict[str, Any]] = {}
    structural: list[dict[str, Any]] = []
    for manifest in manifests:
        for row in manifest["entries"]:
            if row["entry_class"] == "OWNED_PAYLOAD":
                rel = row["payload_path"]
                if rel in expected_owned:
                    raise RuntimeError(f"duplicate manifest ownership: {rel}")
                expected_owned[rel] = row
            else:
                structural.append(row)
    if set(expected_owned) != owned:
        raise RuntimeError("materialized ownership set does not match selected manifests")
    actual = observed_paths(prefix)
    if actual != set(expected_owned):
        missing = sorted(set(expected_owned) - actual)
        extra = sorted(actual - set(expected_owned))
        raise RuntimeError(f"materialized prefix path mismatch: missing={missing[:5]} extra={extra[:5]}")
    for rel, row in expected_owned.items():
        path = prefix / rel
        mode = f"{stat.S_IMODE(path.lstat().st_mode):04o}"
        if mode != row["mode"]:
            raise RuntimeError(f"materialized mode mismatch: {rel}")
        if row["type"] == "directory":
            if not path.is_dir() or path.is_symlink():
                raise RuntimeError(f"materialized directory mismatch: {rel}")
        elif row["type"] == "regular":
            if not path.is_file() or path.is_symlink() or path.stat().st_size != row["size"] or sha256_file(path) != row["sha256"]:
                raise RuntimeError(f"materialized regular identity mismatch: {rel}")
        elif row["type"] == "symlink":
            if not path.is_symlink() or os.readlink(path) != row["symlink_target"]:
                raise RuntimeError(f"materialized symlink mismatch: {rel}")
    for row in structural:
        path = prefix / row["payload_path"]
        if not path.is_dir() or path.is_symlink():
            raise RuntimeError(f"structural parent missing after composition: {row['payload_path']}")
    return {
        "owned_path_count": len(expected_owned),
        "structural_reference_count": len(structural),
        "launcher_sha256": sha256_file(prefix / "bin/python3.14"),
    }


def atomic_replace_directory(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup = destination.with_name(destination.name + ".previous")
    if backup.exists() or backup.is_symlink():
        if backup.is_dir() and not backup.is_symlink():
            shutil.rmtree(backup)
        else:
            backup.unlink()
    if destination.exists() or destination.is_symlink():
        os.replace(destination, backup)
    try:
        os.replace(source, destination)
    except Exception:
        if backup.exists() or backup.is_symlink():
            os.replace(backup, destination)
        raise
    if backup.exists() or backup.is_symlink():
        if backup.is_dir() and not backup.is_symlink():
            shutil.rmtree(backup)
        else:
            backup.unlink()


def project_value(name: str, default: str) -> str:
    return os.environ.get(name, default)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--authority-root", type=Path)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--out-root", type=Path)
    parser.add_argument("--no-acquire", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    binding_path = args.binding.resolve()
    binding = read_json(binding_path)
    if binding.get("schema_version") != 1 or binding.get("binding_version") != 1:
        raise RuntimeError("unsupported producer binding contract")
    if binding.get("status") != "frozen-authority-bound":
        raise RuntimeError("producer binding is not frozen")

    authority_root = (args.authority_root or Path(os.environ.get(
        "HW_T_CPYTHON3146_AUTHORITY_ROOT",
        str(Path.home() / ".cache/hw-t-authorities/cpython-android-cli/e2p2-termux-native-cpython3146-frozen-product-v1"),
    ))).expanduser().resolve()
    acquisition = acquire(binding, authority_root, args.no_acquire)

    target_id = project_value("TARGET_ID", "aarch64-linux-android24")
    build_profile = project_value("BUILD_PROFILE", "release")
    work_root = (args.work_root or root / binding["materialization"]["work_root"]).resolve()
    out_root = (args.out_root or root / "out" / target_id / build_profile).resolve()

    selected = binding["composition"]["selected_artifacts"]
    manifests: list[dict[str, Any]] = []
    artifact_results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="e2p2-binding-work-", dir=str(work_root.parent if work_root.parent.exists() else root)) as temp_name:
        temp = Path(temp_name)
        staged_work = temp / "work"
        prefix = staged_work / "prefix"
        prefix.mkdir(parents=True)
        owned: set[str] = set()
        for artifact_name in selected:
            spec = binding["artifacts"][artifact_name]
            archive = authority_root / spec["archive"]["path"]
            manifest_path = authority_root / spec["manifest"]["path"]
            manifest = read_json(manifest_path)
            manifests.append(manifest)
            artifact_results.append(materialize_artifact(archive, manifest_path, artifact_name, prefix, owned))
        prefix_verification = verify_prefix(prefix, manifests, owned)
        if prefix_verification["owned_path_count"] != binding["composition"]["expected_owned_paths"]:
            raise RuntimeError("selected prefix owned-path count mismatch")
        if prefix_verification["structural_reference_count"] != binding["composition"]["expected_structural_references"]:
            raise RuntimeError("selected prefix structural-reference count mismatch")
        if prefix_verification["launcher_sha256"] != binding["product"]["launcher_sha256"]:
            raise RuntimeError("selected prefix launcher identity mismatch")

        receipt = {
            "schema_version": 1,
            "receipt_kind": "e2p2-termux-native-cpython3146-producer-binding",
            "status": "passed",
            "binding": {
                "path": str(binding_path.relative_to(root)) if binding_path.is_relative_to(root) else str(binding_path),
                "binding_version": binding["binding_version"],
                "authority_remote": binding["authority"]["remote"],
                "authority_index_sha256": binding["authority"]["index"]["sha256"],
            },
            "composition": {
                "selected_artifacts": selected,
                "preserved_unselected_artifacts": binding["composition"]["preserved_unselected_artifacts"],
                **prefix_verification,
            },
            "artifacts": artifact_results,
            "acquisition": acquisition,
        }
        (staged_work / "producer-binding.json").write_bytes(canonical_json_bytes(receipt))
        atomic_replace_directory(staged_work, work_root)

    with tempfile.TemporaryDirectory(prefix="e2p2-binding-out-", dir=str(out_root.parent if out_root.parent.exists() else root)) as temp_name:
        staged_out = Path(temp_name) / "out"
        artifact_dir = staged_out / "producer-artifacts"
        metadata_dir = staged_out / "metadata"
        bin_dir = staged_out / "bin"
        artifact_dir.mkdir(parents=True)
        metadata_dir.mkdir(parents=True)
        bin_dir.mkdir(parents=True)
        for artifact_name, spec in binding["artifacts"].items():
            shutil.copyfile(authority_root / spec["archive"]["path"], artifact_dir / spec["archive"]["filename"])
        shutil.copyfile(root / binding["repository_product_lock"], metadata_dir / "cpython-product.json")
        shutil.copyfile(work_root / "prefix/bin/python3.14", bin_dir / "python3.14")
        os.chmod(bin_dir / "python3.14", 0o755)
        out_root.mkdir(parents=True, exist_ok=True)
        for name in ("producer-artifacts", "metadata", "bin"):
            atomic_replace_directory(staged_out / name, out_root / name)

    result = {
        "schema_version": 1,
        "operation": "materialize-frozen-producer",
        "pass": True,
        "authority_root": str(authority_root),
        "work_root": str(work_root),
        "out_root": str(out_root),
        "selected_artifacts": selected,
        "owned_path_count": binding["composition"]["expected_owned_paths"],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    print("E2P2_TERMUX_NATIVE_CPYTHON3146_FACADE_MATERIALIZATION=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
