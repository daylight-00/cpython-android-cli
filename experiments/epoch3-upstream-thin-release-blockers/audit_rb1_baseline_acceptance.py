#!/usr/bin/env python3
"""Independent audit of accepted RB-1 baseline evidence."""
from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 verifier=ROOT/"experiments/epoch3-upstream-thin-release-blockers/verify_rb1_baseline_acceptance.py"
 p=subprocess.run([sys.executable,str(verifier),"--root",str(ROOT)],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:r=json.loads(p.stdout)
 except json.JSONDecodeError:r={}
 bound=[
  "components/upstream-thin/lib/license_census.py",
  "components/upstream-thin/tests/test_license_census.py",
  "experiments/epoch3-upstream-thin-release-blockers/accepted-rb1-baseline-r1-return.json",
  "experiments/epoch3-upstream-thin-release-blockers/baseline-contract.json",
  "experiments/epoch3-upstream-thin-release-blockers/run_release_blocker_baseline.py",
  "experiments/epoch3-upstream-thin-release-blockers/audit_release_blocker_baseline.py",
  "experiments/epoch3-upstream-thin-release-blockers/verify_rb1_baseline_acceptance.py",
 ]
 checks={
  "primary_pass":p.returncode==0 and r.get("pass") is True,
  "all_primary_checks":bool(r.get("checks")) and all(r.get("checks",{}).values()),
  "baseline_freezable":r.get("claim_boundary",{}).get("rb1_baseline_authority_can_freeze") is True,
  "claims_bounded":r.get("claim_boundary",{}).get("rb1_closed") is False and r.get("claim_boundary",{}).get("selectable") is False and r.get("claim_boundary",{}).get("publication") is False,
  "bound_files_present":all((ROOT/x).is_file() for x in bound),
 }
 failed=sorted(k for k,v in checks.items() if v is not True)
 out={"schema_version":1,"audit_kind":"epoch3-rb1-baseline-acceptance-independent-audit","pass":not failed,"checks":dict(sorted(checks.items())),"failed_checks":failed,"primary_verification_sha256":hashlib.sha256((p.stdout.rstrip()+"\n").encode()).hexdigest() if p.stdout else None,"bound_file_identities":{x:sha(ROOT/x) for x in bound if (ROOT/x).is_file()},"stderr":p.stderr,"claim_boundary":{"rb1_baseline_frozen":not failed,"component_license_mapping_complete":False,"rb1_closed":False,"selectable":False,"publication":False}}
 print(json.dumps(out,indent=2,sort_keys=True));return 0 if out["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
