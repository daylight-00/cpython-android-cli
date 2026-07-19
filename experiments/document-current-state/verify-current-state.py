#!/usr/bin/env python3
"""Verify registry v2, the sole current source, generated views, and binding boundary."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from typing import Any
REGISTRY=Path("docs/documentation/document-registry.json")
REGISTRY_SCHEMA=Path("docs/documentation/document-registry-v2.schema.json")
STATE=Path("docs/current/STATE.json")
STATE_SCHEMA=Path("docs/current/STATE.schema.json")
BASELINE=Path("docs/documentation/legacy-live-binding-baseline.json")
RENDERER=Path("experiments/document-current-state/render-current-views.py")
ALLOWED_CLASSES={"STABLE","STABLE_WITH_GENERATED_SECTION","CURRENT_SOURCE","CURRENT_REGISTRY","CURRENT_INPUT_LOCK","ACTIVE_PLAN","APPEND_ONLY_LOG","FROZEN_AUTHORITY","HISTORICAL_SNAPSHOT","GENERATED_VIEW","REFERENCE","RAW_REFERENCE"}
REQUIRED={"path","format","lifecycle_class","authority_domain","owner","mutability","update_trigger","supersession_rule","onboarding_visibility","machine_binding_policy","migration_action"}
RENDER_TARGETS={"README.md","docs/CURRENT_CONTEXT.md","docs/INDEX.md","docs/SESSION_ONBOARDING.md"}

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()
def load(p:Path)->Any:return json.loads(p.read_text(encoding="utf-8"))
def tracked(root:Path)->set[str]:
 out=subprocess.run(["git","ls-files","-z"],cwd=root,check=True,stdout=subprocess.PIPE).stdout.decode().split("\0")
 return {p for p in out if p and Path(p).suffix in {".md",".json"}}
def bindings(root:Path,paths:set[str])->set[tuple[str,str,str]]:
 found=set()
 def walk(o:Any,ap:str):
  if isinstance(o,dict):
   fi=o.get("file_identities")
   if isinstance(fi,dict):
    for t,v in fi.items():
     d=v.get("sha256") if isinstance(v,dict) else v
     if isinstance(t,str) and isinstance(d,str):found.add((ap,t,d))
   for v in o.values():walk(v,ap)
  elif isinstance(o,list):
   for v in o:walk(v,ap)
 for p in sorted(paths):
  try:walk(load(root/p),p)
  except Exception:pass
 return found

def verify(root:Path)->dict[str,Any]:
 checks={};errors={}
 def ck(n,v,e=""):
  checks[n]=bool(v)
  if not v and e:errors[n]=e
 try:
  reg=load(root/REGISTRY);rs=load(root/REGISTRY_SCHEMA);state=load(root/STATE);ss=load(root/STATE_SCHEMA);base=load(root/BASELINE);ck("control_files_parse",True)
 except Exception as exc:
  reg={};rs={};state={};ss={};base={};ck("control_files_parse",False,f"{type(exc).__name__}: {exc}")
 ck("registry_v2_identity",reg.get("schema_version")==2 and reg.get("registry_kind")=="document-lifecycle-registry" and reg.get("schema_path")==str(REGISTRY_SCHEMA))
 basis=reg.get("basis",{})
 ck("phase2_boundary",basis.get("migration_phase")==2 and basis.get("current_source_present") is True and basis.get("current_source_path")==str(STATE) and basis.get("generated_views_enabled") is True and basis.get("physical_moves_allowed") is False)
 ck("registry_schema_identity",rs.get("$id")=="urn:cpython-android-cli:document-registry:v2" and rs.get("type")=="object")
 ck("state_schema_identity",ss.get("$id")=="urn:cpython-android-cli:current-state:v1" and ss.get("type")=="object")
 ck("lifecycle_class_set",set(reg.get("lifecycle_classes",[]))==ALLOWED_CLASSES)
 docs=reg.get("documents",[]); paths=[d.get("path") for d in docs if isinstance(d,dict)]
 ck("registry_paths_unique",len(paths)==len(set(paths)))
 ck("required_metadata_complete",all(isinstance(d,dict) and REQUIRED.issubset(d) and all(isinstance(d.get(k),str) and d.get(k) for k in REQUIRED) for d in docs))
 try:t=tracked(root);ck("git_document_inventory",True)
 except Exception as exc:t=set();ck("git_document_inventory",False,str(exc))
 rp={p for p in paths if isinstance(p,str)}
 ck("tracked_documents_exact",t==rp,f"missing={sorted(t-rp)} extra={sorted(rp-t)}")
 ck("registry_count_exact",basis.get("tracked_document_count")==len(t)==len(rp)==425)
 by={d["path"]:d for d in docs if isinstance(d,dict) and isinstance(d.get("path"),str)}
 current=[p for p,d in by.items() if d.get("lifecycle_class")=="CURRENT_SOURCE"]
 ck("single_current_source",current==[str(STATE)])
 ck("render_target_classification",by.get("docs/CURRENT_CONTEXT.md",{}).get("lifecycle_class")=="GENERATED_VIEW" and by.get("docs/INDEX.md",{}).get("lifecycle_class")=="GENERATED_VIEW" and by.get("README.md",{}).get("lifecycle_class")=="STABLE_WITH_GENERATED_SECTION" and by.get("docs/SESSION_ONBOARDING.md",{}).get("lifecycle_class")=="STABLE_WITH_GENERATED_SECTION")
 ck("state_identity",state.get("schema_version")==1 and state.get("state_kind")=="project-current-state" and state.get("state_revision")==1)
 ck("state_predecessor",state.get("predecessor")=={"commit":"7248859ff5c24990f6cc06ad696a21b2d2793202","tree":"3a85792eec9c8e78e4955aa1a227e737d9c4c509"})
 program=state.get("program",{});control=state.get("control_work",{})
 ck("program_gate",program.get("epoch",{}).get("id")=="E2" and program.get("gate",{}).get("id")=="E2-R1/UT-0" and program.get("next_action_class")=="execute-e2-r1-ut0-exact-official-upstream-control")
 ck("control_next_action",control.get("completed_phase")==2 and control.get("next_phase")==3 and control.get("next_action_class")==state.get("next_action_class")=="execute-document-lifecycle-phase3-generated-navigation" and control.get("resume_program_action_class")==program.get("next_action_class"))
 plan=state.get("active_plan",{}); pp=root/str(plan.get("path",""))
 ck("active_plan_identity",pp.is_file() and sha(pp)==plan.get("sha256"))
 auths=state.get("accepted_authorities",[]); ids=[a.get("id") for a in auths if isinstance(a,dict)]
 ck("accepted_authorities_unique",len(ids)==len(set(ids))==5)
 auth_ok=True
 for a in auths:
  p=root/str(a.get("path",""))
  if not p.is_file() or sha(p)!=a.get("sha256"):auth_ok=False
 ck("accepted_authority_identities",auth_ok)
 ck("state_collections",isinstance(state.get("blockers"),list) and all(isinstance(x,str) for x in state.get("blockers",[])) and isinstance(state.get("unresolved_risks"),list) and all(isinstance(x,str) for x in state.get("unresolved_risks",[])))
 claims=state.get("claim_boundaries",{})
 ck("claim_boundary",claims=={"dual_real_device_aarch64_termux_compatibility":True,"emulator_qualified":False,"selectable":False,"publication_authorized":False,"epoch3_feature_selection_started":False})
 ck("render_target_contract",set(state.get("render_targets",[]))==RENDER_TARGETS)
 ck("no_self_commit_claim","as_of_commit" not in state and "as_of_tree" not in state)
 render=subprocess.run([sys.executable,str(root/RENDERER),"--root",str(root),"--check"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 ck("generated_views_exact",render.returncode==0,render.stdout+render.stderr)
 orientation_entry=by.get("docs/PROJECT_ORIENTATION.md",{})
 ck("legacy_orientation_reclassified",orientation_entry.get("lifecycle_class")=="HISTORICAL_SNAPSHOT" and orientation_entry.get("onboarding_visibility")=="history" and orientation_entry.get("current_successors")==[str(STATE)])
 baseline={(b.get("authority_path"),b.get("target_path"),b.get("recorded_sha256")) for b in base.get("bindings",[]) if isinstance(b,dict)}
 forbidden={p for p,d in by.items() if d.get("lifecycle_class") in {"CURRENT_SOURCE","CURRENT_REGISTRY","GENERATED_VIEW","STABLE_WITH_GENERATED_SECTION","ACTIVE_PLAN"} or "forbidden" in str(d.get("machine_binding_policy","")).lower() or "legacy" in str(d.get("machine_binding_policy","")).lower()}
 observed=bindings(root,{p for p in t if p.endswith(".json")}); ob={b for b in observed if b[1] in forbidden}
 ck("legacy_bindings_preserved",ob==baseline,f"missing={sorted(baseline-ob)} extra={sorted(ob-baseline)}")
 ck("live_state_not_bound",not any(b[1]==str(STATE) for b in observed))
 ck("live_registry_not_bound",not any(b[1]==str(REGISTRY) for b in observed))
 ck("no_new_live_generated_binding",not (ob-baseline))
 successors=True
 for d in docs:
  for q in d.get("current_successors",[]) or []:
   if q not in by or not (root/q).is_file():successors=False
 ck("current_successors_exist",successors)
 failed=[n for n,v in checks.items() if not v]
 return {"schema_version":1,"verifier_kind":"document-current-state-and-registry-v2","pass":not failed,"check_count":len(checks),"pass_count":len(checks)-len(failed),"failed_checks":failed,"checks":checks,"errors":errors,"metrics":{"tracked_document_count":len(t),"registry_document_count":len(rp),"legacy_binding_count":len(baseline),"forbidden_target_count":len(forbidden)}}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--root",default=".");a=p.parse_args();r=verify(Path(a.root).resolve());print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["pass"] else 1
if __name__=="__main__":sys.exit(main())
