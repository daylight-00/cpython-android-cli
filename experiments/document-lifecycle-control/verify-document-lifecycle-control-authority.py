#!/usr/bin/env python3
"""Verify the frozen Phase 1 document lifecycle control-plane authority."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from typing import Any
AUTHORITY=Path("experiments/document-lifecycle-control/document-lifecycle-control-authority.json")
AUDIT=Path("experiments/document-lifecycle-control/document-lifecycle-control-external-audit.json")
EVIDENCE=Path("docs/evidence/DOCUMENT_LIFECYCLE_CONTROL_PLANE_AUTHORITY_FREEZE.md")
HANDOFF=Path("docs/handoff/2026-07-19-document-lifecycle-control-plane.md")
def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
 return h.hexdigest()
def load(path:Path)->Any: return json.loads(path.read_text(encoding="utf-8"))
def verify(root:Path)->dict[str,Any]:
 checks={}; errors={}
 def ck(n,v,e=""):
  checks[n]=bool(v)
  if not v and e: errors[n]=e
 try:
  authority=load(root/AUTHORITY); audit=load(root/AUDIT); ck("authority_and_audit_parse",True)
 except Exception as exc:
  authority={}; audit={}; ck("authority_and_audit_parse",False,f"{type(exc).__name__}: {exc}")
 ck("authority_identity",authority.get("schema_version")==1 and authority.get("authority_kind")=="document-lifecycle-control-plane-phase1" and authority.get("authority_version")==1)
 ck("authority_status",authority.get("status")=="frozen-pass-control-plane-established")
 ck("predecessor_identity",authority.get("predecessor")=={"commit":"e4e684ae8488df6e7b991d34c1da222c1ce3b900","tree":"2df6889f498df57eceadaf57d24771c8b26e56c3"})
 scope=authority.get("scope",{})
 ck("scope_counts",scope.get("tracked_markdown_json_count")==415 and scope.get("legacy_document_count")==405 and scope.get("new_control_plane_document_count")==10)
 ck("non_disruptive_scope",scope.get("path_moves") is False and scope.get("historical_byte_rewrites") is False and scope.get("current_source_introduced") is False and scope.get("current_quartet_regenerated") is False)
 boundary=authority.get("claim_boundary",{})
 ck("claim_boundary",boundary=={"current_state_single_writer":False,"document_content_migration":False,"documentation_control_plane":True,"generated_navigation":False,"historical_authority_reinterpretation":False,"product_or_experiment_claim_change":False})
 ck("next_action",authority.get("next_action_class")=="execute-document-lifecycle-phase2-single-current-state-authority")
 legacy=authority.get("legacy_binding_boundary",{})
 ck("legacy_boundary",legacy.get("grandfathered_binding_count")==24 and legacy.get("new_live_generated_bindings_allowed") is False)
 identities=authority.get("file_identities",{})
 ok=isinstance(identities,dict) and bool(identities)
 if ok:
  for rel,expected in identities.items():
   p=root/rel
   if not p.is_file() or sha(p)!=expected: ok=False; break
 ck("file_identities",ok)
 ck("live_registry_not_bound","docs/documentation/document-registry.json" not in identities)
 ck("frozen_registry_snapshot_bound","experiments/document-lifecycle-control/baseline-document-registry.json" in identities)
 authority_sha=sha(root/AUTHORITY) if (root/AUTHORITY).is_file() else ""
 ck("audit_identity",audit.get("schema_version")==1 and audit.get("audit_kind")=="document-lifecycle-control-plane-phase1-external-audit")
 ck("audit_source",audit.get("source",{}).get("authority_sha256")==authority_sha)
 ck("audit_pass",audit.get("pass") is True and audit.get("check_count")==audit.get("pass_count") and audit.get("failed_checks")==[] and all(audit.get("checks",{}).values()))
 ck("audit_boundary",audit.get("claim_boundary")==boundary)
 evidence=(root/EVIDENCE).read_text(encoding="utf-8") if (root/EVIDENCE).is_file() else ""
 handoff=(root/HANDOFF).read_text(encoding="utf-8") if (root/HANDOFF).is_file() else ""
 ck("evidence_binding",authority_sha in evidence and "415" in evidence and "24 exact grandfathered bindings" in evidence)
 ck("handoff_binding",authority_sha in handoff and authority.get("next_action_class","") in handoff)
 failed=[k for k,v in checks.items() if not v]
 return {"schema_version":1,"verifier_kind":"document-lifecycle-control-plane-authority-v1","pass":not failed,"check_count":len(checks),"pass_count":len(checks)-len(failed),"failed_checks":failed,"checks":checks,"errors":errors}
def main()->int:
 p=argparse.ArgumentParser(); p.add_argument("--root",default="."); a=p.parse_args(); r=verify(Path(a.root).resolve()); print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r["pass"] else 1
if __name__=="__main__": sys.exit(main())
