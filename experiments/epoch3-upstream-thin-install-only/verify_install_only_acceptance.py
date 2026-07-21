#!/usr/bin/env python3
"""Verify the returned canonical install-only candidate before authority promotion."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_FULL = {
    "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-full.tar.zst",
    "sha256": "20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12",
    "size_bytes": 39408292,
}
EXPECTED_INSTALL = {
    "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-install_only.tar.gz",
    "sha256": "84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76",
    "size_bytes": 23841726,
    "member_count": 3699,
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(*, root: Path = ROOT, evidence_dir: Path | None = None, accepted_path: Path | None = None) -> dict[str, Any]:
    evidence = evidence_dir or root / "experiments/epoch3-upstream-thin-install-only/authority-evidence"
    accepted_file = accepted_path or root / "experiments/epoch3-upstream-thin-install-only/accepted-r1-return.json"
    required = [
        "full-input-identity.json",
        "install-only-reproducibility.json",
        "install-only-verification.json",
        "install-only-target-qualification.json",
        "gate-diagnostics.json",
        "independent-audit.json",
    ]
    checks: dict[str, bool] = {}
    errors: dict[str, str] = {}
    docs: dict[str, dict[str, Any]] = {}
    for name in required:
        try:
            docs[name] = load(evidence / name)
            checks[f"parse:{name}"] = True
        except Exception as exc:  # noqa: BLE001
            docs[name] = {}
            checks[f"parse:{name}"] = False
            errors[f"parse:{name}"] = f"{type(exc).__name__}: {exc}"
    try:
        accepted = load(accepted_file)
        checks["parse:accepted-return"] = True
    except Exception as exc:  # noqa: BLE001
        accepted = {}
        checks["parse:accepted-return"] = False
        errors["parse:accepted-return"] = f"{type(exc).__name__}: {exc}"

    identity = docs["full-input-identity.json"]
    checks["source_full_exact"] = identity.get("pass") is True and identity.get("observed") == EXPECTED_FULL

    repro = docs["install-only-reproducibility.json"]
    expected_repro = {k: EXPECTED_INSTALL[k] for k in ("filename", "sha256", "size_bytes")}
    checks["install_only_byte_reproducible"] = repro.get("pass") is True and repro.get("first") == expected_repro and repro.get("second") == expected_repro

    projection = docs["install-only-verification.json"]
    pchecks = projection.get("checks", {})
    checks["exact_projection_pass"] = projection.get("pass") is True and not projection.get("failed_checks")
    checks["projection_identity"] = projection.get("artifact", {}).get("sha256") == EXPECTED_INSTALL["sha256"] and projection.get("artifact", {}).get("size_bytes") == EXPECTED_INSTALL["size_bytes"] and projection.get("artifact", {}).get("member_count") == EXPECTED_INSTALL["member_count"]
    checks["projection_semantics"] = all(pchecks.get(k) is True for k in ("exact_projection", "payload_bytes_unchanged", "full_metadata_absent", "one_python_root", "deterministic_tar_metadata", "deterministic_gzip_header", "no_duplicate_members"))

    target = docs["install-only-target-qualification.json"]
    tchecks = target.get("checks", {})
    checks["android_target_pass"] = target.get("pass") is True and not target.get("failed_checks")
    checks["android_runtime_surface"] = all(tchecks.get(k) is True for k in ("runtime_location_a", "whole_prefix_relocation", "read_only_install", "all_67_extensions", "pip_surface", "fresh_venv", "python_config_surface", "pkg_config_surface", "python_alias_commands"))
    claims = target.get("claim_boundary", {})
    checks["target_claims_bounded"] = claims.get("install_only_authority_frozen") is False and claims.get("stripped_started") is False and claims.get("selectable") is False and claims.get("publication") is False and claims.get("api24_runtime_claim") is False and claims.get("actual_16k_runtime_claim") is False and claims.get("non_termux_context_claim") is False

    gate = docs["gate-diagnostics.json"]
    checks["candidate_gate_pass"] = gate.get("pass") is True and not gate.get("failed_gates") and all(gate.get("gates", {}).values())
    checks["candidate_gate_identity"] = gate.get("artifact", {}).get("sha256") == EXPECTED_INSTALL["sha256"] and gate.get("artifact", {}).get("size_bytes") == EXPECTED_INSTALL["size_bytes"] and gate.get("artifact", {}).get("projection_member_count") == EXPECTED_INSTALL["member_count"]
    checks["stripped_not_started"] = gate.get("claim_boundary", {}).get("stripped_implementation_started") is False

    audit = docs["independent-audit.json"]
    checks["independent_audit_pass"] = audit.get("pass") is True and not audit.get("failed_checks") and all(audit.get("checks", {}).values())
    checks["independent_projection_identity"] = audit.get("independent_projection_rerun", {}).get("artifact", {}).get("sha256") == EXPECTED_INSTALL["sha256"]

    checks["accepted_artifact_identity"] = accepted.get("artifact") == EXPECTED_INSTALL
    checks["accepted_source_full"] = accepted.get("source_full") == EXPECTED_FULL
    checks["accepted_repository_transition"] = accepted.get("repository_result") == {
        "pre_head": "54f942bcd13b5a3282c13965eb2cc9b283c6bebb",
        "pre_tree": "4383874f02e198df796c187881ad9da4698140b5",
        "post_head": "992947ee1023d806e22c6cfdfc88efc2f0d1d76f",
        "post_tree": "b4dc1e9ef61b8eb49e55638f3659e5b5216496f0",
        "remote_post_head": "992947ee1023d806e22c6cfdfc88efc2f0d1d76f",
    }
    expected_evidence = accepted.get("evidence_files", {})
    checks["accepted_evidence_hashes"] = len(expected_evidence) == len(required) and all((evidence / Path(rel).name).is_file() and sha256(evidence / Path(rel).name) == digest for rel, digest in expected_evidence.items())
    checks["result_archive_identity"] = accepted.get("result_archive") == {
        "filename": "cpython-android-cli-e3-first-real-install-only-r1-results.tar.zst",
        "sha256": "6d96f8f11023eb0966816bc64a5c027be8499499789735d9c917c34102d56a7b",
        "size_bytes": 71368064,
    }

    code_paths = [
        "components/upstream-thin/lib/assemble_install_only.py",
        "components/upstream-thin/lib/verify_install_only.py",
        "components/upstream-thin/lib/qualify_install_only.py",
        "experiments/epoch3-upstream-thin-install-only/run_install_only_target.py",
        "experiments/epoch3-upstream-thin-install-only/audit_install_only_target.py",
    ]
    code_ids = {rel: sha256(root / rel) for rel in code_paths if (root / rel).is_file()}
    checks["claim_code_complete"] = len(code_ids) == len(code_paths)

    failed = sorted(k for k, v in checks.items() if v is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-canonical-install-only-return-acceptance",
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": len(checks) - len(failed),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "errors": errors,
        "artifact": EXPECTED_INSTALL,
        "source_full": EXPECTED_FULL,
        "claim_code_identities": code_ids,
        "claim_boundary": {
            "install_only_complete": not failed,
            "stripped_authorized_to_start": not failed,
            "selectable": False,
            "publication": False,
            "api24_runtime": False,
            "actual_16k_runtime": False,
            "non_termux_context": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--evidence-dir")
    parser.add_argument("--accepted-return")
    args = parser.parse_args()
    result = verify(root=Path(args.root).resolve(), evidence_dir=Path(args.evidence_dir).resolve() if args.evidence_dir else None, accepted_path=Path(args.accepted_return).resolve() if args.accepted_return else None)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
