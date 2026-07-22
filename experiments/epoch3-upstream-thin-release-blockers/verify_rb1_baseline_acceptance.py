#!/usr/bin/env python3
"""Verify the accepted owner RB-1 baseline receipt before authority freeze."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=Path("experiments/epoch3-upstream-thin-release-blockers")
EVID=BASE/"rb1-baseline-authority-evidence"
EXPECTED={
 "family":"87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302",
 "full":"20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12",
 "transition":{"pre_head":"0b6146c01c4ca8c20f73cc1143e0a4a447fe351b","pre_tree":"ccbad2f55601718b1881c968d11c2fa9b823c5fb","post_head":"a42ee1e45132aacfd74e4949695df39856c1646c","post_tree":"beb8f96cfb7f9961938e1476c254b11ec57c1262","remote_post_head":"a42ee1e45132aacfd74e4949695df39856c1646c"},
 "result":{"filename":"cpython-android-cli-e3-release-blocker-rb1-baseline-r1-results.tar.zst","sha256":"f16b484cdf92afac84d3ecdc5f462d23747bf29087899a372d6511f0444f4000","size_bytes":11220,"drive_file_id":"1NXw2j4lBjw9rZnuGqq17OpWDbp0rLXxo"},
}
def load(path:Path):
 return json.loads(path.read_text(encoding="utf-8"))
def sha(path:Path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify(root:Path):
 checks={};errors={}
 def read(name,path):
  try: value=load(root/path);checks[f"parse:{name}"]=True;return value
  except Exception as exc: checks[f"parse:{name}"]=False;errors[name]=f"{type(exc).__name__}: {exc}";return {}
 accepted=read("accepted-return",BASE/"accepted-rb1-baseline-r1-return.json")
 result=read("baseline-result",EVID/"baseline-result.json")
 census=read("component-census",EVID/"component-census.json")
 gaps=read("license-gap-register",EVID/"license-gap-register.json")
 audit=read("independent-audit",EVID/"independent-audit.json")
 repro=read("reproducibility",EVID/"reproducibility.json")
 summary=read("result-summary",EVID/"result-summary.json")
 checks["accepted_action"]=accepted.get("action")=="applied-rb1-component-license-baseline-censused-audited-pushed" and accepted.get("transaction_rc")==0
 checks["accepted_transition"]=accepted.get("repository_transition")==EXPECTED["transition"]
 checks["accepted_result_archive"]=accepted.get("result_archive")==EXPECTED["result"]
 checks["accepted_metrics"]=accepted.get("metrics")=={"blocking_gap_count":12,"component_count":12,"exact_version_count":10,"unresolved_version_components":["libffi"]}
 checks["family_identity"]=census.get("family",{}).get("fingerprint_sha256")==EXPECTED["family"] and gaps.get("family_fingerprint_sha256")==EXPECTED["family"]
 checks["full_identity"]=result.get("full_artifact_identity_preserved") is True and census.get("subject",{}).get("sha256")==EXPECTED["full"]
 cs=census.get("summary",{})
 checks["census_metrics"]=cs.get("component_count")==12 and cs.get("exact_version_count")==10 and cs.get("unresolved_version_components")==["libffi"] and cs.get("blocking_gap_count")==12
 classes=[r.get("component_class") for r in census.get("components",[]) if isinstance(r,dict)]
 checks["component_classes"]=classes==["cpython","project-launcher","pip","openssl","sqlite","bzip2","xz-liblzma","zstd","expat","libmpdec","libffi","android-system-providers"]
 checks["gap_register"]=gaps.get("blocking_gap_count")==12 and gaps.get("closure_status")=="incomplete" and any(g.get("code")=="libffi-version-unresolved" for g in gaps.get("gaps",[]))
 checks["audit_pass"]=audit.get("pass") is True and audit.get("failed_checks")==[] and all(audit.get("checks",{}).values())
 checks["reproducibility_pass"]=repro.get("pass") is True and all(repro.get("checks",{}).values())
 checks["result_pass"]=result.get("pass") is True and summary.get("failure_reason")=="none"
 claim_docs=[accepted.get("claim_boundary",{}),result.get("claim_boundary",{}),census.get("claim_boundary",{}),gaps.get("claim_boundary",{}),audit.get("claim_boundary",{}),summary.get("claim_boundary",{})]
 checks["claims_bounded"]=all(d.get("selectable") is False and d.get("publication") is False and d.get("component_license_mapping_complete") is False for d in claim_docs) and accepted.get("claim_boundary",{}).get("rb1_closed") is False
 expected_sha={"component-census.json":"3ff0379f5f76c503e32d6bbf3df32677d0e0d2d44ed973d0bd8696e312a8ccf0","license-gap-register.json":"9ac84e6c625d1bdeadd1cbe2a87f1947af4e05aebdabb5a64ed2c11b348c7f01","independent-audit.json":"c83c5b811ee25727b3c69d638c3dee954cb38caf24f61b904ead033634b265cf","baseline-result.json":"cff5718480b1360999c3cb9b7d6954dd6d99ec2655436a883f9aa849614bf240"}
 checks["evidence_identity"]=all((root/EVID/name).is_file() and sha(root/EVID/name)==digest for name,digest in expected_sha.items())
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {"schema_version":1,"verifier_kind":"epoch3-rb1-baseline-owner-return-acceptance","pass":not failed and not errors,"check_count":len(checks),"pass_count":len(checks)-len(failed),"checks":dict(sorted(checks.items())),"failed_checks":failed,"errors":errors,"claim_boundary":{"rb1_baseline_authority_can_freeze":not failed and not errors,"component_license_mapping_complete":False,"rb1_closed":False,"selectable":False,"publication":False},"evidence_identities":{str(EVID/name):sha(root/EVID/name) for name in sorted(expected_sha) if (root/EVID/name).is_file()}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",default=str(ROOT));a=p.parse_args();r=verify(Path(a.root).resolve());print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
