#!/usr/bin/env python3
"""Assemble the canonical full upstream-thin artifact."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from archive import copy_entry, copy_tree_contents, safe_extract_tar, sha256_file, tree_manifest, write_json, write_tar_zst
from elf import patch_lr3
from metadata import build_python_json
from normalize import normalize_runtime_metadata
from pip_surface import install_upstream_pip


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON must be object: {path}")
    return value


def verify_input(path: Path, lock: dict[str, Any], fixture_mode: bool) -> dict[str, Any]:
    observed = {"filename": path.name, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
    if not fixture_mode:
        expected = lock["archive"]
        failures = [key for key in ("filename", "size_bytes", "sha256") if observed[key] != expected[key]]
        if failures:
            raise RuntimeError(f"official input mismatch: {failures}; observed={observed}")
    return observed


def install_launcher(install: Path, launcher: Path, python_mm: str) -> list[dict[str, str]]:
    bindir = install / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    executable = bindir / f"python{python_mm}"
    shutil.copyfile(launcher, executable)
    os.chmod(executable, 0o755)
    aliases: list[dict[str, str]] = []
    for name in ("python3", "python"):
        alias = bindir / name
        if alias.exists() or alias.is_symlink():
            alias.unlink()
        os.symlink(f"python{python_mm}", alias)
        aliases.append({"path": f"bin/{name}", "target": f"python{python_mm}"})
    return aliases


def copy_upstream_material(extracted: Path, archive: Path, build: Path) -> None:
    package = build / "upstream/package"
    package.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(archive, package / archive.name)
    metadata = build / "upstream/extracted-metadata"
    metadata.mkdir(parents=True, exist_ok=True)
    for child in sorted(extracted.iterdir(), key=lambda item: item.name):
        if child.name == "prefix":
            continue
        target = metadata / child.name
        copy_entry(child, target)


def assemble(args: argparse.Namespace) -> dict[str, Any]:
    contract_path = Path(args.contract).resolve()
    contract = load_json(contract_path)
    root = contract_path.parents[3]
    lock_path = root / contract["input_lock"]
    lock = load_json(lock_path)
    contract["resolved_input_lock"] = lock
    archive = Path(args.upstream_archive).resolve()
    launcher = Path(args.launcher).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    observed_input = verify_input(archive, lock, args.fixture_mode)
    python_mm = lock["python"]["major_minor"]
    artifact_stem = f"cpython-{lock['python']['version']}+{args.release_id}-{lock['target']['triple']}"
    artifact = output_dir / f"{artifact_stem}-full.tar.zst"
    with tempfile.TemporaryDirectory(prefix="e3-full-") as tmp:
        workspace = Path(tmp)
        extracted = workspace / "upstream"
        safe_extract_tar(archive, extracted)
        prefix = extracted / "prefix"
        if not prefix.is_dir():
            raise RuntimeError("official archive is missing prefix/")
        if not args.fixture_mode and (prefix / "bin").exists():
            raise RuntimeError("official embedding package unexpectedly contains prefix/bin")
        full_parent = workspace / "full"
        python_root = full_parent / "python"
        install = python_root / "install"
        build = python_root / "build"
        copy_tree_contents(prefix, install)
        aliases = install_launcher(install, launcher, python_mm)
        metadata_normalization: dict[str, Any] = {"schema_version": 1, "fixture_mode": True, "status": "not-applied"}
        pip_surface: dict[str, Any] = {"schema_version": 1, "fixture_mode": True, "status": "not-applied"}
        mutation_rows: list[dict[str, Any]] = []
        if not args.fixture_mode:
            metadata_normalization = normalize_runtime_metadata(install)
            pip_surface = install_upstream_pip(install)
            mutation_rows = patch_lr3(install, args.patchelf, args.readelf)
        copy_upstream_material(extracted, archive, build)
        hw = build / "hw-t"
        write_json(hw / "input.json", {"schema_version": 1, "official_input": observed_input, "lock": contract["input_lock"]})
        write_json(hw / "launcher.json", {"schema_version": 1, "source": "components/upstream-thin/src/python.c", "binary": {"sha256": sha256_file(launcher), "size_bytes": launcher.stat().st_size}, "aliases": aliases})
        write_json(hw / "mutations.json", {"schema_version": 1, "model": "LR-3-plus-upstream-preserved-profile-M-consumer-overlay", "fixture_mode": args.fixture_mode, "elf_objects": mutation_rows, "runtime_metadata": metadata_normalization, "pip_surface": pip_surface})
        python_json = build_python_json(install, contract, readelf=args.readelf, fixture_mode=args.fixture_mode)
        write_json(python_root / "PYTHON.json", python_json)
        manifest_path = hw / "full-member-manifest.json"
        excluded = {"python/build/hw-t/full-member-manifest.json"}
        manifest_rows = tree_manifest(python_root, exclude=excluded)
        write_json(manifest_path, {"schema_version": 1, "manifest_kind": "self-excluding-full-tree-manifest", "excluded_paths": sorted(excluded), "members": manifest_rows})
        final_rows = write_tar_zst(python_root, artifact, args.zstd)
        receipt = {
            "schema_version": 1,
            "receipt_kind": "epoch3-upstream-thin-full-local-assembly",
            "status": "passed-structural-fixture" if args.fixture_mode else "passed-local-full-assembly",
            "selectable": False,
            "publication": False,
            "artifact": {"path": str(artifact), "sha256": sha256_file(artifact), "size_bytes": artifact.stat().st_size, "member_count": len(final_rows)},
            "official_input": observed_input,
            "launcher_sha256": sha256_file(launcher),
            "lr3_object_count": len(mutation_rows),
            "runtime_metadata_normalized": not args.fixture_mode,
            "pip_surface_installed": not args.fixture_mode,
            "python_json_standard_top_level_keys": sorted(python_json),
        }
        write_json(output_dir / f"{artifact_stem}-full.receipt.json", receipt)
        return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default="components/upstream-thin/contracts/product-v1.json")
    parser.add_argument("--upstream-archive", required=True)
    parser.add_argument("--launcher", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--release-id", default="e3-dev")
    parser.add_argument("--patchelf", default="patchelf")
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--zstd", default="zstd")
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args()
    print(json.dumps(assemble(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
