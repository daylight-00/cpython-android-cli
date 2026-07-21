#!/usr/bin/env python3
"""Assemble and qualify the first real canonical Epoch 3 full archive on Android."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))

from archive import safe_extract_tar, sha256_file, write_json  # noqa: E402
from observe_astral import compare, observe  # noqa: E402
from qualify_full import qualify  # noqa: E402
from verify_full import verify  # noqa: E402


def run(command: list[str], *, cwd: Path | None = None, timeout: int = 1800) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"command": command, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "timed_out": True}


def extract_candidate_json(archive: Path, destination: Path, zstd: str) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    tar_path = destination / "candidate.tar"
    proc = subprocess.run([zstd, "-q", "-d", "-f", str(archive), "-o", str(tar_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise RuntimeError(proc.stderr)
    tree = destination / "candidate-tree"
    safe_extract_tar(tar_path, tree, "r:")
    return tree / "python/PYTHON.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-archive", required=True)
    parser.add_argument("--astral-golden", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--cc", required=True)
    parser.add_argument("--patchelf", required=True)
    parser.add_argument("--readelf", required=True)
    parser.add_argument("--pkg-config", required=True)
    parser.add_argument("--zstd", required=True)
    parser.add_argument("--release-id", default="e3-full-r1")
    args = parser.parse_args()

    official = Path(args.official_archive).resolve()
    golden_path = Path(args.astral_golden).resolve()
    output = Path(args.output_dir).resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    receipts = output / "receipts"
    receipts.mkdir()
    artifacts = output / "artifacts"
    artifacts.mkdir()
    work_products = output / "work-products"
    work_products.mkdir()

    input_identity = {
        "filename": official.name,
        "sha256": sha256_file(official),
        "size_bytes": official.stat().st_size,
    }
    golden_identity = {
        "filename": golden_path.name,
        "sha256": sha256_file(golden_path),
        "size_bytes": golden_path.stat().st_size,
    }
    write_json(receipts / "input-identities.json", {"schema_version": 1, "official": input_identity, "astral_golden": golden_identity})

    with tempfile.TemporaryDirectory(prefix="e3-full-target-") as tmp:
        workspace = Path(tmp)
        extracted = workspace / "official"
        safe_extract_tar(official, extracted)
        prefix = extracted / "prefix"
        if not prefix.is_dir():
            raise SystemExit("official input lacks prefix/")
        launcher = work_products / "python3.14"
        launcher_build = run([
            str(ROOT / "components/upstream-thin/bin/build-launcher"),
            "--prefix", str(prefix), "--cc", args.cc, "--patchelf", args.patchelf,
            "--readelf", args.readelf, "--output", str(launcher),
        ], cwd=ROOT, timeout=600)
        write_json(receipts / "launcher-build.json", launcher_build)
        if launcher_build["returncode"]:
            print(json.dumps({"pass": False, "stage": "launcher-build", "detail": launcher_build}, indent=2))
            return 1

        assembly_dirs = [workspace / "assembly-a", workspace / "assembly-b"]
        assembly_rows: list[dict[str, Any]] = []
        full_paths: list[Path] = []
        for index, assembly_dir in enumerate(assembly_dirs, 1):
            row = run([
                str(ROOT / "components/upstream-thin/bin/cpython-android-upstream-thin"), "assemble-full",
                "--upstream-archive", str(official), "--launcher", str(launcher),
                "--output-dir", str(assembly_dir), "--release-id", args.release_id,
                "--patchelf", args.patchelf, "--readelf", args.readelf, "--zstd", args.zstd,
            ], cwd=ROOT, timeout=3600)
            assembly_rows.append(row)
            write_json(receipts / f"assembly-{index}.json", row)
            matches = sorted(assembly_dir.glob("*-full.tar.zst"))
            if row["returncode"] or len(matches) != 1:
                print(json.dumps({"pass": False, "stage": f"assembly-{index}", "detail": row, "artifacts": [str(p) for p in matches]}, indent=2))
                return 1
            full_paths.append(matches[0])

        reproducible = full_paths[0].read_bytes() == full_paths[1].read_bytes()
        reproducibility = {
            "schema_version": 1,
            "pass": reproducible,
            "first": {"sha256": sha256_file(full_paths[0]), "size_bytes": full_paths[0].stat().st_size},
            "second": {"sha256": sha256_file(full_paths[1]), "size_bytes": full_paths[1].stat().st_size},
        }
        write_json(receipts / "full-reproducibility.json", reproducibility)
        if not reproducible:
            print(json.dumps({"pass": False, "stage": "reproducibility", "detail": reproducibility}, indent=2))
            return 1

        final_full = artifacts / full_paths[0].name
        shutil.copyfile(full_paths[0], final_full)
        static = verify(final_full, zstd=args.zstd, readelf=args.readelf, fixture_mode=False)
        write_json(receipts / "full-static-verification.json", static)

        target = qualify(final_full, output=receipts / "full-target-qualification.json", zstd=args.zstd, pkg_config=args.pkg_config)

        golden_lock = json.loads((ROOT / "config/products/astral-cpython-3.14.6-aarch64-linux-gnu-golden-v1.lock.json").read_text(encoding="utf-8"))
        golden = observe(golden_path, expected_sha256=golden_lock["asset"]["sha256"], zstd=args.zstd)
        write_json(receipts / "astral-golden-observation.json", golden)
        candidate_json_path = extract_candidate_json(final_full, workspace / "candidate-observation", args.zstd)
        candidate_json = json.loads(candidate_json_path.read_text(encoding="utf-8"))
        conformance = compare(golden, candidate_json)
        conformance.update({
            "candidate_archive": {"sha256": sha256_file(final_full), "size_bytes": final_full.stat().st_size},
            "golden_archive": golden["asset"],
            "candidate_install_bin_entries": sorted(path.name for path in (candidate_json_path.parent / "install/bin").glob("*")) if (candidate_json_path.parent / "install/bin").is_dir() else [],
        })
        write_json(receipts / "astral-conformance-decision-input.json", conformance)

        gates = {
            "exact_official_input": input_identity == {
                "filename": "python-3.14.6-aarch64-linux-android.tar.gz",
                "sha256": "38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5",
                "size_bytes": 22358404,
            },
            "launcher_build": launcher_build["returncode"] == 0,
            "assembly_a": assembly_rows[0]["returncode"] == 0,
            "assembly_b": assembly_rows[1]["returncode"] == 0,
            "full_reproducible": reproducibility["pass"],
            "full_static_verification": static["pass"],
            "full_target_qualification": target["pass"],
            "astral_golden_observation": golden["pass"],
            "astral_conformance_boundary": conformance["pass"],
            "only_full_artifact": len(list(artifacts.iterdir())) == 1 and final_full.name.endswith("-full.tar.zst"),
        }
        failed = sorted(key for key, value in gates.items() if value is not True)
        diagnostics = {
            "schema_version": 1,
            "gate_kind": "epoch3-upstream-thin-first-real-full-candidate",
            "pass": not failed,
            "gates": gates,
            "failed_gates": failed,
            "artifact": {"path": f"artifacts/{final_full.name}", "sha256": sha256_file(final_full), "size_bytes": final_full.stat().st_size},
            "launcher": {"path": "work-products/python3.14", "sha256": sha256_file(launcher), "size_bytes": launcher.stat().st_size},
            "claim_boundary": {
                "candidate_full_assembled": not failed,
                "full_authority_frozen": False,
                "install_only_implementation_started": False,
                "selectable": False,
                "publication": False,
                "api24_runtime_claim": False,
                "actual_16k_runtime_claim": False,
                "non_termux_context_claim": False,
            },
        }
        write_json(receipts / "gate-diagnostics.json", diagnostics)
        write_json(output / "result-summary.json", diagnostics)
        print(json.dumps(diagnostics, indent=2, sort_keys=True))
        return 0 if diagnostics["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
