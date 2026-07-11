#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

from archive_serialization_contract import (
    ARTIFACTS,
    EXPECTED_MANIFEST_HASHES,
    EXPECTED_MANIFEST_INDEX,
    EXPECTED_PRODUCT_LOCK,
    archive_filename,
    canonical_json_bytes,
    envelope_members,
    payload_member_name,
    read_json,
    safe_relative,
    sha256_file,
)


def normalize_link(member_name: str, target: str) -> tuple[str, ...] | None:
    if not target or target.startswith("/") or "\\" in target:
        return None
    parts: list[str] = []
    for part in PurePosixPath(member_name).parent.joinpath(target).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
        else:
            parts.append(part)
    return tuple(parts) if parts else None


def expected_names(manifest: dict[str, Any]) -> list[str]:
    artifact_id = manifest["artifact"]["artifact_id"]
    return envelope_members(artifact_id) + [
        payload_member_name(artifact_id, entry["archive_path"])
        for entry in manifest["entries"]
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-results", required=True, type=Path)
    parser.add_argument("--archive-results", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifest_results = args.manifest_results.resolve()
    archive_results = args.archive_results.resolve()
    index_path = manifest_results / "manifest-index.json"
    lock_path = manifest_results / "input/product-lock.json"
    manifest_paths = {
        name: manifest_results / "manifests" / f"{name}.manifest.json"
        for name in ARTIFACTS
    }
    manifests = {name: read_json(path) for name, path in manifest_paths.items()}

    checks: dict[str, bool] = {
        "manifest_index_hash_exact": sha256_file(index_path)
        == EXPECTED_MANIFEST_INDEX,
        "product_lock_hash_exact": sha256_file(lock_path) == EXPECTED_PRODUCT_LOCK,
        "manifest_hashes_exact": {
            name: sha256_file(path) for name, path in manifest_paths.items()
        }
        == EXPECTED_MANIFEST_HASHES,
        "artifact_set_exact": set(manifests) == set(ARTIFACTS),
    }
    observed: dict[str, Any] = {}

    for artifact in ARTIFACTS:
        manifest = manifests[artifact]
        artifact_id = manifest["artifact"]["artifact_id"]
        archive_path = archive_results / "archives" / archive_filename(manifest)
        archive_exists = archive_path.is_file()
        names: list[str] = []
        allowed_types = False
        hardlinks_zero = False
        paths_safe = False
        symlinks_exact = False
        parent_symlink_traversal_zero = False
        if archive_exists:
            with tarfile.open(archive_path, "r:gz") as archive:
                members = archive.getmembers()
                names = [member.name for member in members]
                by_name = {member.name: member for member in members}
                allowed_types = all(
                    member.isdir() or member.isreg() or member.issym()
                    for member in members
                )
                hardlinks_zero = all(not member.islnk() for member in members)
                paths_safe = all(
                    safe_relative(member.name)
                    and PurePosixPath(member.name).parts[0] == artifact_id
                    for member in members
                )
                symlinks_exact = True
                expected_symlink_paths: set[str] = set()
                for entry in manifest["entries"]:
                    if entry["type"] != "symlink":
                        continue
                    name = payload_member_name(artifact_id, entry["archive_path"])
                    expected_symlink_paths.add(name)
                    member = by_name.get(name)
                    resolved = (
                        normalize_link(name, member.linkname)
                        if member is not None and member.issym()
                        else None
                    )
                    if (
                        member is None
                        or not member.issym()
                        or member.linkname != entry["symlink_target"]
                        or resolved is None
                        or resolved[0] != artifact_id
                    ):
                        symlinks_exact = False
                observed_symlink_paths = {
                    member.name for member in members if member.issym()
                }
                symlinks_exact = (
                    symlinks_exact
                    and observed_symlink_paths == expected_symlink_paths
                )
                symlink_paths = {
                    PurePosixPath(member.name) for member in members if member.issym()
                }
                parent_symlink_traversal_zero = all(
                    not any(parent in symlink_paths for parent in PurePosixPath(member.name).parents)
                    for member in members
                )

        expected = expected_names(manifest)
        checks.update(
            {
                f"{artifact}_archive_exists": archive_exists,
                f"{artifact}_member_order_exact": names == expected,
                f"{artifact}_member_names_unique": len(set(names)) == len(names),
                f"{artifact}_paths_safe": paths_safe,
                f"{artifact}_entry_types_allowed": allowed_types,
                f"{artifact}_hardlinks_zero": hardlinks_zero,
                f"{artifact}_symlinks_exact_and_contained": symlinks_exact,
                f"{artifact}_parent_symlink_traversal_zero": parent_symlink_traversal_zero,
            }
        )
        observed[artifact] = {
            "archive": str(archive_path),
            "member_count": len(names),
            "expected_member_count": len(expected),
        }

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "observed": observed,
        "claim_boundary": {
            "proved": (
                "Only the exact trusted manifest member set with allowed types and "
                "contained symlinks may proceed to staging extraction."
            ),
            "not_proved": (
                "Payload bytes and extracted fidelity until the archive verifier passes."
            ),
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 34


if __name__ == "__main__":
    raise SystemExit(main())
