#!/usr/bin/env python3
"""Assemble and verify the profile-M successor technical-family candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
import sys
sys.path.insert(0, str(LIB))

from archive import canonical_json_bytes, sha256_file, write_json  # noqa: E402
from successor_release_family import (  # noqa: E402
    AUTHORIZATION_CONTRACT,
    EXECUTION_CONTRACT,
    FLAVORS,
    PREDECESSOR_AUTHORITY,
    RELEASE_ID,
    assemble_successor_release_family,
    expected_family,
    verify_successor_release_family,
)

PREDECESSOR_LOCK = "config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-artifact-family-r1.lock.json"
SUCCESSOR_AUTHORITIES = (
    "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-authority.json",
    "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-authority.json",
    "experiments/epoch3-upstream-thin-release-blockers/rb3-successor-stripped-m-authority.json",
)


def identity(path: Path) -> dict[str, Any]:
    return {"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def inventory(directory: Path) -> list[dict[str, Any]]:
    return [
        {"path": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        for path in sorted(directory.iterdir(), key=lambda item: item.name)
        if path.is_file()
    ]


def protected_state(root: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for rel in (PREDECESSOR_AUTHORITY, PREDECESSOR_LOCK, AUTHORIZATION_CONTRACT, EXECUTION_CONTRACT, *SUCCESSOR_AUTHORITIES):
        path = root / rel
        rows[rel] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", type=Path, required=True)
    parser.add_argument("--install-only", type=Path, required=True)
    parser.add_argument("--stripped", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zstd", default="zstd")
    args = parser.parse_args()

    output = args.output_dir.resolve()
    if output.exists():
        shutil.rmtree(output)
    receipts = output / "receipts"
    artifacts = output / "artifacts"
    receipts.mkdir(parents=True)
    artifacts.mkdir(parents=True)

    expected = expected_family(ROOT)
    inputs = {
        "full": args.full.resolve(),
        "install_only": args.install_only.resolve(),
        "install_only_stripped": args.stripped.resolve(),
    }
    observed_inputs = {flavor: identity(path) for flavor, path in inputs.items()}
    input_checks = {
        flavor: all(observed_inputs[flavor].get(key) == expected[flavor].get(key) for key in ("filename", "sha256", "size_bytes"))
        for flavor in FLAVORS
    }
    write_json(
        receipts / "input-identities.json",
        {
            "schema_version": 1,
            "receipt_kind": "epoch3-rb3-successor-technical-family-input-identities",
            "pass": all(input_checks.values()),
            "checks": input_checks,
            "observed": observed_inputs,
            "expected": expected,
        },
    )
    before = protected_state(ROOT)

    with tempfile.TemporaryDirectory(prefix="rb3-successor-family-") as temporary:
        temporary_root = Path(temporary)
        assembly_a = temporary_root / "assembly-a" / RELEASE_ID
        assembly_b = temporary_root / "assembly-b" / RELEASE_ID
        receipt_a = assemble_successor_release_family(
            inputs["full"], inputs["install_only"], inputs["install_only_stripped"],
            assembly_a, root=ROOT, expected=expected, zstd=args.zstd,
        )
        receipt_b = assemble_successor_release_family(
            inputs["full"], inputs["install_only"], inputs["install_only_stripped"],
            assembly_b, root=ROOT, expected=expected, zstd=args.zstd,
        )
        inventory_a = inventory(assembly_a)
        inventory_b = inventory(assembly_b)
        names_equal = [row["path"] for row in inventory_a] == [row["path"] for row in inventory_b]
        byte_equal = names_equal and all(
            (assembly_a / row["path"]).read_bytes() == (assembly_b / row["path"]).read_bytes()
            for row in inventory_a
        )
        reproducibility = {
            "schema_version": 1,
            "receipt_kind": "epoch3-rb3-successor-technical-family-reproducibility",
            "pass": inventory_a == inventory_b and byte_equal,
            "inventory_byte_identical": inventory_a == inventory_b,
            "all_files_byte_identical": byte_equal,
            "first": {
                "inventory": inventory_a,
                "fingerprint_sha256": hashlib.sha256(canonical_json_bytes(inventory_a)).hexdigest(),
                "assembly": receipt_a,
            },
            "second": {
                "inventory": inventory_b,
                "fingerprint_sha256": hashlib.sha256(canonical_json_bytes(inventory_b)).hexdigest(),
                "assembly": receipt_b,
            },
        }
        write_json(receipts / "technical-family-reproducibility.json", reproducibility)
        verify_a = verify_successor_release_family(assembly_a, root=ROOT, expected=expected, zstd=args.zstd)
        verify_b = verify_successor_release_family(assembly_b, root=ROOT, expected=expected, zstd=args.zstd)
        write_json(receipts / "technical-family-verification-a.json", verify_a)
        write_json(receipts / "technical-family-verification-b.json", verify_b)
        final_family = artifacts / RELEASE_ID
        shutil.copytree(assembly_a, final_family)

    final_verification = verify_successor_release_family(final_family, root=ROOT, expected=expected, zstd=args.zstd)
    write_json(receipts / "technical-family-verification.json", final_verification)
    after = protected_state(ROOT)
    predecessor = {
        "schema_version": 1,
        "receipt_kind": "epoch3-rb3-successor-technical-family-protected-state",
        "pass": before == after,
        "before": before,
        "after": after,
        "predecessor_family_unchanged": before.get(PREDECESSOR_AUTHORITY) == after.get(PREDECESSOR_AUTHORITY)
        and before.get(PREDECESSOR_LOCK) == after.get(PREDECESSOR_LOCK),
        "successor_authorities_unchanged": all(before.get(rel) == after.get(rel) for rel in SUCCESSOR_AUTHORITIES),
        "contracts_unchanged": before.get(AUTHORIZATION_CONTRACT) == after.get(AUTHORIZATION_CONTRACT)
        and before.get(EXECUTION_CONTRACT) == after.get(EXECUTION_CONTRACT),
    }
    write_json(receipts / "protected-state.json", predecessor)

    artifact_identity_checks = all(
        (final_family / row["filename"]).is_file()
        and sha256_file(final_family / row["filename"]) == row["sha256"]
        and (final_family / row["filename"]).stat().st_size == row["size_bytes"]
        for row in expected.values()
    )
    checks = {
        "exact_accepted_inputs": all(input_checks.values()),
        "assembly_a_pass": receipt_a.get("pass") is True,
        "assembly_b_pass": receipt_b.get("pass") is True,
        "two_assemblies_byte_identical": reproducibility.get("pass") is True,
        "verification_a_pass": verify_a.get("pass") is True,
        "verification_b_pass": verify_b.get("pass") is True,
        "final_verification_pass": final_verification.get("pass") is True,
        "exact_23_file_family": final_verification.get("file_count") == 23,
        "accepted_artifact_bytes_reused": artifact_identity_checks,
        "protected_state_unchanged": predecessor.get("pass") is True,
        "predecessor_family_unchanged": predecessor.get("predecessor_family_unchanged") is True,
        "successor_authorities_unchanged": predecessor.get("successor_authorities_unchanged") is True,
        "candidate_boundary": final_verification.get("claim_boundary", {}).get("successor_technical_family_candidate") is True
        and final_verification.get("claim_boundary", {}).get("successor_technical_family_accepted") is False,
        "legal_integration_not_started": final_verification.get("claim_boundary", {}).get("legal_family_integration_started") is False,
        "predecessor_not_superseded": final_verification.get("claim_boundary", {}).get("predecessor_family_superseded") is False,
        "rb3_open": final_verification.get("claim_boundary", {}).get("rb3_closed") is False,
        "not_selectable_or_published": final_verification.get("claim_boundary", {}).get("selectable") is False
        and final_verification.get("claim_boundary", {}).get("publication") is False,
        "user_wheel_repair_out_of_scope": final_verification.get("claim_boundary", {}).get("portable_user_built_wheel_claim") is False
        and final_verification.get("claim_boundary", {}).get("user_built_wheel_repair") is False,
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    result = {
        "schema_version": 1,
        "result_kind": "epoch3-rb3-profile-M-successor-technical-family-candidate",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "release_family": {
            "release_id": RELEASE_ID,
            "directory": str(final_family),
            "file_count": final_verification.get("file_count"),
            "fingerprint_sha256": final_verification.get("fingerprint_sha256"),
            "release_sha256": final_verification.get("release_sha256"),
            "release_index": final_verification.get("release_index"),
            "checksums": final_verification.get("checksums"),
        },
        "inputs": observed_inputs,
        "claim_boundary": {
            "successor_full_accepted": True,
            "successor_install_only_accepted": True,
            "successor_stripped_accepted": True,
            "successor_technical_family_started": True,
            "successor_technical_family_candidate": True,
            "successor_technical_family_accepted": False,
            "legal_family_integration_started": False,
            "predecessor_family_superseded": False,
            "rb1_rebound": False,
            "rb2_rebound": False,
            "rb3_closed": False,
            "selectable": False,
            "publication": False,
            "portable_user_built_wheel_claim": False,
            "user_built_wheel_postprocessing": "out-of-scope-external-tool-responsibility",
        },
    }
    write_json(output / "rb3-successor-technical-family-m-result.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
