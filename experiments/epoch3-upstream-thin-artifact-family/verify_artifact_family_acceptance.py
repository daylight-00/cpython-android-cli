#!/usr/bin/env python3
"""Verify the accepted owner return for the canonical Epoch 3 artifact family."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE = Path("experiments/epoch3-upstream-thin-artifact-family")
EVIDENCE = BASE / "authority-evidence"
EXPECTED = {
    "result_archive": {
        "filename": "cpython-android-cli-e3-artifact-family-r1-results.tar.zst",
        "sha256": "1fc50a26840cd33d15ef53cd85674fd3cc4a46c96ea00657eef9f6f3fdb93ade",
        "size_bytes": 87506952,
    },
    "transition": {
        "pre_head": "bc7b655059c376f50f06c6c6171b508fbf2eb1a2",
        "pre_tree": "8d9a61713fb3de00e49d11b0a01fa314040e57a0",
        "post_head": "0b6146c01c4ca8c20f73cc1143e0a4a447fe351b",
        "post_tree": "ccbad2f55601718b1881c968d11c2fa9b823c5fb",
        "remote_post_head": "0b6146c01c4ca8c20f73cc1143e0a4a447fe351b",
    },
    "release_family": {
        "release_id": "cpython-3.14.6+e3-r1-aarch64-linux-android",
        "file_count": 23,
        "fingerprint_sha256": "87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302",
        "release_index_sha256": "b60274ac64b40c43fc174e4ea4a238743216452b5dfe8af300adde37c4fd7389",
        "release_sha256": "81bd66f5cd1978485eb50991d5a6e773b55b51defb52483db6db5215c1a91a9e",
        "sha256sums_sha256": "b47f399a48526e75aad98499aff841126986f8436702a7cd5c9cd25784ac6082",
    },
    "artifacts": {
        "full": {
            "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-full.tar.zst",
            "sha256": "20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12",
            "size_bytes": 39408292,
        },
        "install_only": {
            "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-install_only.tar.gz",
            "sha256": "84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76",
            "size_bytes": 23841726,
        },
        "install_only_stripped": {
            "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-install_only_stripped.tar.gz",
            "sha256": "40951002c5880b223fa78c7b956dfcf2929e3ebf8e8beb9420c4179b98231134",
            "size_bytes": 23841241,
        },
    },
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    errors: dict[str, str] = {}

    def read(label: str, rel: Path) -> dict[str, Any]:
        try:
            value = load(root / rel)
            checks[f"parse:{label}"] = True
            return value
        except Exception as exc:  # noqa: BLE001
            checks[f"parse:{label}"] = False
            errors[label] = f"{type(exc).__name__}: {exc}"
            return {}

    accepted = read("accepted-return", BASE / "accepted-r1-return.json")
    gate = read("gate-diagnostics", EVIDENCE / "gate-diagnostics.json")
    reproduction = read("artifact-family-reproducibility", EVIDENCE / "artifact-family-reproducibility.json")
    verification = read("artifact-family-verification", EVIDENCE / "artifact-family-verification.json")
    audit = read("independent-audit", EVIDENCE / "independent-audit.json")
    inputs = read("input-identities", EVIDENCE / "input-identities.json")
    summary = read("result-summary", EVIDENCE / "result-summary.json")
    lock = read("artifact-family-lock", Path("config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-artifact-family-r1.lock.json"))

    checks["accepted_action"] = accepted.get("action") == "applied-artifact-family-assembled-verified-audited-pushed" and accepted.get("transaction_rc") == 0
    checks["accepted_repository_transition"] = accepted.get("repository_transition") == EXPECTED["transition"]
    checks["accepted_result_archive"] = all(accepted.get("result_archive", {}).get(k) == v for k, v in EXPECTED["result_archive"].items())
    checks["accepted_release_family"] = accepted.get("release_family") == EXPECTED["release_family"]
    checks["accepted_artifacts"] = accepted.get("artifacts") == EXPECTED["artifacts"]

    checks["candidate_gate_pass"] = gate.get("pass") is True and gate.get("failed_gates") == [] and all(gate.get("gates", {}).values())
    checks["candidate_gate_identity"] = gate.get("release_family", {}).get("file_count") == 23 and gate.get("release_family", {}).get("fingerprint_sha256") == EXPECTED["release_family"]["fingerprint_sha256"] and gate.get("release_family", {}).get("release_index", {}).get("sha256") == EXPECTED["release_family"]["release_index_sha256"] and gate.get("release_family", {}).get("release_sha256") == EXPECTED["release_family"]["release_sha256"] and gate.get("release_family", {}).get("sha256sums", {}).get("sha256") == EXPECTED["release_family"]["sha256sums_sha256"]
    checks["candidate_inputs_exact"] = gate.get("inputs") == EXPECTED["artifacts"]

    checks["family_verification_pass"] = verification.get("pass") is True and verification.get("failed_checks") == [] and len(verification.get("checks", {})) == 12 and all(verification.get("checks", {}).values())
    checks["family_verification_identity"] = verification.get("release_index", {}).get("sha256") == EXPECTED["release_family"]["release_index_sha256"] and verification.get("release_sha256") == EXPECTED["release_family"]["release_sha256"]

    first = reproduction.get("first", {})
    second = reproduction.get("second", {})
    checks["family_reproducibility"] = reproduction.get("pass") is True and first == second and first.get("file_count") == 23 and first.get("fingerprint_sha256") == EXPECTED["release_family"]["fingerprint_sha256"]
    inventory = first.get("files", [])
    by_path = {row.get("path"): row for row in inventory if isinstance(row, dict)}
    checks["family_inventory_exact"] = len(by_path) == 23 and all(by_path.get(value["filename"], {}).get("sha256") == value["sha256"] and by_path.get(value["filename"], {}).get("size_bytes") == value["size_bytes"] for value in EXPECTED["artifacts"].values()) and by_path.get("release-index.json", {}).get("sha256") == EXPECTED["release_family"]["release_index_sha256"] and by_path.get("SHA256SUMS", {}).get("sha256") == EXPECTED["release_family"]["sha256sums_sha256"]

    checks["independent_audit_pass"] = audit.get("pass") is True and audit.get("failed_checks") == [] and len(audit.get("checks", {})) == 10 and all(audit.get("checks", {}).values()) and audit.get("independent_verification", {}).get("pass") is True
    checks["input_identity_receipt"] = inputs.get("pass") is True and all(inputs.get("checks", {}).values()) and inputs.get("observed") == EXPECTED["artifacts"]
    checks["result_summary_pass"] = summary.get("pass") is True and summary.get("release_family", {}).get("file_count") == 23 and summary.get("release_family", {}).get("fingerprint_sha256") == EXPECTED["release_family"]["fingerprint_sha256"]

    claim_docs = [accepted.get("claim_boundary", {}), gate.get("claim_boundary", {}), verification.get("claim_boundary", {}), audit.get("claim_boundary", {}), summary.get("claim_boundary", {})]
    checks["claims_bounded"] = all(doc.get("selectable") is False and doc.get("publication") is False and doc.get("component_license_mapping_complete") is False for doc in claim_docs) and all(doc.get("api24_runtime", doc.get("api24_runtime_claim", False)) is False for doc in claim_docs if "api24_runtime" in doc or "api24_runtime_claim" in doc) and all(doc.get("actual_16k_runtime", doc.get("actual_16k_runtime_claim", False)) is False for doc in claim_docs if "actual_16k_runtime" in doc or "actual_16k_runtime_claim" in doc)

    checks["lock_identity"] = lock.get("release_family") == EXPECTED["release_family"] and lock.get("artifacts") == EXPECTED["artifacts"] and lock.get("files") == inventory
    evidence_paths = [EVIDENCE / name for name in ("gate-diagnostics.json", "artifact-family-reproducibility.json", "artifact-family-verification.json", "independent-audit.json", "input-identities.json", "result-summary.json")]
    checks["evidence_present"] = all((root / path).is_file() for path in evidence_paths)

    failed = sorted(key for key, value in checks.items() if value is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-artifact-family-owner-return-acceptance",
        "pass": not failed and not errors,
        "check_count": len(checks),
        "pass_count": len(checks) - len(failed),
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "release_family": EXPECTED["release_family"],
        "artifacts": EXPECTED["artifacts"],
        "evidence_identities": {str(path): sha(root / path) for path in evidence_paths if (root / path).is_file()},
        "claim_boundary": {
            "artifact_family_complete": not failed and not errors,
            "artifact_family_authority_can_freeze": not failed and not errors,
            "component_license_mapping_complete": False,
            "api24_runtime": False,
            "actual_16k_runtime": False,
            "non_termux_context": False,
            "selectable": False,
            "publication": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    result = verify(Path(args.root).resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
