#!/usr/bin/env python3
"""Derive and qualify canonical install_only_stripped from accepted install_only."""
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

INSTALL_LOCK = ROOT / "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-install-only-r1.lock.json"
INSTALL_AUTHORITY_VERIFIER = ROOT / "experiments/epoch3-upstream-thin-install-only/verify_install_only_authority.py"
CLI = ROOT / "components/upstream-thin/bin/cpython-android-upstream-thin"
EXPECTED_CHANGED_PATHS = ["bin/python3.14"]
EXPECTED_REGULAR_ELF_COUNT = 81


def run(command: list[str], *, timeout: int = 3600) -> dict[str, Any]:
    try:
        process = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "command": command,
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
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
    try:
        value = json.loads(row.get("stdout", ""))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def artifact_identity(path: Path) -> dict[str, Any]:
    return {"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-only-archive", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--strip-tool", required=True)
    parser.add_argument("--readelf", required=True)
    parser.add_argument("--pkg-config", required=True)
    args = parser.parse_args()

    source = Path(args.install_only_archive).resolve()
    output = Path(args.output_dir).resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    receipts = output / "receipts"
    artifacts = output / "artifacts"
    receipts.mkdir()
    artifacts.mkdir()

    lock = json.loads(INSTALL_LOCK.read_text(encoding="utf-8"))
    expected_source = lock["artifact"]
    observed_source = artifact_identity(source)
    identity_keys = ("filename", "sha256", "size_bytes")
    source_identity_pass = all(observed_source[key] == expected_source[key] for key in identity_keys)
    write_json(
        receipts / "install-only-input-identity.json",
        {
            "schema_version": 1,
            "pass": source_identity_pass,
            "expected": {key: expected_source[key] for key in identity_keys},
            "observed": observed_source,
        },
    )
    if not source_identity_pass:
        print(json.dumps({"pass": False, "stage": "install-only-input-identity", "observed": observed_source}, indent=2))
        return 1

    authority_row = run([sys.executable, str(INSTALL_AUTHORITY_VERIFIER), "--root", str(ROOT)])
    write_json(receipts / "install-only-authority-verification-command.json", authority_row)
    authority = parse_stdout_json(authority_row)
    write_json(receipts / "install-only-authority-verification.json", authority)
    if authority_row["returncode"] != 0 or authority.get("pass") is not True:
        print(json.dumps({"pass": False, "stage": "install-only-authority", "detail": authority_row}, indent=2))
        return 1

    assembly_paths: list[Path] = []
    assembly_receipts: list[dict[str, Any]] = []
    assembly_rows: list[dict[str, Any]] = []
    for index in (1, 2):
        destination = output / f"assembly-{index}"
        row = run(
            [
                str(CLI),
                "assemble-stripped",
                "--install-only-archive",
                str(source),
                "--output-dir",
                str(destination),
                "--strip-tool",
                args.strip_tool,
                "--readelf",
                args.readelf,
            ],
            timeout=3600,
        )
        assembly_rows.append(row)
        write_json(receipts / f"assembly-{index}-command.json", row)
        parsed = parse_stdout_json(row)
        assembly_receipts.append(parsed)
        write_json(receipts / f"assembly-{index}-receipt.json", parsed)
        matches = sorted(destination.glob("*-install_only_stripped.tar.gz"))
        if row["returncode"] != 0 or len(matches) != 1 or parsed.get("decision") != "distinct-archive":
            print(
                json.dumps(
                    {
                        "pass": False,
                        "stage": f"assembly-{index}",
                        "detail": row,
                        "decision": parsed.get("decision"),
                        "matches": [str(path) for path in matches],
                    },
                    indent=2,
                )
            )
            return 1
        assembly_paths.append(matches[0])

    reproducibility = {
        "schema_version": 1,
        "pass": filecmp.cmp(assembly_paths[0], assembly_paths[1], shallow=False),
        "first": artifact_identity(assembly_paths[0]),
        "second": artifact_identity(assembly_paths[1]),
        "first_changed_paths": assembly_receipts[0].get("changed_paths"),
        "second_changed_paths": assembly_receipts[1].get("changed_paths"),
    }
    write_json(receipts / "stripped-reproducibility.json", reproducibility)
    if not reproducibility["pass"] or reproducibility["first"] != reproducibility["second"]:
        print(json.dumps({"pass": False, "stage": "reproducibility", "detail": reproducibility}, indent=2))
        return 1

    final_artifact = artifacts / assembly_paths[0].name
    shutil.copyfile(assembly_paths[0], final_artifact)
    mutation_receipt = receipts / "stripped-mutation-receipt.json"
    write_json(mutation_receipt, assembly_receipts[0])

    verify_row = run(
        [
            str(CLI),
            "verify-stripped",
            str(final_artifact),
            "--install-only-archive",
            str(source),
            "--mutation-receipt",
            str(mutation_receipt),
            "--readelf",
            args.readelf,
        ],
        timeout=3600,
    )
    write_json(receipts / "stripped-verification-command.json", verify_row)
    verification = parse_stdout_json(verify_row)
    write_json(receipts / "stripped-verification.json", verification)

    qualification_path = receipts / "stripped-target-qualification.json"
    qualify_row = run(
        [
            str(CLI),
            "qualify-stripped",
            str(final_artifact),
            "--output",
            str(qualification_path),
            "--pkg-config",
            args.pkg_config,
        ],
        timeout=3600,
    )
    write_json(receipts / "stripped-target-qualification-command.json", qualify_row)
    qualification = (
        json.loads(qualification_path.read_text(encoding="utf-8"))
        if qualification_path.is_file()
        else parse_stdout_json(qualify_row)
    )
    if not qualification_path.is_file():
        write_json(qualification_path, qualification)

    receipt = assembly_receipts[0]
    artifact_files = sorted(path.name for path in artifacts.iterdir())
    gates = {
        "accepted_install_only_identity": source_identity_pass,
        "install_only_authority": authority.get("pass") is True,
        "assembly_1": assembly_rows[0]["returncode"] == 0,
        "assembly_2": assembly_rows[1]["returncode"] == 0,
        "distinct_archive_decision": all(row.get("decision") == "distinct-archive" for row in assembly_receipts),
        "byte_reproducible": reproducibility["pass"] is True and reproducibility["first"] == reproducibility["second"],
        "regular_elf_count_81": receipt.get("regular_elf_count") == EXPECTED_REGULAR_ELF_COUNT,
        "eligible_elf_count_1": receipt.get("eligible_elf_count") == 1,
        "changed_elf_count_1": receipt.get("changed_elf_count") == 1,
        "only_project_launcher_changed": receipt.get("eligible_paths") == EXPECTED_CHANGED_PATHS and receipt.get("changed_paths") == EXPECTED_CHANGED_PATHS,
        "exact_stripped_derivation": verify_row["returncode"] == 0 and verification.get("pass") is True,
        "non_elf_bytes_unchanged": verification.get("checks", {}).get("non_elf_bytes_unchanged") is True,
        "elf_dynamic_alignment_preserved": verification.get("checks", {}).get("elf_dynamic_alignment_preserved") is True,
        "android_target_qualification": qualify_row["returncode"] == 0 and qualification.get("pass") is True,
        "one_stripped_artifact": artifact_files == [final_artifact.name],
    }
    failed = sorted(name for name, value in gates.items() if value is not True)
    summary = {
        "schema_version": 1,
        "gate_kind": "epoch3-upstream-thin-first-real-install-only-stripped-candidate",
        "pass": not failed,
        "gates": dict(sorted(gates.items())),
        "failed_gates": failed,
        "source_install_only": observed_source,
        "artifact": {
            "path": f"artifacts/{final_artifact.name}",
            **artifact_identity(final_artifact),
            "member_count": verification.get("artifact", {}).get("member_count"),
        },
        "strip_surface": {
            "operation": "--strip-unneeded",
            "regular_elf_count": receipt.get("regular_elf_count"),
            "eligible_elf_count": receipt.get("eligible_elf_count"),
            "changed_elf_count": receipt.get("changed_elf_count"),
            "eligible_paths": receipt.get("eligible_paths"),
            "changed_paths": receipt.get("changed_paths"),
            "strip_tool": receipt.get("strip_tool"),
            "readelf_tool": receipt.get("readelf_tool"),
        },
        "claim_boundary": {
            "stripped_candidate_qualified": not failed,
            "stripped_authority_frozen": False,
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
