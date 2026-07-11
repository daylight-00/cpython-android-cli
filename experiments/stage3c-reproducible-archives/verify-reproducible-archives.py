#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

from archive_serialization_contract import (
    ARTIFACTS,
    ENVELOPE_DIRECTORY_MODE,
    EXPECTED_MANIFEST_HASHES,
    EXPECTED_MANIFEST_INDEX,
    EXPECTED_PRODUCT_LOCK,
    GZIP_LEVEL,
    LICENSE_PATH,
    METADATA_FILE_MODE,
    NORMALIZED_GID,
    NORMALIZED_MTIME,
    NORMALIZED_UID,
    archive_filename,
    canonical_json_bytes,
    envelope_members,
    parse_mode,
    payload_member_name,
    read_json,
    safe_relative,
    sha256_bytes,
    sha256_file,
)

ALLOWED_PAX_HEADERS = {"path", "linkpath"}


def member_map(members: list[tarfile.TarInfo]) -> dict[str, tarfile.TarInfo]:
    return {member.name: member for member in members}


def expected_member_names(manifest: dict[str, Any]) -> list[str]:
    artifact_id = manifest["artifact"]["artifact_id"]
    return envelope_members(artifact_id) + [
        payload_member_name(artifact_id, entry["archive_path"])
        for entry in manifest["entries"]
    ]


def safe_symlink(member_name: str, target: str, root: str) -> bool:
    if not target or target.startswith("/") or "\\" in target:
        return False
    resolved = PurePosixPath(member_name).parent.joinpath(target)
    normalized: list[str] = []
    for part in resolved.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not normalized:
                return False
            normalized.pop()
        else:
            normalized.append(part)
    return bool(normalized) and normalized[0] == root


def extract_safely(archive_path: Path, destination: Path, expected_root: str) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            if not safe_relative(member.name):
                raise ValueError(f"unsafe archive path: {member.name}")
            if PurePosixPath(member.name).parts[0] != expected_root:
                raise ValueError(f"unexpected archive root: {member.name}")
            target_path = destination.joinpath(*PurePosixPath(member.name).parts)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if member.isdir():
                target_path.mkdir(parents=True, exist_ok=True)
                os.chmod(target_path, member.mode)
            elif member.isreg():
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError(f"missing regular-file data: {member.name}")
                with target_path.open("wb") as output:
                    shutil.copyfileobj(stream, output)
                os.chmod(target_path, member.mode)
            elif member.issym():
                if not safe_symlink(member.name, member.linkname, expected_root):
                    raise ValueError(f"unsafe symlink: {member.name} -> {member.linkname}")
                os.symlink(member.linkname, target_path)
            else:
                raise ValueError(f"unsupported archive entry: {member.name}")


def metadata_expected(
    manifest_path: Path,
    index_path: Path,
    lock_path: Path,
    license_path: Path,
    artifact_id: str,
) -> dict[str, bytes]:
    root = artifact_id
    return {
        f"{root}/metadata/manifest.json": manifest_path.read_bytes(),
        f"{root}/metadata/manifest-index.json": index_path.read_bytes(),
        f"{root}/metadata/product-lock.json": lock_path.read_bytes(),
        f"{root}/metadata/licenses/CPython-LICENSE.txt": license_path.read_bytes(),
    }


def verify_archive(
    archive_path: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    index_path: Path,
    lock_path: Path,
    license_path: Path,
    staging_root: Path,
) -> tuple[dict[str, bool], list[str], dict[str, Any]]:
    artifact = manifest["artifact"]["name"]
    artifact_id = manifest["artifact"]["artifact_id"]
    errors: list[str] = []
    raw_header = archive_path.read_bytes()[:10]
    expected_gzip_header = bytes([0x1F, 0x8B, 8, 0, 0, 0, 0, 0, 2, 255])
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        by_name = member_map(members)
        expected_names = expected_member_names(manifest)
        metadata = metadata_expected(
            manifest_path, index_path, lock_path, license_path, artifact_id
        )
        normalized = all(
            member.uid == NORMALIZED_UID
            and member.gid == NORMALIZED_GID
            and member.uname == ""
            and member.gname == ""
            and int(member.mtime) == NORMALIZED_MTIME
            for member in members
        )
        pax_safe = all(
            set(member.pax_headers) <= ALLOWED_PAX_HEADERS for member in members
        )
        allowed_types = all(
            member.isdir() or member.isreg() or member.issym() for member in members
        )
        paths_safe = all(
            safe_relative(member.name)
            and PurePosixPath(member.name).parts[0] == artifact_id
            for member in members
        )
        hardlinks_zero = all(not member.islnk() for member in members)
        envelope_modes = all(
            by_name[name].isdir()
            and by_name[name].mode == ENVELOPE_DIRECTORY_MODE
            for name in envelope_members(artifact_id)[:4]
            if name in by_name
        )
        metadata_modes = all(
            by_name[name].isreg() and by_name[name].mode == METADATA_FILE_MODE
            for name in metadata
            if name in by_name
        )
        metadata_bytes_exact = True
        for name, expected in metadata.items():
            member = by_name.get(name)
            if member is None:
                metadata_bytes_exact = False
                continue
            stream = archive.extractfile(member)
            observed = stream.read() if stream is not None else b""
            if observed != expected:
                metadata_bytes_exact = False
        payload_headers_exact = True
        payload_bytes_exact = True
        payload_symlinks_exact = True
        for entry in manifest["entries"]:
            name = payload_member_name(artifact_id, entry["archive_path"])
            member = by_name.get(name)
            if member is None:
                payload_headers_exact = False
                continue
            if member.mode != parse_mode(entry["mode"]):
                payload_headers_exact = False
            if entry["type"] == "directory":
                if not member.isdir() or member.size != 0:
                    payload_headers_exact = False
            elif entry["type"] == "regular":
                if not member.isreg() or member.size != entry["size"]:
                    payload_headers_exact = False
                stream = archive.extractfile(member)
                observed = stream.read() if stream is not None else b""
                if len(observed) != entry["size"] or sha256_bytes(observed) != entry["sha256"]:
                    payload_bytes_exact = False
            elif entry["type"] == "symlink":
                if not member.issym() or member.linkname != entry["symlink_target"]:
                    payload_symlinks_exact = False
                if not safe_symlink(member.name, member.linkname, artifact_id):
                    payload_symlinks_exact = False
            else:
                payload_headers_exact = False

    extraction_ok = True
    extracted_metadata_exact = True
    extracted_payload_exact = True
    extracted_symlink_exact = True
    stage = staging_root / artifact
    try:
        extract_safely(archive_path, stage, artifact_id)
        root = stage / artifact_id
        for name, expected in metadata_expected(
            manifest_path, index_path, lock_path, license_path, artifact_id
        ).items():
            relative = PurePosixPath(name).relative_to(artifact_id)
            path = root.joinpath(*relative.parts)
            if not path.is_file() or path.read_bytes() != expected:
                extracted_metadata_exact = False
        for entry in manifest["entries"]:
            path = root / entry["archive_path"]
            if entry["type"] == "directory":
                if not path.is_dir() or path.is_symlink():
                    extracted_payload_exact = False
            elif entry["type"] == "regular":
                if (
                    not path.is_file()
                    or path.is_symlink()
                    or path.stat().st_size != entry["size"]
                    or sha256_file(path) != entry["sha256"]
                ):
                    extracted_payload_exact = False
            elif entry["type"] == "symlink":
                if not path.is_symlink() or os.readlink(path) != entry["symlink_target"]:
                    extracted_symlink_exact = False
    except Exception as exc:  # evidence records the exact extraction failure
        extraction_ok = False
        errors.append(repr(exc))

    checks = {
        f"{artifact}_archive_exists": archive_path.is_file(),
        f"{artifact}_gzip_header_exact": raw_header == expected_gzip_header,
        f"{artifact}_member_order_exact": names == expected_names,
        f"{artifact}_member_count_exact": len(names) == 8 + len(manifest["entries"]),
        f"{artifact}_member_names_unique": len(set(names)) == len(names),
        f"{artifact}_paths_safe": paths_safe,
        f"{artifact}_entry_types_allowed": allowed_types,
        f"{artifact}_hardlinks_zero": hardlinks_zero,
        f"{artifact}_normalized_owner_time": normalized,
        f"{artifact}_pax_headers_allowed": pax_safe,
        f"{artifact}_envelope_modes_exact": envelope_modes,
        f"{artifact}_metadata_modes_exact": metadata_modes,
        f"{artifact}_metadata_bytes_exact": metadata_bytes_exact,
        f"{artifact}_payload_headers_exact": payload_headers_exact,
        f"{artifact}_payload_regular_bytes_exact": payload_bytes_exact,
        f"{artifact}_payload_symlinks_exact": payload_symlinks_exact,
        f"{artifact}_safe_extraction_pass": extraction_ok,
        f"{artifact}_extracted_metadata_exact": extracted_metadata_exact,
        f"{artifact}_extracted_payload_exact": extracted_payload_exact,
        f"{artifact}_extracted_symlinks_exact": extracted_symlink_exact,
    }
    observed = {
        "artifact": artifact,
        "filename": archive_path.name,
        "member_count": len(names),
        "sha256": sha256_file(archive_path),
        "size": archive_path.stat().st_size,
        "gzip_header_hex": raw_header.hex(),
        "pax_header_keys": sorted(
            {key for member in members for key in member.pax_headers}
        ),
    }
    return checks, errors, observed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-results", required=True, type=Path)
    parser.add_argument("--archive-results", required=True, type=Path)
    parser.add_argument("--canonical-prefix", required=True, type=Path)
    parser.add_argument("--staging-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifest_results = args.manifest_results.resolve()
    archive_results = args.archive_results.resolve()
    canonical = args.canonical_prefix.resolve()
    staging = args.staging_dir.resolve()
    reproducibility = read_json(archive_results / "reproducibility.json")
    build_a = read_json(archive_results / "build-a-index.json")
    build_b = read_json(archive_results / "build-b-index.json")
    index_path = manifest_results / "manifest-index.json"
    lock_path = manifest_results / "input/product-lock.json"
    manifest_paths = {
        name: manifest_results / "manifests" / f"{name}.manifest.json"
        for name in ARTIFACTS
    }
    manifests = {name: read_json(path) for name, path in manifest_paths.items()}
    license_path = canonical / LICENSE_PATH
    a_by_name = {item["artifact"]: item for item in build_a["artifacts"]}
    b_by_name = {item["artifact"]: item for item in build_b["artifacts"]}

    checks: dict[str, bool] = {
        "reproducibility_pass_31": reproducibility.get("pass") is True
        and reproducibility.get("check_count") == 31
        and reproducibility.get("failed_checks") == []
        and reproducibility.get("source_errors") == [],
        "manifest_index_hash_exact": sha256_file(index_path)
        == EXPECTED_MANIFEST_INDEX,
        "product_lock_hash_exact": sha256_file(lock_path) == EXPECTED_PRODUCT_LOCK,
        "manifest_hashes_exact": {
            name: sha256_file(path) for name, path in manifest_paths.items()
        }
        == EXPECTED_MANIFEST_HASHES,
        "build_index_artifact_sets_exact": set(a_by_name)
        == set(b_by_name)
        == set(ARTIFACTS),
        "build_a_b_sha256_exact": all(
            a_by_name[name]["sha256"] == b_by_name[name]["sha256"]
            for name in ARTIFACTS
        ),
        "build_a_b_size_exact": all(
            a_by_name[name]["size"] == b_by_name[name]["size"]
            for name in ARTIFACTS
        ),
    }
    errors: dict[str, list[str]] = {}
    observed: dict[str, Any] = {}
    for artifact in ARTIFACTS:
        archive_path = archive_results / "archives" / archive_filename(
            manifests[artifact]
        )
        artifact_checks, artifact_errors, artifact_observed = verify_archive(
            archive_path,
            manifest_paths[artifact],
            manifests[artifact],
            index_path,
            lock_path,
            license_path,
            staging,
        )
        checks.update(artifact_checks)
        errors[artifact] = artifact_errors
        observed[artifact] = artifact_observed
        checks[f"{artifact}_retained_hash_matches_build_index"] = (
            artifact_observed["sha256"] == a_by_name[artifact]["sha256"]
        )
        checks[f"{artifact}_retained_size_matches_build_index"] = (
            artifact_observed["size"] == a_by_name[artifact]["size"]
        )
        checks[f"{artifact}_retained_member_count_matches_build_index"] = (
            artifact_observed["member_count"]
            == a_by_name[artifact]["member_count"]
        )

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "errors": errors,
        "observed": observed,
        "claim_boundary": {
            "proved": (
                "Retained normalized archives exactly match schema-v1 metadata and "
                "payload, and the tested safe staging extraction reproduces them."
            ),
            "not_proved": (
                "Direct installation, collision handling, upgrades, rollback, or uninstall."
            ),
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 32


if __name__ == "__main__":
    raise SystemExit(main())
