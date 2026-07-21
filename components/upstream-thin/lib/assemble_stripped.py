#!/usr/bin/env python3
"""Derive Astral-like install_only_stripped strictly from frozen install_only."""
from __future__ import annotations

import argparse
import gzip
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from archive import safe_extract_tar, sha256_file, tree_manifest, write_json, write_tar_gz
from elf import is_elf
from strip_surface import section_census, strip_one, tool_identity

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-install-only-r1.lock.json"


def identity(path: Path) -> dict[str, Any]:
    return {"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def output_filename(source: Path, release_id: str | None = None) -> str:
    if release_id:
        return f"{release_id}-install_only_stripped.tar.gz"
    suffix = "-install_only.tar.gz"
    if source.name.endswith(suffix):
        return source.name[: -len(suffix)] + "-install_only_stripped.tar.gz"
    suffix = "_install_only.tar.gz"
    if source.name.endswith(suffix):
        return source.name[: -len(suffix)] + "_install_only_stripped.tar.gz"
    raise ValueError(f"install-only filename lacks canonical suffix: {source.name}")


def assemble(
    source: Path,
    output_dir: Path,
    *,
    strip_tool: str,
    readelf: str = "readelf",
    lock_path: Path = DEFAULT_LOCK,
    fixture_mode: bool = False,
    release_id: str | None = None,
) -> dict[str, Any]:
    lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.is_file() else {}
    expected = lock.get("artifact", {})
    observed = identity(source)
    identity_keys = ("filename", "sha256", "size_bytes")
    if not fixture_mode and any(observed.get(key) != expected.get(key) for key in identity_keys):
        raise ValueError(f"accepted install-only mismatch: {observed} != {expected}")

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_filename(source, release_id)
    strip_identity = tool_identity(strip_tool)
    readelf_identity = tool_identity(readelf)

    with tempfile.TemporaryDirectory(prefix="assemble-stripped-") as temporary:
        root = Path(temporary)
        tar_path = root / "input.tar"
        with gzip.open(source, "rb") as input_stream, tar_path.open("wb") as output_stream:
            shutil.copyfileobj(input_stream, output_stream)
        extracted = root / "extracted"
        safe_extract_tar(tar_path, extracted, "r:")
        tree = extracted / "python"
        if not tree.is_dir() or sorted(path.name for path in extracted.iterdir()) != ["python"]:
            raise ValueError("install-only input must contain one python root")

        before_manifest = tree_manifest(tree)
        rows: list[dict[str, Any]] = []
        regular_elf: list[str] = []
        eligible: list[str] = []
        for path in sorted(tree.rglob("*")):
            if not is_elf(path):
                continue
            relative = path.relative_to(tree).as_posix()
            regular_elf.append(relative)
            census = section_census(path, readelf)
            row: dict[str, Any] = {
                "path": relative,
                "before": {
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                    "section_census": census,
                },
                "eligible": census["eligible"],
                "operation": "none",
            }
            if census["eligible"]:
                eligible.append(relative)
                mutation = strip_one(
                    path,
                    strip_tool=strip_tool,
                    readelf=readelf,
                    display_path=relative,
                )
                row.update({"operation": "strip --strip-unneeded", "mutation": mutation})
                if not mutation["dynamic_and_alignment_surface_preserved"]:
                    raise RuntimeError(f"strip changed dynamic/alignment surface: {relative}")
                if not mutation["removable_sections_removed"]:
                    raise RuntimeError(f"strip left removable sections: {relative}")
                if not mutation["changed"]:
                    raise RuntimeError(f"eligible ELF did not change after strip: {relative}")
            rows.append(row)

        changed = [row["path"] for row in rows if row.get("mutation", {}).get("changed") is True]
        if changed != eligible:
            raise RuntimeError(f"eligible/changed mismatch: {eligible} != {changed}")
        decision = "distinct-archive" if changed else "producer-already-stripped-alias"
        artifact: Path | None = None
        archive_rows: list[dict[str, Any]] = []
        if changed:
            artifact = output_dir / filename
            archive_rows = write_tar_gz(tree, artifact)

        receipt = {
            "schema_version": 1,
            "assembler_kind": "epoch3-upstream-thin-install-only-stripped",
            "decision": decision,
            "source_install_only": observed,
            "strip_tool": strip_identity,
            "readelf_tool": readelf_identity,
            "strip_operation": "--strip-unneeded",
            "regular_elf_count": len(regular_elf),
            "eligible_elf_count": len(eligible),
            "changed_elf_count": len(changed),
            "regular_elf_paths": regular_elf,
            "eligible_paths": eligible,
            "changed_paths": changed,
            "mutations": rows,
            "tree_before": before_manifest,
            "tree_after": tree_manifest(tree),
            "artifact": None
            if artifact is None
            else {
                "filename": artifact.name,
                "sha256": sha256_file(artifact),
                "size_bytes": artifact.stat().st_size,
                "member_count": len(archive_rows),
            },
            "claim_boundary": {
                "stripped_candidate": bool(changed),
                "alias_decision": not changed,
                "stripped_authority_frozen": False,
                "selectable": False,
                "publication": False,
            },
        }
        receipt_path = output_dir / f"{filename}.receipt.json"
        write_json(receipt_path, receipt)
        return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-only-archive", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--strip-tool", required=True)
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--install-only-lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--release-id")
    args = parser.parse_args()
    try:
        result = assemble(
            Path(args.install_only_archive).resolve(),
            Path(args.output_dir).resolve(),
            strip_tool=args.strip_tool,
            readelf=args.readelf,
            lock_path=Path(args.install_only_lock).resolve(),
            fixture_mode=args.fixture_mode,
            release_id=args.release_id,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"{type(exc).__name__}: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
