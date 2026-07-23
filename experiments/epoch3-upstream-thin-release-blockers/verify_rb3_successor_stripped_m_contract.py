#!/usr/bin/env python3
"""Verify the completed successor stripped transition and technical-family routing."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from typing import Any
EXPECTED_STRIPPED={"filename":"cpython-3.14.6+e3-full-r5-aarch64-linux-android-install_only_stripped.tar.gz","sha256":"9cffe27e4e7e6b82d3bace2ea4ce56473abae683bad041d38106ec481b83d9e5","size_bytes":23842721,"member_count":3699}
RESULT={"filename":"cpython-android-cli-e3-rb3-successor-stripped-m-r1-results.tar.zst","sha256":"db5ff3a3f9a5a8de4731ae5e5cebad7739bcf0330f12de01bdecb01528acd1d7","size_bytes":47423566,"self_index_exact":True,"self_index_file_count":84}
BASE="experiments/epoch3-upstream-thin-release-blockers/"
def load(root:Path,p:str)->dict[str,Any]:return json.loads((root/p).read_text(encoding="utf-8"))
def sha(root:Path,p:str)->str:return hashlib.sha256((root/p).read_bytes()).hexdigest()
def verify(root:Path)->dict[str,Any]:
 contract=load(root,BASE+"rb3-successor-stripped-m-contract.json");execution=load(root,BASE+"rb3-successor-stripped-m-r1-execution-contract.json");acceptance_contract=load(root,BASE+"rb3-successor-stripped-m-acceptance-contract.json");inspection=load(root,BASE+"rb3-successor-stripped-m-r1-return-inspection.json");accepted=load(root,BASE+"accepted-rb3-successor-stripped-m-r1-return.json");authority=load(root,BASE+"rb3-successor-stripped-m-authority.json");technical=load(root,BASE+"rb3-successor-technical-family-m-contract.json");lock=load(root,"config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-successor-install-only-stripped-r5.lock.json");state=load(root,"docs/current/STATE.json");catalog=load(root,"docs/agent/TASK_CATALOG.json");task=next(x for x in catalog["tasks"] if x["task_id"]=="E3-RELEASE-BLOCKERS");registry=load(root,"docs/documentation/document-registry.json");registered={x["path"] for x in registry["documents"]}
 checks={
  "contract_frozen":contract.get("status")=="authorized-pending-owner-derivation-after-install-only-acceptance" and contract.get("proposed_candidate",{}).get("filename")==EXPECTED_STRIPPED["filename"],
  "execution_frozen":execution.get("status")=="prepared-owner-derivation-pending" and execution.get("candidate",{}).get("filename")==EXPECTED_STRIPPED["filename"],
  "acceptance_contract":acceptance_contract.get("status")=="candidate-qualified-accepted-by-successor-stripped-authority" and acceptance_contract.get("accepted_candidate")==EXPECTED_STRIPPED and acceptance_contract.get("result_archive")==RESULT,
  "inspection_exact":inspection.get("candidate_stripped")==EXPECTED_STRIPPED and inspection.get("result_archive")==RESULT,
  "accepted_exact":accepted.get("candidate_stripped")==EXPECTED_STRIPPED and accepted.get("result_archive")==RESULT,
  "authority_exact":authority.get("accepted_stripped")==EXPECTED_STRIPPED and authority.get("status")=="successor-stripped-r5-accepted-technical-family-derivation-authorized",
  "authority_registered":any(x.get("path")==BASE+"rb3-successor-stripped-m-authority.json" and x.get("sha256")==sha(root,BASE+"rb3-successor-stripped-m-authority.json") for x in state.get("accepted_authorities",[])),
  "lock_exact":lock.get("artifact")==EXPECTED_STRIPPED and lock.get("authority_path")==BASE+"rb3-successor-stripped-m-authority.json",
  "state_active_work":state.get("active_work_package")==BASE+"rb3-successor-technical-family-m-contract.json",
  "state_boundaries":state.get("claim_boundaries",{}).get("successor_stripped_accepted") is True and state.get("claim_boundaries",{}).get("successor_technical_family_started") is False and state.get("claim_boundaries",{}).get("successor_technical_family_accepted") is False,
  "task_transition":task.get("deliverable",{}).get("current_bounded_transition")=="rb3-profile-M-successor-technical-family-owner-assembly-and-audit",
  "task_reads":all(any(x.get("path")==p for x in task.get("required_reads",[])) for p in (BASE+"rb3-successor-stripped-m-r1-return-inspection.json",BASE+"rb3-successor-stripped-m-authority.json",BASE+"rb3-successor-stripped-m-acceptance-contract.json",BASE+"rb3-successor-technical-family-m-contract.json")),
  "task_binds":all(any(x.get("path")==p and x.get("sha256")==sha(root,p) for x in task.get("required_authorities",[])) for p in (BASE+"rb3-successor-stripped-m-r1-return-inspection.json",BASE+"rb3-successor-stripped-m-authority.json")),
  "technical_contract":technical.get("status")=="authorized-pending-owner-assembly-after-stripped-acceptance" and technical.get("accepted_inputs",{}).get("install_only_stripped",{}).get("sha256")==EXPECTED_STRIPPED["sha256"] and technical.get("success_boundary",{}).get("successor_technical_family_candidate") is True and technical.get("success_boundary",{}).get("predecessor_family_superseded") is False,
  "registry_complete":{BASE+"accepted-rb3-successor-stripped-m-r1-return.json",BASE+"rb3-successor-stripped-m-r1-return-inspection.json",BASE+"rb3-successor-stripped-m-authority.json",BASE+"rb3-successor-stripped-m-acceptance-contract.json",BASE+"rb3-successor-technical-family-m-contract.json","config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-successor-install-only-stripped-r5.lock.json"}.issubset(registered),
  "rb3_open":authority.get("claim_boundary",{}).get("artifact_family_superseded") is False and authority.get("claim_boundary",{}).get("rb3_closed") is False and authority.get("claim_boundary",{}).get("selectable") is False and authority.get("claim_boundary",{}).get("publication") is False,
 }
 failed=sorted(k for k,v in checks.items() if v is not True);return {"schema_version":1,"verifier_kind":"epoch3-rb3-successor-stripped-accepted-technical-family-routing","pass":not failed,"checks":dict(sorted(checks.items())),"failed_checks":failed}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path("."));a=p.parse_args()
 try:r=verify(a.root.resolve())
 except Exception as e:r={"schema_version":1,"pass":False,"error":f"{type(e).__name__}: {e}"}
 print(json.dumps(r,indent=2,sort_keys=True));return 0 if r.get("pass") is True else 1
if __name__=="__main__":raise SystemExit(main())
