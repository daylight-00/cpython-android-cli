#!/usr/bin/env python3
"""Verify Phase 3 state, registry v3, complete generated navigation, and binding boundary."""
from __future__ import annotations
import argparse,hashlib,json,os,re,subprocess,sys
from pathlib import Path
from collections import Counter
from typing import Any
REG=Path('docs/documentation/document-registry.json');RS=Path('docs/documentation/document-registry-v3.schema.json');STATE=Path('docs/current/STATE.json');SS=Path('docs/current/STATE-v2.schema.json');BASE=Path('docs/documentation/legacy-live-binding-baseline.json');MAN=Path('experiments/document-navigation/navigation-targets.json');RENDER=Path('experiments/document-navigation/render-document-views.py')
CLASSES={'STABLE','STABLE_WITH_GENERATED_SECTION','CURRENT_SOURCE','CURRENT_REGISTRY','CURRENT_INPUT_LOCK','ACTIVE_PLAN','APPEND_ONLY_LOG','FROZEN_AUTHORITY','HISTORICAL_SNAPSHOT','GENERATED_VIEW','REFERENCE','RAW_REFERENCE'}
REQ={'path','format','lifecycle_class','authority_domain','owner','mutability','update_trigger','supersession_rule','onboarding_visibility','machine_binding_policy','migration_action'}
CURRENT={'README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md','docs/SESSION_ONBOARDING.md'}

def sha(p:Path)->str:
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def load(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def tracked(root:Path)->set[str]:
 out=subprocess.run(['git','ls-files','-z'],cwd=root,check=True,stdout=subprocess.PIPE).stdout.decode().split('\0');return {x for x in out if x and Path(x).suffix in {'.md','.json'}}
def bindings(root:Path,paths:set[str])->set[tuple[str,str,str]]:
 found=set()
 def walk(o:Any,ap:str):
  if isinstance(o,dict):
   fi=o.get('file_identities')
   if isinstance(fi,dict):
    for t,v in fi.items():
     d=v.get('sha256') if isinstance(v,dict) else v
     if isinstance(t,str) and isinstance(d,str):found.add((ap,t,d))
   for v in o.values():walk(v,ap)
  elif isinstance(o,list):
   for v in o:walk(v,ap)
 for p in sorted(paths):
  try:walk(load(root/p),p)
  except Exception:pass
 return found
def assignment(path:str,targets:set[str])->str:
 if path in targets:return 'docs/navigation/README.md'
 pairs=[('docs/current/','docs/current/README.md'),('docs/documentation/','docs/documentation/README.md'),('docs/decisions/','docs/decisions/README.md'),('docs/epochs/','docs/epochs/README.md'),('docs/architecture/','docs/architecture/README.md'),('docs/roadmap/','docs/roadmap/README.md'),('docs/contracts/','docs/contracts/README.md'),('docs/evidence/','docs/evidence/README.md'),('docs/stages/','docs/stages/README.md'),('docs/handoff/','docs/handoff/README.md'),('docs/references/','docs/references/README.md'),('experiments/','experiments/README.md')]
 for prefix,target in pairs:
  if path.startswith(prefix):return target
 return 'docs/navigation/README.md'
def verify(root:Path)->dict[str,Any]:
 checks={};errors={}
 def ck(n,v,e=''):
  checks[n]=bool(v)
  if not v and e:errors[n]=e
 try:reg=load(root/REG);rs=load(root/RS);state=load(root/STATE);ss=load(root/SS);base=load(root/BASE);man=load(root/MAN);ck('control_files_parse',True)
 except Exception as exc:reg={};rs={};state={};ss={};base={};man={};ck('control_files_parse',False,str(exc))
 ck('registry_v3_identity',reg.get('schema_version')==3 and reg.get('registry_kind')=='document-lifecycle-registry' and reg.get('schema_path')==str(RS))
 basis=reg.get('basis',{});ck('phase3_boundary',basis.get('migration_phase')==3 and basis.get('predecessor_head')=='909c600e2f822b82be2cfab807c14836991ba0e3' and basis.get('predecessor_tree')=='e12ab142db1a7b3c9dfe063d3db26d83e1cb58a9' and basis.get('current_source_present') is True and basis.get('full_navigation_enabled') is True and basis.get('physical_moves_allowed') is False)
 ck('registry_schema_identity',rs.get('$id')=='urn:cpython-android-cli:document-registry:v3');ck('state_schema_identity',ss.get('$id')=='urn:cpython-android-cli:current-state:v2');ck('lifecycle_class_set',set(reg.get('lifecycle_classes',[]))==CLASSES)
 docs=reg.get('documents',[]);paths=[d.get('path') for d in docs if isinstance(d,dict)];ck('registry_paths_unique',len(paths)==len(set(paths)));ck('required_metadata_complete',all(isinstance(d,dict) and REQ.issubset(d) and all(isinstance(d.get(k),str) and d.get(k) for k in REQ) for d in docs))
 try:t=tracked(root);ck('git_document_inventory',True)
 except Exception as exc:t=set();ck('git_document_inventory',False,str(exc))
 rp={p for p in paths if isinstance(p,str)};ck('tracked_documents_exact',t==rp,f'missing={sorted(t-rp)} extra={sorted(rp-t)}');ck('registry_count_exact',basis.get('tracked_document_count')==len(t)==len(rp)==447)
 by={d['path']:d for d in docs if isinstance(d,dict) and isinstance(d.get('path'),str)};ck('single_current_source',[p for p,d in by.items() if d.get('lifecycle_class')=='CURRENT_SOURCE']==[str(STATE)]);ck('single_current_registry',[p for p,d in by.items() if d.get('lifecycle_class')=='CURRENT_REGISTRY']==[str(REG)])
 ck('state_identity',state.get('schema_version')==2 and state.get('schema_path')==str(SS) and state.get('state_kind')=='project-current-state' and state.get('state_revision')==2);ck('state_predecessor',state.get('predecessor')=={'commit':'909c600e2f822b82be2cfab807c14836991ba0e3','tree':'e12ab142db1a7b3c9dfe063d3db26d83e1cb58a9'})
 program=state.get('program',{});control=state.get('control_work',{});ck('program_gate',program.get('epoch',{}).get('id')=='E2' and program.get('gate',{}).get('id')=='E2-R1/UT-0' and program.get('next_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control');ck('control_next_action',control.get('completed_phase')==3 and control.get('next_phase')==4 and control.get('next_action_class')==state.get('next_action_class')=='execute-document-lifecycle-phase4-mixed-document-correction' and control.get('resume_program_action_class')==program.get('next_action_class'))
 auths=state.get('accepted_authorities',[]);ids=[a.get('id') for a in auths if isinstance(a,dict)];ck('accepted_authorities_unique',len(ids)==len(set(ids))==6);ok=True
 for a in auths:
  p=root/str(a.get('path',''))
  if not p.is_file() or sha(p)!=a.get('sha256'):ok=False
 ck('accepted_authority_identities',ok);ck('phase3_authority_selected','document-generated-navigation-phase3' in ids)
 rt=state.get('render_targets',{});current=set(rt.get('current',[]));navigation=set(rt.get('navigation',[]));manifest_targets={x.get('path') for x in man.get('targets',[]) if isinstance(x,dict)};ck('current_target_contract',current==CURRENT);ck('navigation_manifest_identity',man.get('schema_version')==1 and man.get('manifest_kind')=='document-navigation-targets' and len(manifest_targets)==13);ck('navigation_target_contract',navigation==manifest_targets and basis.get('navigation_target_count')==len(navigation)==state.get('navigation',{}).get('target_count')==13)
 ck('navigation_target_classification',all(by.get(p,{}).get('lifecycle_class')=='GENERATED_VIEW' and by.get(p,{}).get('mutability')=='generated' for p in navigation));ck('navigation_root',state.get('navigation',{}).get('root')=='docs/navigation/README.md' and state.get('navigation',{}).get('coverage')=='all-tracked-markdown-json')
 render=subprocess.run([sys.executable,str(root/RENDER),'--root',str(root),'--check'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);ck('generated_views_exact',render.returncode==0,render.stdout+render.stderr)
 # Every non-target path has exactly one canonical assignment and each target exists.
 assigned={p:assignment(p,navigation) for p in rp if p not in navigation};ck('canonical_assignment_complete',set(assigned)==(rp-navigation) and all(v in navigation for v in assigned.values()));ck('generated_entrypoints_exist',all((root/p).is_file() for p in navigation));ck('historical_handoff_preserved',(root/'docs/handoff/2026-07-16-stage3f-successor-session-reading-path-snapshot.md').is_file() and by.get('docs/handoff/2026-07-16-stage3f-successor-session-reading-path-snapshot.md',{}).get('lifecycle_class')=='HISTORICAL_SNAPSHOT')
 # Basic generated-link integrity.
 broken=[]
 link_re=re.compile(r'\[[^\]]*\]\(([^)]+)\)')
 for src in sorted(current|navigation):
  text=(root/src).read_text(encoding='utf-8')
  for href in link_re.findall(text):
   if '://' in href or href.startswith('#'):continue
   target=(root/Path(src).parent/href.split('#',1)[0]).resolve()
   if not target.exists():broken.append((src,href))
 ck('generated_links_resolve',not broken,str(broken[:20]));ck('current_views_link_navigation',all('docs/navigation/README.md' in (root/p).read_text(encoding='utf-8') or 'navigation/README.md' in (root/p).read_text(encoding='utf-8') for p in current))
 baseline={(b.get('authority_path'),b.get('target_path'),b.get('recorded_sha256')) for b in base.get('bindings',[]) if isinstance(b,dict)};forbidden={p for p,d in by.items() if d.get('lifecycle_class') in {'CURRENT_SOURCE','CURRENT_REGISTRY','GENERATED_VIEW','STABLE_WITH_GENERATED_SECTION','ACTIVE_PLAN'} or 'forbidden' in str(d.get('machine_binding_policy','')).lower() or 'legacy' in str(d.get('machine_binding_policy','')).lower()};observed=bindings(root,{p for p in t if p.endswith('.json')});ob={b for b in observed if b[1] in forbidden};ck('legacy_bindings_preserved',ob==baseline,f'missing={sorted(baseline-ob)} extra={sorted(ob-baseline)}');ck('live_state_not_bound',not any(b[1]==str(STATE) for b in observed));ck('live_registry_not_bound',not any(b[1]==str(REG) for b in observed));ck('generated_navigation_not_bound',not any(b[1] in navigation for b in observed));ck('no_new_live_generated_binding',not(ob-baseline))
 successors=True
 for d in docs:
  for q in d.get('current_successors',[]) or []:
   if q not in by or not (root/q).is_file():successors=False
 ck('current_successors_exist',successors);ck('claim_boundary_unchanged',state.get('claim_boundaries')=={'dual_real_device_aarch64_termux_compatibility':True,'emulator_qualified':False,'selectable':False,'publication_authorized':False,'epoch3_feature_selection_started':False});ck('no_self_commit_claim','as_of_commit' not in state and 'as_of_tree' not in state)
 failed=[n for n,v in checks.items() if not v];return {'schema_version':1,'verifier_kind':'document-generated-navigation-phase3','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':errors,'metrics':{'tracked_document_count':len(t),'registry_document_count':len(rp),'navigation_target_count':len(navigation),'canonical_assignment_count':len(assigned),'legacy_binding_count':len(baseline),'broken_link_count':len(broken)}}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args();r=verify(Path(a.root).resolve());print(json.dumps(r,indent=2,sort_keys=True));return 0 if r['pass'] else 1
if __name__=='__main__':sys.exit(main())
