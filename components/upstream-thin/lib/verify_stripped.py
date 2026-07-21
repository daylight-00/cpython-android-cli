#!/usr/bin/env python3
"""Verify exact install_only -> install_only_stripped derivation."""
from __future__ import annotations

import argparse
import gzip
import json
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from archive import safe_extract_tar, sha256_file, tree_manifest
from elf import elf_surface, is_elf
from strip_surface import section_census

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-install-only-r1.lock.json"
SURFACE_KEYS = ("type", "machine", "needed", "soname", "rpath", "runpath", "load_alignments")


def extract_gz(path: Path, destination: Path) -> Path:
    tar_path = destination.parent / f"{destination.name}.tar"
    with gzip.open(path, "rb") as source, tar_path.open("wb") as target:
        shutil.copyfileobj(source, target)
    safe_extract_tar(tar_path, destination, "r:")
    roots = sorted(item.name for item in destination.iterdir())
    if roots != ["python"]:
        raise ValueError(f"archive must contain one python root: {roots}")
    return destination / "python"


def tar_meta(path: Path) -> dict[str, Any]:
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        normalized = all(
            member.uid == 0
            and member.gid == 0
            and member.uname == ""
            and member.gname == ""
            and member.mtime == 0
            for member in members
        )
    with path.open("rb") as stream:
        header = stream.read(8)
    return {
        "member_count": len(members),
        "duplicate": len(names) != len(set(names)),
        "tar_normalized": normalized,
        "gzip_mtime": int.from_bytes(header[4:8], "little"),
    }


def relative_manifest(root: Path) -> dict[str, dict[str, Any]]:
    prefix = f"{root.name}/"
    result: dict[str, dict[str, Any]] = {}
    for row in tree_manifest(root):
        path = row["path"]
        relative = "" if path == root.name else path.removeprefix(prefix)
        result[relative] = row
    return result


def verify(
    stripped: Path,
    source: Path,
    receipt_path: Path,
    *,
    readelf: str = "readelf",
    lock_path: Path = DEFAULT_LOCK,
    fixture_mode: bool = False,
) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    observed: dict[str, Any] = {}
    changed: list[str] = []
    eligible_before: list[str] = []
    artifact_member_count: int | None = None
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.is_file() else {}
        expected = lock.get("artifact", {})
        observed = {"filename": source.name, "sha256": sha256_file(source), "size_bytes": source.stat().st_size}
        identity_keys = ("filename", "sha256", "size_bytes")
        checks["accepted_install_only_identity"] = fixture_mode or all(observed.get(key) == expected.get(key) for key in identity_keys)

        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        checks["receipt_parse"] = isinstance(receipt, dict)
        checks["receipt_source_identity"] = receipt.get("source_install_only") == observed
        checks["receipt_decision_distinct"] = receipt.get("decision") == "distinct-archive"

        with tempfile.TemporaryDirectory(prefix="verify-stripped-") as temporary:
            root = Path(temporary)
            before = extract_gz(source, root / "before")
            after = extract_gz(stripped, root / "after")
            before_manifest = relative_manifest(before)
            after_manifest = relative_manifest(after)
            common_paths = sorted(set(before_manifest) & set(after_manifest))
            checks["path_set_identity"] = set(before_manifest) == set(after_manifest)
            checks["type_mode_symlink_identity"] = checks["path_set_identity"] and all(
                (
                    before_manifest[path]["type"],
                    before_manifest[path]["mode"],
                    before_manifest[path]["linkname"],
                )
                == (
                    after_manifest[path]["type"],
                    after_manifest[path]["mode"],
                    after_manifest[path]["linkname"],
                )
                for path in common_paths
            )

            non_elf_unchanged = True
            surfaces_preserved = True
            removable_absent = True
            regular_elf_paths: list[str] = []
            for relative in common_paths:
                row_before = before_manifest[relative]
                row_after = after_manifest[relative]
                if row_before["type"] != "file":
                    continue
                before_path = before / relative
                after_path = after / relative
                byte_changed = row_before["sha256"] != row_after["sha256"]
                if byte_changed:
                    changed.append(relative)
                if not is_elf(before_path):
                    if byte_changed:
                        non_elf_unchanged = False
                    continue
                regular_elf_paths.append(relative)
                census_before = section_census(before_path, readelf)
                if census_before["eligible"]:
                    eligible_before.append(relative)
                surface_before = elf_surface(before_path, readelf)
                surface_after = elf_surface(after_path, readelf)
                if any(surface_before[key] != surface_after[key] for key in SURFACE_KEYS):
                    surfaces_preserved = False
                if byte_changed and section_census(after_path, readelf)["eligible"]:
                    removable_absent = False

            receipt_changed = receipt.get("changed_paths", [])
            receipt_eligible = receipt.get("eligible_paths", [])
            checks["regular_elf_paths_exact"] = regular_elf_paths == receipt.get("regular_elf_paths", [])
            checks["eligible_paths_exact"] = eligible_before == receipt_eligible
            checks["changed_paths_exact"] = changed == receipt_changed
            checks["all_and_only_eligible_elf_changed"] = changed == eligible_before and bool(changed)
            checks["changed_count_exact"] = len(changed) == receipt.get("changed_elf_count")
            checks["eligible_count_exact"] = len(eligible_before) == receipt.get("eligible_elf_count")
            checks["regular_elf_count_exact"] = len(regular_elf_paths) == receipt.get("regular_elf_count")
            checks["distinct_byte_delta"] = bool(changed) and sha256_file(stripped) != sha256_file(source)
            checks["non_elf_bytes_unchanged"] = non_elf_unchanged
            checks["elf_dynamic_alignment_preserved"] = surfaces_preserved
            checks["removable_sections_absent_after"] = removable_absent

            metadata = tar_meta(stripped)
            artifact_member_count = metadata["member_count"]
            checks["no_duplicate_members"] = not metadata["duplicate"]
            checks["deterministic_tar_metadata"] = metadata["tar_normalized"]
            checks["deterministic_gzip_header"] = metadata["gzip_mtime"] == 0
            artifact = receipt.get("artifact", {})
            checks["artifact_identity_matches_receipt"] = (
                artifact.get("filename") == stripped.name
                and artifact.get("sha256") == sha256_file(stripped)
                and artifact.get("size_bytes") == stripped.stat().st_size
                and artifact.get("member_count") == metadata["member_count"]
            )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{type(exc).__name__}: {exc}")

    failed = sorted(key for key, value in checks.items() if value is not True)
    passed = not failed and not errors
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-upstream-thin-install-only-stripped",
        "pass": passed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "source_install_only": observed,
        "artifact": {
            "path": str(stripped),
            "filename": stripped.name if stripped.is_file() else None,
            "sha256": sha256_file(stripped) if stripped.is_file() else None,
            "size_bytes": stripped.stat().st_size if stripped.is_file() else None,
            "member_count": artifact_member_count,
        },
        "eligible_paths": eligible_before,
        "changed_paths": changed,
        "claim_boundary": {
            "stripped_candidate": passed,
            "stripped_authority_frozen": False,
            "selectable": False,
            "publication": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stripped_archive")
    parser.add_argument("--install-only-archive", required=True)
    parser.add_argument("--mutation-receipt", required=True)
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--install-only-lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args()
    result = verify(
        Path(args.stripped_archive).resolve(),
        Path(args.install_only_archive).resolve(),
        Path(args.mutation_receipt).resolve(),
        readelf=args.readelf,
        lock_path=Path(args.install_only_lock).resolve(),
        fixture_mode=args.fixture_mode,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
