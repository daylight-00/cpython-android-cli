#!/usr/bin/env python3
"""Verify the returned canonical full candidate before authority promotion."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_FULL = {
    "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-full.tar.zst",
    "sha256": "20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12",
    "size_bytes": 39408292,
}
EXPECTED_OFFICIAL = {
    "filename": "python-3.14.6-aarch64-linux-android.tar.gz",
    "sha256": "38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5",
    "size_bytes": 22358404,
}
EXPECTED_GOLDEN = {
    "filename": "cpython-3.14.6+20260610-aarch64-unknown-linux-gnu-pgo+lto-full.tar.zst",
    "sha256": "451113b0af15ded8986def51f05dc3a3f4516974dd78c3b27d768a1cb221a231",
    "size_bytes": 102585386,
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(*, root: Path = ROOT, evidence_dir: Path | None = None, accepted_path: Path | None = None) -> dict[str, Any]:
    evidence = evidence_dir or root / "experiments/epoch3-upstream-thin-full/authority-evidence"
    accepted_file = accepted_path or root / "experiments/epoch3-upstream-thin-full/accepted-r4-return.json"
    checks: dict[str, bool] = {}
    errors: dict[str, str] = {}
    docs: dict[str, dict[str, Any]] = {}

    required = [
        "input-identities.json",
        "full-reproducibility.json",
        "full-static-verification.json",
        "full-target-qualification.json",
        "astral-conformance.json",
        "gate-diagnostics.json",
        "independent-audit.json",
    ]
    for name in required:
        path = evidence / name
        try:
            docs[name] = load(path)
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

    identities = docs["input-identities.json"]
    checks["official_input_exact"] = identities.get("official") == EXPECTED_OFFICIAL
    checks["astral_golden_exact"] = identities.get("astral_golden") == EXPECTED_GOLDEN

    reproducibility = docs["full-reproducibility.json"]
    expected_artifact_identity = {"sha256": EXPECTED_FULL["sha256"], "size_bytes": EXPECTED_FULL["size_bytes"]}
    checks["full_byte_reproducible"] = (
        reproducibility.get("pass") is True
        and reproducibility.get("first") == expected_artifact_identity
        and reproducibility.get("second") == expected_artifact_identity
    )

    static = docs["full-static-verification.json"]
    checks["full_static_pass"] = static.get("pass") is True and not static.get("failed_checks")
    checks["full_static_identity"] = static.get("archive", {}).get("sha256") == EXPECTED_FULL["sha256"] and static.get("archive", {}).get("size_bytes") == EXPECTED_FULL["size_bytes"]
    metrics = static.get("metrics", {})
    checks["full_inventory_exact"] = metrics.get("archive_member_count") == 3752 and metrics.get("elf_count") == 81 and metrics.get("python_json_extension_count") == 67
    checks["termux_native_dependency_zero"] = static.get("checks", {}).get("release_needed_closure") is True and static.get("checks", {}).get("active_tree_host_neutral") is True

    target = docs["full-target-qualification.json"]
    checks["android_target_pass"] = target.get("pass") is True and not target.get("failed_checks")
    target_checks = target.get("checks", {})
    checks["android_runtime_surface"] = all(target_checks.get(key) is True for key in (
        "runtime_location_a", "whole_prefix_relocation", "read_only_install", "all_67_extensions",
        "pip_surface", "fresh_venv", "python_config_surface", "pkg_config_surface",
    ))
    claims = target.get("claim_boundary", {})
    checks["target_claims_bounded"] = (
        claims.get("qualified_context") == "current owner Termux app process on Android/Bionic"
        and claims.get("api24_runtime_claim") is False
        and claims.get("actual_16k_runtime_claim") is False
        and claims.get("non_termux_context_claim") is False
        and claims.get("selectable") is False
        and claims.get("publication") is False
    )

    conformance = docs["astral-conformance.json"]
    checks["astral_conformance_pass"] = conformance.get("pass") is True and conformance.get("canonical_roots_match") is True
    checks["astral_difference_truthful"] = len(conformance.get("intentional_non_equivalence", [])) == 3 and conformance.get("candidate_only_python_json_keys") == []

    gate = docs["gate-diagnostics.json"]
    checks["target_gate_pass"] = gate.get("pass") is True and not gate.get("failed_gates") and all(gate.get("gates", {}).values())
    checks["target_gate_identity"] = gate.get("artifact", {}).get("sha256") == EXPECTED_FULL["sha256"] and gate.get("artifact", {}).get("size_bytes") == EXPECTED_FULL["size_bytes"]
    checks["downstream_not_started"] = gate.get("claim_boundary", {}).get("install_only_implementation_started") is False

    audit = docs["independent-audit.json"]
    checks["independent_audit_pass"] = audit.get("pass") is True and not audit.get("failed_checks") and all(audit.get("checks", {}).values())
    checks["independent_rerun_identity"] = audit.get("independent_static_rerun", {}).get("archive", {}).get("sha256") == EXPECTED_FULL["sha256"]

    accepted_artifact = accepted.get("artifact", {})
    checks["accepted_return_identity"] = all(accepted_artifact.get(key) == value for key, value in EXPECTED_FULL.items())
    checks["accepted_repository_transition"] = accepted.get("repository_result") == {
        "pre_head": "00ac96f96e79e173f549956e323f2b2d6a725bc1",
        "pre_tree": "0e2eed023820b57fdff40d015affd93460cb4698",
        "post_head": "54f942bcd13b5a3282c13965eb2cc9b283c6bebb",
        "post_tree": "4383874f02e198df796c187881ad9da4698140b5",
        "remote_post_head": "54f942bcd13b5a3282c13965eb2cc9b283c6bebb",
    }
    expected_evidence = accepted.get("evidence_files", {})
    evidence_hashes_ok = True
    for rel, expected in expected_evidence.items():
        source = evidence / Path(rel).name
        if not source.is_file() or sha256(source) != expected:
            evidence_hashes_ok = False
    checks["accepted_evidence_hashes"] = len(expected_evidence) == len(required) and evidence_hashes_ok

    code_paths = [
        "components/upstream-thin/lib/assemble_full.py",
        "components/upstream-thin/lib/verify_full.py",
        "components/upstream-thin/lib/qualify_full.py",
        "components/upstream-thin/lib/observe_astral.py",
        "experiments/epoch3-upstream-thin-full/run_full_target.py",
        "experiments/epoch3-upstream-thin-full/audit_full_target.py",
    ]
    code_identities = {}
    for rel in code_paths:
        path = root / rel
        if path.is_file():
            code_identities[rel] = sha256(path)
    checks["claim_code_complete"] = len(code_identities) == len(code_paths)

    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-canonical-full-return-acceptance",
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": len(checks) - len(failed),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "errors": errors,
        "artifact": EXPECTED_FULL,
        "claim_code_identities": code_identities,
        "claim_boundary": {
            "canonical_full_complete": not failed,
            "install_only_authorized_to_start": not failed,
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
    result = verify(
        root=Path(args.root).resolve(),
        evidence_dir=Path(args.evidence_dir).resolve() if args.evidence_dir else None,
        accepted_path=Path(args.accepted_return).resolve() if args.accepted_return else None,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
