#!/usr/bin/env python3
"""Independently verify one E2-P3 archive-qualification profile result."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

RESULT_NAME = "qualification-result.json"
EXACT_RESULT_KEYS = {
    "schema_version", "qualification_kind", "contract_version", "profile",
    "artifact_id", "input", "host", "checks", "check_count", "pass_count",
    "failed_checks", "pass", "status", "selectable", "observations",
    "evidence", "claim_boundary",
}
CLAIM_BOUNDARY = {
    "combined_target_qualification": False,
    "installer_conversion": False,
    "metadata_finalization": False,
    "publication": False,
    "selectability": False,
    "transition_behavior": False,
}


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_canonical_json(path: Path, errors: dict[str, str]) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("top-level value is not an object")
        if raw != canonical_json_bytes(value):
            raise ValueError("JSON is not canonical UTF-8/indent/sort/newline form")
        return value
    except Exception as exc:  # fail-closed verifier
        errors[str(path)] = f"{type(exc).__name__}: {exc}"
        return {}


def exact_file_ref(ref: Any, path: Path) -> bool:
    return (
        isinstance(ref, dict)
        and set(ref) == {"filename", "sha256", "size"}
        and ref.get("filename") == path.name
        and path.is_file()
        and ref.get("sha256") == sha256_file(path)
        and ref.get("size") == path.stat().st_size
    )


def verify_result(root: Path, contract_path: Path, result_dir: Path) -> dict[str, Any]:
    root = root.resolve()
    contract_path = contract_path.resolve()
    result_dir = result_dir.resolve()
    errors: dict[str, str] = {}
    checks: dict[str, bool] = {}

    contract = read_canonical_json(contract_path, errors)
    result_path = result_dir / RESULT_NAME
    result = read_canonical_json(result_path, errors) if result_path.is_file() else {}

    def ck(name: str, value: Any) -> None:
        checks[name] = bool(value)

    profile = result.get("profile")
    expected_checks = contract.get("profile_checks", {}).get(profile, []) if isinstance(profile, str) else []
    expected_evidence = contract.get("profile_evidence", {}).get(profile, []) if isinstance(profile, str) else []
    artifact = contract.get("artifact", {})
    input_authority = contract.get("input_authority", {})
    profile_contract = contract.get("profiles", {}).get(profile, {}) if isinstance(profile, str) else {}

    ck("contract_identity", contract.get("schema_version") == 1 and contract.get("contract_version") == 1 and contract.get("qualification_kind") == "hw-t-standalone-archive-qualification")
    ck("result_present", result_path.is_file())
    ck("result_top_keys", set(result) == EXACT_RESULT_KEYS)
    ck("result_identity", result.get("schema_version") == 1 and result.get("qualification_kind") == "hw-t-standalone-archive-qualification-result" and result.get("contract_version") == 1)
    ck("profile_known", profile in {"static", "termux-real", "termux-emulator"} and bool(expected_checks))
    ck("artifact_identity", result.get("artifact_id") == artifact.get("artifact_id"))
    expected_input = {
        "archive_sha256": artifact.get("archive_sha256"),
        "execution_authority": input_authority.get("execution_authority"),
        "private_authority_index_sha256": input_authority.get("private_authority_index_sha256"),
        "release_index_sha256": artifact.get("release_index_sha256"),
    }
    ck("input_identity", result.get("input") == expected_input)
    result_checks = result.get("checks", {})
    ck("check_names_exact", isinstance(result_checks, dict) and list(result_checks) == sorted(expected_checks) and set(result_checks) == set(expected_checks))
    failed = sorted(name for name, passed in result_checks.items() if passed is not True) if isinstance(result_checks, dict) else []
    ck("check_accounting", result.get("check_count") == len(expected_checks) and result.get("pass_count") == len(expected_checks) - len(failed) and result.get("failed_checks") == failed)
    expected_pass = not failed and not errors
    ck("pass_semantics", result.get("pass") is expected_pass and result.get("status") == ("passed-individual-profile" if expected_pass else "failed"))
    ck("never_selectable", result.get("selectable") is False)
    ck("claim_boundary", result.get("claim_boundary") == CLAIM_BOUNDARY)

    host = result.get("host", {})
    ck("host_object", isinstance(host, dict) and host.get("host_role") == profile_contract.get("host_role"))
    if profile == "static":
        ck("host_profile", host.get("target_execution") is False and host.get("device_kind") == "not-applicable")
    elif profile == "termux-real":
        ck("host_profile", host.get("target_execution") is True and host.get("device_kind") == "real" and host.get("project_role") == "termux")
    elif profile == "termux-emulator":
        ck("host_profile", host.get("target_execution") is True and host.get("device_kind") == "emulator" and host.get("project_role") == "termux")
    else:
        ck("host_profile", False)

    evidence = result.get("evidence", {})
    ck("evidence_names_exact", isinstance(evidence, dict) and set(evidence) == set(expected_evidence))
    evidence_refs_ok = True
    canonical_evidence_ok = True
    if isinstance(evidence, dict):
        for name in expected_evidence:
            path = result_dir / "evidence" / name
            if not exact_file_ref(evidence.get(name), path):
                evidence_refs_ok = False
            if path.is_file():
                _ = read_canonical_json(path, errors)
                if str(path) in errors:
                    canonical_evidence_ok = False
            else:
                canonical_evidence_ok = False
    else:
        evidence_refs_ok = False
        canonical_evidence_ok = False
    ck("evidence_refs", evidence_refs_ok)
    ck("evidence_canonical", canonical_evidence_ok)
    ck("observations_object", isinstance(result.get("observations"), dict))
    ck("no_unexpected_files", result_dir.is_dir() and {p.relative_to(result_dir).as_posix() for p in result_dir.rglob("*") if p.is_file()} == {RESULT_NAME, *{f"evidence/{name}" for name in expected_evidence}})

    failed_verifier = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": 1,
        "verification_kind": "hw-t-e2p3-archive-qualification-result-v1",
        "pass": not failed_verifier and not errors,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "failed_checks": failed_verifier,
        "parse_errors": errors,
        "checks": dict(sorted(checks.items())),
        "profile": profile,
        "claim_boundary": "One profile result only; combined target qualification, metadata finalization, selectability, publication, installer conversion, and transitions remain unclaimed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    args = parser.parse_args()
    result = verify_result(args.root, args.contract, args.result_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
