#!/usr/bin/env python3
"""Verify the frozen RB-3 profile-M successor-full r5 acceptance authority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/epoch3-upstream-thin-release-blockers"
AUTHORITY = BASE / "rb3-successor-full-m-authority.json"
ACCEPTED = BASE / "accepted-rb3-successor-full-m-r4-return.json"
EVIDENCE = BASE / "rb3-successor-full-m-authority-evidence"
NEXT_CONTRACT = BASE / "rb3-successor-family-derivation-contract.json"
EXPECTED_RESULT_SHA = "0bf2f2ff4e180206f0b6b59f4e6ff2368fea326d1d64efb5ddd23e5d0db7cc0d"
EXPECTED_CANDIDATE_SHA = "b13206f67d900c1954ee6720c1b3d9337c467c9008b93a0384c16fb6127260d2"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path = ROOT) -> dict[str, Any]:
    base = root / "experiments/epoch3-upstream-thin-release-blockers"
    authority = load(base / AUTHORITY.name)
    accepted = load(base / ACCEPTED.name)
    evidence = base / EVIDENCE.name
    next_contract = load(base / NEXT_CONTRACT.name)
    external = load(evidence / "external-acceptance-audit.json")
    owner = load(evidence / "owner-result.json")
    owner_summary = load(evidence / "owner-summary.json")
    owner_audit = load(evidence / "owner-independent-audit.json")
    repro = load(evidence / "reproducibility.json")
    structural = load(evidence / "full-structural-verification.json")
    android = load(evidence / "full-android-qualification.json")
    direct = load(evidence / "native-wheel-elf-boundary.json")
    managed = load(evidence / "native-managed-wheel-elf-boundary.json")
    protected = load(evidence / "protected-state.json")
    index = load(evidence / "result-index.json")

    identities = authority.get("file_identities", {})
    identity_checks = {
        rel: (root / rel).is_file() and sha256_file(root / rel) == expected
        for rel, expected in identities.items()
    }
    accepted_candidate = accepted.get("candidate_full", {})
    authority_candidate = authority.get("accepted_full", {})
    checks = {
        "authority_kind": authority.get("authority_kind")
        == "epoch3-rb3-profile-M-successor-full-r5",
        "file_identities": bool(identity_checks) and all(identity_checks.values()),
        "accepted_return_status": accepted.get("status")
        == "accepted-pass-successor-full-r5-authorized-family-derivation-pending",
        "result_identity": accepted.get("result_archive", {}).get("sha256")
        == authority.get("accepted_evidence", {}).get("result_archive_sha256")
        == EXPECTED_RESULT_SHA
        and accepted.get("result_archive", {}).get("size_bytes") == 63029723
        and accepted.get("result_archive", {}).get("self_index_file_count") == 77,
        "self_index_count": len(index.get("files", [])) == 77,
        "candidate_identity": all(
            accepted_candidate.get(key) == authority_candidate.get(key)
            for key in ("filename", "sha256", "size_bytes")
        )
        and accepted_candidate.get("sha256") == EXPECTED_CANDIDATE_SHA
        and accepted_candidate.get("size_bytes") == 39414556,
        "external_audit": external.get("pass") is True
        and not external.get("failed_checks")
        and external.get("result_archive", {}).get("sha256") == EXPECTED_RESULT_SHA
        and external.get("candidate_full", {}).get("sha256") == EXPECTED_CANDIDATE_SHA,
        "owner_result": owner.get("pass") is True
        and not owner.get("failed_checks")
        and bool(owner.get("checks"))
        and all(value is True for value in owner["checks"].values()),
        "owner_summary": owner_summary.get("claim_transaction_rc") == 0
        and owner_summary.get("failure_reason") == "none"
        and owner_summary.get("claim_boundary", {}).get("successor_full_candidate") is True
        and owner_summary.get("claim_boundary", {}).get("successor_full_accepted") is False,
        "owner_audit": owner_audit.get("pass") is True
        and not owner_audit.get("failed_checks"),
        "reproducibility": repro.get("pass") is True
        and repro.get("byte_identical") is True
        and repro.get("assembly_a", {}).get("sha256") == EXPECTED_CANDIDATE_SHA
        and repro.get("assembly_b", {}).get("sha256") == EXPECTED_CANDIDATE_SHA,
        "structural": structural.get("pass") is True and not structural.get("failed_checks"),
        "android": android.get("pass") is True and not android.get("failed_checks"),
        "direct_sdk": direct.get("pass") is True
        and direct.get("wheel_import_returncode") == 0
        and direct.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "managed_sdk": managed.get("pass") is True
        and managed.get("wheel_import_returncode") == 0
        and managed.get("raw_extension", {}).get("all_load_alignments_16k") is True,
        "wheel_repair_boundary": direct.get("raw_policy_clean") is False
        and managed.get("raw_policy_clean") is False
        and direct.get("postprocessing_boundary")
        == managed.get("postprocessing_boundary")
        == "out-of-scope-external-tool-responsibility",
        "protected_state": all(
            protected.get(key) is True
            for key in (
                "candidate_full_unchanged",
                "predecessor_full_unchanged",
                "real_managed_root_unchanged",
            )
        ),
        "acceptance_boundary": accepted.get("claim_boundary", {}).get("successor_full_accepted")
        is True
        and accepted.get("claim_boundary", {}).get("successor_install_only_authorized")
        is True
        and accepted.get("claim_boundary", {}).get("successor_install_only_started")
        is False
        and accepted.get("claim_boundary", {}).get("artifact_family_superseded")
        is False
        and accepted.get("claim_boundary", {}).get("rb3_closed") is False
        and accepted.get("claim_boundary", {}).get("selectable") is False
        and accepted.get("claim_boundary", {}).get("publication") is False,
        "authority_boundary": authority.get("claim_boundary")
        == {
            "artifact_family_superseded": False,
            "canonical_predecessor_family_unchanged": True,
            "portable_raw_wheel_claim": False,
            "publication": False,
            "rb3_closed": False,
            "selectable": False,
            "successor_full_accepted": True,
            "successor_full_candidate": True,
            "successor_install_only_authorized": True,
            "successor_install_only_started": False,
            "user_built_wheel_postprocessing": "out-of-scope-external-tool-responsibility",
        },
        "next_contract": next_contract.get("contract_kind")
        == "epoch3-rb3-successor-profile-M-family-derivation"
        and next_contract.get("exact_input", {}).get("full", {}).get("sha256")
        == EXPECTED_CANDIDATE_SHA
        and next_contract.get("claim_boundary", {}).get("predecessor_family_superseded")
        is False
        and next_contract.get("claim_boundary", {}).get("rb3_closed") is False,
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-rb3-profile-M-successor-full-r5-acceptance",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "identity_checks": dict(sorted(identity_checks.items())),
    }


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
