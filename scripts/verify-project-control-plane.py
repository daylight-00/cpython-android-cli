#!/usr/bin/env python3
"""Verify frozen Stage 3-E and active Stage 3-F through corrected Gate 4."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

BRANCH = "agent/stage3f-publication-acquisition"
S3E_HEAD = "6419e107e4aa8400ebd3d98f3583999075b8b935"
S3E_TREE = "e16edd99bfadf2135d0b632ddef4d292c0d80ea6"
MAIN = "b5a2ca39d1250122312355dd3dbc6165b9409786"
F1_HEAD = "39e5c6d56a45495a4f23b73b6fa0704ba28fbc74"
F1_TREE = "7a0c476e60280c23dd8edd2627b25b42e3fa1429"
F1_RESULT = "eb6f1356fa09473bc4564e0e3a1ae1d7940ecac287d69baa2abf4bd8c494a438"
F2_HEAD = "82c21757e08b040fb7167c90e60fa48af323efb0"
F2_TREE = "ba85ac5bf09bdfc2aac7482077535ac2942cbc38"
F2_RESULT = "c8175e85a738a3decb078b5a6f858c175bead1ecd46608366dff3b27acf61d5d"
G2 = "3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2"
G2A = "5813305c22528354e6af686330e8f635db2b90a8a7a48ed5ed3c9ad4d1a4fb4d"
G4 = "4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112"
G4A = "794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a"
G5_BLOB = "651789e14f899b852f8fb8b4cbeceeaca318b19a"
SNAPSHOT = "a00027a81956ef175bf537eff3a92286e26c1120fa536d0a8ad6a096a1760f8c"
SNAPSHOT_FILE = "c942b9863e33c2edf7d628780bfeef0957b427fb12259ba49e708cb4858c52bc"
A145 = "18832bb7982a679fcee067e2d33e106dac84307687b63803be105714596d422f"
A146 = "9575edef24d84b2fce32c55093ab01cb8b2b1a41b521d2011653fae87b5bcb64"
K145 = "cpython-3.14.5-linux-aarch64-none"
K146 = "cpython-3.14.6-linux-aarch64-none"
FIXTURE_A = "c40fe3e0affea04d95a55601be476f46aa74561c4108e80f1dfcf4a010316cf9"
FIXTURE_B = "5a09b2f32ae9d2cc5b90f48ae24f69fb518bbadb675a90331e78e72241ee5f75"
G3_HEAD = "72713db607bbead29f45e86617edc7ca05617fc4"
G3_TREE = "8c1b67d4dfebbc9266213f8374db0a3cf912fd91"
G3_RESULT = "c6305495f6a1b21031dd0469e43273bb87de5b0e11d3fad722f0ee4c75bdeb09"
G4_V1_RESULT = "2a076288652f1c342da49eccbe4507291df05d1d596b5c6f1d5646610b5990be"
G4_RESULT = "6cba95839a5dc05a7d4261467f1b7693e9d232fd44abe21ca4712e09b8e1977b"
RETAINED_SNAPSHOT = "dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233"
RETAINED_SNAPSHOT_FILE = "419a9d4303fd6b3d7686400c7a275117ae6fe3421c93c30ff356529fc483b9e3"
RA145 = "2edec6cfaf20a44b2458567856c1d505e6942d0e43da0e8ba2a36761ebc05be2"
RA146 = "f0c449f7bc5b5bd740f4776f43bec4418645d5f33da220fa523409b6aa0af208"


def dig(value: Any, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def verify(root: Path) -> dict[str, Any]:
    root = root.resolve()
    missing: list[str] = []
    parse_errors: dict[str, str] = {}

    def text(path: str) -> str:
        target = root / path
        if not target.is_file():
            missing.append(path)
            return ""
        try:
            return target.read_text(encoding="utf-8")
        except Exception as exc:
            parse_errors[path] = f"{type(exc).__name__}: {exc}"
            return ""

    def data(path: str) -> dict[str, Any]:
        raw = text(path)
        if not raw:
            return {}
        try:
            value = json.loads(raw)
        except Exception as exc:
            parse_errors[path] = f"{type(exc).__name__}: {exc}"
            return {}
        if not isinstance(value, dict):
            parse_errors[path] = "top-level JSON is not object"
            return {}
        return value

    readme = text("README.md")
    ctx3e = text("docs/PROJECT_CONTEXT_STAGE3E.md")
    scope3e = text("docs/stages/STAGE3E_SCOPE.md")
    ctx3f = text("docs/PROJECT_CONTEXT_STAGE3F.md")
    scope3f = text("docs/stages/STAGE3F_SCOPE.md")
    orient = text("docs/PROJECT_ORIENTATION.md")
    handoff = text("docs/handoff/README.md")
    start = text("docs/handoff/2026-07-16-stage3f-gate1-authority-start.md")
    g2handoff = text("docs/handoff/2026-07-16-stage3f-gate2-contract-freeze.md")
    g3handoff = text("docs/handoff/2026-07-16-stage3f-gate3-loopback-freeze.md")

    e2ev = text("docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md")
    g4ev = text("docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md")
    summary = text("docs/evidence/STAGE3E_FINAL_SUMMARY.md")
    g1ev = text("docs/evidence/STAGE3F_GATE1_AUTHORITY_DESIGN_RESULT.md")
    g1tx = text("docs/evidence/STAGE3F_GATE1_REPOSITORY_TRANSACTION_RESULT.md")
    g2result = text("docs/evidence/STAGE3F_GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_RESULT.md")
    g2tx = text("docs/evidence/STAGE3F_GATE2_REPOSITORY_TRANSACTION_RESULT.md")
    g3result = text("docs/evidence/STAGE3F_GATE3_LOOPBACK_TRANSPORT_ACQUISITION_RESULT.md")
    g4fail = text("docs/evidence/STAGE3F_GATE4_V1_DERIVATION_FAILURE.md")
    g4result = text("docs/evidence/STAGE3F_GATE4_RETAINED_ARTIFACT_ACQUISITION_RESULT.md")
    g4doc = text("experiments/stage3f-publication-acquisition/GATE4_TERMUX_RETAINED_ARTIFACT_ACQUISITION.md")
    g4handoff = text("docs/handoff/2026-07-16-stage3f-gate4-retention-correction-acceptance.md")

    g1doc = text("experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md")
    g2doc = text("experiments/stage3f-publication-acquisition/GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT.md")
    g3doc = text("experiments/stage3f-publication-acquisition/GATE3_LOOPBACK_TRANSPORT_ACQUISITION_IMPLEMENTATION.md")
    g3source = text("experiments/stage3f-publication-acquisition/loopback_acquisition.py")
    g3verify = text("experiments/stage3f-publication-acquisition/verify-gate3-loopback-acquisition.py")
    g3run = text("experiments/stage3f-publication-acquisition/run-gate3-loopback-acquisition.sh")

    g6 = data("experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json")
    e1 = data("experiments/stage3e-managed-python-distribution/gate1-authority.json")
    e2 = data("experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json")
    e2a = data("experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json")
    e3 = data("experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json")
    e4 = data("experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json")
    e4a = data("experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json")
    e5doc = text("experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md")
    e5 = data("experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json")
    f1 = data("experiments/stage3f-publication-acquisition/gate1-authority.json")
    f2 = data("experiments/stage3f-publication-acquisition/gate2-publication-snapshot-authority.json")
    f3 = data("experiments/stage3f-publication-acquisition/gate3-loopback-acquisition-authority.json")
    correction = data("experiments/stage3f-publication-acquisition/gate2-retention-correction-authority.json")
    f4 = data("experiments/stage3f-publication-acquisition/gate4-retained-artifact-acquisition-authority.json")
    snap = data("experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json")
    retained = data("experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json")

    required = [
        "README.md",
        "docs/PROJECT_CONTEXT_STAGE3D.md",
        "docs/PROJECT_CONTEXT_STAGE3E.md",
        "docs/stages/STAGE3E_SCOPE.md",
        "docs/PROJECT_CONTEXT_STAGE3F.md",
        "docs/stages/STAGE3F_SCOPE.md",
        "docs/PROJECT_ORIENTATION.md",
        "docs/handoff/README.md",
        "docs/handoff/2026-07-16-stage3e-frozen-session-close.md",
        "docs/handoff/2026-07-16-stage3f-gate1-authority-start.md",
        "docs/handoff/2026-07-16-stage3f-gate2-contract-freeze.md",
        "docs/handoff/2026-07-16-stage3f-gate3-loopback-freeze.md",
        "docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md",
        "docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md",
        "docs/evidence/STAGE3E_FINAL_SUMMARY.md",
        "docs/evidence/STAGE3F_GATE1_AUTHORITY_DESIGN_RESULT.md",
        "docs/evidence/STAGE3F_GATE1_REPOSITORY_TRANSACTION_RESULT.md",
        "docs/evidence/STAGE3F_GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_RESULT.md",
        "docs/evidence/STAGE3F_GATE2_REPOSITORY_TRANSACTION_RESULT.md",
        "docs/evidence/STAGE3F_GATE3_LOOPBACK_TRANSPORT_ACQUISITION_RESULT.md",
        "experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json",
        "experiments/stage3e-managed-python-distribution/gate1-authority.json",
        "experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json",
        "experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json",
        "experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json",
        "experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json",
        "experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json",
        "experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md",
        "experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json",
        "experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md",
        "experiments/stage3f-publication-acquisition/gate1-authority.json",
        "experiments/stage3f-publication-acquisition/GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT.md",
        "experiments/stage3f-publication-acquisition/publication_snapshot.py",
        "experiments/stage3f-publication-acquisition/generate-gate2-publication-snapshot.py",
        "experiments/stage3f-publication-acquisition/verify-gate2-publication-snapshot.py",
        "experiments/stage3f-publication-acquisition/run-gate2-publication-snapshot.sh",
        "experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json",
        "experiments/stage3f-publication-acquisition/gate2-publication-snapshot-authority.json",
        "experiments/stage3f-publication-acquisition/GATE3_LOOPBACK_TRANSPORT_ACQUISITION_IMPLEMENTATION.md",
        "experiments/stage3f-publication-acquisition/loopback_acquisition.py",
        "experiments/stage3f-publication-acquisition/verify-gate3-loopback-acquisition.py",
        "experiments/stage3f-publication-acquisition/run-gate3-loopback-acquisition.sh",
        "experiments/stage3f-publication-acquisition/gate3-loopback-acquisition-authority.json",
        "experiments/stage3f-publication-acquisition/gate2-retention-correction-authority.json",
        "experiments/stage3f-publication-acquisition/GATE4_TERMUX_RETAINED_ARTIFACT_ACQUISITION.md",
        "experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json",
        "experiments/stage3f-publication-acquisition/gate4-retained-artifact-acquisition-authority.json",
        "docs/evidence/STAGE3F_GATE4_V1_DERIVATION_FAILURE.md",
        "docs/evidence/STAGE3F_GATE4_RETAINED_ARTIFACT_ACQUISITION_RESULT.md",
        "docs/handoff/2026-07-16-stage3f-gate4-retention-correction-acceptance.md",
        "scripts/test-verify-project-control-plane.py",
    ]

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    branch = git("symbolic-ref", "--quiet", "--short", "HEAD")
    diff = git("diff", "--check", "HEAD")
    snap_path = root / "experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json"
    snap_raw = snap_path.read_bytes() if snap_path.is_file() else b""
    snap_body = dig(snap, "snapshot", default={})
    retained_path = root / "experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json"
    retained_raw = retained_path.read_bytes() if retained_path.is_file() else b""
    retained_body = dig(retained, "snapshot", default={})
    retained_rows = dig(retained, "snapshot", "rows", default=[])
    retained_rowmap = {row.get("key"): row for row in retained_rows if isinstance(row, dict)} if isinstance(retained_rows, list) else {}
    snap_rows = dig(snap, "snapshot", "rows", default=[])
    rowmap = {row.get("key"): row for row in snap_rows if isinstance(row, dict)} if isinstance(snap_rows, list) else {}

    checks = {
        "required_files": all((root / path).is_file() for path in required),
        "parse_clean": not parse_errors,
        "branch_active": branch.returncode == 0 and branch.stdout.strip() == BRANCH,
        "readme_stage3e_frozen": "frozen — Gate 5 independent distribution freeze complete" in readme,
        "readme_gate4": G4 in readme and "37/37" in readme and "74/74" in readme,
        "readme_stage3f": "Stage 3-F  publication and acquisition boundaries" in readme and "Gate 4 retained acquisition frozen" in readme and "Gate 5 next" in readme,
        "context3e_status": "> **Status:** Stage 3-E frozen through Gate 5 independent distribution freeze" in ctx3e,
        "scope3e_status": "> **Status:** FROZEN — Gate 5 independent distribution freeze complete" in scope3e,
        "orientation_stage3e": "Stage 3-E is complete" in orient and "target 37/37 and independent 74/74" in orient,
        "handoff_stage3e": "Stage 3-E Gate 5 independent distribution freeze        FROZEN" in handoff,
        "gate2_evidence": G2 in e2ev and "117/117" in e2ev,
        "gate4_evidence": G4 in g4ev and G4A in g4ev and "191" in g4ev and "186/186" in g4ev,
        "summary_identity": G2 in summary and G2A in summary and G4 in summary and G4A in summary,
        "gate6_frozen": dig(g6, "status") == "accepted-bounded-feasibility",
        "stage3e_gate1_frozen": dig(e1, "status") == "design-frozen",
        "stage3e_gate2_frozen": dig(e2, "status") == "target-evidence-accepted-by-external-reaudit" and dig(e2, "accepted_result", "archive_sha256") == G2,
        "stage3e_gate2_audit": e2a.get("accepted") is True and e2a.get("check_count") == 117 and e2a.get("pass_count") == 117,
        "stage3e_gate3_frozen": e3.get("status") == "contract-frozen" and dig(e3, "selection_contract", "canonical") == "exact-patch-version-request",
        "stage3e_gate4_status": e4.get("status") == "accepted-target-evidence",
        "stage3e_gate4_archive": dig(e4, "accepted_result", "archive_sha256") == G4 and dig(e4, "accepted_result", "archive_size") == 54299,
        "stage3e_gate4_safety": dig(e4, "accepted_result", "safe_member_count") == 191 and dig(e4, "accepted_result", "result_index_count") == 186,
        "stage3e_gate4_target": dig(e4, "accepted_result", "target_verification", "check_count") == 37 and dig(e4, "accepted_result", "target_verification", "pass_count") == 37,
        "stage3e_gate4_external": dig(e4, "accepted_result", "independent_audit", "sha256") == G4A and dig(e4, "accepted_result", "independent_audit", "check_count") == 74 and dig(e4, "accepted_result", "independent_audit", "pass_count") == 74,
        "stage3e_gate4_audit": e4a.get("accepted") is True and e4a.get("check_count") == 74 and e4a.get("pass_count") == 74 and e4a.get("failed_checks") == [],
        "stage3e_gate5_doc": "> **Status:** FROZEN" in e5doc and "Gate 5 closes Stage 3-E" in e5doc,
        "stage3e_gate5_status": e5.get("status") == "independent-freeze-complete",
        "stage3e_gate5_boundary": "require a new stage" in dig(e5, "claim_boundary", default=""),
        "context3f_status": "> **Status:** Stage 3-F frozen through corrected Gate 4 retained-artifact acquisition" in ctx3f,
        "context3f_gate5": "Gate 5  independent publication/acquisition freeze       ACTIVE NEXT" in ctx3f,
        "scope3f_status": "> **Status:** ACTIVE — corrected Gate 4 frozen; Gate 5 active next" in scope3f,
        "gate1_doc": "> **Status:** DESIGN FROZEN" in g1doc,
        "gate1_evidence": "> **Status:** FROZEN — repository-only authority design" in g1ev,
        "stage_start": S3E_HEAD in start and S3E_TREE in start and MAIN in start and "control-wrapper false negative" in start,
        "gate1_transaction": F1_HEAD in g1tx and F1_TREE in g1tx and F1_RESULT in g1tx and "46/46" in g1tx,
        "stage3f_gate1_status": f1.get("status") == "design-frozen" and f1.get("class") == "R-repository-only",
        "stage3f_transition": dig(f1, "repository_transition", "source_head") == S3E_HEAD and dig(f1, "repository_transition", "source_tree") == S3E_TREE and dig(f1, "repository_transition", "resolved_main") == MAIN and dig(f1, "repository_transition", "active_branch") == BRANCH,
        "stage3f_gate5_input": dig(f1, "frozen_inputs", "stage3e_gate5_authority", "git_blob") == G5_BLOB,
        "stage3f_authorities": set(f1.get("authority_separation", [])) == {"product-identity", "catalog-row", "publication-snapshot", "endpoint-locator", "transport-observation", "acquisition-candidate", "verified-cache", "installation-root"},
        "gate2_doc": "> **Status:** CONTRACT FROZEN — local behavior verified" in g2doc and SNAPSHOT in g2doc and "18/18 PASS" in g2doc,
        "gate2_result": "> **Status:** FROZEN — local deterministic behavior verified" in g2result and SNAPSHOT_FILE in g2result and "18/18 PASS" in g2result,
        "gate2_handoff": SNAPSHOT in g2handoff and "Gate 3" in g2handoff,
        "gate2_transaction": F2_HEAD in g2tx and F2_TREE in g2tx and F2_RESULT in g2tx and "46/46" in g2tx and "56/56" in g2tx,
        "stage3f_gate2_status": f2.get("status") == "contract-frozen-local-behavior-verified" and f2.get("class") == "L-local-behavior",
        "stage3f_gate2_input": dig(f2, "frozen_inputs", "gate1_commit") == F1_HEAD and dig(f2, "frozen_inputs", "gate1_tree") == F1_TREE and dig(f2, "frozen_inputs", "gate1_result_archive_sha256") == F1_RESULT,
        "stage3f_gate2_snapshot_authority": dig(f2, "snapshot", "snapshot_sha256") == SNAPSHOT and dig(f2, "snapshot", "canonical_file_sha256") == SNAPSHOT_FILE and dig(f2, "snapshot", "canonical_file_size") == 2328 and dig(f2, "snapshot", "row_count") == 2,
        "stage3f_gate2_verification": dig(f2, "verification", "check_count") == 18 and dig(f2, "verification", "pass_count") == 18 and dig(f2, "verification", "failed_checks") == [] and dig(f2, "verification", "deterministic_repeat") is True,
        "snapshot_envelope": set(snap) == {"schema_version", "snapshot", "snapshot_sha256"} and snap.get("schema_version") == 1,
        "snapshot_digest": snap.get("snapshot_sha256") == SNAPSHOT and hashlib.sha256(canonical_bytes(snap_body)).hexdigest() == SNAPSHOT,
        "snapshot_file_identity": len(snap_raw) == 2328 and hashlib.sha256(snap_raw).hexdigest() == SNAPSHOT_FILE and snap_raw == canonical_bytes(snap),
        "snapshot_rows": isinstance(snap_rows, list) and [row.get("key") for row in snap_rows if isinstance(row, dict)] == [K145, K146],
        "snapshot_145": dig(rowmap.get(K145, {}), "artifact", "size") == 9761522 and dig(rowmap.get(K145, {}), "artifact", "sha256") == A145,
        "snapshot_146": dig(rowmap.get(K146, {}), "artifact", "size") == 11789074 and dig(rowmap.get(K146, {}), "artifact", "sha256") == A146,
        "snapshot_provenance": all(dig(rowmap.get(key, {}), "provenance", "evidence_archive_sha256") == G2 for key in (K145, K146)),
        "snapshot_locator_nonidentity": all(set(dig(rowmap.get(key, {}), "locators", default=[{}])[0]) == {"kind", "value"} for key in (K145, K146)),
        "gate3_doc": "> **Status:** IMPLEMENTATION FROZEN — local loopback behavior verified" in g3doc and "31/31" in g3doc and SNAPSHOT in g3doc,
        "gate3_result": "> **Status:** FROZEN — local loopback behavior verified" in g3result and "31/31" in g3result and "isolated fixture paths only" in g3result,
        "gate3_handoff": F2_HEAD in g3handoff and F2_TREE in g3handoff and F2_RESULT in g3handoff and "31/31 PASS" in g3handoff,
        "stage3f_gate3_status": f3.get("status") == "implementation-frozen-local-loopback-verified" and f3.get("class") == "L-local-behavior",
        "stage3f_gate3_input": dig(f3, "frozen_inputs", "gate2_commit") == F2_HEAD and dig(f3, "frozen_inputs", "gate2_tree") == F2_TREE and dig(f3, "frozen_inputs", "gate2_result_archive_sha256") == F2_RESULT,
        "stage3f_gate3_snapshot": dig(f3, "frozen_inputs", "snapshot_sha256") == SNAPSHOT and dig(f3, "frozen_inputs", "snapshot_file_sha256") == SNAPSHOT_FILE and dig(f3, "frozen_inputs", "snapshot_file_size") == 2328,
        "stage3f_gate3_verification": dig(f3, "verification", "check_count") == 31 and dig(f3, "verification", "pass_count") == 31 and dig(f3, "verification", "failed_checks") == [] and dig(f3, "verification", "success_count") == 12 and dig(f3, "verification", "expected_negative_count") == 14 and dig(f3, "verification", "incomplete_count") == 5,
        "stage3f_gate3_fixture_identity": dig(f3, "fixture_artifacts", "fixture-a", "sha256") == FIXTURE_A and dig(f3, "fixture_artifacts", "fixture-b", "sha256") == FIXTURE_B,
        "stage3f_gate3_policy": dig(f3, "implementation", "endpoint") == "http://127.0.0.1:<ephemeral-port>" and dig(f3, "implementation", "redirects") == "rejected" and dig(f3, "cache_contract", "existing_mismatch") == "fail-closed-no-overwrite",
        "stage3f_gate3_gate4": dig(f3, "gate_sequence", "gate3") == "FROZEN_LOOPBACK_TRANSPORT_ACQUISITION_IMPLEMENTATION" and dig(f3, "gate_sequence", "gate4") == "ACTIVE_NEXT_TERMUX_TARGET_NETWORK_ACQUISITION_VALIDATION",
        "gate3_source_loopback": 'ThreadingHTTPServer(("127.0.0.1", 0)' in g3source and 'parsed.hostname != "127.0.0.1"' in g3source,
        "gate3_source_fail_closed": "os.O_EXCL" in g3source and "existing-content-addressed-object-mismatch" in g3source and "candidate.unlink" in g3source,
        "gate3_source_no_redirect": "class _NoRedirect" in g3source and "redirect_request" in g3source,
        "gate3_verifier_matrix": "expected_negative" in g3verify and "incomplete" in g3verify and "deterministic-repeat" in g3verify,
        "gate3_run_bounded": "PYTHONDONTWRITEBYTECODE=1" in g3run and "verify-gate3-loopback-acquisition.py" in g3run,
        "stage3f_no_external_or_install": dig(f3, "protected_state", "target_product_execution") is False and dig(f3, "protected_state", "uv_invocation") is False and dig(f3, "cache_contract", "installation_permitted") is False and "No public endpoint" in dig(f3, "claim_boundary", default=""),
        "gate4_failure_preserved": G4_V1_RESULT in g4fail and "derive rc        1" in g4fail and "target rc        not run" in g4fail,
        "gate4_result_doc": G4_RESULT in g4result and "16/16 PASS" in g4result and "31/31 PASS" in g4result and "46/46 exact" in g4result,
        "gate4_contract_doc": "> **Status:** FROZEN" in g4doc and RETAINED_SNAPSHOT in g4doc and RA145 in g4doc and RA146 in g4doc,
        "gate4_handoff": G3_HEAD in g4handoff and G3_TREE in g4handoff and G4_V1_RESULT in g4handoff and G4_RESULT in g4handoff,
        "retention_correction_status": correction.get("status") == "accepted-explicit-authority-correction",
        "retention_correction_history": dig(correction, "historical_snapshot", "snapshot_sha256") == SNAPSHOT and dig(correction, "historical_snapshot", "exact_bytes_retained") is False and dig(correction, "historical_snapshot", "status") == "historical-local-contract-fixture-not-selectable-for-acquisition",
        "retention_correction_policy": dig(correction, "correction_policy", "ordinary_exact_key_redefinition_allowed") is False and dig(correction, "correction_policy", "historical_snapshot_selectable") is False and dig(correction, "correction_policy", "retained_snapshot_selectable") is True,
        "retention_correction_v1": dig(correction, "trigger", "gate4_v1_result_archive_sha256") == G4_V1_RESULT and dig(correction, "trigger", "derive_rc") == 1,
        "gate4_authority_status": f4.get("status") == "accepted-target-evidence-independent-audit-complete",
        "gate4_authority_input": dig(f4, "repository_input", "head") == G3_HEAD and dig(f4, "repository_input", "tree") == G3_TREE and dig(f4, "repository_input", "main") == MAIN,
        "gate4_authority_archive": dig(f4, "accepted_result", "archive_sha256") == G4_RESULT and dig(f4, "accepted_result", "archive_size") == 42968242 and dig(f4, "accepted_result", "safe_member_count") == 62 and dig(f4, "accepted_result", "result_index_count") == 46,
        "gate4_authority_checks": dig(f4, "accepted_result", "target_matrix", "check_count") == 16 and dig(f4, "accepted_result", "target_matrix", "pass_count") == 16 and dig(f4, "accepted_result", "independent_audit", "check_count") == 31 and dig(f4, "accepted_result", "independent_audit", "pass_count") == 31,
        "gate4_authority_boundary": dig(f4, "protected_state", "uv_invocation") is False and dig(f4, "protected_state", "product_execution") is False and dig(f4, "protected_state", "installation_mutation") is False and dig(f4, "protected_state", "external_network") is False,
        "retained_snapshot_envelope": set(retained) == {"schema_version", "snapshot", "snapshot_sha256"} and retained.get("schema_version") == 1,
        "retained_snapshot_digest": retained.get("snapshot_sha256") == RETAINED_SNAPSHOT and hashlib.sha256(canonical_bytes(retained_body)).hexdigest() == RETAINED_SNAPSHOT,
        "retained_snapshot_file": len(retained_raw) == 2997 and hashlib.sha256(retained_raw).hexdigest() == RETAINED_SNAPSHOT_FILE and retained_raw == canonical_bytes(retained),
        "retained_snapshot_rows": isinstance(retained_rows, list) and [row.get("key") for row in retained_rows if isinstance(row, dict)] == [K145, K146],
        "retained_snapshot_145": dig(retained_rowmap.get(K145, {}), "artifact", "size") == 9761545 and dig(retained_rowmap.get(K145, {}), "artifact", "sha256") == RA145,
        "retained_snapshot_146": dig(retained_rowmap.get(K146, {}), "artifact", "size") == 11788907 and dig(retained_rowmap.get(K146, {}), "artifact", "sha256") == RA146,
        "gate4_gate5_transition": dig(f4, "gate_sequence", "gate4") == "FROZEN_RETAINED_ACTUAL_BYTES" and dig(f4, "gate_sequence", "gate5") == "ACTIVE_NEXT_INDEPENDENT_PUBLICATION_ACQUISITION_FREEZE",
        "git_diff_check": diff.returncode == 0,
    }

    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": 5,
        "verification_kind": "project-control-plane-through-stage3f-gate4-retention-correction",
        "pass": not failed and not missing and not parse_errors,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "failed_checks": failed,
        "missing_files": sorted(set(missing)),
        "parse_errors": parse_errors,
        "checks": dict(sorted(checks.items())),
        "claim_boundary": "Stage 3-F Gate 4 accepts retained actual archive acquisition over Termux loopback and isolated cache, with explicit correction of the non-retained Gate 2 concrete snapshot. Public hosting, origin trust, uv acquisition, execution, installation, recovery, concurrency, durability, third products, and upstream support remain unaccepted.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = verify(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
