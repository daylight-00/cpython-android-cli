#!/usr/bin/env python3
"""Verify the frozen E2-P3 archive-qualification contract and harness authority."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

AUTHORITY_PATH = "experiments/epoch2-archive-qualification/qualification-contract-authority.json"
AUDIT_PATH = "experiments/epoch2-archive-qualification/qualification-contract-external-audit.json"
CONTRACT_PATH = "components/standalone/contracts/qualification-v1.json"
SCHEMA_PATH = "components/standalone/schemas/qualification-result-v1.schema.json"
VERIFY_PATH = "experiments/epoch2-archive-qualification/verify-qualification-contract.py"
PREDECESSOR_VERIFY = "experiments/epoch2-termux-native-cpython3146-facade-execution/verify-execution-authority.py"
EXECUTION_AUTHORITY = "experiments/epoch2-termux-native-cpython3146-facade-execution/execution-authority.json"
EXPECTED_PREDECESSOR_FAILURES = {"binding_adjudication", "documentation", "file_identities", "verify_route"}
EXPECTED_BINDING_FAILURES = {"documentation", "file_identities", "historical_facade_adjudication", "verify_route"}
EXPECTED_PRE_HEAD = "f1e7390f3bb3e4d074e45d0f274ef116b1411efe"
EXPECTED_PRE_TREE = "0ed8a6521529e647430af867cb9be6fe11dbaa00"
EXPECTED_ARCHIVE = "66c2a39b7164701d3a14cff538be298abcf30c696150f6abf7785e212c1b4727"
EXPECTED_RELEASE = "64825d3afabbda7c90992debfb11e771baeff5514f2b6e6d13584dc7ac6fcf85"
EXPECTED_PRIVATE = "5fd8c03b53bcb749cfa221277e75f16b2392e6cec3a184b716f98e24d84fe0b5"


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    if raw != canonical_json_bytes(value):
        raise ValueError(f"noncanonical JSON: {path}")
    return value


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(argv: list[str], root: Path, env: dict[str, str] | None = None, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


def parsed(proc: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        value = json.loads(proc.stdout)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.root.resolve()
    checks: dict[str, bool] = {}
    errors: dict[str, str] = {}

    def ck(name: str, value: Any) -> None:
        checks[name] = bool(value)

    values: dict[str, dict[str, Any]] = {}
    for name, rel in {
        "authority": AUTHORITY_PATH,
        "audit": AUDIT_PATH,
        "contract": CONTRACT_PATH,
        "schema": SCHEMA_PATH,
        "facade": "components/standalone/contracts/facade-v1.json",
        "execution": EXECUTION_AUTHORITY,
    }.items():
        try:
            values[name] = read(root / rel)
        except Exception as exc:
            values[name] = {}
            errors[name] = f"{type(exc).__name__}: {exc}"

    authority = values["authority"]
    audit = values["audit"]
    contract = values["contract"]
    schema = values["schema"]
    facade = values["facade"]
    execution = values["execution"]

    branch = run(["git", "branch", "--show-current"], root)
    ck("branch_main", branch.returncode == 0 and branch.stdout.strip() == "main")
    ck("diff_check", run(["git", "diff", "--check", "HEAD"], root).returncode == 0)
    ck("authority_identity", authority.get("schema_version") == 1 and authority.get("authority_kind") == "e2p3-archive-qualification-contract" and authority.get("contract_version") == 1 and authority.get("status") == "frozen-design-no-target-evidence")
    ck("authority_predecessor", authority.get("predecessor") == {"commit": EXPECTED_PRE_HEAD, "tree": EXPECTED_PRE_TREE})
    ck("authority_input", authority.get("input_authority", {}).get("archive_sha256") == EXPECTED_ARCHIVE and authority.get("input_authority", {}).get("release_index_sha256") == EXPECTED_RELEASE and authority.get("input_authority", {}).get("private_authority_index_sha256") == EXPECTED_PRIVATE)
    ck("authority_claim_boundary", authority.get("claim_boundary") == {"combined_target_qualification": False, "installer_conversion": False, "metadata_finalization": False, "publication": False, "selectability": False, "target_execution": False, "transition_behavior": False})
    identities = authority.get("file_identities", {})
    ck("file_identities", isinstance(identities, dict) and bool(identities) and all((root / path).is_file() and sha(root / path) == digest for path, digest in identities.items()))
    ck("external_audit", audit.get("schema_version") == 1 and audit.get("audit_kind") == "e2p3-archive-qualification-contract-external-audit" and audit.get("pass") is True and audit.get("check_count") == 25 and audit.get("pass_count") == 25 and audit.get("failed_checks") == [])
    ck("contract_identity", contract.get("schema_version") == 1 and contract.get("contract_version") == 1 and contract.get("qualification_kind") == "hw-t-standalone-archive-qualification" and contract.get("status") == "frozen-design-no-target-evidence")
    input_authority = contract.get("input_authority", {})
    ck("contract_input", input_authority.get("execution_authority") == EXECUTION_AUTHORITY and input_authority.get("private_authority_index_sha256") == EXPECTED_PRIVATE and input_authority.get("private_authority_remote") == "gdrive:HW-T/cpython-android-cli/authorities/e2p2/envelopes/termux-native-cpython3146/install-only-stripped-v1")
    artifact = contract.get("artifact", {})
    ck("contract_artifact", artifact == {"archive_sha256": EXPECTED_ARCHIVE, "artifact_id": "cpython-3.14.6-aarch64-linux-android24-install_only_stripped", "manifest_entry_count": 1169, "release_index_sha256": EXPECTED_RELEASE, "stripped_elf_count": 81})
    profiles = contract.get("profiles", {})
    ck("contract_profiles", set(profiles) == {"static", "termux-real", "termux-emulator"} and profiles.get("static", {}).get("target_execution") is False and profiles.get("termux-real", {}).get("android_emulator_required") is False and profiles.get("termux-emulator", {}).get("android_emulator_required") is True)
    matrix = contract.get("profile_checks", {})
    ck("contract_check_matrix", set(matrix) == {"static", "termux-real", "termux-emulator"} and len(matrix.get("static", [])) == 9 and len(matrix.get("termux-real", [])) == 35 and len(matrix.get("termux-emulator", [])) == 35 and all(rows == sorted(rows) and len(rows) == len(set(rows)) for rows in matrix.values()))
    evidence = contract.get("profile_evidence", {})
    ck("contract_evidence_matrix", set(evidence) == set(matrix) and len(evidence.get("static", [])) == 4 and len(evidence.get("termux-real", [])) == 14 and evidence.get("termux-real") == evidence.get("termux-emulator"))
    ck("contract_selection_policy", contract.get("selection_policy") == {"individual_result_selectable": False, "required_profiles": ["termux-real", "termux-emulator"], "selectability_requires_metadata_finalization": True})
    ck("result_schema", schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema" and schema.get("type") == "object" and schema.get("properties", {}).get("selectable", {}).get("const") is False and set(schema.get("properties", {}).get("profile", {}).get("enum", [])) == {"static", "termux-real", "termux-emulator"})
    stable = root / contract.get("stable_command", "")
    ck("stable_command", stable.is_file() and os.access(stable, os.X_OK) and contract.get("stable_command") == "components/standalone/bin/cpython-android-qualify")
    plan_results = []
    for profile in ("static", "termux-real", "termux-emulator"):
        proc = run([str(stable), "plan", "--profile", profile], root)
        plan_results.append((proc, parsed(proc), profile))
    ck("stable_plans", all(proc.returncode == 0 and data.get("profile") == profile and data.get("required_checks") == matrix[profile] and data.get("required_evidence") == evidence[profile] for proc, data, profile in plan_results))
    test_proc = run([sys.executable, str(root / "experiments/epoch2-archive-qualification/test-qualification-contract.py")], root, timeout=600)
    test_data = parsed(test_proc)
    ck("regression", test_proc.returncode == 0 and test_data.get("pass") is True and test_data.get("test_count") == 19 and test_data.get("pass_count") == 19)
    ck("static_replay", audit.get("evidence", {}).get("static_qualification") == "9/9" and audit.get("evidence", {}).get("static_result_verifier") == "19/19")
    qualification = facade.get("qualification_contract", {})
    ck("facade_route", facade.get("operations", {}).get("verify", {}).get("repository_implementation") == VERIFY_PATH and qualification == {"contract_path": CONTRACT_PATH, "contract_version": 1, "execution_authority": EXECUTION_AUTHORITY, "status": "frozen-design-no-target-evidence"})
    ck("execution_authority_preserved", execution.get("status") == "frozen-pass-unqualified-envelope" and execution.get("envelope", {}).get("archive", {}).get("sha256") == EXPECTED_ARCHIVE and execution.get("private_authority", {}).get("index_sha256") == EXPECTED_PRIVATE and execution.get("claim_boundary", {}).get("target_qualification") is False)
    env = {**os.environ, "PROJECT_ROLE": "termux", "TARGET_ID": "aarch64-linux-android24", "TARGET_HOST": "aarch64-linux-android", "ANDROID_API": "24", "PYTHON_VERSION": "3.14.6", "PYTHON_MM": "3.14", "BUILD_PROFILE": "release", "PYTHONDONTWRITEBYTECODE": "1"}
    predecessor = run([sys.executable, str(root / PREDECESSOR_VERIFY), "--root", str(root)], root, env, 900)
    predecessor_data = parsed(predecessor)
    predecessor_binding = predecessor_data.get("historical", {}).get("binding", {})
    ck("predecessor_adjudication", predecessor.returncode == 1 and predecessor_data.get("check_count") == 24 and predecessor_data.get("pass_count") == 20 and set(predecessor_data.get("failed_checks", [])) == EXPECTED_PREDECESSOR_FAILURES and predecessor_binding.get("raw_rc") == 1 and set(predecessor_binding.get("failed_checks", [])) == EXPECTED_BINDING_FAILURES)
    current = (root / "docs/CURRENT_CONTEXT.md").read_text(encoding="utf-8")
    roadmap = (root / "docs/roadmap/EPOCH2_ROADMAP.md").read_text(encoding="utf-8")
    contract_doc = (root / "docs/contracts/E2P3_ARCHIVE_QUALIFICATION_CONTRACT.md").read_text(encoding="utf-8")
    ck("documentation", "E2-P3 archive qualification contract frozen" in current and "contract and harness frozen" in roadmap and "Gate 1 design and harness frozen" in contract_doc)
    ck("no_target_claim", authority.get("verification", {}).get("target_execution") == "not-run" and audit.get("claim_boundary", {}).get("target_execution") is False)
    ck("next_action", authority.get("next_action_class") == "execute-e2p3-real-termux-archive-qualification")

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "verification_kind": "e2p3-archive-qualification-contract",
        "pass": not failed and not errors,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "failed_checks": failed,
        "parse_errors": errors,
        "checks": dict(sorted(checks.items())),
        "historical": {"execution_authority": {"raw_rc": predecessor.returncode, "failed_checks": predecessor_data.get("failed_checks"), "binding": predecessor_binding}},
        "claim_boundary": "Contract and harness only; Android target execution, combined qualification, metadata finalization, selectability, publication, installer conversion, and transitions remain unclaimed.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
