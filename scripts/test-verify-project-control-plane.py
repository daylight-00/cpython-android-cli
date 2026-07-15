#!/usr/bin/env python3
"""Exercise Stage 3-E Gate 5 project-control success, expected-negative, and incomplete fixtures."""
from __future__ import annotations
import importlib.util,json,shutil,subprocess,tempfile
from pathlib import Path
SCRIPT=Path(__file__).resolve().with_name("verify-project-control-plane.py")
def w(p:Path,s:str):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding="utf-8")
def j(p:Path,v):w(p,json.dumps(v,indent=2,sort_keys=True)+"\n")
def load():
 s=importlib.util.spec_from_file_location("v",SCRIPT);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def make(r:Path):
 w(r/"README.md","frozen — Gate 5 independent distribution freeze complete\n4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112 37/37 74/74\n")
 w(r/"docs/PROJECT_CONTEXT_STAGE3D.md","frozen\n")
 w(r/"docs/PROJECT_CONTEXT_STAGE3E.md","> **Status:** Stage 3-E frozen through Gate 5 independent distribution freeze\nGate 4  project-owned persistent-root validation        FROZEN\nGate 5  independent distribution freeze                 FROZEN\n")
 w(r/"docs/stages/STAGE3E_SCOPE.md","> **Status:** FROZEN — Gate 5 independent distribution freeze complete\n")
 w(r/"docs/PROJECT_ORIENTATION.md","Stage 3-E is complete\ntarget 37/37 and independent 74/74\n")
 w(r/"docs/handoff/README.md","Stage 3-E Gate 5 independent distribution freeze        FROZEN\n")
 w(r/"docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md","3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2 117/117\n")
 w(r/"docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md","4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112\n794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a\n191 186/186\n")
 w(r/"docs/evidence/STAGE3E_FINAL_SUMMARY.md","3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2\n5813305c22528354e6af686330e8f635db2b90a8a7a48ed5ed3c9ad4d1a4fb4d\n4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112\n794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a\n")
 j(r/"experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json",{"status":"accepted-bounded-feasibility"})
 j(r/"experiments/stage3e-managed-python-distribution/gate1-authority.json",{"status":"design-frozen"})
 j(r/"experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json",{"status":"target-evidence-accepted-by-external-reaudit","accepted_result":{"archive_sha256":"3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2"}})
 j(r/"experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json",{"accepted":True,"check_count":117,"pass_count":117})
 j(r/"experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json",{"status":"contract-frozen","selection_contract":{"canonical":"exact-patch-version-request"}})
 j(r/"experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json",{"status":"accepted-target-evidence","persistent_root":"$HOME/.local/share/hw-t/cpython-managed/gate4-validation-v2","correction_lineage":{"v1":{"verification":"36/37","classification":"umask-mode-narrowing"}},"accepted_result":{"archive_sha256":"4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112","archive_size":54299,"safe_member_count":191,"result_index_count":186,"target_verification":{"check_count":37,"pass_count":37},"independent_audit":{"sha256":"794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a","check_count":74,"pass_count":74}}})
 j(r/"experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json",{"accepted":True,"check_count":74,"pass_count":74,"failed_checks":[],"archive":{"sha256":"4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112","safe_member_count":191,"result_index_count":186}})
 w(r/"experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md","> **Status:** FROZEN\nGate 5 closes Stage 3-E\n")
 j(r/"experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json",{"status":"independent-freeze-complete","gate_sequence":{"gate1":"FROZEN","gate2":"FROZEN","gate3":"FROZEN","gate4":"FROZEN","gate5":"FROZEN"},"input_authorities":{"gate4_archive_sha256":"4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112","gate4_independent_audit_sha256":"794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a"},"accepted_surface":{"system_python_contract":"unchanged-and-independent"},"deferred_to_new_stage":["uv-default-managed-root"],"claim_boundary":"Broader operations require a new stage authority."})
 (r/"scripts").mkdir(parents=True,exist_ok=True);shutil.copy2(SCRIPT,r/"scripts/verify-project-control-plane.py");shutil.copy2(Path(__file__).resolve(),r/"scripts/test-verify-project-control-plane.py")
 subprocess.run(["git","init","-q","-b","agent/stage3e-managed-python-distribution"],cwd=r,check=True);subprocess.run(["git","config","user.name","fixture"],cwd=r,check=True);subprocess.run(["git","config","user.email","fixture@example.invalid"],cwd=r,check=True);subprocess.run(["git","add","-A"],cwd=r,check=True);subprocess.run(["git","commit","-qm","fixture"],cwd=r,check=True)
def main():
 m=load()
 with tempfile.TemporaryDirectory() as t:
  r=Path(t)/"r";r.mkdir();make(r);s=m.verify(r)
  if not s["pass"]:raise SystemExit(s)
  p=r/"experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json";d=json.loads(p.read_text());d["status"]="broken";j(p,d);n=m.verify(r)
  if n["pass"] or n["failed_checks"]!=["gate5_status"]:raise SystemExit(n)
  d["status"]="independent-freeze-complete";j(p,d);q=r/"experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json";q.unlink();i=m.verify(r)
  if i["pass"] or "required_files" not in i["failed_checks"] or str(q.relative_to(r)) not in i["missing_files"]:raise SystemExit(i)
  print(json.dumps({"schema_version":1,"verification_kind":"project-control-plane-fixtures-through-stage3e-gate5","pass":True,"fixtures":{"success":s["check_count"],"expected_negative":n["failed_checks"],"incomplete":i["missing_files"]}},indent=2,sort_keys=True))
if __name__=="__main__":raise SystemExit(main())
