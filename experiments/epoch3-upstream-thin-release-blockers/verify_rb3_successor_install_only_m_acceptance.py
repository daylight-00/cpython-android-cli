#!/usr/bin/env python3
"""Verify the frozen RB-3 profile-M successor install-only r5 acceptance authority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE_NAME = "experiments/epoch3-upstream-thin-release-blockers"
EXPECTED_RESULT_SHA = "d8f4d13c34d1ce3eae3ba5ca8002fbc9a357941aa2b46c16fedc032d82b975be"
EXPECTED_CANDIDATE_SHA = "c904a4d1da527e512c715a3227c62da99728ec62747487795292320cee71ab56"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path = ROOT) -> dict[str, Any]:
    base = root / BASE_NAME
    authority = load(base / "rb3-successor-install-only-m-authority.json")
    accepted = load(base / "accepted-rb3-successor-install-only-m-r2-return.json")
    inspection = load(base / "rb3-successor-install-only-m-r2-return-inspection.json")
    evidence = base / "rb3-successor-install-only-m-authority-evidence"
    next_contract = load(base / "rb3-successor-stripped-m-contract.json")
    external = load(evidence / "external-acceptance-audit.json")
    owner = load(evidence / "owner-result.json")
    summary = load(evidence / "owner-summary.json")
    owner_audit = load(evidence / "owner-independent-audit.json")
    repro = load(evidence / "reproducibility.json")
    projection = load(evidence / "install-only-verification.json")
    android = load(evidence / "install-only-android-qualification.json")
    direct = load(evidence / "native-wheel-elf-boundary.json")
    managed = load(evidence / "native-managed-wheel-elf-boundary.json")
    protected = load(evidence / "protected-state.json")
    index = load(evidence / "result-index.json")

    identities = authority.get("file_identities", {})
    identity_checks = {
        rel: (root / rel).is_file() and sha256_file(root / rel) == expected
        for rel, expected in identities.items()
    }
    accepted_candidate = accepted.get("candidate_install_only", {})
    authority_candidate = authority.get("accepted_install_only", {})
    expected_boundary = {
        "artifact_family_superseded": False,
        "canonical_predecessor_family_unchanged": True,
        "portable_raw_wheel_claim": False,
        "publication": False,
        "rb3_closed": False,
        "selectable": False,
        "successor_full_accepted": True,
        "successor_install_only_accepted": True,
        "successor_install_only_candidate": True,
        "successor_stripped_authorized": True,
        "successor_stripped_started": False,
        "successor_technical_family_accepted": False,
        "user_built_wheel_postprocessing": "out-of-scope-external-tool-responsibility",
    }
    checks = {
        "authority_kind": authority.get("authority_kind") == "epoch3-rb3-profile-M-successor-install-only-r5",
        "file_identities": bool(identity_checks) and all(identity_checks.values()),
        "accepted_return_status": accepted.get("status") == "accepted-pass-successor-install-only-r5-authorized-stripped-derivation-pending",
        "inspection_status": inspection.get("status") == "accepted-complete-pass-candidate-ready-for-bounded-acceptance",
        "result_identity": accepted.get("result_archive", {}).get("sha256")
        == authority.get("accepted_evidence", {}).get("result_archive_sha256")
        == inspection.get("result_archive", {}).get("sha256")
        == EXPECTED_RESULT_SHA
        and accepted.get("result_archive", {}).get("size_bytes") == 47232364
        and accepted.get("result_archive", {}).get("self_index_file_count") == 72,
        "self_index_count": len(index.get("files", [])) == 72,
        "candidate_identity": all(
            accepted_candidate.get(key) == authority_candidate.get(key)
            for key in ("filename", "sha256", "size_bytes", "member_count")
        )
        and accepted_candidate.get("sha256") == EXPECTED_CANDIDATE_SHA
        and accepted_candidate.get("size_bytes") == 23843355
        and accepted_candidate.get("member_count") == 3699,
        "external_audit": external.get("pass") is True
        and not external.get("failed_checks")
        and external.get("result_archive", {}).get("sha256") == EXPECTED_RESULT_SHA
        and external.get("candidate_install_only", {}).get("sha256") == EXPECTED_CANDIDATE_SHA,
        "owner_result": owner.get("pass") is True
        and not owner.get("failed_checks")
        and bool(owner.get("checks"))
        and all(value is True for value in owner["checks"].values()),
        "owner_summary": summary.get("claim_transaction_rc") == 0
        and summary.get("failure_reason") == "none"
        and summary.get("claim_boundary", {}).get("successor_install_only_candidate") is True
        and summary.get("claim_boundary", {}).get("successor_install_only_accepted") is False,
        "owner_audit": owner_audit.get("pass") is True
        and not owner_audit.get("failed_checks")
        and bool(owner_audit.get("checks"))
        and all(value is True for value in owner_audit["checks"].values()),
        "reproducibility": repro.get("pass") is True
        and repro.get("byte_identical") is True
        and repro.get("first", {}).get("sha256") == EXPECTED_CANDIDATE_SHA
        and repro.get("second", {}).get("sha256") == EXPECTED_CANDIDATE_SHA,
        "projection": projection.get("pass") is True
        and not projection.get("failed_checks")
        and projection.get("artifact", {}).get("sha256") == EXPECTED_CANDIDATE_SHA,
        "android": android.get("pass") is True
        and not android.get("failed_checks")
        and bool(android.get("checks"))
        and all(value is True for value in android["checks"].values()),
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
                "accepted_full_unchanged",
                "predecessor_install_only_unchanged",
                "real_managed_root_unchanged",
            )
        ),
        "acceptance_boundary": accepted.get("claim_boundary") == expected_boundary,
        "authority_boundary": authority.get("claim_boundary") == expected_boundary,
        "next_contract": next_contract.get("contract_kind") == "epoch3-rb3-profile-M-successor-install-only-stripped-derivation"
        and next_contract.get("accepted_input", {}).get("sha256") == EXPECTED_CANDIDATE_SHA
        and next_contract.get("success_boundary", {}).get("successor_stripped_candidate") is True
        and next_contract.get("success_boundary", {}).get("predecessor_family_superseded") is False
        and next_contract.get("success_boundary", {}).get("rb3_closed") is False,
    }
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-rb3-profile-M-successor-install-only-r5-acceptance",
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
