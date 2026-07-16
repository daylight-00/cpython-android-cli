#!/usr/bin/env python3
"""Independently verify the Epoch 2 Phase 1 standalone artifact contract."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

ARTIFACT_ID = "cpython-3.14.6-aarch64-linux-android24-install_only_stripped"
ARCHIVE_NAME = f"{ARTIFACT_ID}.tar.zst"
SIDECAR_KINDS = ("artifact", "manifest", "provenance", "qualification", "licenses")
SCHEMA_FILES = tuple(f"{name}.schema.json" for name in ("artifact", "manifest", "provenance", "qualification", "licenses", "release-index"))
EXPECTED_SCHEMA_IDS = {
    "artifact.schema.json": "https://daylight-00.github.io/cpython-android-cli/schemas/e2p1/artifact-v1.json",
    "manifest.schema.json": "https://daylight-00.github.io/cpython-android-cli/schemas/e2p1/manifest-v1.json",
    "provenance.schema.json": "https://daylight-00.github.io/cpython-android-cli/schemas/e2p1/provenance-v1.json",
    "qualification.schema.json": "https://daylight-00.github.io/cpython-android-cli/schemas/e2p1/qualification-v1.json",
    "licenses.schema.json": "https://daylight-00.github.io/cpython-android-cli/schemas/e2p1/licenses-v1.json",
    "release-index.schema.json": "https://daylight-00.github.io/cpython-android-cli/schemas/e2p1/release-index-v1.json",
}
FORBIDDEN_TERMUX_IDENTITY = (
    "/data/data/com.termux",
    "/data/user/0/com.termux",
    "com.termux/files/usr",
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MODE = re.compile(r"^[0-7]{4}$")
ARTIFACT_ID_RE = re.compile(r"^cpython-\d+\.\d+\.\d+-aarch64-linux-android\d+-[a-z0-9_]+$")


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def canonical_body_bytes(value: Any) -> bytes:
    return canonical_json_bytes(value)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(path: object) -> bool:
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or "\x00" in path:
        return False
    parts = PurePosixPath(path).parts
    return all(part not in {"", ".", ".."} for part in parts)


def safe_symlink_target(member_path: str, target: object) -> bool:
    if not isinstance(target, str) or not target or target.startswith("/") or "\\" in target:
        return False
    resolved: list[str] = list(PurePosixPath(member_path).parent.parts)
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


def read_json(path: Path, parse_errors: dict[str, str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        parse_errors[str(path)] = f"{type(exc).__name__}: {exc}"
        return {}
    if not isinstance(value, dict):
        parse_errors[str(path)] = "top-level value is not an object"
        return {}
    return value


def exact_keys(value: Any, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def file_ref_matches(ref: Any, path: Path) -> bool:
    return (
        isinstance(ref, dict)
        and set(ref) == {"filename", "sha256", "size"}
        and ref.get("filename") == path.name
        and ref.get("sha256") == sha256_file(path)
        and ref.get("size") == path.stat().st_size
    )


def verify(root: Path, fixture_dir: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    contract = root / "experiments/epoch2-standalone-artifact-contract"
    schemas_dir = contract / "schemas"
    canonical_fixture = (contract / "fixtures/valid").resolve()
    fixture = (fixture_dir or canonical_fixture).resolve()
    parse_errors: dict[str, str] = {}
    missing: list[str] = []

    required = [
        contract / "README.md",
        contract / "E2P1_STANDALONE_ARTIFACT_CONTRACT.md",
        contract / "e2p1-authority.json",
        contract / "verify-e2p1-standalone-artifact-contract.py",
        contract / "test-verify-e2p1-standalone-artifact-contract.py",
        contract / "run-e2p1-standalone-artifact-contract.sh",
        root / "docs/contracts/E2P1_STANDALONE_ARTIFACT_CONTRACT.md",
        root / "docs/evidence/E2P1_STANDALONE_ARTIFACT_CONTRACT_RESULT.md",
        root / "docs/handoff/2026-07-16-epoch2-p1-standalone-artifact-contract.md",
    ]
    required.extend(schemas_dir / name for name in SCHEMA_FILES)
    required.extend(fixture / f"{ARTIFACT_ID}.{kind}.json" for kind in SIDECAR_KINDS)
    required.extend((fixture / ARCHIVE_NAME, fixture / "SHA256SUMS", fixture / "release-index.json"))
    for path in required:
        if not path.is_file():
            missing.append(str(path.relative_to(root)) if path.is_relative_to(root) else str(path))

    schemas = {name: read_json(schemas_dir / name, parse_errors) for name in SCHEMA_FILES if (schemas_dir / name).is_file()}
    artifact_path = fixture / f"{ARTIFACT_ID}.artifact.json"
    manifest_path = fixture / f"{ARTIFACT_ID}.manifest.json"
    provenance_path = fixture / f"{ARTIFACT_ID}.provenance.json"
    qualification_path = fixture / f"{ARTIFACT_ID}.qualification.json"
    licenses_path = fixture / f"{ARTIFACT_ID}.licenses.json"
    release_path = fixture / "release-index.json"
    archive_path = fixture / ARCHIVE_NAME
    checksums_path = fixture / "SHA256SUMS"
    authority_path = contract / "e2p1-authority.json"

    artifact = read_json(artifact_path, parse_errors) if artifact_path.is_file() else {}
    manifest = read_json(manifest_path, parse_errors) if manifest_path.is_file() else {}
    provenance = read_json(provenance_path, parse_errors) if provenance_path.is_file() else {}
    qualification = read_json(qualification_path, parse_errors) if qualification_path.is_file() else {}
    licenses = read_json(licenses_path, parse_errors) if licenses_path.is_file() else {}
    release_index = read_json(release_path, parse_errors) if release_path.is_file() else {}
    authority = read_json(authority_path, parse_errors) if authority_path.is_file() else {}

    checks: dict[str, bool] = {}
    checks["required_files"] = not missing
    checks["json_parse_clean"] = not parse_errors
    checks["schema_count_6"] = len(schemas) == 6
    checks["schema_draft_2020_12"] = all(value.get("$schema") == "https://json-schema.org/draft/2020-12/schema" for value in schemas.values())
    checks["schema_ids_exact"] = all(schemas.get(name, {}).get("$id") == expected for name, expected in EXPECTED_SCHEMA_IDS.items())
    checks["schema_top_level_strict"] = all(value.get("type") == "object" and value.get("additionalProperties") is False for value in schemas.values())
    checks["schema_version_const_1"] = all(value.get("properties", {}).get("schema_version", {}).get("const") == 1 for value in schemas.values())
    checks["json_canonical"] = all(path.read_bytes() == canonical_json_bytes(json.loads(path.read_text(encoding="utf-8"))) for path in [*(schemas_dir / n for n in SCHEMA_FILES), artifact_path, manifest_path, provenance_path, qualification_path, licenses_path, release_path, authority_path] if path.is_file())

    checks["artifact_top_keys"] = exact_keys(artifact, {"schema_version","metadata_kind","artifact_id","distribution","target","artifact","layout","profiles","compatibility","extensions"})
    checks["artifact_identity"] = artifact.get("schema_version") == 1 and artifact.get("metadata_kind") == "hw-t-standalone-artifact" and artifact.get("artifact_id") == ARTIFACT_ID and bool(ARTIFACT_ID_RE.fullmatch(ARTIFACT_ID))
    dist = artifact.get("distribution", {})
    target = artifact.get("target", {})
    art = artifact.get("artifact", {})
    layout = artifact.get("layout", {})
    profiles = artifact.get("profiles", {})
    compat = artifact.get("compatibility", {})
    consumer = compat.get("consumer_mappings", {}) if isinstance(compat, dict) else {}
    checks["distribution_identity"] = dist == {
        "implementation":"cpython","python_version":"3.14.6","python_major_minor":"3.14","python_tag":"cp314","python_abi_tag":"cp314","soabi":"cpython-314-aarch64-linux-android","multiarch":"aarch64-linux-android"
    }
    checks["target_identity"] = target == {
        "os":"android","kernel":"linux","libc":"bionic","architecture":"aarch64","target_triple":"aarch64-linux-android","android_abi":"arm64-v8a","android_api_min":24,"wheel_platform_tag":"android_24_arm64_v8a","sysconfig_platform":"android-24-arm64_v8a"
    }
    checks["wheel_api_consistency"] = target.get("wheel_platform_tag") == f"android_{target.get('android_api_min')}_arm64_v8a" and target.get("sysconfig_platform") == f"android-{target.get('android_api_min')}-arm64_v8a"
    checks["artifact_archive_identity"] = art.get("flavor") == "install_only_stripped" and art.get("archive_filename") == ARCHIVE_NAME and art.get("archive_format") == "pax-tar+zstd" and art.get("archive_sha256") == (sha256_file(archive_path) if archive_path.is_file() else None) and art.get("archive_size") == (archive_path.stat().st_size if archive_path.is_file() else None)
    checks["artifact_payload_split"] = art.get("payload_classes") == ["runtime","development"] and art.get("excluded_payload_classes") == ["tests","build","debug_symbols"] and art.get("native_debug") == "stripped"
    checks["layout_direct_runnable"] = layout == {"archive_root":"python/","install_root":"python/","python_executable":"python/bin/python3.14","direct_extract_runnable":True,"prefix_model":"whole-prefix-relocatable"}
    checks["termux_profile_not_binary_identity"] = profiles.get("primary") == "termux-cli" and profiles.get("qualified") == ["termux-cli"] and profiles.get("binary_identity_requires_termux") is False
    checks["compatibility_identity"] = compat.get("android_api_rule") == "host-api-greater-than-or-equal-to-minimum" and compat.get("required_os") == "android" and compat.get("required_libc") == "bionic" and compat.get("required_abi") == "arm64-v8a"
    checks["uv_mapping_noncanonical"] = consumer.get("uv_catalog_key") == "cpython-3.14.6-linux-aarch64-none" and consumer.get("uv_catalog_key_is_canonical_identity") is False
    artifact_text = artifact_path.read_text(encoding="utf-8") if artifact_path.is_file() else ""
    checks["no_termux_absolute_identity"] = not any(marker in artifact_text for marker in FORBIDDEN_TERMUX_IDENTITY)

    checks["manifest_top_keys"] = exact_keys(manifest, {"schema_version","metadata_kind","artifact_id","archive","serialization","ownership","entries","extensions"})
    checks["manifest_identity"] = manifest.get("schema_version") == 1 and manifest.get("metadata_kind") == "hw-t-standalone-manifest" and manifest.get("artifact_id") == ARTIFACT_ID
    checks["manifest_archive_identity"] = manifest.get("archive") == {"filename":ARCHIVE_NAME,"sha256":art.get("archive_sha256"),"size":art.get("archive_size"),"root":"python/"}
    serialization = manifest.get("serialization", {})
    checks["serialization_contract"] = serialization == {"format":"pax-tar+zstd","member_order":"lexicographic-posix-path","mtime":0,"uid":0,"gid":0,"uname":"","gname":"","hardlinks":"forbidden","special_entries":"forbidden","symlink_policy":"relative-non-escaping","pax_headers":"path-and-linkpath-only-when-required","compression_profile_recorded_in_provenance":True}
    checks["ownership_contract"] = manifest.get("ownership") == {"unit":"exact-manifest-path","unowned_descendant_policy":"preserve","directory_removal_rule":"remove-owned-directory-only-when-empty","installer_repacking":"forbidden"}
    entries = manifest.get("entries", [])
    checks["manifest_entries_nonempty"] = isinstance(entries, list) and bool(entries)
    paths = [entry.get("path") for entry in entries if isinstance(entry, dict)] if isinstance(entries, list) else []
    checks["manifest_paths_sorted_unique"] = paths == sorted(paths) and len(paths) == len(set(paths))
    checks["manifest_paths_safe_rooted"] = bool(paths) and all(safe_relative(path) and (path == "python" or path.startswith("python/")) for path in paths)
    checks["manifest_entry_types"] = all(isinstance(entry, dict) and entry.get("type") in {"directory","regular","symlink"} and isinstance(entry.get("mode"), str) and bool(MODE.fullmatch(entry["mode"])) and entry.get("payload_class") in {"runtime","development"} for entry in entries) if isinstance(entries, list) else False
    checks["manifest_regular_fields"] = all((entry.get("type") != "regular") or (isinstance(entry.get("size"), int) and entry.get("size") >= 0 and isinstance(entry.get("sha256"), str) and bool(HEX64.fullmatch(entry["sha256"])) and "symlink_target" not in entry) for entry in entries) if isinstance(entries, list) else False
    checks["manifest_directory_fields"] = all((entry.get("type") != "directory") or all(key not in entry for key in ("size","sha256","symlink_target")) for entry in entries) if isinstance(entries, list) else False
    checks["manifest_symlink_fields"] = all((entry.get("type") != "symlink") or ("size" not in entry and "sha256" not in entry and safe_symlink_target(entry.get("path", ""), entry.get("symlink_target"))) for entry in entries) if isinstance(entries, list) else False
    checks["manifest_payload_classes_present"] = {entry.get("payload_class") for entry in entries if isinstance(entry, dict)} == {"runtime","development"}

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
    checks["archive_single_root"] = bool(member_names) and all(name == "python" or name.startswith("python/") for name in member_names)
    checks["archive_headers_normalized"] = all(member.mtime == 0 and member.uid == 0 and member.gid == 0 and member.uname == "" and member.gname == "" for member in archive_members)
    checks["archive_types_safe"] = all(member.isdir() or member.isfile() or member.issym() for member in archive_members) and not any(member.islnk() or member.isdev() or member.isfifo() for member in archive_members)
    checks["archive_modes_match"] = all((next((entry for entry in entries if entry.get("path") == member.name), {}).get("mode") == f"{member.mode & 0o7777:04o}") for member in archive_members)
    manifest_by_path = {entry.get("path"): entry for entry in entries if isinstance(entry, dict)}
    checks["archive_regular_bytes_match"] = all(member.name in archive_data and len(archive_data[member.name]) == manifest_by_path[member.name].get("size") and sha256_bytes(archive_data[member.name]) == manifest_by_path[member.name].get("sha256") for member in archive_members if member.isfile())
    checks["archive_symlinks_safe"] = all(safe_symlink_target(member.name, member.linkname) for member in archive_members if member.issym())

    checks["provenance_identity"] = provenance.get("schema_version") == 1 and provenance.get("metadata_kind") == "hw-t-standalone-provenance" and provenance.get("artifact_id") == ARTIFACT_ID
    checks["provenance_source"] = provenance.get("source") == {"implementation":"cpython","version":"3.14.6","tag":"v3.14.6","commit":"c63aec69bd59c55314c06c23f4c22c03de76fe45"}
    checks["provenance_toolchain"] = provenance.get("toolchain") == {"ndk_version":"27.3.13750724","target_compiler":"aarch64-linux-android24-clang","android_api":24}
    build = provenance.get("build", {})
    checks["provenance_fixture_only"] = build.get("repository") == "daylight-00/cpython-android-cli" and build.get("commit") == "a34e5fdc6224e66aa7ed335e921780fbadd728dc" and build.get("tree") == "7543e0a8ff86a3bee1fcda33fc86b11692c90b92" and build.get("build_options") == [] and build.get("fixture_only") is True
    checks["provenance_serialization"] = provenance.get("archive_serialization") == {"tar_format":"pax","zstd_tool":"zstd-cli-1.5.7","zstd_level":19,"zstd_threads":1,"frame_checksum":True}
    pred = provenance.get("predecessor_authority", {})
    checks["provenance_predecessor"] = pred.get("epoch1_commit") == "e1de252740a96c40f3d587269136235a2c84ea16" and pred.get("epoch1_tree") == "66c976f3fc182496d2843771b46faaf98fc267da" and pred.get("stage3f_publication_snapshot") == "dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233"

    checks["qualification_identity"] = qualification.get("schema_version") == 1 and qualification.get("metadata_kind") == "hw-t-standalone-qualification" and qualification.get("artifact_id") == ARTIFACT_ID
    checks["qualification_fixture_unselectable"] = qualification.get("status") == "not-qualified" and qualification.get("selectable") is False and qualification.get("checks") == {"static":"not-run","emulator":"not-run","termux":"not-run"}
    checks["qualification_profile"] = qualification.get("profiles") == ["termux-cli"]
    checks["qualification_claim_boundary"] = isinstance(qualification.get("claim_boundary"), list) and len(qualification["claim_boundary"]) >= 2 and "not CPython" in " ".join(qualification["claim_boundary"])

    checks["licenses_identity"] = licenses.get("schema_version") == 1 and licenses.get("metadata_kind") == "hw-t-standalone-licenses" and licenses.get("artifact_id") == ARTIFACT_ID
    license_entries = licenses.get("entries", [])
    license_manifest = manifest_by_path.get("python/lib/python3.14/LICENSE.txt", {})
    checks["licenses_match_manifest"] = isinstance(license_entries, list) and len(license_entries) == 1 and license_entries[0].get("archive_path") == "python/lib/python3.14/LICENSE.txt" and license_entries[0].get("sha256") == license_manifest.get("sha256") and license_entries[0].get("size") == license_manifest.get("size")
    checks["licenses_fixture_incomplete"] = licenses.get("complete_for_published_payload") is False

    checks["release_index_top_keys"] = exact_keys(release_index, {"schema_version","release","release_sha256"})
    release = release_index.get("release", {})
    checks["release_index_digest"] = isinstance(release, dict) and release_index.get("release_sha256") == sha256_bytes(canonical_body_bytes(release))
    checks["release_fixture_unselectable"] = release.get("format") == "hw-t-standalone-release-v1" and release.get("contract_version") == 1 and release.get("channel") == "fixture" and release.get("selectable") is False
    products = release.get("products", [])
    row = products[0] if isinstance(products, list) and len(products) == 1 and isinstance(products[0], dict) else {}
    checks["release_product_identity"] = row.get("artifact_id") == ARTIFACT_ID and row.get("selectable") is False and row.get("archive") == {"filename":ARCHIVE_NAME,"sha256":art.get("archive_sha256"),"size":art.get("archive_size")}
    metadata = row.get("metadata", {}) if isinstance(row, dict) else {}
    sidecar_paths = {kind: fixture / f"{ARTIFACT_ID}.{kind}.json" for kind in SIDECAR_KINDS}
    checks["release_sidecar_refs"] = isinstance(metadata, dict) and set(metadata) == set(SIDECAR_KINDS) and all(file_ref_matches(metadata.get(kind), path) for kind, path in sidecar_paths.items())
    checks["release_checksums_ref"] = file_ref_matches(release.get("checksums"), checksums_path) if isinstance(release, dict) and checksums_path.is_file() else False
    checks["release_selectability_consistent"] = row.get("selectable") is False and release.get("selectable") is False and qualification.get("selectable") is False and qualification.get("status") != "passed"

    expected_sum_rows = [(art.get("archive_sha256"), ARCHIVE_NAME)] + [(sha256_file(path), path.name) for path in sidecar_paths.values() if path.is_file()]
    expected_sums = "".join(f"{digest}  {name}\n" for digest, name in sorted(expected_sum_rows, key=lambda item: item[1]))
    checks["checksums_exact"] = checksums_path.is_file() and checksums_path.read_text(encoding="utf-8") == expected_sums
    checks["checksums_no_self_cycle"] = "release-index.json" not in expected_sums and "SHA256SUMS" not in expected_sums

    checks["authority_identity"] = authority.get("schema_version") == 1 and authority.get("authority_kind") == "epoch2-p1-standalone-artifact-contract" and authority.get("status") == "frozen-repository-contract"
    checks["authority_repository_input"] = authority.get("repository_input") == {"branch":"agent/epoch2-documentation-foundation","head":"a34e5fdc6224e66aa7ed335e921780fbadd728dc","tree":"7543e0a8ff86a3bee1fcda33fc86b11692c90b92"}
    authority_files = authority.get("file_identities", {})
    authority_expected_paths = [
        *(schemas_dir / n for n in SCHEMA_FILES),
        canonical_fixture / ARCHIVE_NAME,
        canonical_fixture / f"{ARTIFACT_ID}.artifact.json",
        canonical_fixture / f"{ARTIFACT_ID}.manifest.json",
        canonical_fixture / f"{ARTIFACT_ID}.provenance.json",
        canonical_fixture / f"{ARTIFACT_ID}.qualification.json",
        canonical_fixture / f"{ARTIFACT_ID}.licenses.json",
        canonical_fixture / "SHA256SUMS",
        canonical_fixture / "release-index.json",
        contract / "verify-e2p1-standalone-artifact-contract.py",
        contract / "test-verify-e2p1-standalone-artifact-contract.py",
        contract / "run-e2p1-standalone-artifact-contract.sh",
        contract / "E2P1_STANDALONE_ARTIFACT_CONTRACT.md",
    ]
    checks["authority_file_set"] = isinstance(authority_files, dict) and set(authority_files) == {str(path.relative_to(contract)) for path in authority_expected_paths}
    checks["authority_file_identities"] = isinstance(authority_files, dict) and all((contract / rel).is_file() and ref == {"sha256":sha256_file(contract / rel),"size":(contract / rel).stat().st_size} for rel, ref in authority_files.items())
    checks["authority_contract_fields"] = authority.get("contract") == {"version":1,"primary_flavor":"install_only_stripped","archive_root":"python/","archive_format":"pax-tar+zstd","payload_classes":["runtime","development"],"primary_profile":"termux-cli","target_triple":"aarch64-linux-android","android_abi":"arm64-v8a","android_api_min":24,"wheel_platform_tag":"android_24_arm64_v8a"}

    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": 1,
        "verification_kind": "epoch2-p1-standalone-artifact-contract",
        "pass": not failed and not missing and not parse_errors,
        "check_count": len(checks),
        "pass_count": sum(bool(value) for value in checks.values()),
        "failed_checks": failed,
        "missing_files": sorted(set(missing)),
        "parse_errors": parse_errors,
        "archive_error": archive_error,
        "checks": dict(sorted(checks.items())),
        "claim_boundary": "Repository contract and deterministic fixture verification only; no real CPython artifact, target runtime, release, installer, or upstream uv claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--fixture-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.root, args.fixture_dir)
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
