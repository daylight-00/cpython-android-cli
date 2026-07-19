#!/usr/bin/env python3
"""Positive and negative regression tests for the UT-1 focused verifier."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import stat
import tarfile
import tempfile
from pathlib import Path


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("ut1_verify", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--output-dir", type=Path, default=Path("experiments/epoch2-upstream-thin-artifact-prototype"))
    args = ap.parse_args()
    root = args.root.resolve()
    source = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    module = load_module(source / "verify_artifact_prototype.py")
    generator = load_module(source / "generate_artifact_prototype.py")
    results = {}

    canonical = module.verify(root, source, None)
    results["canonical_pass"] = canonical.get("pass") is True

    with tempfile.TemporaryDirectory(prefix="ut1-verifier-fixtures-") as td:
        temp = Path(td)

        case = temp / "availability"
        shutil.copytree(source, case)
        data = json.loads((case / "python-json-schema-mapping.json").read_text())
        data["python_exe"]["availability"] = "available"
        dump(case / "python-json-schema-mapping.json", data)
        results["availability_mutation_rejected"] = module.verify(root, case, None).get("pass") is False

        case = temp / "missing"
        shutil.copytree(source, case)
        (case / "consumer-extraction-contract.json").unlink()
        results["missing_required_output_rejected"] = module.verify(root, case, None).get("pass") is False

        case = temp / "fabricated"
        shutil.copytree(source, case)
        data = json.loads((case / "PYTHON.json").read_text())
        data["build_info"]["core"]["objs"] = ["build/fabricated.o"]
        dump(case / "PYTHON.json", data)
        results["fabricated_object_surface_rejected"] = module.verify(root, case, None).get("pass") is False

        archive = temp / "root-marker.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            root_info = tarfile.TarInfo(".")
            root_info.type = tarfile.DIRTYPE
            root_info.mode = 0o755
            tf.addfile(root_info)
            prefix_info = tarfile.TarInfo("prefix")
            prefix_info.type = tarfile.DIRTYPE
            prefix_info.mode = 0o755
            tf.addfile(prefix_info)
        extracted = temp / "root-marker-extracted"
        rows = generator.safe_extract(archive, extracted)
        results["archive_root_directory_marker_excluded"] = [row["path"] for row in rows] == ["prefix"]

        bad_archive = temp / "bad-root-marker.tar.gz"
        with tarfile.open(bad_archive, "w:gz") as tf:
            bad_root = tarfile.TarInfo(".")
            bad_root.type = tarfile.REGTYPE
            bad_root.size = 0
            tf.addfile(bad_root)
        try:
            generator.safe_extract(bad_archive, temp / "bad-root-extracted")
        except ValueError:
            results["archive_root_non_directory_rejected"] = True
        else:
            results["archive_root_non_directory_rejected"] = False

        metadata_tree = temp / "metadata-tree/python"
        metadata_tree.mkdir(parents=True)
        os.chmod(metadata_tree, 0o700)
        target = metadata_tree / "target.so"
        target.write_bytes(b"target")
        os.chmod(target, 0o644)
        os.symlink("target.so", metadata_tree / "alias.so")
        extracted_rows = [
            {"path": "prefix", "type": "directory", "mode": "0o755"},
            {"path": "prefix/target.so", "type": "file", "mode": "0o644"},
            {"path": "prefix/alias.so", "type": "symlink", "mode": "0o755"},
        ]
        overrides = generator.official_mode_overrides(extracted_rows, "python")
        manifest = generator.tree_manifest(metadata_tree, overrides)
        by_path = {row["path"]: row for row in manifest}
        results["official_root_mode_preserved"] = by_path["python"]["mode"] == "0755"
        results["official_symlink_tar_mode_preserved"] = by_path["python/alias.so"]["mode"] == "0755"
        metadata_tar = temp / "metadata.tar"
        generator.write_tar(metadata_tree, manifest, metadata_tar)
        with tarfile.open(metadata_tar, "r:") as tf:
            root_member = tf.getmember("python")
            link_member = tf.getmember("python/alias.so")
            results["serialized_root_mode_preserved"] = stat.S_IMODE(root_member.mode) == 0o755
            results["serialized_symlink_mode_preserved"] = stat.S_IMODE(link_member.mode) == 0o755

    passed = all(results.values())
    print(json.dumps({"schema_version": 1, "test_kind": "e2-r1-ut1-verifier-regressions", "pass": passed, "checks": results}, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
