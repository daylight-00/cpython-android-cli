#!/usr/bin/env python3
"""Derive and qualify the canonical install-only archive from the accepted full."""
from __future__ import annotations

import argparse
import filecmp
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

FULL_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-full-r4.lock.json"
FULL_AUTHORITY = ROOT / "experiments/epoch3-upstream-thin-full/full-authority.json"
FULL_AUTHORITY_VERIFIER = ROOT / "experiments/epoch3-upstream-thin-full/verify_full_authority.py"
CLI = ROOT / "components/upstream-thin/bin/cpython-android-upstream-thin"


def run(command: list[str], *, timeout: int = 3600) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "command": command,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
        }
    except OSError as exc:
        return {
            "command": command,
            "returncode": 127,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "timed_out": False,
        }


def parse_stdout_json(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("returncode") != 0:
        return {}
    try:
        value = json.loads(row.get("stdout", ""))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-archive", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--zstd", required=True)
    parser.add_argument("--pkg-config", required=True)
    args = parser.parse_args()

    full = Path(args.full_archive).resolve()
    output = Path(args.output_dir).resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    receipts = output / "receipts"
    artifacts = output / "artifacts"
    receipts.mkdir()
    artifacts.mkdir()

    full_lock = json.loads(FULL_LOCK.read_text(encoding="utf-8"))
    expected_full = full_lock["artifact"]
    observed_full = {
        "filename": full.name,
        "sha256": sha256_file(full),
        "size_bytes": full.stat().st_size,
    }
    full_identity_pass = all(
        observed_full[key] == expected_full[key]
        for key in ("filename", "sha256", "size_bytes")
    )
    write_json(
        receipts / "full-input-identity.json",
        {
            "schema_version": 1,
            "pass": full_identity_pass,
            "expected": {key: expected_full[key] for key in ("filename", "sha256", "size_bytes")},
            "observed": observed_full,
        },
    )
    if not full_identity_pass:
        print(json.dumps({"pass": False, "stage": "full-input-identity", "observed": observed_full}, indent=2))
        return 1

    authority_row = run([sys.executable, str(FULL_AUTHORITY_VERIFIER), "--root", str(ROOT)])
    write_json(receipts / "full-authority-verification-command.json", authority_row)
    authority = parse_stdout_json(authority_row)
    write_json(receipts / "full-authority-verification.json", authority)
    if authority_row["returncode"] != 0 or authority.get("pass") is not True:
        print(json.dumps({"pass": False, "stage": "full-authority", "detail": authority_row}, indent=2))
        return 1

    assembly_paths: list[Path] = []
    assembly_rows: list[dict[str, Any]] = []
    assembly_receipts: list[dict[str, Any]] = []
    for index in (1, 2):
        destination = output / f"assembly-{index}"
        row = run(
            [
                str(CLI),
                "assemble-install-only",
                "--full-archive",
                str(full),
                "--output-dir",
                str(destination),
                "--zstd",
                args.zstd,
            ],
            timeout=3600,
        )
        assembly_rows.append(row)
        write_json(receipts / f"assembly-{index}-command.json", row)
        parsed = parse_stdout_json(row)
        assembly_receipts.append(parsed)
        write_json(receipts / f"assembly-{index}-receipt.json", parsed)
        matches = sorted(destination.glob("*-install_only.tar.gz"))
        if row["returncode"] != 0 or len(matches) != 1:
            print(json.dumps({"pass": False, "stage": f"assembly-{index}", "detail": row, "matches": [str(path) for path in matches]}, indent=2))
            return 1
        assembly_paths.append(matches[0])

    reproducibility = {
        "schema_version": 1,
        "pass": filecmp.cmp(assembly_paths[0], assembly_paths[1], shallow=False),
        "first": {
            "filename": assembly_paths[0].name,
            "sha256": sha256_file(assembly_paths[0]),
            "size_bytes": assembly_paths[0].stat().st_size,
        },
        "second": {
            "filename": assembly_paths[1].name,
            "sha256": sha256_file(assembly_paths[1]),
            "size_bytes": assembly_paths[1].stat().st_size,
        },
    }
    write_json(receipts / "install-only-reproducibility.json", reproducibility)
    if not reproducibility["pass"]:
        print(json.dumps({"pass": False, "stage": "reproducibility", "detail": reproducibility}, indent=2))
        return 1

    final_artifact = artifacts / assembly_paths[0].name
    shutil.copyfile(assembly_paths[0], final_artifact)

    verify_row = run(
        [
            str(CLI),
            "verify-install-only",
            str(final_artifact),
            "--full-archive",
            str(full),
            "--zstd",
            args.zstd,
        ],
        timeout=3600,
    )
    write_json(receipts / "install-only-verification-command.json", verify_row)
    verification = parse_stdout_json(verify_row)
    write_json(receipts / "install-only-verification.json", verification)

    qualification_path = receipts / "install-only-target-qualification.json"
    qualify_row = run(
        [
            str(CLI),
            "qualify-install-only",
            str(final_artifact),
            "--output",
            str(qualification_path),
            "--pkg-config",
            args.pkg_config,
        ],
        timeout=3600,
    )
    write_json(receipts / "install-only-target-qualification-command.json", qualify_row)
    qualification = (
        json.loads(qualification_path.read_text(encoding="utf-8"))
        if qualification_path.is_file()
        else parse_stdout_json(qualify_row)
    )
    if not qualification_path.is_file():
        write_json(qualification_path, qualification)

    artifact_files = sorted(path.name for path in artifacts.iterdir())
    gates = {
        "accepted_full_identity": full_identity_pass,
        "full_authority": authority.get("pass") is True,
        "assembly_1": assembly_rows[0]["returncode"] == 0,
        "assembly_2": assembly_rows[1]["returncode"] == 0,
        "byte_reproducible": reproducibility["pass"] is True and reproducibility["first"] == reproducibility["second"],
        "exact_full_projection": verify_row["returncode"] == 0 and verification.get("pass") is True,
        "android_target_qualification": qualify_row["returncode"] == 0 and qualification.get("pass") is True,
        "one_install_only_artifact": artifact_files == [final_artifact.name],
        "no_stripped_artifact": not any("stripped" in name for name in artifact_files),
    }
    failed = sorted(name for name, value in gates.items() if value is not True)
    summary = {
        "schema_version": 1,
        "gate_kind": "epoch3-upstream-thin-first-real-install-only-candidate",
        "pass": not failed,
        "gates": dict(sorted(gates.items())),
        "failed_gates": failed,
        "source_full": observed_full,
        "artifact": {
            "path": f"artifacts/{final_artifact.name}",
            "filename": final_artifact.name,
            "sha256": sha256_file(final_artifact),
            "size_bytes": final_artifact.stat().st_size,
            "projection_member_count": verification.get("artifact", {}).get("member_count"),
        },
        "projection": {
            "source": "python/install/**",
            "target": "python/**",
            "filtering": "none-preserve-all-install-members",
            "payload_bytes_unchanged": verification.get("checks", {}).get("payload_bytes_unchanged") is True,
        },
        "claim_boundary": {
            "install_only_candidate_qualified": not failed,
            "install_only_authority_frozen": False,
            "stripped_implementation_started": False,
            "selectable": False,
            "publication": False,
            "api24_runtime_claim": False,
            "actual_16k_runtime_claim": False,
            "non_termux_context_claim": False,
        },
    }
    write_json(receipts / "gate-diagnostics.json", summary)
    write_json(output / "result-summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
