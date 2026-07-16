#!/usr/bin/env python3
"""Exercise Stage 3-F Gate 2 project-control success, expected-negative, and incomplete fixtures."""
from __future__ import annotations
import sys
sys.dont_write_bytecode=True
import importlib.util,json,shutil,subprocess,tempfile
from pathlib import Path
SCRIPT=Path(__file__).resolve().with_name("verify-project-control-plane.py")
SOURCE=Path(__file__).resolve().parents[1]
def w(p:Path,s:str):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding="utf-8")
def j(p:Path,v):w(p,json.dumps(v,indent=2,sort_keys=True)+"\n")
def cp(rel:str,r:Path):
 src=SOURCE/rel;dst=r/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def load():
 s=importlib.util.spec_from_file_location("v",SCRIPT);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def make(r:Path):
 w(r/"README.md","frozen — Gate 5 independent distribution freeze complete\n4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112 37/37 74/74\nStage 3-F  publication and acquisition boundaries active — Gate 2 snapshot contract frozen; Gate 3 next\n")
 w(r/"docs/PROJECT_CONTEXT_STAGE3D.md","frozen\n");w(r/"docs/PROJECT_CONTEXT_STAGE3E.md","> **Status:** Stage 3-E frozen through Gate 5 independent distribution freeze\n");w(r/"docs/stages/STAGE3E_SCOPE.md","> **Status:** FROZEN — Gate 5 independent distribution freeze complete\n")
 for rel in ["docs/PROJECT_CONTEXT_STAGE3F.md","docs/stages/STAGE3F_SCOPE.md","docs/PROJECT_ORIENTATION.md","docs/handoff/README.md","docs/handoff/2026-07-16-stage3f-gate2-contract-freeze.md","docs/evidence/STAGE3F_GATE1_REPOSITORY_TRANSACTION_RESULT.md","docs/evidence/STAGE3F_GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_RESULT.md","experiments/stage3f-publication-acquisition/GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT.md","experiments/stage3f-publication-acquisition/publication_snapshot.py","experiments/stage3f-publication-acquisition/generate-gate2-publication-snapshot.py","experiments/stage3f-publication-acquisition/verify-gate2-publication-snapshot.py","experiments/stage3f-publication-acquisition/run-gate2-publication-snapshot.sh","experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json","experiments/stage3f-publication-acquisition/gate2-publication-snapshot-authority.json"]:cp(rel,r)
 w(r/"docs/handoff/2026-07-16-stage3e-frozen-session-close.md","close\n");w(r/"docs/handoff/2026-07-16-stage3f-gate1-authority-start.md","6419e107e4aa8400ebd3d98f3583999075b8b935 e16edd99bfadf2135d0b632ddef4d292c0d80ea6 b5a2ca39d1250122312355dd3dbc6165b9409786 control-wrapper false negative\n")
 w(r/"docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md","3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2 117/117\n");w(r/"docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md","4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112 794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a 191 186/186\n");w(r/"docs/evidence/STAGE3E_FINAL_SUMMARY.md","3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2 5813305c22528354e6af686330e8f635db2b90a8a7a48ed5ed3c9ad4d1a4fb4d 4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112 794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a\n")
 w(r/"experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md","> **Status:** DESIGN FROZEN\n");w(r/"docs/evidence/STAGE3F_GATE1_AUTHORITY_DESIGN_RESULT.md","> **Status:** FROZEN — repository-only authority design\n")
 j(r/"experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json",{"status":"accepted-bounded-feasibility"});j(r/"experiments/stage3e-managed-python-distribution/gate1-authority.json",{"status":"design-frozen"});j(r/"experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json",{"status":"target-evidence-accepted-by-external-reaudit","accepted_result":{"archive_sha256":"3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2"}});j(r/"experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json",{"accepted":True,"check_count":117,"pass_count":117});j(r/"experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json",{"status":"contract-frozen","selection_contract":{"canonical":"exact-patch-version-request"}})
 j(r/"experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json",{"status":"accepted-target-evidence","accepted_result":{"archive_sha256":"4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112","archive_size":54299,"safe_member_count":191,"result_index_count":186,"target_verification":{"check_count":37,"pass_count":37},"independent_audit":{"sha256":"794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a","check_count":74,"pass_count":74}}});j(r/"experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json",{"accepted":True,"check_count":74,"pass_count":74,"failed_checks":[]});w(r/"experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md","> **Status:** FROZEN\nGate 5 closes Stage 3-E\n");j(r/"experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json",{"status":"independent-freeze-complete","claim_boundary":"Broader work require a new stage authority."})
 cp("experiments/stage3f-publication-acquisition/gate1-authority.json",r)
 (r/"scripts").mkdir(parents=True,exist_ok=True);shutil.copy2(SCRIPT,r/"scripts/verify-project-control-plane.py");shutil.copy2(Path(__file__).resolve(),r/"scripts/test-verify-project-control-plane.py")
 subprocess.run(["git","init","-q","-b","agent/stage3f-publication-acquisition"],cwd=r,check=True);subprocess.run(["git","config","user.name","fixture"],cwd=r,check=True);subprocess.run(["git","config","user.email","fixture@example.invalid"],cwd=r,check=True);subprocess.run(["git","add","-A"],cwd=r,check=True);subprocess.run(["git","commit","-qm","fixture"],cwd=r,check=True)
def main():
 m=load()
 with tempfile.TemporaryDirectory() as t:
  r=Path(t)/"r";r.mkdir();make(r);s=m.verify(r)
  if not s["pass"]:raise SystemExit(s)
  p=r/"experiments/stage3f-publication-acquisition/gate2-publication-snapshot-authority.json";d=json.loads(p.read_text());d["status"]="broken";j(p,d);n=m.verify(r)
  if n["pass"] or n["failed_checks"]!=["stage3f_gate2_status"]:raise SystemExit(n)
  d["status"]="contract-frozen-local-behavior-verified";j(p,d);p.unlink();i=m.verify(r)
  if i["pass"] or "required_files" not in i["failed_checks"] or str(p.relative_to(r)) not in i["missing_files"]:raise SystemExit(i)
  print(json.dumps({"schema_version":1,"verification_kind":"project-control-plane-fixtures-through-stage3f-gate2","pass":True,"fixtures":{"success":s["check_count"],"expected_negative":n["failed_checks"],"incomplete":i["missing_files"]}},indent=2,sort_keys=True))
if __name__=="__main__":raise SystemExit(main())
