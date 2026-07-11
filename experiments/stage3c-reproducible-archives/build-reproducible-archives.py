#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import shutil
import stat
import tarfile
import tempfile
from pathlib import Path
from typing import Any, BinaryIO

from archive_serialization_contract import (
    ARTIFACTS,
    ENVELOPE_DIRECTORY_MODE,
    EXPECTED_CANONICAL_FINGERPRINT,
    EXPECTED_MANIFEST_HASHES,
    EXPECTED_MANIFEST_INDEX,
    EXPECTED_PRODUCT_LOCK,
    EXPECTED_RUNTIME_FINGERPRINT,
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


def tar_info(name: str, mode: int, entry_type: bytes, size: int = 0) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.mode = mode
    info.uid = NORMALIZED_UID
    info.gid = NORMALIZED_GID
    info.uname = ""
    info.gname = ""
    info.mtime = NORMALIZED_MTIME
    info.type = entry_type
    info.size = size
    info.pax_headers = {}
    return info


def add_directory(archive: tarfile.TarFile, name: str, mode: int) -> None:
    archive.addfile(tar_info(name, mode, tarfile.DIRTYPE))


def add_bytes(archive: tarfile.TarFile, name: str, data: bytes, mode: int) -> None:
    archive.addfile(
        tar_info(name, mode, tarfile.REGTYPE, len(data)),
        io.BytesIO(data),
    )


def source_for_artifact(name: str, canonical: Path, runtime: Path) -> Path:
    return runtime if name == "runtime-base" else canonical


def validate_source_entry(
    entry: dict[str, Any],
    artifact: str,
    canonical: Path,
    runtime: Path,
) -> tuple[bool, str | None]:
    source_root = source_for_artifact(artifact, canonical, runtime)
    if entry["entry_class"] == "STRUCTURAL_PARENT":
        source_root = canonical
    path = source_root / entry["payload_path"]
    expected_mode = parse_mode(entry["mode"])
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return False, f"missing source path: {path}"
    actual_mode = stat.S_IMODE(observed.st_mode)
    if actual_mode != expected_mode:
        return False, f"mode mismatch: {path}: {actual_mode:04o} != {expected_mode:04o}"
    if entry["type"] == "regular":
        if not stat.S_ISREG(observed.st_mode):
            return False, f"not a regular file: {path}"
        if observed.st_size != entry["size"]:
            return False, f"size mismatch: {path}"
        if sha256_file(path) != entry["sha256"]:
            return False, f"sha256 mismatch: {path}"
    elif entry["type"] == "directory":
        if not stat.S_ISDIR(observed.st_mode):
            return False, f"not a directory: {path}"
    elif entry["type"] == "symlink":
        if not stat.S_ISLNK(observed.st_mode):
            return False, f"not a symlink: {path}"
        if os.readlink(path) != entry["symlink_target"]:
            return False, f"symlink mismatch: {path}"
    else:
        return False, f"unsupported entry type: {entry['type']}"
    return True, None


def add_payload_entry(
    archive: tarfile.TarFile,
    entry: dict[str, Any],
    artifact: str,
    artifact_id: str,
    canonical: Path,
    runtime: Path,
) -> None:
    member_name = payload_member_name(artifact_id, entry["archive_path"])
    mode = parse_mode(entry["mode"])
    source_root = source_for_artifact(artifact, canonical, runtime)
    if entry["entry_class"] == "STRUCTURAL_PARENT":
        source_root = canonical
    source = source_root / entry["payload_path"]
    if entry["type"] == "directory":
        add_directory(archive, member_name, mode)
    elif entry["type"] == "regular":
        info = tar_info(member_name, mode, tarfile.REGTYPE, entry["size"])
        with source.open("rb") as stream:
            archive.addfile(info, stream)
    elif entry["type"] == "symlink":
        info = tar_info(member_name, mode, tarfile.SYMTYPE)
        info.linkname = entry["symlink_target"]
        archive.addfile(info)
    else:
        raise ValueError(f"unsupported entry type: {entry['type']}")


def build_archive(
    output: Path,
    artifact: str,
    manifest_path: Path,
    manifest: dict[str, Any],
    manifest_index_path: Path,
    product_lock_path: Path,
    license_path: Path,
    canonical: Path,
    runtime: Path,
) -> dict[str, Any]:
    artifact_id = manifest["artifact"]["artifact_id"]
    manifest_bytes = manifest_path.read_bytes()
    index_bytes = manifest_index_path.read_bytes()
    lock_bytes = product_lock_path.read_bytes()
    license_bytes = license_path.read_bytes()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as raw:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            compresslevel=GZIP_LEVEL,
            fileobj=raw,
            mtime=NORMALIZED_MTIME,
        ) as compressed:
            with tarfile.open(
                fileobj=compressed,
                mode="w",
                format=tarfile.PAX_FORMAT,
            ) as archive:
                root, metadata, licenses, payload, *metadata_files = envelope_members(
                    artifact_id
                )
                add_directory(archive, root, ENVELOPE_DIRECTORY_MODE)
                add_directory(archive, metadata, ENVELOPE_DIRECTORY_MODE)
                add_directory(archive, licenses, ENVELOPE_DIRECTORY_MODE)
                add_directory(archive, payload, ENVELOPE_DIRECTORY_MODE)
                add_bytes(archive, metadata_files[0], manifest_bytes, METADATA_FILE_MODE)
                add_bytes(archive, metadata_files[1], index_bytes, METADATA_FILE_MODE)
                add_bytes(archive, metadata_files[2], lock_bytes, METADATA_FILE_MODE)
                add_bytes(archive, metadata_files[3], license_bytes, METADATA_FILE_MODE)
                for entry in manifest["entries"]:
                    add_payload_entry(
                        archive,
                        entry,
                        artifact,
                        artifact_id,
                        canonical,
                        runtime,
                    )
    with tarfile.open(output, "r:gz") as archive:
        member_count = len(archive.getmembers())
    return {
        "artifact": artifact,
        "artifact_id": artifact_id,
        "filename": output.name,
        "manifest_sha256": sha256_file(manifest_path),
        "member_count": member_count,
        "sha256": sha256_file(output),
        "size": output.stat().st_size,
    }


def build_set(
    output_dir: Path,
    manifests: dict[str, dict[str, Any]],
    manifest_paths: dict[str, Path],
    manifest_index_path: Path,
    product_lock_path: Path,
    license_path: Path,
    canonical: Path,
    runtime: Path,
) -> dict[str, Any]:
    items = []
    for artifact in ARTIFACTS:
        destination = output_dir / archive_filename(manifests[artifact])
        items.append(
            build_archive(
                destination,
                artifact,
                manifest_paths[artifact],
                manifests[artifact],
                manifest_index_path,
                product_lock_path,
                license_path,
                canonical,
                runtime,
            )
        )
    return {
        "schema_version": 1,
        "archive_format": "pax-tar+gzip",
        "gzip_level": GZIP_LEVEL,
        "normalized_mtime": NORMALIZED_MTIME,
        "artifacts": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-results", required=True, type=Path)
    parser.add_argument("--canonical-prefix", required=True, type=Path)
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    manifest_results = args.manifest_results.resolve()
    canonical = args.canonical_prefix.resolve()
    runtime = args.runtime_prefix.resolve()
    output = args.output_dir.resolve()
    archives_dir = output / "archives"
    manifest_index_path = manifest_results / "manifest-index.json"
    product_lock_path = manifest_results / "input/product-lock.json"
    generation = read_json(manifest_results / "generation.json")
    verification = read_json(manifest_results / "verification.json")
    workflow = read_json(manifest_results / "workflow-status.json")
    index = read_json(manifest_index_path)
    canonical_before = read_json(manifest_results / "canonical-before.json")
    canonical_after = read_json(manifest_results / "canonical-after.json")
    runtime_before = read_json(manifest_results / "runtime-before.json")
    runtime_after = read_json(manifest_results / "runtime-after.json")
    manifest_paths = {
        name: manifest_results / "manifests" / f"{name}.manifest.json"
        for name in ARTIFACTS
    }
    manifests = {name: read_json(path) for name, path in manifest_paths.items()}
    license_path = canonical / LICENSE_PATH

    source_errors: list[str] = []
    for artifact in ARTIFACTS:
        for entry in manifests[artifact]["entries"]:
            passed, error = validate_source_entry(
                entry, artifact, canonical, runtime
            )
            if not passed and error:
                source_errors.append(error)

    workflow_codes = workflow.get("returncodes", {})
    checks = {
        "generation_pass_42": generation.get("pass") is True
        and generation.get("check_count") == 42
        and generation.get("failed_checks") == [],
        "verification_pass_48": verification.get("pass") is True
        and verification.get("check_count") == 48
        and verification.get("failed_checks") == []
        and verification.get("missing_outputs") == []
        and verification.get("parse_errors") == {},
        "manifest_workflow_pass": workflow.get("pass") is True,
        "manifest_workflow_returncodes_zero": bool(workflow_codes)
        and all(value == 0 for value in workflow_codes.values()),
        "manifest_index_hash_exact": sha256_file(manifest_index_path)
        == EXPECTED_MANIFEST_INDEX,
        "product_lock_hash_exact": sha256_file(product_lock_path)
        == EXPECTED_PRODUCT_LOCK,
        "manifest_hashes_exact": {
            name: sha256_file(path) for name, path in manifest_paths.items()
        }
        == EXPECTED_MANIFEST_HASHES,
        "manifest_artifact_set_exact": set(manifests) == set(ARTIFACTS),
        "manifest_index_artifact_set_exact": {
            item.get("artifact") for item in index.get("artifacts", [])
        }
        == set(ARTIFACTS),
        "canonical_manifest_input_unchanged": canonical_before.get("fingerprint")
        == canonical_after.get("fingerprint")
        == EXPECTED_CANONICAL_FINGERPRINT,
        "runtime_manifest_input_unchanged": runtime_before.get("fingerprint")
        == runtime_after.get("fingerprint")
        == EXPECTED_RUNTIME_FINGERPRINT,
        "canonical_prefix_exists": canonical.is_dir(),
        "runtime_prefix_exists": runtime.is_dir(),
        "license_source_exists": license_path.is_file(),
        "license_hash_matches_all_manifests": all(
            sha256_file(license_path) == manifests[name]["license"]["sha256"]
            for name in ARTIFACTS
        ),
        "license_size_matches_all_manifests": all(
            license_path.stat().st_size == manifests[name]["license"]["size"]
            for name in ARTIFACTS
        ),
        "all_manifest_archive_paths_safe": all(
            safe_relative(entry.get("archive_path"))
            for manifest in manifests.values()
            for entry in manifest["entries"]
        ),
        "all_manifest_payload_paths_safe": all(
            safe_relative(entry.get("payload_path"))
            for manifest in manifests.values()
            for entry in manifest["entries"]
        ),
        "source_entries_match_manifests": not source_errors,
    }

    output.mkdir(parents=True, exist_ok=True)
    build_a_dir = archives_dir
    temp_b = Path(tempfile.mkdtemp(prefix="stage3c-archive-build-b-"))
    try:
        build_a = build_set(
            build_a_dir,
            manifests,
            manifest_paths,
            manifest_index_path,
            product_lock_path,
            license_path,
            canonical,
            runtime,
        )
        build_b = build_set(
            temp_b,
            manifests,
            manifest_paths,
            manifest_index_path,
            product_lock_path,
            license_path,
            canonical,
            runtime,
        )
    finally:
        pass

    (output / "build-a-index.json").write_bytes(canonical_json_bytes(build_a))
    (output / "build-b-index.json").write_bytes(canonical_json_bytes(build_b))
    a_by_name = {item["artifact"]: item for item in build_a["artifacts"]}
    b_by_name = {item["artifact"]: item for item in build_b["artifacts"]}
    checks.update(
        {
            "build_a_artifact_set_exact": set(a_by_name) == set(ARTIFACTS),
            "build_b_artifact_set_exact": set(b_by_name) == set(ARTIFACTS),
            "build_a_archives_exist": all(
                (archives_dir / a_by_name[name]["filename"]).is_file()
                for name in ARTIFACTS
            ),
            "build_a_manifest_hashes_exact": all(
                a_by_name[name]["manifest_sha256"]
                == EXPECTED_MANIFEST_HASHES[name]
                for name in ARTIFACTS
            ),
            "build_b_manifest_hashes_exact": all(
                b_by_name[name]["manifest_sha256"]
                == EXPECTED_MANIFEST_HASHES[name]
                for name in ARTIFACTS
            ),
            "build_a_b_sha256_identical": all(
                a_by_name[name]["sha256"] == b_by_name[name]["sha256"]
                for name in ARTIFACTS
            ),
            "build_a_b_size_identical": all(
                a_by_name[name]["size"] == b_by_name[name]["size"]
                for name in ARTIFACTS
            ),
            "build_a_b_member_count_identical": all(
                a_by_name[name]["member_count"]
                == b_by_name[name]["member_count"]
                for name in ARTIFACTS
            ),
            "archive_filenames_unique": len(
                {a_by_name[name]["filename"] for name in ARTIFACTS}
            )
            == 3,
            "archive_hashes_unique": len(
                {a_by_name[name]["sha256"] for name in ARTIFACTS}
            )
            == 3,
            "archive_sizes_positive": all(
                a_by_name[name]["size"] > 0 for name in ARTIFACTS
            ),
            "archive_member_counts_exact": all(
                a_by_name[name]["member_count"]
                == 8 + len(manifests[name]["entries"])
                for name in ARTIFACTS
            ),
        }
    )
    shutil.rmtree(temp_b)

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "source_errors": source_errors,
        "build_a": build_a,
        "build_b": build_b,
        "claim_boundary": {
            "proved": (
                "The accepted manifests serialize twice to byte-identical normalized "
                "pax tar.gz archives on the target runtime."
            ),
            "not_proved": (
                "Archive members and safe extraction match the manifests until the "
                "independent archive verifier passes."
            ),
        },
    }
    (output / "reproducibility.json").write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(
        "STAGE3C_PHASE3_REPRODUCIBLE_ARCHIVE_BUILD="
        + ("PASS" if result["pass"] else "FAIL")
    )
    if args.require_pass and not result["pass"]:
        return 31
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
