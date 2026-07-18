#!/usr/bin/env python3
"""Verify the frozen E2-P3 contract, harness correction, and real-Termux authority."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ORIGINAL_AUTHORITY_PATH = "experiments/epoch2-archive-qualification/qualification-contract-authority.json"
ORIGINAL_AUDIT_PATH = "experiments/epoch2-archive-qualification/qualification-contract-external-audit.json"
CORRECTION_AUTHORITY_PATH = "experiments/epoch2-archive-qualification/qualification-harness-correction-authority.json"
CORRECTION_AUDIT_PATH = "experiments/epoch2-archive-qualification/qualification-harness-correction-external-audit.json"
REAL_AUTHORITY_PATH = "experiments/epoch2-archive-qualification/real-termux-qualification-authority.json"
REAL_AUDIT_PATH = "experiments/epoch2-archive-qualification/real-termux-qualification-external-audit.json"
AMENDMENT_AUTHORITY_PATH = "experiments/epoch2-archive-qualification/secondary-real-device-amendment-authority.json"
AMENDMENT_AUDIT_PATH = "experiments/epoch2-archive-qualification/secondary-real-device-amendment-external-audit.json"
CONTRACT_PATH = "components/standalone/contracts/qualification-v1.json"
SCHEMA_PATH = "components/standalone/schemas/qualification-result-v1.schema.json"
VERIFY_PATH = "experiments/epoch2-archive-qualification/verify-qualification-contract.py"
TEST_PATH = "experiments/epoch2-archive-qualification/test-qualification-contract.py"
QUALIFIER_PATH = "components/standalone/lib/qualify_archive.py"
EXECUTION_AUTHORITY = "experiments/epoch2-termux-native-cpython3146-facade-execution/execution-authority.json"
PREDECESSOR_VERIFY = "experiments/epoch2-termux-native-cpython3146-facade-execution/verify-execution-authority.py"
PRE_CORRECTION_COMMIT = "ecfe4fafb048e9649f9cb91657c36b45b838ab7d"
PRE_CORRECTION_TREE = "be86487e89d7335421cf71ebfc73361f17f6bac2"
PRIOR_CONTRACT_RESULT_SHA = "ec38ed8bb5b42dbcd32c106ae6887433e59e17b0cb9573491761443683b85caf"
FAILED_REAL_RESULT_SHA = "0864173ef3b6b735ef3168b26aed6c5052296289a7c0771cb05754318fb63a79"
HARNESS_CORRECTION_RESULT_SHA = "938466af2d5dc58e1551a1ef4a66cab38b85d847f06e4dde3214335f3f432a1b"
REAL_RESULT_ARCHIVE_SHA = "b92b041b78b21e0a3b402e54a15e008008db13320a264284d604f39046907e0b"
REAL_TARGET_INDEX_SHA = "9fbd2ce1f9c288bcdb92b19c0fffce24086671d40b2cce658f524935ad473ab1"
PRE_AMENDMENT_COMMIT = "c05cf9b608b69903aabaf42047cfa921276a6069"
PRE_AMENDMENT_TREE = "8ed6e6ed6b00378324d6774132e211353b7caa75"
EMULATOR_PHYSICAL_FAILURE_SHA = "ff30d1ddc9be0102c9daf759e6a0b1bed08cf334edfe6a042f9a6959b4c57e73"
ARM64_AVD_X86_NEGATIVE_SHA = "74523e3743353cb83a750ab4ae7606213ef276568fafba9e4e697d057d5302fe"
PRE_REAL_COMMIT = "2a60dfa977e6f14e34203f876dcb1cafaf83f15c"
PRE_REAL_TREE = "acd6c00d96e3831aabc23a80508489c3a2e4eb7c"
EXPECTED_ARCHIVE = "66c2a39b7164701d3a14cff538be298abcf30c696150f6abf7785e212c1b4727"
EXPECTED_RELEASE = "64825d3afabbda7c90992debfb11e771baeff5514f2b6e6d13584dc7ac6fcf85"
EXPECTED_PRIVATE = "5fd8c03b53bcb749cfa221277e75f16b2392e6cec3a184b716f98e24d84fe0b5"
EXPECTED_HISTORICAL_FAILURES = {"documentation", "file_identities", "regression"}
EXPECTED_EXECUTION_FAILURES = {"binding_adjudication", "documentation", "file_identities", "verify_route"}
EXPECTED_BINDING_FAILURES = {"documentation", "file_identities", "historical_facade_adjudication", "verify_route"}
EXPECTED_REAL_DRIFT = {
    "README.md",
    "docs/CURRENT_CONTEXT.md",
    "docs/INDEX.md",
    "docs/roadmap/EPOCH2_ROADMAP.md",
    "experiments/epoch2-archive-qualification/README.md",
    VERIFY_PATH,
}
EXPECTED_CORRECTION_DRIFT = {
    "README.md",
    "docs/CURRENT_CONTEXT.md",
    "docs/INDEX.md",
    "docs/roadmap/EPOCH2_ROADMAP.md",
    "experiments/epoch2-archive-qualification/README.md",
    VERIFY_PATH,
}
EXPECTED_ORIGINAL_DRIFT = {
    "README.md",
    QUALIFIER_PATH,
    "docs/CURRENT_CONTEXT.md",
    "docs/INDEX.md",
    "docs/contracts/E2P3_ARCHIVE_QUALIFICATION_CONTRACT.md",
    "docs/roadmap/EPOCH2_ROADMAP.md",
    "experiments/epoch2-archive-qualification/README.md",
    TEST_PATH,
    VERIFY_PATH,
}


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


def run(argv: list[str], root: Path, env: dict[str, str] | None = None, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


def parsed(proc: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        value = json.loads(proc.stdout)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def historical_verifier(root: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    show = run(["git", "show", f"{PRE_CORRECTION_COMMIT}:{VERIFY_PATH}"], root)
    if show.returncode != 0:
        return show, {}
    with tempfile.TemporaryDirectory(prefix="e2p3-historical-verifier-") as temp:
        path = Path(temp) / "verify-qualification-contract.py"
        path.write_text(show.stdout, encoding="utf-8")
        proc = run([sys.executable, str(path), "--root", str(root)], root, timeout=1200)
        return proc, parsed(proc)


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
        "original_authority": ORIGINAL_AUTHORITY_PATH,
        "original_audit": ORIGINAL_AUDIT_PATH,
        "correction_authority": CORRECTION_AUTHORITY_PATH,
        "correction_audit": CORRECTION_AUDIT_PATH,
        "real_authority": REAL_AUTHORITY_PATH,
        "real_audit": REAL_AUDIT_PATH,
        "amendment_authority": AMENDMENT_AUTHORITY_PATH,
        "amendment_audit": AMENDMENT_AUDIT_PATH,
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

    original = values["original_authority"]
    original_audit = values["original_audit"]
    correction = values["correction_authority"]
    correction_audit = values["correction_audit"]
    real_authority = values["real_authority"]
    real_audit = values["real_audit"]
    amendment = values["amendment_authority"]
    amendment_audit = values["amendment_audit"]
    contract = values["contract"]
    schema = values["schema"]
    facade = values["facade"]
    execution = values["execution"]

    ck("branch_main", run(["git", "branch", "--show-current"], root).stdout.strip() == "main")
    ck("diff_check", run(["git", "diff", "--check", "HEAD"], root).returncode == 0)
    ck("original_authority_identity", original.get("schema_version") == 1 and original.get("authority_kind") == "e2p3-archive-qualification-contract" and original.get("contract_version") == 1 and original.get("status") == "frozen-design-no-target-evidence")
    ck("original_authority_predecessor", original.get("predecessor") == {"commit": "f1e7390f3bb3e4d074e45d0f274ef116b1411efe", "tree": "0ed8a6521529e647430af867cb9be6fe11dbaa00"})
    ck("original_authority_input", original.get("input_authority", {}).get("archive_sha256") == EXPECTED_ARCHIVE and original.get("input_authority", {}).get("release_index_sha256") == EXPECTED_RELEASE and original.get("input_authority", {}).get("private_authority_index_sha256") == EXPECTED_PRIVATE)
    ck("original_authority_claim_boundary", original.get("claim_boundary") == {"combined_target_qualification": False, "installer_conversion": False, "metadata_finalization": False, "publication": False, "selectability": False, "target_execution": False, "transition_behavior": False})
    original_ids = original.get("file_identities", {})
    original_drift = {
        path for path, digest in original_ids.items()
        if not (root / path).is_file() or sha(root / path) != digest
    } if isinstance(original_ids, dict) else set()
    ck("original_authority_drift_adjudication", original_drift == EXPECTED_ORIGINAL_DRIFT)
    ck("original_external_audit_preserved", original_audit.get("schema_version") == 1 and original_audit.get("audit_kind") == "e2p3-archive-qualification-contract-external-audit" and original_audit.get("pass") is True and original_audit.get("check_count") == 25 and original_audit.get("pass_count") == 25 and original_audit.get("failed_checks") == [])

    ck("correction_authority_identity", correction.get("schema_version") == 1 and correction.get("authority_kind") == "e2p3-archive-qualification-harness-correction" and correction.get("correction_version") == 1 and correction.get("status") == "frozen-corrected-design-no-target-evidence")
    ck("correction_authority_predecessor", correction.get("predecessor") == {"commit": PRE_CORRECTION_COMMIT, "tree": PRE_CORRECTION_TREE, "contract_result_sha256": PRIOR_CONTRACT_RESULT_SHA, "failed_real_result_sha256": FAILED_REAL_RESULT_SHA})
    ck("correction_defect_adjudication", correction.get("defect_adjudication") == {"failed_checks": ["venv_relocation", "wheel_tag_android24"], "passed_checks": 33, "total_checks": 35, "runtime_defect": False, "harness_defect": True})
    ck("correction_harness_semantics", correction.get("harness") == {"check_matrix_unchanged": True, "venv_identity": "lexical-symlink-aware", "wheel_tag_source": "created-venv-pip-vendored-packaging"})
    ck("correction_claim_boundary", correction.get("claim_boundary") == {"combined_target_qualification": False, "installer_conversion": False, "metadata_finalization": False, "publication": False, "selectability": False, "target_execution": False, "transition_behavior": False})
    correction_ids = correction.get("file_identities", {})
    correction_drift = {
        path for path, digest in correction_ids.items()
        if not (root / path).is_file() or sha(root / path) != digest
    } if isinstance(correction_ids, dict) else set()
    ck("correction_authority_drift_adjudication", correction_drift == EXPECTED_CORRECTION_DRIFT)
    ck("correction_external_audit", correction_audit.get("schema_version") == 1 and correction_audit.get("audit_kind") == "e2p3-archive-qualification-harness-correction-external-audit" and correction_audit.get("source_failed_real_result_sha256") == FAILED_REAL_RESULT_SHA and correction_audit.get("pass") is True and correction_audit.get("check_count") == 31 and correction_audit.get("pass_count") == 31 and correction_audit.get("failed_checks") == [])

    ck("real_authority_identity", real_authority.get("schema_version") == 1 and real_authority.get("authority_kind") == "e2p3-real-termux-archive-qualification-freeze" and real_authority.get("authority_version") == 1 and real_authority.get("status") == "frozen-pass-individual-real-termux-profile")
    ck("real_authority_predecessor", real_authority.get("predecessor") == {"commit": PRE_REAL_COMMIT, "tree": PRE_REAL_TREE})
    real_input = real_authority.get("input_authority", {})
    ck("real_authority_input", real_input == {"artifact_id": "cpython-3.14.6-aarch64-linux-android24-install_only_stripped", "contract_result_sha256": PRIOR_CONTRACT_RESULT_SHA, "envelope_archive_sha256": EXPECTED_ARCHIVE, "failed_real_result_sha256": FAILED_REAL_RESULT_SHA, "harness_correction_result_sha256": HARNESS_CORRECTION_RESULT_SHA, "private_authority_index_sha256": EXPECTED_PRIVATE, "release_index_sha256": EXPECTED_RELEASE})
    real_profile = real_authority.get("profile", {})
    real_observations = real_profile.get("observations", {})
    ck("real_authority_profile", real_profile.get("name") == "termux-real" and real_profile.get("status") == "passed-individual-profile" and real_profile.get("device_kind") == "real" and real_profile.get("host_role") == "termux" and real_profile.get("machine") == "aarch64" and real_profile.get("android_api") == 36 and real_profile.get("check_count") == 35)
    ck("real_authority_observations", real_observations == {"elf_count": 81, "extension_import_count": 67, "https_status": 200, "manifest_entry_count": 1169, "needed_edge_count": 329, "uv_version": "uv 0.11.28 (aarch64-linux-android)"})
    real_result = real_authority.get("result_archive", {})
    ck("real_authority_result_archive", real_result == {"drive_file_id": "1V91v9v0jELPbnH42w10-FNKzQMMsVjl6", "drive_folder_id": "10ce2TUR0P2K8Ams5eGWP2-Ajrb-S1FDw", "filename": "20260718-e2p3-real-termux-archive-qualification-v2-results.tar.zst", "sha256": REAL_RESULT_ARCHIVE_SHA, "size": 68447})
    real_target = real_authority.get("target_authority", {})
    ck("real_authority_target", real_target == {"drive_folder_id": "1zKPFqqcGF-Y8HzblRZBl_aFweKoSsdMb", "index_file_id": "1xG3fjjNx3yqHhmeVjvly5S3mRkBmDAUw", "index_sha256": REAL_TARGET_INDEX_SHA, "remote": "gdrive:HW-T/cpython-android-cli/authorities/e2p3/qualifications/termux-native-cpython3146/termux-real-v1"})
    real_boundary = {"combined_target_qualification": False, "emulator_profile": False, "individual_real_termux_profile": True, "installer_conversion": False, "metadata_finalization": False, "publication": False, "selectability": False, "transition_behavior": False}
    ck("real_authority_claim_boundary", real_authority.get("claim_boundary") == real_boundary)
    ck("real_authority_verification", real_authority.get("verification") == {"external_audit": "34/34", "independent_review": "38/38", "qualification": "35/35", "repository": "44/44-staged-and-commit", "result_verifier": "19/19"})
    real_ids = real_authority.get("file_identities", {})
    real_drift = {
        path for path, digest in real_ids.items()
        if not (root / path).is_file() or sha(root / path) != digest
    } if isinstance(real_ids, dict) else set()
    ck("real_authority_drift_adjudication", real_drift == EXPECTED_REAL_DRIFT)
    ck("real_external_audit", real_audit.get("schema_version") == 1 and real_audit.get("audit_kind") == "e2p3-real-termux-archive-qualification-external-audit" and real_audit.get("source", {}).get("result_archive_sha256") == REAL_RESULT_ARCHIVE_SHA and real_audit.get("source", {}).get("target_authority_index_sha256") == REAL_TARGET_INDEX_SHA and real_audit.get("claim_boundary") == real_boundary and real_audit.get("pass") is True and real_audit.get("check_count") == 34 and real_audit.get("pass_count") == 34 and real_audit.get("failed_checks") == [] and all(real_audit.get("checks", {}).values()))

    amendment_boundary = {
        "combined_real_emulator_acceptance": False,
        "dual_real_device_acceptance": False,
        "emulator_profile": False,
        "installer_conversion": False,
        "metadata_finalization": False,
        "original_contract_fully_satisfied": False,
        "primary_real_device_profile": True,
        "publication": False,
        "secondary_real_device_profile": False,
        "selectability": False,
        "transition_behavior": False,
    }
    ck("amendment_identity", amendment.get("schema_version") == 1 and amendment.get("authority_kind") == "e2p3-secondary-real-device-amendment" and amendment.get("amendment_version") == 1 and amendment.get("status") == "frozen-design-secondary-real-device-next")
    ck("amendment_predecessor", amendment.get("predecessor") == {"commit": PRE_AMENDMENT_COMMIT, "tree": PRE_AMENDMENT_TREE})
    original_contract = amendment.get("original_contract", {})
    ck("amendment_original_contract_preserved", original_contract == {"path": CONTRACT_PATH, "preserved_unchanged": True, "required_profiles": ["termux-real", "termux-emulator"], "original_combined_acceptance_met": False})
    primary = amendment.get("primary_profile", {})
    ck("amendment_primary_identity", primary.get("authority_name") == "termux-real-primary-s22-ultra-api36" and primary.get("qualifier_profile") == "termux-real" and primary.get("machine") == "aarch64" and primary.get("android_api") == 36 and primary.get("android_release") == "16" and primary.get("hardware") == "qcom" and primary.get("qemu") is False and primary.get("kernel") == "5.10.236-android12-9-31998796-abS908NKSS9GZE5")
    ck("amendment_primary_authority", primary.get("qualification") == "35/35" and primary.get("result_verifier") == "19/19" and primary.get("independent_review") == "38/38" and primary.get("result_archive_sha256") == REAL_RESULT_ARCHIVE_SHA and primary.get("target_authority_index_sha256") == REAL_TARGET_INDEX_SHA)
    emulator = amendment.get("emulator_disposition", {})
    ck("amendment_emulator_infeasibility", emulator == {"status": "waived-infrastructure-infeasible-not-qualified", "physical_device_attempt_result_sha256": EMULATOR_PHYSICAL_FAILURE_SHA, "arm64_avd_x86_host_negative_archive_sha256": ARM64_AVD_X86_NEGATIVE_SHA, "x86_64_avd_product_fidelity": False, "emulator_claim": False})
    secondary = amendment.get("secondary_profile", {})
    ck("amendment_secondary_identity", secondary.get("authority_name") == "termux-real-secondary-exynos9810-api29" and secondary.get("qualifier_profile") == "termux-real" and secondary.get("device") == "Samsung Galaxy Note9" and secondary.get("soc") == "Exynos 9810" and secondary.get("machine") == "aarch64" and secondary.get("abilist") == ["arm64-v8a", "armeabi-v7a", "armeabi"] and secondary.get("android_api") == 29 and secondary.get("android_release") == "10" and secondary.get("hardware") == "samsungexynos9810" and secondary.get("qemu") is False and secondary.get("kernel") == "4.9.118-24343300" and secondary.get("prefix") == "/data/data/com.termux/files/usr")
    ck("amendment_secondary_matrix", secondary.get("check_count") == 35 and secondary.get("evidence_count") == 14 and secondary.get("authority_remote") == "gdrive:HW-T/cpython-android-cli/authorities/e2p3/qualifications/termux-native-cpython3146/termux-real-secondary-exynos9810-api29-v1")
    ck("amendment_harness_preserved", amendment.get("harness") == {"stable_command": "components/standalone/bin/cpython-android-qualify", "matrix_unchanged": True, "qualifier_profile": "termux-real", "wrapper_exact_device_preflight": True})
    ck("amendment_closure_policy", amendment.get("closure_policy") == {"required_profiles": ["termux-real-primary-s22-ultra-api36", "termux-real-secondary-exynos9810-api29"], "accepted_claim_after_secondary_freeze": "dual-real-device-aarch64-termux-compatibility", "emulator_claim": False, "real_emulator_combined_claim": False})
    ck("amendment_claim_boundary", amendment.get("claim_boundary") == amendment_boundary)
    amendment_ids = amendment.get("file_identities", {})
    ck("amendment_file_identities", isinstance(amendment_ids, dict) and bool(amendment_ids) and all((root / path).is_file() and sha(root / path) == digest for path, digest in amendment_ids.items()))
    audit_sources = amendment_audit.get("sources", {})
    ck("amendment_external_audit", amendment_audit.get("schema_version") == 1 and amendment_audit.get("audit_kind") == "e2p3-secondary-real-device-amendment-external-audit" and amendment_audit.get("pass") is True and amendment_audit.get("check_count") == 30 and amendment_audit.get("pass_count") == 30 and amendment_audit.get("failed_checks") == [] and all(amendment_audit.get("checks", {}).values()) and amendment_audit.get("claim_boundary") == amendment_boundary and audit_sources.get("primary_result_archive_sha256") == REAL_RESULT_ARCHIVE_SHA and audit_sources.get("primary_target_authority_index_sha256") == REAL_TARGET_INDEX_SHA and audit_sources.get("physical_device_emulator_attempt_sha256") == EMULATOR_PHYSICAL_FAILURE_SHA and audit_sources.get("arm64_avd_x86_host_negative_archive_sha256") == ARM64_AVD_X86_NEGATIVE_SHA)
    ck("amendment_next_action", amendment.get("next_action_class") == "execute-e2p3-secondary-real-device-archive-qualification")

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
    test_proc = run([sys.executable, str(root / TEST_PATH)], root, timeout=900)
    test_data = parsed(test_proc)
    ck("regression", test_proc.returncode == 0 and test_data.get("pass") is True and test_data.get("test_count") == 21 and test_data.get("pass_count") == 21)
    ck("static_replay", correction_audit.get("evidence", {}).get("static_qualification") == "9/9" and correction_audit.get("evidence", {}).get("static_result_verifier") == "19/19")
    qualification = facade.get("qualification_contract", {})
    ck("facade_route", facade.get("operations", {}).get("verify", {}).get("repository_implementation") == VERIFY_PATH and qualification == {"contract_path": CONTRACT_PATH, "contract_version": 1, "execution_authority": EXECUTION_AUTHORITY, "status": "frozen-design-no-target-evidence"})
    ck("execution_authority_preserved", execution.get("status") == "frozen-pass-unqualified-envelope" and execution.get("envelope", {}).get("archive", {}).get("sha256") == EXPECTED_ARCHIVE and execution.get("private_authority", {}).get("index_sha256") == EXPECTED_PRIVATE and execution.get("claim_boundary", {}).get("target_qualification") is False)

    historical_proc, historical_data = historical_verifier(root)
    historical_execution = historical_data.get("historical", {}).get("execution_authority", {})
    historical_binding = historical_execution.get("binding", {})
    ck("historical_contract_adjudication", historical_proc.returncode == 1 and historical_data.get("check_count") == 26 and historical_data.get("pass_count") == 23 and set(historical_data.get("failed_checks", [])) == EXPECTED_HISTORICAL_FAILURES and historical_execution.get("raw_rc") == 1 and set(historical_execution.get("failed_checks", [])) == EXPECTED_EXECUTION_FAILURES and historical_binding.get("raw_rc") == 1 and set(historical_binding.get("failed_checks", [])) == EXPECTED_BINDING_FAILURES)

    current = (root / "docs/CURRENT_CONTEXT.md").read_text(encoding="utf-8")
    roadmap = (root / "docs/roadmap/EPOCH2_ROADMAP.md").read_text(encoding="utf-8")
    contract_doc = (root / "docs/contracts/E2P3_ARCHIVE_QUALIFICATION_CONTRACT.md").read_text(encoding="utf-8")
    experiment = (root / "experiments/epoch2-archive-qualification/README.md").read_text(encoding="utf-8")
    evidence_doc = root / "docs/evidence/E2P3_REAL_TERMUX_ARCHIVE_QUALIFICATION_AUTHORITY_FREEZE.md"
    handoff_doc = root / "docs/handoff/2026-07-18-e2p3-real-termux-archive-qualification-authority-freeze.md"
    amendment_contract_doc = root / "docs/contracts/E2P3_SECONDARY_REAL_DEVICE_AMENDMENT.md"
    amendment_evidence_doc = root / "docs/evidence/E2P3_EMULATOR_INFEASIBILITY_AND_SECONDARY_REAL_DEVICE_AMENDMENT.md"
    amendment_handoff_doc = root / "docs/handoff/2026-07-18-e2p3-secondary-real-device-amendment.md"
    ck("documentation", "E2-P3 secondary real-device amendment frozen" in current and "secondary Note9 profile next; emulator waived" in roadmap and "Harness correction v1" in contract_doc and "second physical-device run" in experiment and evidence_doc.is_file() and handoff_doc.is_file() and amendment_contract_doc.is_file() and amendment_evidence_doc.is_file() and amendment_handoff_doc.is_file())
    ck("real_target_claim", real_authority.get("claim_boundary", {}).get("individual_real_termux_profile") is True and real_authority.get("claim_boundary", {}).get("emulator_profile") is False and real_authority.get("claim_boundary", {}).get("selectability") is False)
    ck("next_action", amendment.get("next_action_class") == "execute-e2p3-secondary-real-device-archive-qualification")

    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "verification_kind": "e2p3-secondary-real-device-amendment",
        "pass": not failed and not errors,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "failed_checks": failed,
        "parse_errors": errors,
        "checks": dict(sorted(checks.items())),
        "historical": {
            "contract_verifier": {
                "raw_rc": historical_proc.returncode,
                "failed_checks": historical_data.get("failed_checks"),
                "execution_authority": historical_execution,
            }
        },
        "claim_boundary": "The primary real-device profile is frozen. The emulator objective is waived without qualification and a Note9 secondary physical-device run is next. Dual-device acceptance, original real-plus-emulator acceptance, metadata finalization, selectability, publication, installer conversion, and transitions remain unclaimed.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
