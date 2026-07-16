#!/usr/bin/env python3
"""Verify frozen Stage 3-E and active Stage 3-F through Gate 1."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
from typing import Any
BRANCH="agent/stage3f-publication-acquisition"
S3E_HEAD="6419e107e4aa8400ebd3d98f3583999075b8b935"
S3E_TREE="e16edd99bfadf2135d0b632ddef4d292c0d80ea6"
MAIN="b5a2ca39d1250122312355dd3dbc6165b9409786"
G2="3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2"
G2A="5813305c22528354e6af686330e8f635db2b90a8a7a48ed5ed3c9ad4d1a4fb4d"
G4="4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112"
G4A="794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a"
G5_BLOB="651789e14f899b852f8fb8b4cbeceeaca318b19a"
def dig(v:Any,*ks,default=None):
 for k in ks:
  if not isinstance(v,dict) or k not in v:return default
  v=v[k]
 return v
def verify(root:Path)->dict[str,Any]:
 root=root.resolve();missing=[];parse_errors={}
 def text(path):
  p=root/path
  if not p.is_file():missing.append(path);return ""
  try:return p.read_text(encoding="utf-8")
  except Exception as e:parse_errors[path]=f"{type(e).__name__}: {e}";return ""
 def data(path):
  raw=text(path)
  if not raw:return {}
  try:v=json.loads(raw)
  except Exception as e:parse_errors[path]=f"{type(e).__name__}: {e}";return {}
  if not isinstance(v,dict):parse_errors[path]="top-level JSON is not object";return {}
  return v
 readme=text("README.md");ctx3e=text("docs/PROJECT_CONTEXT_STAGE3E.md");scope3e=text("docs/stages/STAGE3E_SCOPE.md");orient=text("docs/PROJECT_ORIENTATION.md");handoff=text("docs/handoff/README.md")
 ctx3f=text("docs/PROJECT_CONTEXT_STAGE3F.md");scope3f=text("docs/stages/STAGE3F_SCOPE.md");g1doc=text("experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md");g1ev=text("docs/evidence/STAGE3F_GATE1_AUTHORITY_DESIGN_RESULT.md");start=text("docs/handoff/2026-07-16-stage3f-gate1-authority-start.md")
 g2ev=text("docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md");g4ev=text("docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md");summary=text("docs/evidence/STAGE3E_FINAL_SUMMARY.md")
 g6=data("experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json");e1=data("experiments/stage3e-managed-python-distribution/gate1-authority.json");e2=data("experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json");e2a=data("experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json");e3=data("experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json")
 e4=data("experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json");e4a=data("experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json");e5doc=text("experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md");e5=data("experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json");f1=data("experiments/stage3f-publication-acquisition/gate1-authority.json")
 required=["README.md","docs/PROJECT_CONTEXT_STAGE3D.md","docs/PROJECT_CONTEXT_STAGE3E.md","docs/stages/STAGE3E_SCOPE.md","docs/PROJECT_CONTEXT_STAGE3F.md","docs/stages/STAGE3F_SCOPE.md","docs/PROJECT_ORIENTATION.md","docs/handoff/README.md","docs/handoff/2026-07-16-stage3e-frozen-session-close.md","docs/handoff/2026-07-16-stage3f-gate1-authority-start.md","docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md","docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md","docs/evidence/STAGE3E_FINAL_SUMMARY.md","docs/evidence/STAGE3F_GATE1_AUTHORITY_DESIGN_RESULT.md","experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json","experiments/stage3e-managed-python-distribution/gate1-authority.json","experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json","experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json","experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json","experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json","experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json","experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md","experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json","experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md","experiments/stage3f-publication-acquisition/gate1-authority.json","scripts/test-verify-project-control-plane.py"]
 def git(*args):return subprocess.run(["git",*args],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 br=git("symbolic-ref","--quiet","--short","HEAD");diff=git("diff","--check","HEAD")
 checks={
  "required_files":all((root/p).is_file() for p in required),"parse_clean":not parse_errors,"branch_active":br.returncode==0 and br.stdout.strip()==BRANCH,
  "readme_stage3e_frozen":"frozen — Gate 5 independent distribution freeze complete" in readme,"readme_gate4":G4 in readme and "37/37" in readme and "74/74" in readme,
  "readme_stage3f":"Stage 3-F  publication and acquisition boundaries" in readme and "Gate 1 authority design frozen" in readme,
  "context3e_status":"> **Status:** Stage 3-E frozen through Gate 5 independent distribution freeze" in ctx3e,"scope3e_status":"> **Status:** FROZEN — Gate 5 independent distribution freeze complete" in scope3e,
  "orientation_stage3e":"Stage 3-E is complete" in orient and "target 37/37 and independent 74/74" in orient,
  "handoff_stage3e":"Stage 3-E Gate 5 independent distribution freeze        FROZEN" in handoff,
  "gate2_evidence":G2 in g2ev and "117/117" in g2ev,"gate4_evidence":G4 in g4ev and G4A in g4ev and "191" in g4ev and "186/186" in g4ev,"summary_identity":G2 in summary and G2A in summary and G4 in summary and G4A in summary,
  "gate6_frozen":dig(g6,"status")=="accepted-bounded-feasibility","stage3e_gate1_frozen":dig(e1,"status")=="design-frozen",
  "stage3e_gate2_frozen":dig(e2,"status")=="target-evidence-accepted-by-external-reaudit" and dig(e2,"accepted_result","archive_sha256")==G2,
  "stage3e_gate2_audit":e2a.get("accepted") is True and e2a.get("check_count")==117 and e2a.get("pass_count")==117,
  "stage3e_gate3_frozen":e3.get("status")=="contract-frozen" and dig(e3,"selection_contract","canonical")=="exact-patch-version-request",
  "stage3e_gate4_status":e4.get("status")=="accepted-target-evidence","stage3e_gate4_archive":dig(e4,"accepted_result","archive_sha256")==G4 and dig(e4,"accepted_result","archive_size")==54299,
  "stage3e_gate4_safety":dig(e4,"accepted_result","safe_member_count")==191 and dig(e4,"accepted_result","result_index_count")==186,
  "stage3e_gate4_target":dig(e4,"accepted_result","target_verification","check_count")==37 and dig(e4,"accepted_result","target_verification","pass_count")==37,
  "stage3e_gate4_external":dig(e4,"accepted_result","independent_audit","sha256")==G4A and dig(e4,"accepted_result","independent_audit","check_count")==74 and dig(e4,"accepted_result","independent_audit","pass_count")==74,
  "stage3e_gate4_audit":e4a.get("accepted") is True and e4a.get("check_count")==74 and e4a.get("pass_count")==74 and e4a.get("failed_checks")==[],
  "stage3e_gate5_doc":"> **Status:** FROZEN" in e5doc and "Gate 5 closes Stage 3-E" in e5doc,"stage3e_gate5_status":e5.get("status")=="independent-freeze-complete",
  "stage3e_gate5_boundary":"require a new stage" in dig(e5,"claim_boundary",default=""),
  "context3f_status":"> **Status:** Stage 3-F Gate 1 publication/acquisition authority design frozen" in ctx3f,
  "context3f_next":"Gate 2  immutable publication snapshot contract         ACTIVE NEXT" in ctx3f,
  "scope3f_status":"> **Status:** ACTIVE — Gate 1 authority design frozen; Gate 2 active next" in scope3f,
  "gate1_doc":"> **Status:** DESIGN FROZEN" in g1doc and "deterministic immutable-publication snapshot contract" in g1doc,
  "gate1_evidence":"> **Status:** FROZEN — repository-only authority design" in g1ev and "No target rerun" in g1ev,
  "stage_start":S3E_HEAD in start and S3E_TREE in start and MAIN in start and "control-wrapper false negative" in start,
  "stage3f_status":f1.get("status")=="design-frozen" and f1.get("class")=="R-repository-only",
  "stage3f_transition":dig(f1,"repository_transition","source_branch")=="agent/stage3e-managed-python-distribution" and dig(f1,"repository_transition","source_head")==S3E_HEAD and dig(f1,"repository_transition","source_tree")==S3E_TREE and dig(f1,"repository_transition","resolved_main")==MAIN and dig(f1,"repository_transition","active_branch")==BRANCH,
  "stage3f_gate5_input":dig(f1,"frozen_inputs","stage3e_gate5_authority","git_blob")==G5_BLOB and dig(f1,"frozen_inputs","stage3e_gate5_authority","status")=="independent-freeze-complete",
  "stage3f_authorities":set(f1.get("authority_separation",[]))=={"product-identity","catalog-row","publication-snapshot","endpoint-locator","transport-observation","acquisition-candidate","verified-cache","installation-root"},
  "stage3f_identity":dig(f1,"identity_contract","locator_is_identity") is False and dig(f1,"identity_contract","endpoint_is_identity") is False and dig(f1,"identity_contract","existing_exact_key_redefinition") is False,
  "stage3f_publication":dig(f1,"publication_contract","snapshot")=="canonical-immutable-metadata" and dig(f1,"publication_contract","mutable_endpoint")=="may-select-immutable-snapshot-only",
  "stage3f_acquisition":dig(f1,"acquisition_contract","receive_state")=="untrusted-candidate" and dig(f1,"acquisition_contract","failed_candidate_mutates_verified_state") is False and dig(f1,"acquisition_contract","failed_candidate_mutates_installation") is False,
  "stage3f_cache":dig(f1,"cache_contract","verified_key")=="artifact-sha256" and dig(f1,"cache_contract","unverified_partial_authoritative") is False,
  "stage3f_installation":dig(f1,"installation_contract","stage3e_project_owned_root")=="unchanged-and-independent" and dig(f1,"installation_contract","uv_default_managed_root") is False,
  "stage3f_gate_sequence":dig(f1,"gate_sequence","gate1")=="FROZEN_AUTHORITY_DESIGN" and dig(f1,"gate_sequence","gate2")=="ACTIVE_NEXT_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT",
  "stage3f_gate2":dig(f1,"selected_gate2","kind")=="deterministic-immutable-publication-snapshot-contract-and-fixture-census" and dig(f1,"selected_gate2","class")=="L-local-behavior" and dig(f1,"selected_gate2","network")=="none" and set(dig(f1,"selected_gate2","required_fixtures",default=[]))=={"success","expected-negative","incomplete"},
  "stage3f_no_target":"No target rerun or independent target audit is required" in g1ev and dig(f1,"selected_gate2","target_execution")=="none",
  "git_diff_check":diff.returncode==0,
 }
 failed=sorted(k for k,v in checks.items() if not v)
 return {"schema_version":2,"verification_kind":"project-control-plane-through-stage3f-gate1","pass":not failed and not missing and not parse_errors,"check_count":len(checks),"pass_count":sum(checks.values()),"failed_checks":failed,"missing_files":sorted(set(missing)),"parse_errors":parse_errors,"checks":dict(sorted(checks.items())),"claim_boundary":"Stage 3-F Gate 1 freezes publication/acquisition authority separation only. Gate 2 is repository-local; network, uv acquisition, target execution, installation, origin trust, upgrades, recovery, concurrency, durability, third products, and upstream support remain unaccepted."}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();r=verify(a.root);print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
