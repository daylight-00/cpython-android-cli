#!/usr/bin/env python3
"""Build and qualify the exact RB-2 CA/timezone data product candidates."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))

from archive import safe_extract_tar, sha256_file, write_json  # noqa: E402
from data_products import activate_data_release, assemble_data_product, install_data_product, qualify_data_product, verify_data_product  # noqa: E402
from owner_approval_review import verify_family  # noqa: E402

LOCK = ROOT / "config/products/cpython-android-cli-e3-rb2-data-products-r1.lock.json"
INSTALL_ONLY_NAME = "cpython-3.14.6+e3-full-r4-aarch64-linux-android-install_only.tar.gz"
INSTALL_ONLY_SHA = "84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76"
INSTALL_ONLY_SIZE = 23841726


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def file_snapshot(root: Path) -> list[dict[str, Any]]:
    return [
        {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        for path in sorted(root.rglob("*")) if path.is_file() and not path.is_symlink()
    ]


def identity(path: Path) -> dict[str, Any]:
    return {"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def exact_input(input_dir: Path, expected: dict[str, Any]) -> Path:
    path = input_dir / expected["filename"]
    actual = identity(path) if path.is_file() else None
    wanted = {key: expected[key] for key in ("filename", "sha256", "size_bytes")}
    if actual != wanted:
        raise ValueError(f"input identity mismatch: actual={actual!r} expected={wanted!r}")
    return path


def assemble_twice(name: str, entry: dict[str, Any], inputs: Path, output: Path, zstd: str) -> dict[str, Any]:
    certifi = exact_input(inputs, entry["certifi"])
    tzdata = exact_input(inputs, entry["tzdata"])
    results: list[dict[str, Any]] = []
    archives: list[Path] = []
    for run in ("run-a", "run-b"):
        run_dir = output / "builds" / name / run
        result = assemble_data_product(
            certifi,
            tzdata,
            run_dir,
            ca_version=entry["certifi"]["version"],
            tzdata_version=entry["tzdata"]["version"],
            revision="r1",
            expected_certifi=entry["certifi"],
            expected_tzdata=entry["tzdata"],
            zstd=zstd,
        )
        results.append(result)
        archives.append(run_dir / result["artifact"]["filename"])
    if archives[0].read_bytes() != archives[1].read_bytes():
        raise ValueError(f"{name} product is not byte reproducible")
    if results[0]["release_id"] != entry["release_id"] or results[1]["release_id"] != entry["release_id"]:
        raise ValueError(f"{name} release identity does not match the provider lock")
    accepted = output / "artifacts" / archives[0].name
    accepted.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(archives[0], accepted)
    return {
        "name": name,
        "release_id": results[0]["release_id"],
        "artifact": identity(accepted),
        "two_run_byte_identity": True,
        "verification": verify_data_product(accepted, zstd=zstd),
        "run_a": results[0],
        "run_b": results[1],
    }


def extract_exact_python(family: Path, destination: Path) -> Path:
    archive = family / INSTALL_ONLY_NAME
    actual = identity(archive) if archive.is_file() else None
    expected = {"filename": INSTALL_ONLY_NAME, "sha256": INSTALL_ONLY_SHA, "size_bytes": INSTALL_ONLY_SIZE}
    if actual != expected:
        raise ValueError(f"frozen install_only identity mismatch: actual={actual!r} expected={expected!r}")
    safe_extract_tar(archive, destination, "r:gz")
    python = destination / "python/bin/python3.14"
    if not python.is_file() or not os.access(python, os.X_OK):
        raise ValueError("exact frozen install_only interpreter is missing or non-executable")
    return python


def run(inputs: Path, family: Path, output: Path, *, zstd: str = "zstd") -> dict[str, Any]:
    inputs = inputs.resolve(); family = family.resolve(); output = output.resolve()
    family_verification = verify_family(family, ROOT)
    if not family_verification["pass"]:
        raise ValueError(f"invalid exact legally integrated family: {family_verification}")
    before = file_snapshot(family)
    lock = load(LOCK)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    rollback = assemble_twice("rollback", lock["releases"]["rollback"], inputs, output, zstd)
    current = assemble_twice("current", lock["releases"]["current"], inputs, output, zstd)
    write_json(output / "reproducibility.json", {
        "schema_version": 1,
        "check_kind": "epoch3-rb2-data-product-reproducibility",
        "pass": rollback["two_run_byte_identity"] and current["two_run_byte_identity"],
        "rollback": rollback,
        "current": current,
    })

    with tempfile.TemporaryDirectory(prefix="e3-rb2-lifecycle-") as tmp:
        temp = Path(tmp)
        data_home = temp / "data-home"
        rollback_archive = output / "artifacts" / rollback["artifact"]["filename"]
        current_archive = output / "artifacts" / current["artifact"]["filename"]
        events = [
            {"event": "install-rollback", "result": install_data_product(rollback_archive, data_home, zstd=zstd)},
            {"event": "install-current", "result": install_data_product(current_archive, data_home, zstd=zstd)},
            {"event": "rollback", "result": activate_data_release(data_home, rollback["release_id"])},
            {"event": "reactivate-current", "result": activate_data_release(data_home, current["release_id"])},
        ]
        current_link = os.readlink(data_home / "current")
        lifecycle = {
            "schema_version": 1,
            "check_kind": "epoch3-rb2-data-update-rollback",
            "pass": current_link == f"releases/{current['release_id']}",
            "events": events,
            "final_current_link": current_link,
            "release_directories": sorted(path.name for path in (data_home / "releases").iterdir() if path.is_dir()),
            "python_install_root_written": False,
        }
        write_json(output / "lifecycle.json", lifecycle)

        python_root = temp / "python-runtime"
        python = extract_exact_python(family, python_root)
        qualification = qualify_data_product(python, data_home / "current")
        write_json(output / "runtime-qualification.json", qualification)

    after = file_snapshot(family)
    invariance = {
        "schema_version": 1,
        "check_kind": "epoch3-rb2-frozen-python-family-invariance",
        "pass": before == after,
        "file_count": len(before),
        "before_fingerprint_sha256": hashlib.sha256(json.dumps(before, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "after_fingerprint_sha256": hashlib.sha256(json.dumps(after, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "exact_files": before,
    }
    write_json(output / "frozen-family-invariance.json", invariance)
    checks = {
        "exact_legally_integrated_family": family_verification["pass"],
        "rollback_reproducible": rollback["two_run_byte_identity"] and rollback["verification"]["pass"],
        "current_reproducible": current["two_run_byte_identity"] and current["verification"]["pass"],
        "update_rollback_reactivation": lifecycle["pass"],
        "exact_frozen_python_runtime": qualification["pass"],
        "frozen_python_family_unchanged": invariance["pass"],
    }
    failed = sorted(key for key, value in checks.items() if value is not True)
    result = {
        "schema_version": 1,
        "result_kind": "epoch3-rb2-ca-timezone-data-product-owner-result",
        "pass": not failed,
        "checks": checks,
        "failed_checks": failed,
        "family_verification": family_verification,
        "rollback": {"release_id": rollback["release_id"], "artifact": rollback["artifact"]},
        "current": {"release_id": current["release_id"], "artifact": current["artifact"]},
        "claim_boundary": {"rb2_closed": False, "selectable": False, "publication": False},
    }
    write_json(output / "rb2-data-product-result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--family-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zstd", default="zstd")
    args = parser.parse_args()
    try:
        result = run(args.input_dir, args.family_dir, args.output_dir, zstd=args.zstd)
    except Exception as exc:  # noqa: BLE001
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
