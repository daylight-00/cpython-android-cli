#!/usr/bin/env python3
"""Exercise project-control verification success, expected-negative, and incomplete fixtures."""
from __future__ import annotations
import importlib.util,json,shutil,subprocess,tempfile
from pathlib import Path
SCRIPT=Path(__file__).resolve().with_name("verify-project-control-plane.py")
def w(p:Path,s:str):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding="utf-8")
def j(p:Path,v):w(p,json.dumps(v,indent=2,sort_keys=True)+"\n")
def load():
 s=importlib.util.spec_from_file_location("v",SCRIPT);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def make(r:Path):
 w(r/"README.md","active — Gate 3 contract frozen; Gate 4 next\n")
 w(r/"docs/PROJECT_CONTEXT_STAGE3D.md","frozen\n")
 w(r/"docs/PROJECT_CONTEXT_STAGE3E.md","> **Status:** Stage 3-E active — Gate 3 managed-Python distribution contract frozen\nFROZEN — external re-audit 117/117\nGate 3  managed-Python distribution contract            FROZEN\nGate 4  target implementation and lifecycle validation  ACTIVE NEXT\n")
 w(r/"docs/stages/STAGE3E_SCOPE.md","> **Status:** ACTIVE — Gate 3 contract frozen; Gate 4 next\nExact patch-version requests are canonical\n")
 w(r/"docs/PROJECT_ORIENTATION.md","Stage 3-E Gate 2 is accepted\nGate 4 is active next\n")
 w(r/"docs/handoff/README.md","Stage 3-E Gate 3 managed-Python distribution contract   FROZEN\nACTIVE NEXT\n")
 w(r/"docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md","3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2\n5813305c22528354e6af686330e8f635db2b90a8a7a48ed5ed3c9ad4d1a4fb4d\n117/117 PASS\n")
 j(r/"experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json",{"status":"accepted-bounded-feasibility"})
 j(r/"experiments/stage3e-managed-python-distribution/gate1-authority.json",{"status":"design-frozen"})
 j(r/"experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json",{"status":"target-evidence-accepted-by-external-reaudit","accepted_result":{"archive_sha256":"3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2","result_index_count":168,"external_audit":{"check_count":117,"pass_count":117,"sha256":"5813305c22528354e6af686330e8f635db2b90a8a7a48ed5ed3c9ad4d1a4fb4d"}},"accepted_observations":{"minor_selection":{"resolved_version":"3.14.6","order_independent":True}}})
 j(r/"experiments/stage3e-managed-python-distribution/gate2-v2-external-reaudit.json",{"accepted":True,"check_count":117,"pass_count":117,"failed_checks":[]})
 w(r/"experiments/stage3e-managed-python-distribution/GATE3_MANAGED_PYTHON_DISTRIBUTION_CONTRACT.md","> **Status:** CONTRACT FROZEN\n")
 j(r/"experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json",{"status":"contract-frozen","selection_contract":{"canonical":"exact-patch-version-request","minor":{"observed":"3.14.6","patch_exact":False},"unspecified":{"observed":"3.14.6","patch_exact":False}},"installation_contract":{"first_persistent_root":"project-owned-explicit-install-dir","uv_default_managed_dir":False},"coexistence":{"stage3d_system_python_contract":"unchanged-and-independent"},"gate_sequence":{"gate4":"ACTIVE_NEXT_PROJECT_OWNED_PERSISTENT_ROOT_VALIDATION"}})
 (r/"scripts").mkdir(parents=True,exist_ok=True);shutil.copy2(SCRIPT,r/"scripts/verify-project-control-plane.py");shutil.copy2(Path(__file__).resolve(),r/"scripts/test-verify-project-control-plane.py")
 subprocess.run(["git","init","-q","-b","agent/stage3e-managed-python-distribution"],cwd=r,check=True);subprocess.run(["git","config","user.name","fixture"],cwd=r,check=True);subprocess.run(["git","config","user.email","fixture@example.invalid"],cwd=r,check=True);subprocess.run(["git","add","-A"],cwd=r,check=True);subprocess.run(["git","commit","-qm","fixture"],cwd=r,check=True)
def main():
 m=load()
 with tempfile.TemporaryDirectory() as t:
  r=Path(t)/"r";r.mkdir();make(r);s=m.verify(r)
  if not s["pass"]:raise SystemExit(s)
  p=r/"experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json";d=json.loads(p.read_text());d["status"]="broken";j(p,d);n=m.verify(r)
  if n["pass"] or n["failed_checks"]!=["gate3_status"]:raise SystemExit(n)
  d["status"]="contract-frozen";j(p,d);q=r/"experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json";q.unlink();i=m.verify(r)
  if i["pass"] or "required_files" not in i["failed_checks"] or str(q.relative_to(r)) not in i["missing_files"]:raise SystemExit(i)
  print(json.dumps({"schema_version":1,"verification_kind":"project-control-plane-fixtures","pass":True,"fixtures":{"success":s["check_count"],"expected_negative":n["failed_checks"],"incomplete":i["missing_files"]}},indent=2,sort_keys=True))
if __name__=="__main__":raise SystemExit(main())
