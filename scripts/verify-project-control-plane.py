#!/usr/bin/env python3
"""Verify frozen Stage 3-D and frozen Stage 3-E through Gate 5."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
from typing import Any
BRANCH="agent/stage3e-managed-python-distribution"
G2="3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2"
G2A="5813305c22528354e6af686330e8f635db2b90a8a7a48ed5ed3c9ad4d1a4fb4d"
G4="4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112"
G4A="794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a"
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
 readme=text("README.md");ctx=text("docs/PROJECT_CONTEXT_STAGE3E.md");scope=text("docs/stages/STAGE3E_SCOPE.md");orient=text("docs/PROJECT_ORIENTATION.md");handoff=text("docs/handoff/README.md")
 g2ev=text("docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md");g4ev=text("docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md");summary=text("docs/evidence/STAGE3E_FINAL_SUMMARY.md")
 g6=data("experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json");g1=data("experiments/stage3e-managed-python-distribution/gate1-authority.json");g2=data("experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json");g2a=data("experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json");g3=data("experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json")
 g4=data("experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json");g4a=data("experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json");g5doc=text("experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md");g5=data("experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json")
 required=["README.md","docs/PROJECT_CONTEXT_STAGE3D.md","docs/PROJECT_CONTEXT_STAGE3E.md","docs/stages/STAGE3E_SCOPE.md","docs/PROJECT_ORIENTATION.md","docs/handoff/README.md","docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md","docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md","docs/evidence/STAGE3E_FINAL_SUMMARY.md","experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json","experiments/stage3e-managed-python-distribution/gate1-authority.json","experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json","experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json","experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json","experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json","experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json","experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md","experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json","scripts/test-verify-project-control-plane.py"]
 def git(*args):return subprocess.run(["git",*args],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 br=git("symbolic-ref","--quiet","--short","HEAD");diff=git("diff","--check","HEAD")
 checks={
  "required_files":all((root/p).is_file() for p in required),"parse_clean":not parse_errors,"branch_frozen":br.returncode==0 and br.stdout.strip()==BRANCH,
  "readme_status":"frozen — Gate 5 independent distribution freeze complete" in readme,
  "readme_gate4":G4 in readme and "37/37" in readme and "74/74" in readme,
  "context_status":"> **Status:** Stage 3-E frozen through Gate 5 independent distribution freeze" in ctx,
  "context_all_gates":"Gate 5  independent distribution freeze                 FROZEN" in ctx and "Gate 4  project-owned persistent-root validation        FROZEN" in ctx,
  "scope_status":"> **Status:** FROZEN — Gate 5 independent distribution freeze complete" in scope,
  "orientation_complete":"Stage 3-E is complete" in orient and "target 37/37 and independent 74/74" in orient,
  "handoff_complete":"Stage 3-E Gate 5 independent distribution freeze        FROZEN" in handoff,
  "gate2_evidence":G2 in g2ev and "117/117" in g2ev,
  "gate4_evidence":G4 in g4ev and G4A in g4ev and "191" in g4ev and "186/186" in g4ev,
  "summary_identity":G2 in summary and G2A in summary and G4 in summary and G4A in summary,
  "gate6_frozen":dig(g6,"status")=="accepted-bounded-feasibility","gate1_frozen":dig(g1,"status")=="design-frozen",
  "gate2_frozen":dig(g2,"status")=="target-evidence-accepted-by-external-reaudit" and dig(g2,"accepted_result","archive_sha256")==G2,
  "gate2_audit":g2a.get("accepted") is True and g2a.get("check_count")==117 and g2a.get("pass_count")==117,
  "gate3_frozen":g3.get("status")=="contract-frozen" and dig(g3,"selection_contract","canonical")=="exact-patch-version-request",
  "gate4_status":g4.get("status")=="accepted-target-evidence",
  "gate4_archive":dig(g4,"accepted_result","archive_sha256")==G4 and dig(g4,"accepted_result","archive_size")==54299,
  "gate4_safety":dig(g4,"accepted_result","safe_member_count")==191 and dig(g4,"accepted_result","result_index_count")==186,
  "gate4_target":dig(g4,"accepted_result","target_verification","check_count")==37 and dig(g4,"accepted_result","target_verification","pass_count")==37,
  "gate4_external":dig(g4,"accepted_result","independent_audit","sha256")==G4A and dig(g4,"accepted_result","independent_audit","check_count")==74 and dig(g4,"accepted_result","independent_audit","pass_count")==74,
  "gate4_correction":dig(g4,"correction_lineage","v1","verification")=="36/37" and "umask" in dig(g4,"correction_lineage","v1","classification",default=""),
  "gate4_root":g4.get("persistent_root")=="$HOME/.local/share/hw-t/cpython-managed/gate4-validation-v2",
  "gate4_audit_pass":g4a.get("accepted") is True and g4a.get("check_count")==74 and g4a.get("pass_count")==74 and g4a.get("failed_checks")==[],
  "gate4_audit_archive":dig(g4a,"archive","sha256")==G4 and dig(g4a,"archive","safe_member_count")==191 and dig(g4a,"archive","result_index_count")==186,
  "gate5_doc":"> **Status:** FROZEN" in g5doc and "Gate 5 closes Stage 3-E" in g5doc,
  "gate5_status":g5.get("status")=="independent-freeze-complete",
  "gate5_sequence":all(str(v).startswith("FROZEN") for v in dig(g5,"gate_sequence",default={}).values()) and len(dig(g5,"gate_sequence",default={}))==5,
  "gate5_inputs":dig(g5,"input_authorities","gate4_archive_sha256")==G4 and dig(g5,"input_authorities","gate4_independent_audit_sha256")==G4A,
  "gate5_boundary":"require a new stage" in dig(g5,"claim_boundary",default=""),
  "system_coexistence":dig(g5,"accepted_surface","system_python_contract")=="unchanged-and-independent",
  "deferred_default_root":"uv-default-managed-root" in dig(g5,"deferred_to_new_stage",default=[]),
  "git_diff_check":diff.returncode==0,
 }
 failed=sorted(k for k,v in checks.items() if not v)
 return {"schema_version":1,"verification_kind":"project-control-plane-through-stage3e-gate5","pass":not failed and not missing and not parse_errors,"check_count":len(checks),"pass_count":sum(checks.values()),"failed_checks":failed,"missing_files":sorted(set(missing)),"parse_errors":parse_errors,"checks":dict(sorted(checks.items())),"claim_boundary":"Stage 3-E is frozen for exact local project-owned persistent-root managed-Python distribution only. Publication, default-root integration, global exposure, upgrades, recovery, concurrency, durability, third products, and upstream support remain unaccepted."}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();r=verify(a.root);print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
