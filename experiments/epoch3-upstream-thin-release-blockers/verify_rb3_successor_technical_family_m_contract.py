#!/usr/bin/env python3
"""Verify the frozen successor technical-family r1 execution contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_ARTIFACTS = {
    "full": ("b13206f67d900c1954ee6720c1b3d9337c467c9008b93a0384c16fb6127260d2", 39414556, 3752),
    "install_only": ("c904a4d1da527e512c715a3227c62da99728ec62747487795292320cee71ab56", 23843355, 3699),
    "install_only_stripped": ("9cffe27e4e7e6b82d3bace2ea4ce56473abae683bad041d38106ec481b83d9e5", 23842721, 3699),
}
EXPECTED_RESULTS = {
    "full": ("0bf2f2ff4e180206f0b6b59f4e6ff2368fea326d1d64efb5ddd23e5d0db7cc0d", 63029723),
    "install_only": ("d8f4d13c34d1ce3eae3ba5ca8002fbc9a357941aa2b46c16fedc032d82b975be", 47232364),
    "install_only_stripped": ("db5ff3a3f9a5a8de4731ae5e5cebad7739bcf0330f12de01bdecb01528acd1d7", 47423566),
    "stripped_acceptance": ("742c316a3dd9c428fb201e54d3cb8c29280cbd1ed8d491afa367636852672b14", 10309),
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path) -> dict[str, Any]:
    base = root / "experiments/epoch3-upstream-thin-release-blockers"
    contract_path = base / "rb3-successor-technical-family-m-r1-execution-contract.json"
    contract = load(contract_path)
    authorization = load(base / "rb3-successor-technical-family-m-contract.json")
    stripped_authority = load(base / "rb3-successor-stripped-m-authority.json")
    inspection = load(base / "rb3-successor-stripped-m-acceptance-r1-return-inspection.json")
    checks = {
        "contract_kind": contract.get("contract_kind") == "epoch3-rb3-profile-M-successor-technical-family-r1-execution",
        "status": contract.get("status") == "active-owner-assembly-pending",
        "authorization_contract": contract.get("authorization", {}).get("sha256") == sha(base / "rb3-successor-technical-family-m-contract.json")
        and authorization.get("status") == "authorized-pending-owner-assembly-after-stripped-acceptance",
        "stripped_authority": contract.get("authorization", {}).get("stripped_authority_sha256") == sha(base / "rb3-successor-stripped-m-authority.json")
        and stripped_authority.get("claim_boundary", {}).get("successor_technical_family_authorized") is True,
        "acceptance_inspection": contract.get("authorization", {}).get("acceptance_return_inspection_sha256") == sha(base / "rb3-successor-stripped-m-acceptance-r1-return-inspection.json")
        and inspection.get("status") == "accepted-complete-pass-technical-family-owner-assembly-authorized",
        "four_result_archives": all(
            contract.get("required_result_archives", {}).get(key, {}).get("sha256") == expected[0]
            and contract.get("required_result_archives", {}).get(key, {}).get("size_bytes") == expected[1]
            for key, expected in EXPECTED_RESULTS.items()
        ),
        "three_accepted_artifacts": all(
            contract.get("accepted_artifacts", {}).get(key, {}).get("sha256") == expected[0]
            and contract.get("accepted_artifacts", {}).get(key, {}).get("size_bytes") == expected[1]
            and contract.get("accepted_artifacts", {}).get(key, {}).get("member_count") == expected[2]
            for key, expected in EXPECTED_ARTIFACTS.items()
        ),
        "candidate_shape": contract.get("candidate", {}).get("release_id") == "cpython-3.14.6+e3-r2-aarch64-linux-android"
        and contract.get("candidate", {}).get("file_count") == 23,
        "implementation_files": bool(contract.get("implementation_files")) and all(
            (root / rel).is_file() and sha(root / rel) == digest
            for rel, digest in contract.get("implementation_files", {}).items()
        ),
        "protected_files": bool(contract.get("protected_files")) and all(
            (root / rel).is_file() and sha(root / rel) == digest
            for rel, digest in contract.get("protected_files", {}).items()
        ),
        "execution_complete": len(contract.get("required_execution", [])) == 6,
        "forbidden_complete": len(contract.get("forbidden", [])) == 7,
        "success_boundary": contract.get("success_boundary") == {
            "legal_family_integration_started": False,
            "predecessor_family_superseded": False,
            "publication": False,
            "rb1_rebound": False,
            "rb2_rebound": False,
            "rb3_closed": False,
            "selectable": False,
            "successor_full_accepted": True,
            "successor_install_only_accepted": True,
            "successor_stripped_accepted": True,
            "successor_technical_family_accepted": False,
            "successor_technical_family_candidate": True,
            "successor_technical_family_started": True,
        },
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-rb3-successor-technical-family-r1-execution-contract",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "contract_sha256": sha(contract_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        result = verify(args.root.resolve())
    except Exception as exc:  # noqa: BLE001
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
