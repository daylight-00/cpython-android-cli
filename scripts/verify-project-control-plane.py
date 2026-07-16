#!/usr/bin/env python3
"""Verify frozen Stage 3-E and active Stage 3-F through Gate 2."""
from __future__ import annotations
import argparse,hashlib,json,subprocess
from pathlib import Path
from typing import Any
BRANCH="agent/stage3f-publication-acquisition"
S3E_HEAD="6419e107e4aa8400ebd3d98f3583999075b8b935"
S3E_TREE="e16edd99bfadf2135d0b632ddef4d292c0d80ea6"
MAIN="b5a2ca39d1250122312355dd3dbc6165b9409786"
F1_HEAD="39e5c6d56a45495a4f23b73b6fa0704ba28fbc74"
F1_TREE="7a0c476e60280c23dd8edd2627b25b42e3fa1429"
F1_RESULT="eb6f1356fa09473bc4564e0e3a1ae1d7940ecac287d69baa2abf4bd8c494a438"
G2="3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2"
G2A="5813305c22528354e6af686330e8f635db2b90a8a7a48ed5ed3c9ad4d1a4fb4d"
G4="4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112"
G4A="794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a"
G5_BLOB="651789e14f899b852f8fb8b4cbeceeaca318b19a"
SNAPSHOT="a00027a81956ef175bf537eff3a92286e26c1120fa536d0a8ad6a096a1760f8c"
SNAPSHOT_FILE="c942b9863e33c2edf7d628780bfeef0957b427fb12259ba49e708cb4858c52bc"
A145="18832bb7982a679fcee067e2d33e106dac84307687b63803be105714596d422f"
A146="9575edef24d84b2fce32c55093ab01cb8b2b1a41b521d2011653fae87b5bcb64"
K145="cpython-3.14.5-linux-aarch64-none";K146="cpython-3.14.6-linux-aarch64-none"
def dig(v:Any,*ks,default=None):
 for k in ks:
  if not isinstance(v,dict) or k not in v:return default
  v=v[k]
 return v
def canonical_bytes(v:Any)->bytes:return (json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()
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
 ctx3f=text("docs/PROJECT_CONTEXT_STAGE3F.md");scope3f=text("docs/stages/STAGE3F_SCOPE.md");g1doc=text("experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md");g1ev=text("docs/evidence/STAGE3F_GATE1_AUTHORITY_DESIGN_RESULT.md");g1tx=text("docs/evidence/STAGE3F_GATE1_REPOSITORY_TRANSACTION_RESULT.md");start=text("docs/handoff/2026-07-16-stage3f-gate1-authority-start.md")
 g2doc=text("experiments/stage3f-publication-acquisition/GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT.md");g2result=text("docs/evidence/STAGE3F_GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_RESULT.md");g2handoff=text("docs/handoff/2026-07-16-stage3f-gate2-contract-freeze.md")
 e2ev=text("docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md");g4ev=text("docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md");summary=text("docs/evidence/STAGE3E_FINAL_SUMMARY.md")
 g6=data("experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json");e1=data("experiments/stage3e-managed-python-distribution/gate1-authority.json");e2=data("experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json");e2a=data("experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json");e3=data("experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json")
 e4=data("experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json");e4a=data("experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json");e5doc=text("experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md");e5=data("experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json")
 f1=data("experiments/stage3f-publication-acquisition/gate1-authority.json");f2=data("experiments/stage3f-publication-acquisition/gate2-publication-snapshot-authority.json");snap=data("experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json")
 required=["README.md","docs/PROJECT_CONTEXT_STAGE3D.md","docs/PROJECT_CONTEXT_STAGE3E.md","docs/stages/STAGE3E_SCOPE.md","docs/PROJECT_CONTEXT_STAGE3F.md","docs/stages/STAGE3F_SCOPE.md","docs/PROJECT_ORIENTATION.md","docs/handoff/README.md","docs/handoff/2026-07-16-stage3e-frozen-session-close.md","docs/handoff/2026-07-16-stage3f-gate1-authority-start.md","docs/handoff/2026-07-16-stage3f-gate2-contract-freeze.md","docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md","docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md","docs/evidence/STAGE3E_FINAL_SUMMARY.md","docs/evidence/STAGE3F_GATE1_AUTHORITY_DESIGN_RESULT.md","docs/evidence/STAGE3F_GATE1_REPOSITORY_TRANSACTION_RESULT.md","docs/evidence/STAGE3F_GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_RESULT.md","experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json","experiments/stage3e-managed-python-distribution/gate1-authority.json","experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json","experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json","experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json","experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json","experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json","experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md","experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json","experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md","experiments/stage3f-publication-acquisition/gate1-authority.json","experiments/stage3f-publication-acquisition/GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT.md","experiments/stage3f-publication-acquisition/publication_snapshot.py","experiments/stage3f-publication-acquisition/generate-gate2-publication-snapshot.py","experiments/stage3f-publication-acquisition/verify-gate2-publication-snapshot.py","experiments/stage3f-publication-acquisition/run-gate2-publication-snapshot.sh","experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json","experiments/stage3f-publication-acquisition/gate2-publication-snapshot-authority.json","scripts/test-verify-project-control-plane.py"]
 def git(*args):return subprocess.run(["git",*args],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 br=git("symbolic-ref","--quiet","--short","HEAD");diff=git("diff","--check","HEAD")
 snap_path=root/"experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json"
 snap_raw=snap_path.read_bytes() if snap_path.is_file() else b""
 snap_body=dig(snap,"snapshot",default={})
 snap_rows=dig(snap,"snapshot","rows",default=[])
 rowmap={r.get("key"):r for r in snap_rows if isinstance(r,dict)} if isinstance(snap_rows,list) else {}
 checks={
  "required_files":all((root/p).is_file() for p in required),"parse_clean":not parse_errors,"branch_active":br.returncode==0 and br.stdout.strip()==BRANCH,
  "readme_stage3e_frozen":"frozen — Gate 5 independent distribution freeze complete" in readme,"readme_gate4":G4 in readme and "37/37" in readme and "74/74" in readme,
  "readme_stage3f":"Stage 3-F  publication and acquisition boundaries" in readme and "Gate 2 snapshot contract frozen" in readme and "Gate 3 next" in readme,
  "context3e_status":"> **Status:** Stage 3-E frozen through Gate 5 independent distribution freeze" in ctx3e,"scope3e_status":"> **Status:** FROZEN — Gate 5 independent distribution freeze complete" in scope3e,
  "orientation_stage3e":"Stage 3-E is complete" in orient and "target 37/37 and independent 74/74" in orient,"handoff_stage3e":"Stage 3-E Gate 5 independent distribution freeze        FROZEN" in handoff,
  "gate2_evidence":G2 in e2ev and "117/117" in e2ev,"gate4_evidence":G4 in g4ev and G4A in g4ev and "191" in g4ev and "186/186" in g4ev,"summary_identity":G2 in summary and G2A in summary and G4 in summary and G4A in summary,
  "gate6_frozen":dig(g6,"status")=="accepted-bounded-feasibility","stage3e_gate1_frozen":dig(e1,"status")=="design-frozen","stage3e_gate2_frozen":dig(e2,"status")=="target-evidence-accepted-by-external-reaudit" and dig(e2,"accepted_result","archive_sha256")==G2,
  "stage3e_gate2_audit":e2a.get("accepted") is True and e2a.get("check_count")==117 and e2a.get("pass_count")==117,"stage3e_gate3_frozen":e3.get("status")=="contract-frozen" and dig(e3,"selection_contract","canonical")=="exact-patch-version-request",
  "stage3e_gate4_status":e4.get("status")=="accepted-target-evidence","stage3e_gate4_archive":dig(e4,"accepted_result","archive_sha256")==G4 and dig(e4,"accepted_result","archive_size")==54299,"stage3e_gate4_safety":dig(e4,"accepted_result","safe_member_count")==191 and dig(e4,"accepted_result","result_index_count")==186,
  "stage3e_gate4_target":dig(e4,"accepted_result","target_verification","check_count")==37 and dig(e4,"accepted_result","target_verification","pass_count")==37,"stage3e_gate4_external":dig(e4,"accepted_result","independent_audit","sha256")==G4A and dig(e4,"accepted_result","independent_audit","check_count")==74 and dig(e4,"accepted_result","independent_audit","pass_count")==74,
  "stage3e_gate4_audit":e4a.get("accepted") is True and e4a.get("check_count")==74 and e4a.get("pass_count")==74 and e4a.get("failed_checks")==[],"stage3e_gate5_doc":"> **Status:** FROZEN" in e5doc and "Gate 5 closes Stage 3-E" in e5doc,"stage3e_gate5_status":e5.get("status")=="independent-freeze-complete","stage3e_gate5_boundary":"require a new stage" in dig(e5,"claim_boundary",default=""),
  "context3f_status":"> **Status:** Stage 3-F frozen through Gate 2 immutable publication snapshot contract" in ctx3f,"context3f_gate3":"Gate 3  loopback transport and acquisition implementation ACTIVE NEXT" in ctx3f,"scope3f_status":"> **Status:** ACTIVE — Gates 1 and 2 frozen; Gate 3 active next" in scope3f,
  "gate1_doc":"> **Status:** DESIGN FROZEN" in g1doc,"gate1_evidence":"> **Status:** FROZEN — repository-only authority design" in g1ev,"stage_start":S3E_HEAD in start and S3E_TREE in start and MAIN in start and "control-wrapper false negative" in start,
  "gate1_transaction":F1_HEAD in g1tx and F1_TREE in g1tx and F1_RESULT in g1tx and "46/46" in g1tx,
  "stage3f_gate1_status":f1.get("status")=="design-frozen" and f1.get("class")=="R-repository-only","stage3f_transition":dig(f1,"repository_transition","source_head")==S3E_HEAD and dig(f1,"repository_transition","source_tree")==S3E_TREE and dig(f1,"repository_transition","resolved_main")==MAIN and dig(f1,"repository_transition","active_branch")==BRANCH,
  "stage3f_gate5_input":dig(f1,"frozen_inputs","stage3e_gate5_authority","git_blob")==G5_BLOB,"stage3f_authorities":set(f1.get("authority_separation",[]))=={"product-identity","catalog-row","publication-snapshot","endpoint-locator","transport-observation","acquisition-candidate","verified-cache","installation-root"},
  "gate2_doc":"> **Status:** CONTRACT FROZEN — local behavior verified" in g2doc and SNAPSHOT in g2doc and "18/18 PASS" in g2doc,"gate2_result":"> **Status:** FROZEN — local deterministic behavior verified" in g2result and SNAPSHOT_FILE in g2result and "18/18 PASS" in g2result,"gate2_handoff":SNAPSHOT in g2handoff and "Gate 3" in g2handoff,
  "stage3f_gate2_status":f2.get("status")=="contract-frozen-local-behavior-verified" and f2.get("class")=="L-local-behavior","stage3f_gate2_input":dig(f2,"frozen_inputs","gate1_commit")==F1_HEAD and dig(f2,"frozen_inputs","gate1_tree")==F1_TREE and dig(f2,"frozen_inputs","gate1_result_archive_sha256")==F1_RESULT,
  "stage3f_gate2_snapshot_authority":dig(f2,"snapshot","snapshot_sha256")==SNAPSHOT and dig(f2,"snapshot","canonical_file_sha256")==SNAPSHOT_FILE and dig(f2,"snapshot","canonical_file_size")==2328 and dig(f2,"snapshot","row_count")==2,
  "stage3f_gate2_verification":dig(f2,"verification","check_count")==18 and dig(f2,"verification","pass_count")==18 and dig(f2,"verification","failed_checks")==[] and dig(f2,"verification","deterministic_repeat") is True,
  "stage3f_gate2_gate3":dig(f2,"gate_sequence","gate2")=="FROZEN_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT" and dig(f2,"gate_sequence","gate3")=="ACTIVE_NEXT_LOOPBACK_TRANSPORT_ACQUISITION_IMPLEMENTATION",
  "snapshot_envelope":set(snap)=={"schema_version","snapshot","snapshot_sha256"} and snap.get("schema_version")==1,"snapshot_digest":snap.get("snapshot_sha256")==SNAPSHOT and hashlib.sha256(canonical_bytes(snap_body)).hexdigest()==SNAPSHOT,
  "snapshot_file_identity":len(snap_raw)==2328 and hashlib.sha256(snap_raw).hexdigest()==SNAPSHOT_FILE and snap_raw==canonical_bytes(snap),"snapshot_rows":isinstance(snap_rows,list) and [r.get("key") for r in snap_rows if isinstance(r,dict)]==[K145,K146],
  "snapshot_145":dig(rowmap.get(K145,{}),"artifact","size")==9761522 and dig(rowmap.get(K145,{}),"artifact","sha256")==A145,"snapshot_146":dig(rowmap.get(K146,{}),"artifact","size")==11789074 and dig(rowmap.get(K146,{}),"artifact","sha256")==A146,
  "snapshot_provenance":all(dig(rowmap.get(k,{}),"provenance","evidence_archive_sha256")==G2 for k in (K145,K146)),"snapshot_locator_nonidentity":all(set(dig(rowmap.get(k,{}),"locators",default=[{}])[0])=={"kind","value"} for k in (K145,K146)),
  "stage3f_no_target":dig(f2,"candidate_observation_contract","actual_cache_mutation") is False and dig(f2,"candidate_observation_contract","actual_installation") is False and "no socket" in dig(f2,"claim_boundary",default="").lower(),
  "git_diff_check":diff.returncode==0,
 }
 failed=sorted(k for k,v in checks.items() if not v)
 return {"schema_version":3,"verification_kind":"project-control-plane-through-stage3f-gate2","pass":not failed and not missing and not parse_errors,"check_count":len(checks),"pass_count":sum(checks.values()),"failed_checks":failed,"missing_files":sorted(set(missing)),"parse_errors":parse_errors,"checks":dict(sorted(checks.items())),"claim_boundary":"Stage 3-F Gate 2 freezes repository-local canonical publication metadata and candidate-observation policy only. Public networking, uv acquisition, target execution, cache mutation, installation, origin trust, recovery, concurrency, durability, third products, and upstream support remain unaccepted."}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();r=verify(a.root);print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
