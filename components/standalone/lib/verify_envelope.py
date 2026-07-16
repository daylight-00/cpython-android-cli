#!/usr/bin/env python3
"""Independently verify a real or synthetic E2-P1 release envelope."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

SIDECAR_KINDS = ("artifact", "manifest", "provenance", "qualification", "licenses")
FORBIDDEN_TERMUX_IDENTITY = ("/data/data/com.termux", "/data/user/0/com.termux", "com.termux/files/usr")
ARTIFACT_ID_RE = re.compile(r"^cpython-(\d+\.\d+\.\d+)-aarch64-linux-android(\d+)-install_only_stripped$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MODE = re.compile(r"^[0-7]{4}$")
EXCLUDED_PATH_PREFIXES = (
    "python/lib/python3.14/test",
    "python/lib/python3.14/__phello__",
    "python/lib/python3.14/tkinter",
    "python/lib/python3.14/idlelib",
    "python/lib/python3.14/turtledemo",
)
EXCLUDED_PATHS = {"python/lib/python3.14/turtle.py", "python/lib/python3.14/turtle.cfg"}


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path, errors: dict[str, str]) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("top-level value is not an object")
        if raw != canonical_json_bytes(value):
            raise ValueError("JSON bytes are not canonical UTF-8/indent/sort/newline form")
        return value
    except Exception as exc:
        errors[str(path)] = f"{type(exc).__name__}: {exc}"
        return {}


def exact_keys(value: Any, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def safe_relative(path: object) -> bool:
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or "\x00" in path:
        return False
    return all(part not in {"", ".", ".."} for part in PurePosixPath(path).parts)


def safe_symlink_target(member_path: str, target: object) -> bool:
    if not isinstance(target, str) or not target or target.startswith("/") or "\\" in target:
        return False
    resolved = list(PurePosixPath(member_path).parent.parts)
    for part in PurePosixPath(target).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not resolved:
                return False
            resolved.pop()
        else:
            resolved.append(part)
    return bool(resolved) and resolved[0] == "python"


def file_ref_matches(ref: Any, path: Path) -> bool:
    return (
        isinstance(ref, dict)
        and set(ref) == {"filename", "sha256", "size"}
        and ref.get("filename") == path.name
        and ref.get("sha256") == sha256_file(path)
        and ref.get("size") == path.stat().st_size
    )


def verify(root: Path, release_dir: Path) -> dict[str, Any]:
    root = root.resolve()
    release_dir = release_dir.resolve()
    checks: dict[str, bool] = {}
    missing: list[str] = []
    parse_errors: dict[str, str] = {}

    release_path = release_dir / "release-index.json"
    checksums_path = release_dir / "SHA256SUMS"
    for path in (release_path, checksums_path):
        if not path.is_file():
            missing.append(str(path))
    release_index = read_json(release_path, parse_errors) if release_path.is_file() else {}
    checks["release_index_top_keys"] = exact_keys(release_index, {"schema_version", "release", "release_sha256"})
    release = release_index.get("release", {})
    checks["release_identity"] = (
        release_index.get("schema_version") == 1
        and isinstance(release, dict)
        and release.get("format") == "hw-t-standalone-release-v1"
        and release.get("contract_version") == 1
        and release.get("channel") in {"fixture", "prerelease", "stable"}
    )
    checks["release_digest"] = isinstance(release, dict) and release_index.get("release_sha256") == sha256_bytes(canonical_json_bytes(release))
    products = release.get("products", []) if isinstance(release, dict) else []
    row = products[0] if isinstance(products, list) and len(products) == 1 and isinstance(products[0], dict) else {}
    artifact_id = row.get("artifact_id", "")
    match = ARTIFACT_ID_RE.fullmatch(artifact_id) if isinstance(artifact_id, str) else None
    checks["single_product"] = bool(row)
    checks["artifact_id"] = match is not None
    version = match.group(1) if match else ""
    api = int(match.group(2)) if match else -1
    archive_path = release_dir / str(row.get("archive", {}).get("filename", ""))
    sidecar_paths = {kind: release_dir / f"{artifact_id}.{kind}.json" for kind in SIDECAR_KINDS}
    for path in [archive_path, *sidecar_paths.values()]:
        if not path.is_file():
            missing.append(str(path))

    artifact = read_json(sidecar_paths["artifact"], parse_errors) if sidecar_paths["artifact"].is_file() else {}
    manifest = read_json(sidecar_paths["manifest"], parse_errors) if sidecar_paths["manifest"].is_file() else {}
    provenance = read_json(sidecar_paths["provenance"], parse_errors) if sidecar_paths["provenance"].is_file() else {}
    qualification = read_json(sidecar_paths["qualification"], parse_errors) if sidecar_paths["qualification"].is_file() else {}
    licenses = read_json(sidecar_paths["licenses"], parse_errors) if sidecar_paths["licenses"].is_file() else {}

    checks["release_archive_ref"] = archive_path.is_file() and file_ref_matches(row.get("archive"), archive_path)
    metadata_refs = row.get("metadata", {})
    checks["release_sidecar_refs"] = (
        isinstance(metadata_refs, dict)
        and set(metadata_refs) == set(SIDECAR_KINDS)
        and all(path.is_file() and file_ref_matches(metadata_refs.get(kind), path) for kind, path in sidecar_paths.items())
    )
    checks["release_checksums_ref"] = checksums_path.is_file() and file_ref_matches(release.get("checksums"), checksums_path)

    raw_all = "\n".join(json.dumps(item, sort_keys=True) for item in (artifact, manifest, provenance, qualification, licenses, release_index))
    checks["no_termux_binary_identity"] = not any(marker in raw_all for marker in FORBIDDEN_TERMUX_IDENTITY)

    checks["artifact_top_keys"] = exact_keys(artifact, {"schema_version", "metadata_kind", "artifact_id", "distribution", "target", "artifact", "layout", "profiles", "compatibility", "extensions"})
    distribution = artifact.get("distribution", {})
    target = artifact.get("target", {})
    art = artifact.get("artifact", {})
    layout = artifact.get("layout", {})
    profiles = artifact.get("profiles", {})
    compatibility = artifact.get("compatibility", {})
    checks["artifact_identity"] = artifact.get("schema_version") == 1 and artifact.get("metadata_kind") == "hw-t-standalone-artifact" and artifact.get("artifact_id") == artifact_id
    checks["distribution_identity"] = (
        distribution.get("implementation") == "cpython"
        and distribution.get("python_version") == version
        and distribution.get("python_major_minor") == ".".join(version.split(".")[:2])
        and distribution.get("multiarch") == "aarch64-linux-android"
        and distribution.get("soabi") == f"cpython-{''.join(version.split('.')[:2])}-aarch64-linux-android"
    )
    checks["target_identity"] = target == {
        "os": "android",
        "kernel": "linux",
        "libc": "bionic",
        "architecture": "aarch64",
        "target_triple": "aarch64-linux-android",
        "android_abi": "arm64-v8a",
        "android_api_min": api,
        "wheel_platform_tag": f"android_{api}_arm64_v8a",
        "sysconfig_platform": f"android-{api}-arm64_v8a",
    }
    checks["artifact_archive_identity"] = (
        archive_path.is_file()
        and art.get("flavor") == "install_only_stripped"
        and art.get("archive_format") == "pax-tar+zstd"
        and art.get("archive_filename") == archive_path.name
        and art.get("archive_sha256") == sha256_file(archive_path)
        and art.get("archive_size") == archive_path.stat().st_size
        and art.get("payload_classes") == ["runtime", "development"]
        and art.get("excluded_payload_classes") == ["tests", "build", "debug_symbols"]
        and art.get("native_debug") == "stripped"
    )
    python_mm = ".".join(version.split(".")[:2]) if version else ""
    checks["layout_identity"] = layout == {
        "archive_root": "python/",
        "install_root": "python/",
        "python_executable": f"python/bin/python{python_mm}",
        "direct_extract_runnable": True,
        "prefix_model": "whole-prefix-relocatable",
    }
    checks["profile_boundary"] = profiles.get("primary") == "termux-cli" and profiles.get("binary_identity_requires_termux") is False
    mappings = compatibility.get("consumer_mappings", {}) if isinstance(compatibility, dict) else {}
    checks["consumer_mapping_noncanonical"] = mappings.get("uv_catalog_key_is_canonical_identity") is False

    checks["manifest_top_keys"] = exact_keys(manifest, {"schema_version", "metadata_kind", "artifact_id", "archive", "serialization", "ownership", "entries", "extensions"})
    checks["manifest_identity"] = manifest.get("schema_version") == 1 and manifest.get("metadata_kind") == "hw-t-standalone-manifest" and manifest.get("artifact_id") == artifact_id
    checks["manifest_archive_identity"] = archive_path.is_file() and manifest.get("archive") == {"filename": archive_path.name, "sha256": sha256_file(archive_path), "size": archive_path.stat().st_size, "root": "python/"}
    serialization = manifest.get("serialization", {})
    checks["serialization_contract"] = serialization == {
        "format": "pax-tar+zstd",
        "member_order": "lexicographic-posix-path",
        "mtime": 0,
        "uid": 0,
        "gid": 0,
        "uname": "",
        "gname": "",
        "hardlinks": "forbidden",
        "special_entries": "forbidden",
        "symlink_policy": "relative-non-escaping",
        "pax_headers": "path-and-linkpath-only-when-required",
        "compression_profile_recorded_in_provenance": True,
    }
    checks["ownership_contract"] = manifest.get("ownership") == {
        "unit": "exact-manifest-path",
        "unowned_descendant_policy": "preserve",
        "directory_removal_rule": "remove-owned-directory-only-when-empty",
        "installer_repacking": "forbidden",
    }
    entries = manifest.get("entries", [])
    paths = [entry.get("path") for entry in entries if isinstance(entry, dict)] if isinstance(entries, list) else []
    checks["manifest_paths_sorted_unique"] = bool(paths) and paths == sorted(paths) and len(paths) == len(set(paths))
    checks["manifest_paths_safe"] = bool(paths) and all(safe_relative(path) for path in paths)
    checks["manifest_single_root"] = bool(paths) and paths[0] == "python" and all(path == "python" or path.startswith("python/") for path in paths)
    checks["manifest_classes_exact"] = {entry.get("payload_class") for entry in entries if isinstance(entry, dict)} == {"runtime", "development"}
    checks["manifest_modes"] = all(isinstance(entry, dict) and bool(MODE.fullmatch(str(entry.get("mode", "")))) for entry in entries)
    checks["excluded_paths_absent"] = all(path not in EXCLUDED_PATHS and not any(path == root_path or path.startswith(root_path + "/") for root_path in EXCLUDED_PATH_PREFIXES) for path in paths)
    manifest_by_path = {entry["path"]: entry for entry in entries if isinstance(entry, dict) and isinstance(entry.get("path"), str)}
    launcher_path = f"python/bin/python{python_mm}"
    checks["launcher_manifest"] = manifest_by_path.get(launcher_path, {}).get("type") == "regular" and manifest_by_path.get(launcher_path, {}).get("mode") == "0755"
    checks["launcher_symlinks"] = manifest_by_path.get("python/bin/python3", {}).get("symlink_target") == f"python{python_mm}" and manifest_by_path.get("python/bin/python", {}).get("symlink_target") == "python3"

    archive_members: list[tarfile.TarInfo] = []
    archive_data: dict[str, bytes] = {}
    archive_error = ""
    if archive_path.is_file():
        try:
            proc = subprocess.run(["zstd", "-q", "-d", "-c", str(archive_path)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode="r:") as archive:
                archive_members = archive.getmembers()
                for member in archive_members:
                    if member.isfile():
                        stream = archive.extractfile(member)
                        archive_data[member.name] = stream.read() if stream else b""
        except Exception as exc:
            archive_error = f"{type(exc).__name__}: {exc}"
    checks["archive_decompress_parse"] = not archive_error and bool(archive_members)
    member_names = [member.name for member in archive_members]
    checks["archive_member_order_exact"] = member_names == paths
    checks["archive_headers_normalized"] = all(member.mtime == 0 and member.uid == 0 and member.gid == 0 and member.uname == "" and member.gname == "" for member in archive_members)
    checks["archive_types_safe"] = all(member.isdir() or member.isfile() or member.issym() for member in archive_members) and not any(member.islnk() or member.isdev() or member.isfifo() for member in archive_members)
    checks["archive_modes_match"] = all(manifest_by_path.get(member.name, {}).get("mode") == f"{member.mode & 0o7777:04o}" for member in archive_members)
    checks["archive_regular_bytes_match"] = all(member.name in archive_data and len(archive_data[member.name]) == manifest_by_path[member.name].get("size") and sha256_bytes(archive_data[member.name]) == manifest_by_path[member.name].get("sha256") for member in archive_members if member.isfile())
    checks["archive_symlinks_safe"] = all(safe_symlink_target(member.name, member.linkname) and manifest_by_path.get(member.name, {}).get("symlink_target") == member.linkname for member in archive_members if member.issym())

    checks["provenance_identity"] = provenance.get("schema_version") == 1 and provenance.get("metadata_kind") == "hw-t-standalone-provenance" and provenance.get("artifact_id") == artifact_id
    source = provenance.get("source", {})
    toolchain = provenance.get("toolchain", {})
    build = provenance.get("build", {})
    archive_serialization = provenance.get("archive_serialization", {})
    checks["provenance_source"] = source.get("implementation") == "cpython" and source.get("version") == version and bool(re.fullmatch(r"[0-9a-f]{40}", str(source.get("commit", ""))))
    checks["provenance_toolchain"] = toolchain.get("android_api") == api and bool(toolchain.get("ndk_version")) and bool(toolchain.get("target_compiler"))
    checks["provenance_build"] = build.get("repository") == "daylight-00/cpython-android-cli" and bool(re.fullmatch(r"[0-9a-f]{40}", str(build.get("commit", "")))) and bool(re.fullmatch(r"[0-9a-f]{40}", str(build.get("tree", "")))) and build.get("fixture_only") is False
    checks["provenance_serialization"] = archive_serialization.get("tar_format") == "pax" and archive_serialization.get("zstd_threads") == 1 and archive_serialization.get("frame_checksum") is True and isinstance(archive_serialization.get("zstd_level"), int)
    e2p2 = provenance.get("extensions", {}).get("e2p2", {}) if isinstance(provenance.get("extensions"), dict) else {}
    checks["provenance_stripping"] = e2p2.get("serialization_replay") == "2/2-byte-identical" and isinstance(e2p2.get("stripped_elf_count"), int) and e2p2.get("stripped_elf_count") > 0 and len(e2p2.get("stripped_elf", [])) == e2p2.get("stripped_elf_count")

    checks["qualification_identity"] = qualification.get("schema_version") == 1 and qualification.get("metadata_kind") == "hw-t-standalone-qualification" and qualification.get("artifact_id") == artifact_id
    checks["qualification_unselectable"] = qualification.get("status") == "not-qualified" and qualification.get("selectable") is False and qualification.get("checks") == {"static": "passed", "emulator": "not-run", "termux": "not-run"}
    checks["release_selectability_consistent"] = release.get("selectable") is False and row.get("selectable") is False and qualification.get("selectable") is False

    checks["licenses_identity"] = licenses.get("schema_version") == 1 and licenses.get("metadata_kind") == "hw-t-standalone-licenses" and licenses.get("artifact_id") == artifact_id
    license_entries = licenses.get("entries", [])
    license_path = f"python/lib/python{python_mm}/LICENSE.txt"
    license_manifest = manifest_by_path.get(license_path, {})
    checks["licenses_match_manifest"] = isinstance(license_entries, list) and len(license_entries) >= 1 and any(item.get("archive_path") == license_path and item.get("sha256") == license_manifest.get("sha256") and item.get("size") == license_manifest.get("size") for item in license_entries if isinstance(item, dict))
    checks["licenses_incomplete_before_publication"] = licenses.get("complete_for_published_payload") is False

    checksum_rows: list[tuple[str, str]] = []
    if archive_path.is_file():
        checksum_rows.append((sha256_file(archive_path), archive_path.name))
    checksum_rows.extend((sha256_file(path), path.name) for path in sidecar_paths.values() if path.is_file())
    expected_sums = "".join(f"{digest}  {name}\n" for digest, name in sorted(checksum_rows, key=lambda item: item[1]))
    checks["checksums_exact"] = checksums_path.is_file() and checksums_path.read_text(encoding="utf-8") == expected_sums
    checks["checksums_no_cycle"] = "release-index.json" not in expected_sums and "SHA256SUMS" not in expected_sums

    expected_assets = {archive_path.name, "SHA256SUMS", "release-index.json", *(path.name for path in sidecar_paths.values())}
    observed_assets = {path.name for path in release_dir.iterdir() if path.is_file()} if release_dir.is_dir() else set()
    checks["release_asset_set_exact"] = observed_assets == expected_assets

    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": 1,
        "verification_kind": "e2p2-e2p1-release-envelope-static-verification",
        "pass": not failed and not missing and not parse_errors,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "failed_checks": failed,
        "missing_files": sorted(set(missing)),
        "parse_errors": parse_errors,
        "checks": dict(sorted(checks.items())),
        "archive_error": archive_error,
        "artifact_id": artifact_id or None,
        "claim_boundary": "Static E2-P1 envelope and deterministic packaging verification only; no Android, Termux, runtime behavior, closure, publication, or selectability claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--release-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(args.root, args.release_dir)
    except Exception as exc:
        print(json.dumps({"pass": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
