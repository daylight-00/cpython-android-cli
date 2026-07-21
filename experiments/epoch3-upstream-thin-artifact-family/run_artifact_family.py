#!/usr/bin/env python3
"""Assemble and verify the canonical three-artifact Epoch 3 release family."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))

from archive import sha256_file, write_json  # noqa: E402

CLI = ROOT / "components/upstream-thin/bin/cpython-android-upstream-thin"
AUTHORITY_VERIFIERS = {
    "full": ROOT / "experiments/epoch3-upstream-thin-full/verify_full_authority.py",
    "install_only": ROOT / "experiments/epoch3-upstream-thin-install-only/verify_install_only_authority.py",
    "install_only_stripped": ROOT / "experiments/epoch3-upstream-thin-stripped/verify_stripped_authority.py",
}
LOCKS = {
    "full": ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-full-r4.lock.json",
    "install_only": ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-install-only-r1.lock.json",
    "install_only_stripped": ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-install-only-stripped-r2.lock.json",
}


def run(command: list[str], *, timeout: int = 3600) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"command": command, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "timed_out": True}
    except OSError as exc:
        return {"command": command, "returncode": 127, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}", "timed_out": False}


def parse_stdout_json(row: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(row.get("stdout", ""))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def identity(path: Path) -> dict[str, Any]:
    return {"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def directory_inventory(directory: Path) -> list[dict[str, Any]]:
    return [
        {"path": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        for path in sorted(directory.iterdir(), key=lambda p: p.name)
        if path.is_file()
    ]


def directory_fingerprint(inventory: list[dict[str, Any]]) -> str:
    payload = json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", required=True)
    parser.add_argument("--install-only", required=True)
    parser.add_argument("--stripped", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--zstd", default="zstd")
    args = parser.parse_args()

    inputs = {
        "full": Path(args.full).resolve(),
        "install_only": Path(args.install_only).resolve(),
        "install_only_stripped": Path(args.stripped).resolve(),
    }
    output = Path(args.output_dir).resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    receipts = output / "receipts"
    artifacts = output / "artifacts"
    receipts.mkdir()
    artifacts.mkdir()

    authority_results: dict[str, dict[str, Any]] = {}
    authority_pass = True
    for flavor, verifier in AUTHORITY_VERIFIERS.items():
        row = run([sys.executable, str(verifier), "--root", str(ROOT)])
        parsed = parse_stdout_json(row)
        write_json(receipts / f"{flavor}-authority-command.json", row)
        write_json(receipts / f"{flavor}-authority-verification.json", parsed)
        authority_results[flavor] = parsed
        authority_pass = authority_pass and row["returncode"] == 0 and parsed.get("pass") is True

    input_checks: dict[str, bool] = {}
    input_identities: dict[str, dict[str, Any]] = {}
    for flavor, path in inputs.items():
        locked = json.loads(LOCKS[flavor].read_text(encoding="utf-8"))["artifact"]
        observed = identity(path) if path.is_file() else {"filename": path.name, "sha256": None, "size_bytes": None}
        input_identities[flavor] = observed
        input_checks[flavor] = path.is_file() and all(observed.get(key) == locked.get(key) for key in ("filename", "sha256", "size_bytes"))
    write_json(receipts / "input-identities.json", {"schema_version": 1, "pass": all(input_checks.values()), "checks": input_checks, "observed": input_identities})

    if not authority_pass or not all(input_checks.values()):
        summary = {"schema_version": 1, "gate_kind": "epoch3-upstream-thin-artifact-family", "pass": False, "stage": "prerequisites", "authority_pass": authority_pass, "input_checks": input_checks}
        write_json(receipts / "gate-diagnostics.json", summary)
        write_json(output / "result-summary.json", summary)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 1

    assembly_dirs: list[Path] = []
    assembly_receipts: list[dict[str, Any]] = []
    inventories: list[list[dict[str, Any]]] = []
    for index in (1, 2):
        destination = output / f"assembly-{index}"
        row = run([
            str(CLI), "assemble-family",
            "--full", str(inputs["full"]),
            "--install-only", str(inputs["install_only"]),
            "--stripped", str(inputs["install_only_stripped"]),
            "--output-dir", str(destination),
            "--zstd", args.zstd,
        ])
        parsed = parse_stdout_json(row)
        write_json(receipts / f"assembly-{index}-command.json", row)
        write_json(receipts / f"assembly-{index}-receipt.json", parsed)
        if row["returncode"] != 0 or parsed.get("pass") is not True:
            summary = {"schema_version": 1, "gate_kind": "epoch3-upstream-thin-artifact-family", "pass": False, "stage": f"assembly-{index}", "detail": row}
            write_json(receipts / "gate-diagnostics.json", summary)
            write_json(output / "result-summary.json", summary)
            print(json.dumps(summary, indent=2, sort_keys=True))
            return 1
        assembly_dirs.append(destination)
        assembly_receipts.append(parsed)
        inventories.append(directory_inventory(destination))

    reproduction = {
        "schema_version": 1,
        "pass": inventories[0] == inventories[1],
        "first": {"file_count": len(inventories[0]), "fingerprint_sha256": directory_fingerprint(inventories[0]), "files": inventories[0]},
        "second": {"file_count": len(inventories[1]), "fingerprint_sha256": directory_fingerprint(inventories[1]), "files": inventories[1]},
    }
    write_json(receipts / "artifact-family-reproducibility.json", reproduction)
    if not reproduction["pass"]:
        summary = {"schema_version": 1, "gate_kind": "epoch3-upstream-thin-artifact-family", "pass": False, "stage": "reproducibility", "detail": reproduction}
        write_json(receipts / "gate-diagnostics.json", summary)
        write_json(output / "result-summary.json", summary)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 1

    final_family = artifacts / "cpython-3.14.6+e3-r1-aarch64-linux-android"
    shutil.copytree(assembly_dirs[0], final_family)
    verify_row = run([str(CLI), "verify-family", str(final_family), "--zstd", args.zstd])
    verification = parse_stdout_json(verify_row)
    write_json(receipts / "artifact-family-verification-command.json", verify_row)
    write_json(receipts / "artifact-family-verification.json", verification)

    final_inventory = directory_inventory(final_family)
    gates = {
        "three_frozen_authorities": authority_pass,
        "three_exact_inputs": all(input_checks.values()),
        "assembly_1": assembly_receipts[0].get("pass") is True,
        "assembly_2": assembly_receipts[1].get("pass") is True,
        "byte_reproducible_family": reproduction["pass"] is True,
        "exact_23_file_family": len(final_inventory) == 23,
        "family_verification": verify_row["returncode"] == 0 and verification.get("pass") is True,
        "artifact_bytes_reused": all(any(row["sha256"] == value["sha256"] and row["path"] == value["filename"] for row in final_inventory) for value in input_identities.values()),
        "claims_withheld": verification.get("claim_boundary", {}).get("selectable") is False and verification.get("claim_boundary", {}).get("publication") is False,
    }
    failed = sorted(key for key, value in gates.items() if value is not True)
    summary = {
        "schema_version": 1,
        "gate_kind": "epoch3-upstream-thin-artifact-family-candidate",
        "pass": not failed,
        "gates": dict(sorted(gates.items())),
        "failed_gates": failed,
        "inputs": input_identities,
        "release_family": {
            "path": f"artifacts/{final_family.name}",
            "file_count": len(final_inventory),
            "fingerprint_sha256": directory_fingerprint(final_inventory),
            "release_index": identity(final_family / "release-index.json"),
            "sha256sums": identity(final_family / "SHA256SUMS"),
            "release_sha256": verification.get("release_sha256"),
        },
        "claim_boundary": {
            "artifact_family_candidate_complete": not failed,
            "artifact_family_authority_frozen": False,
            "selectable": False,
            "publication": False,
            "component_license_mapping_complete": False,
            "api24_runtime_claim": False,
            "actual_16k_runtime_claim": False,
            "non_termux_context_claim": False,
        },
    }
    write_json(receipts / "gate-diagnostics.json", summary)
    write_json(output / "result-summary.json", summary)
    shutil.rmtree(assembly_dirs[0])
    shutil.rmtree(assembly_dirs[1])
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
