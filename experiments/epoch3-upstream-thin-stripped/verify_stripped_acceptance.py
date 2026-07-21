#!/usr/bin/env python3
"""Verify the returned canonical install_only_stripped candidate before authority promotion."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SOURCE = {
    "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-install_only.tar.gz",
    "sha256": "84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76",
    "size_bytes": 23841726,
}
EXPECTED_STRIPPED = {
    "filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-install_only_stripped.tar.gz",
    "sha256": "40951002c5880b223fa78c7b956dfcf2929e3ebf8e8beb9420c4179b98231134",
    "size_bytes": 23841241,
    "member_count": 3699,
}
EXPECTED_CHANGED = ["bin/python3.14"]


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
    evidence = evidence_dir or root / "experiments/epoch3-upstream-thin-stripped/authority-evidence"
    accepted_file = accepted_path or root / "experiments/epoch3-upstream-thin-stripped/accepted-r2-return.json"
    required = [
        "install-only-input-identity.json",
        "stripped-reproducibility.json",
        "stripped-verification.json",
        "stripped-target-qualification.json",
        "stripped-mutation-receipt.json",
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

    identity = docs["install-only-input-identity.json"]
    checks["source_install_only_exact"] = (
        identity.get("pass") is True
        and identity.get("expected") == EXPECTED_SOURCE
        and identity.get("observed") == EXPECTED_SOURCE
    )

    repro = docs["stripped-reproducibility.json"]
    expected_repro = {k: EXPECTED_STRIPPED[k] for k in ("filename", "sha256", "size_bytes")}
    checks["stripped_byte_reproducible"] = (
        repro.get("pass") is True
        and repro.get("first") == expected_repro
        and repro.get("second") == expected_repro
    )

    mutation = docs["stripped-mutation-receipt.json"]
    checks["distinct_archive_decision"] = mutation.get("decision") == "distinct-archive"
    checks["strip_surface_exact"] = (
        mutation.get("regular_elf_count") == 81
        and mutation.get("eligible_elf_count") == 1
        and mutation.get("changed_elf_count") == 1
        and mutation.get("eligible_paths") == EXPECTED_CHANGED
        and mutation.get("changed_paths") == EXPECTED_CHANGED
        and mutation.get("strip_operation") == "--strip-unneeded"
    )
    checks["mutation_source_and_artifact_exact"] = (
        mutation.get("source_install_only") == EXPECTED_SOURCE
        and mutation.get("artifact") == EXPECTED_STRIPPED
    )
    readelf_tool = mutation.get("readelf_tool", {})
    strip_tool = mutation.get("strip_tool", {})
    checks["tool_alias_semantics_recorded"] = (
        readelf_tool.get("path") == "/data/data/com.termux/files/usr/bin/readelf"
        and readelf_tool.get("canonical_path") == "/data/data/com.termux/files/usr/bin/llvm-readobj"
        and readelf_tool.get("sha256") == "f409f88b053ede038c37d2cc844a6c065a9d623cdebdf3f63d544beb8b55630e"
        and strip_tool.get("path") == "/data/data/com.termux/files/usr/bin/llvm-strip"
        and strip_tool.get("canonical_path") == "/data/data/com.termux/files/usr/bin/llvm-objcopy"
        and strip_tool.get("sha256") == "b1196f21e347a912662b0bea76ad97c60f758e68c612b58006d505182a679392"
    )

    derivation = docs["stripped-verification.json"]
    dchecks = derivation.get("checks", {})
    checks["exact_derivation_pass"] = derivation.get("pass") is True and not derivation.get("failed_checks")
    checks["derivation_identity"] = (
        derivation.get("artifact", {}).get("filename") == EXPECTED_STRIPPED["filename"]
        and derivation.get("artifact", {}).get("sha256") == EXPECTED_STRIPPED["sha256"]
        and derivation.get("artifact", {}).get("size_bytes") == EXPECTED_STRIPPED["size_bytes"]
        and derivation.get("artifact", {}).get("member_count") == EXPECTED_STRIPPED["member_count"]
        and derivation.get("source_install_only") == EXPECTED_SOURCE
    )
    required_derivation_checks = (
        "accepted_install_only_identity",
        "all_and_only_eligible_elf_changed",
        "artifact_identity_matches_receipt",
        "changed_count_exact",
        "changed_paths_exact",
        "deterministic_gzip_header",
        "deterministic_tar_metadata",
        "distinct_byte_delta",
        "elf_dynamic_alignment_preserved",
        "eligible_count_exact",
        "eligible_paths_exact",
        "no_duplicate_members",
        "non_elf_bytes_unchanged",
        "path_set_identity",
        "receipt_decision_distinct",
        "regular_elf_count_exact",
        "regular_elf_paths_exact",
        "removable_sections_absent_after",
        "type_mode_symlink_identity",
    )
    checks["derivation_semantics"] = all(dchecks.get(key) is True for key in required_derivation_checks)

    target = docs["stripped-target-qualification.json"]
    tchecks = target.get("checks", {})
    checks["android_target_pass"] = target.get("pass") is True and not target.get("failed_checks")
    checks["android_runtime_surface"] = all(
        tchecks.get(key) is True
        for key in (
            "decompress",
            "direct_archive_root",
            "runtime_location_a",
            "whole_prefix_relocation",
            "read_only_install",
            "all_67_extensions",
            "pip_surface",
            "fresh_venv",
            "python_config_surface",
            "pkg_config_surface",
            "python_alias_commands",
        )
    )
    claims = target.get("claim_boundary", {})
    checks["target_claims_bounded"] = (
        claims.get("install_only_authority_frozen") is True
        and claims.get("stripped_started") is True
        and claims.get("stripped_authority_frozen") is False
        and claims.get("selectable") is False
        and claims.get("publication") is False
        and claims.get("api24_runtime_claim") is False
        and claims.get("actual_16k_runtime_claim") is False
        and claims.get("non_termux_context_claim") is False
    )

    gate = docs["gate-diagnostics.json"]
    checks["candidate_gate_pass"] = gate.get("pass") is True and not gate.get("failed_gates") and all(gate.get("gates", {}).values())
    checks["candidate_gate_identity"] = gate.get("artifact") == {**EXPECTED_STRIPPED, "path": "artifacts/" + EXPECTED_STRIPPED["filename"]}
    checks["candidate_gate_surface"] = gate.get("strip_surface", {}).get("regular_elf_count") == 81 and gate.get("strip_surface", {}).get("eligible_elf_count") == 1 and gate.get("strip_surface", {}).get("changed_elf_count") == 1 and gate.get("strip_surface", {}).get("eligible_paths") == EXPECTED_CHANGED and gate.get("strip_surface", {}).get("changed_paths") == EXPECTED_CHANGED

    audit = docs["independent-audit.json"]
    checks["independent_audit_pass"] = audit.get("pass") is True and not audit.get("failed_checks") and all(audit.get("checks", {}).values())
    rerun = audit.get("independent_derivation_rerun", {})
    checks["independent_derivation_identity"] = rerun.get("pass") is True and rerun.get("artifact", {}).get("sha256") == EXPECTED_STRIPPED["sha256"] and rerun.get("source_install_only", {}).get("sha256") == EXPECTED_SOURCE["sha256"] and rerun.get("changed_paths") == EXPECTED_CHANGED

    checks["accepted_artifact_identity"] = accepted.get("artifact") == EXPECTED_STRIPPED
    checks["accepted_source_install_only"] = accepted.get("source_install_only") == EXPECTED_SOURCE
    checks["accepted_strip_surface"] = accepted.get("strip_surface") == {
        "decision": "distinct-archive",
        "operation": "--strip-unneeded",
        "regular_elf_count": 81,
        "eligible_elf_count": 1,
        "changed_elf_count": 1,
        "eligible_paths": EXPECTED_CHANGED,
        "changed_paths": EXPECTED_CHANGED,
        "non_elf_payload_unchanged": True,
        "dynamic_and_alignment_surface_preserved": True,
    }
    checks["accepted_repository_transition"] = accepted.get("repository_result") == {
        "pre_head": "992947ee1023d806e22c6cfdfc88efc2f0d1d76f",
        "pre_tree": "b4dc1e9ef61b8eb49e55638f3659e5b5216496f0",
        "post_head": "bc7b655059c376f50f06c6c6171b508fbf2eb1a2",
        "post_tree": "8d9a61713fb3de00e49d11b0a01fa314040e57a0",
        "remote_post_head": "bc7b655059c376f50f06c6c6171b508fbf2eb1a2",
    }
    checks["result_archive_identity"] = accepted.get("result_archive") == {
        "filename": "cpython-android-cli-e3-first-real-stripped-r2-results.tar.zst",
        "sha256": "f23fcbaed9cdaad1da8ca355500e8181297f0c70b96618f5f5a802b607b08a93",
        "size_bytes": 71737271,
    }
    expected_evidence = accepted.get("evidence_files", {})
    checks["accepted_evidence_hashes"] = (
        len(expected_evidence) == len(required)
        and all(
            (evidence / Path(rel).name).is_file()
            and sha256(evidence / Path(rel).name) == digest
            for rel, digest in expected_evidence.items()
        )
    )

    code_paths = [
        "components/upstream-thin/lib/assemble_stripped.py",
        "components/upstream-thin/lib/verify_stripped.py",
        "components/upstream-thin/lib/qualify_stripped.py",
        "components/upstream-thin/lib/strip_surface.py",
        "experiments/epoch3-upstream-thin-stripped/run_stripped_target.py",
        "experiments/epoch3-upstream-thin-stripped/audit_stripped_target.py",
    ]
    code_ids = {rel: sha256(root / rel) for rel in code_paths if (root / rel).is_file()}
    checks["claim_code_complete"] = len(code_ids) == len(code_paths)

    failed = sorted(key for key, value in checks.items() if value is not True)
    return {
        "schema_version": 1,
        "verifier_kind": "epoch3-canonical-install-only-stripped-return-acceptance",
        "pass": not failed,
        "check_count": len(checks),
        "pass_count": len(checks) - len(failed),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "errors": errors,
        "artifact": EXPECTED_STRIPPED,
        "source_install_only": EXPECTED_SOURCE,
        "strip_surface": accepted.get("strip_surface", {}),
        "claim_code_identities": code_ids,
        "claim_boundary": {
            "stripped_complete": not failed,
            "artifact_family_authorized_to_start": not failed,
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
