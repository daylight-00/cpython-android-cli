#!/usr/bin/env python3
"""Verify the frozen Phase 2 current-state authority without binding live views."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from typing import Any
A=Path("experiments/document-current-state/document-current-state-authority.json");U=Path("experiments/document-current-state/document-current-state-external-audit.json");E=Path("docs/evidence/DOCUMENT_CURRENT_STATE_AUTHORITY_FREEZE.md");H=Path("docs/handoff/2026-07-19-document-current-state-authority.md")
def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()
def load(p:Path)->Any:return json.loads(p.read_text(encoding="utf-8"))
def verify(root:Path)->dict[str,Any]:
 checks={};errors={}
 def ck(n,v,e=""):
  checks[n]=bool(v)
  if not v and e:errors[n]=e
 try:a=load(root/A);u=load(root/U);ck("authority_and_audit_parse",True)
 except Exception as exc:a={};u={};ck("authority_and_audit_parse",False,str(exc))
 ck("authority_identity",a.get("schema_version")==1 and a.get("authority_kind")=="document-current-state-authority-phase2" and a.get("authority_version")==1)
 ck("authority_status",a.get("status")=="frozen-pass-single-current-state-authority-established")
 ck("predecessor",a.get("predecessor")=={"commit":"7248859ff5c24990f6cc06ad696a21b2d2793202","tree":"3a85792eec9c8e78e4955aa1a227e737d9c4c509"})
 scope=a.get("scope",{});ck("scope",scope.get("current_source")=="docs/current/STATE.json" and scope.get("tracked_markdown_json_count")==425 and scope.get("render_target_count")==4 and scope.get("path_moves") is False and scope.get("historical_byte_rewrites") is False)
 boundary=a.get("claim_boundary",{});ck("claim_boundary",boundary=={"current_state_single_writer":True,"directory_level_generated_navigation":False,"historical_authority_reinterpretation":False,"physical_document_moves":False,"product_or_experiment_claim_change":False})
 ck("next_action",a.get("next_action_class")=="execute-document-lifecycle-phase3-generated-navigation" and a.get("resume_program_action_class")=="execute-e2-r1-ut0-exact-official-upstream-control")
 ids=a.get("file_identities",{});ok=isinstance(ids,dict) and bool(ids)
 if ok:
  for rel,d in ids.items():
   p=root/rel
   if not p.is_file() or sha(p)!=d:ok=False;break
 ck("file_identities",ok)
 live={"docs/current/STATE.json","docs/documentation/document-registry.json","README.md","docs/CURRENT_CONTEXT.md","docs/INDEX.md","docs/SESSION_ONBOARDING.md"}
 ck("live_paths_not_bound",not (set(ids)&live))
 ck("immutable_state_snapshot_bound","experiments/document-current-state/baseline-current-state.json" in ids)
 ck("e2p3_preservation_helper_bound","experiments/document-current-state/verify-frozen-e2p3-snapshot.py" in ids)
 snap=load(root/"experiments/document-current-state/baseline-current-state.json") if (root/"experiments/document-current-state/baseline-current-state.json").is_file() else {}
 ck("snapshot_semantics",snap.get("state_revision")==1 and snap.get("next_action_class")=="execute-document-lifecycle-phase3-generated-navigation" and snap.get("program",{}).get("gate",{}).get("id")=="E2-R1/UT-0")
 hp=a.get("historical_preservation",{});ck("historical_preservation_contract",hp.get("mode")=="exact-frozen-byte-preservation-plus-current-freeze-verifier" and hp.get("protected_paths")==['docs/evidence/E2P3_SECONDARY_REAL_DEVICE_QUALIFICATION_AUTHORITY_FREEZE.md','docs/handoff/2026-07-19-e2p3-secondary-real-device-qualification-authority-freeze.md','docs/roadmap/EPOCH2_ROADMAP.md','docs/roadmap/EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md','experiments/epoch2-archive-qualification/README.md','experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json','experiments/epoch2-archive-qualification/secondary-real-device-qualification-external-audit.json','experiments/epoch2-archive-qualification/test-secondary-real-device-qualification-freeze.py','experiments/epoch2-archive-qualification/verify-qualification-contract.py','experiments/epoch2-archive-qualification/verify-secondary-real-device-qualification-freeze.py'] and hp.get("secondary_freeze_authority_sha256")=="e380198cda8c49cad704483e3edc33c2d745cc65857155b3a7edb1887410f06c" and hp.get("secondary_freeze_audit_sha256")=="90784e8896479e4ae0db5e7d26a035ec91250b0028bc23638a470290f0976979" and a.get("verification",{}).get("frozen_e2p3_preservation")=="12/12" and a.get("verification",{}).get("secondary_freeze_verifier")=="28/28")
 phase1=subprocess.run([sys.executable,str(root/"experiments/document-lifecycle-control/verify-document-lifecycle-control-authority.py"),"--root",str(root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:p1=json.loads(phase1.stdout)
 except Exception:p1={}
 ck("phase1_authority_preserved",phase1.returncode==0 and p1.get("pass") is True and p1.get("check_count")==18)
 ash=sha(root/A) if (root/A).is_file() else ""
 ck("audit_identity",u.get("schema_version")==1 and u.get("audit_kind")=="document-current-state-authority-phase2-external-audit")
 ck("audit_source",u.get("source",{}).get("authority_sha256")==ash)
 ck("audit_pass",u.get("pass") is True and u.get("check_count")==u.get("pass_count") and u.get("failed_checks")==[] and all(u.get("checks",{}).values()))
 ev=(root/E).read_text(encoding="utf-8") if (root/E).is_file() else "";ho=(root/H).read_text(encoding="utf-8") if (root/H).is_file() else ""
 ck("evidence_binding",ash in ev and "425/425" in ev and "24/24" in ev)
 ck("handoff_binding",ash in ho and a.get("next_action_class","") in ho)
 failed=[n for n,v in checks.items() if not v]
 return {"schema_version":1,"verifier_kind":"document-current-state-authority-phase2-v1","pass":not failed,"check_count":len(checks),"pass_count":len(checks)-len(failed),"failed_checks":failed,"checks":checks,"errors":errors}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--root",default=".");x=p.parse_args();r=verify(Path(x.root).resolve());print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["pass"] else 1
if __name__=="__main__":sys.exit(main())
