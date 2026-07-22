#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REL=Path("experiments/epoch3-upstream-thin-release-blockers")
E=REL/"rb1-legal-overlay-authority-evidence"
EXPECTED={"result":"e940816fe3b50e99596d77c82d9c4dd223f48f72bb04066b6095e914ab3a572b","family":"87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302","overlay":"e4378c59eabcc6fdf5d07cccd718bd536d87deda531e5e2fcc3115fb6944a878","post":"611e036367c1723277bdccc2180e215283194978"}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def load(p):
 v=json.loads(p.read_text());
 if not isinstance(v,dict):raise ValueError(f"expected object: {p}")
 return v
def verify(root:Path):
 errors=[];checks={}
 def get(rel):
  p=root/rel
  if not p.is_file():errors.append(f"missing:{rel}");return {}
  try:return load(p)
  except Exception as e:errors.append(f"invalid:{rel}:{e}");return {}
 a=get(REL/"accepted-rb1-legal-overlay-r2-return.json");auth=get(REL/"rb1-legal-overlay-authority.json")
 s=get(E/"result-summary.json");r=get(E/"legal-overlay-result.json");idx=get(E/"legal-overlay-index.json");g=get(E/"updated-gap-register.json");audit=get(E/"independent-audit.json");repro=get(E/"reproducibility.json")
 checks["accepted_action"]=a.get("transaction_rc")==0 and a.get("action")=="applied-rb1-legal-overlay-evidence-synthesized-audited-pushed"
 checks["transition"]=a.get("repository_transition",{}).get("post_head")==EXPECTED["post"] and a.get("repository_transition",{}).get("remote_post_head")==EXPECTED["post"]
 checks["result_archive"]=a.get("result_archive",{}).get("sha256")==EXPECTED["result"] and a.get("result_archive",{}).get("size_bytes")==173369
 checks["metrics"]=a.get("metrics")=={"exact_input_archive_count":7,"legal_overlay_file_count":72,"resolved_gap_count":4,"remaining_gap_count":4}
 checks["overlay_result"]=r.get("pass") is True and r.get("family_identity_preserved") is True and r.get("legal_overlay_fingerprint_sha256")==EXPECTED["overlay"]
 checks["overlay_index"]=idx.get("file_count")==72 and idx.get("fingerprint_sha256")==EXPECTED["overlay"] and len(idx.get("files",[]))==72
 checks["gap_boundary"]=g.get("blocking_gap_count")==4 and {x.get("code") for x in g.get("remaining_gaps",[])}=={"complete-componentization-and-obligation-review-pending","authoritative-license-evidence-not-integrated-into-release-family","project-license-not-in-release-family","final-notice-set-not-owner-approved"}
 checks["audit"]=audit.get("pass") is True and not audit.get("failed_checks") and audit.get("legal_overlay_fingerprint_sha256")==EXPECTED["overlay"]
 checks["reproducibility"]=repro.get("pass") is True and all(x.get("identical") is True for x in repro.get("files",[]))
 checks["summary"]=s.get("transaction_rc")==0 and s.get("post",{}).get("head")==EXPECTED["post"]
 docs=[a.get("claim_boundary",{}),r.get("claim_boundary",{}),g.get("claim_boundary",{}),audit.get("claim_boundary",{}),s.get("claim_boundary",{})]
 checks["claims_bounded"]=all(d.get("selectable") is False and d.get("publication") is False and d.get("rb1_closed") is False for d in docs)
 expected=a.get("output_sha256",{});checks["evidence_identity"]=bool(expected) and all((root/E/n).is_file() and sha(root/E/n)==v for n,v in expected.items())
 ids=auth.get("file_identities",{});checks["authority_file_identities"]=bool(ids) and all((root/p).is_file() and sha(root/p)==v for p,v in ids.items())
 checks["authority_boundary"]=auth.get("frozen_result",{}).get("remaining_gap_count")==4 and auth.get("claim_boundary",{}).get("owner_approved") is False
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {"schema_version":1,"verifier_kind":"epoch3-rb1-legal-overlay-acceptance","pass":not failed and not errors,"check_count":len(checks),"checks":dict(sorted(checks.items())),"failed_checks":failed,"errors":errors}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=ROOT);a=p.parse_args();out=verify(a.root.resolve());print(json.dumps(out,indent=2,sort_keys=True));return 0 if out["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
