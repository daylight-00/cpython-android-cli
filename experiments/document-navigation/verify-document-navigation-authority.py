#!/usr/bin/env python3
"""Verify frozen Phase 3 generated-navigation authority."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
from typing import Any
A=Path('experiments/document-navigation/document-navigation-authority.json');U=Path('experiments/document-navigation/document-navigation-external-audit.json');E=Path('docs/evidence/DOCUMENT_GENERATED_NAVIGATION_AUTHORITY_FREEZE.md');H=Path('docs/handoff/2026-07-19-document-generated-navigation.md')
def sha(p:Path)->str:
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def load(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def verify(root:Path)->dict[str,Any]:
 checks={};errors={}
 def ck(n,v,e=''):checks[n]=bool(v);errors.update({n:e} if not v and e else {})
 try:a=load(root/A);u=load(root/U);state=load(root/'docs/current/STATE.json');ck('authority_and_audit_parse',True)
 except Exception as exc:a={};u={};state={};ck('authority_and_audit_parse',False,str(exc))
 ck('authority_identity',a.get('schema_version')==1 and a.get('authority_kind')=='document-generated-navigation-phase3' and a.get('authority_version')==1);ck('authority_status',a.get('status')=='frozen-pass-complete-generated-navigation-established');ck('predecessor',a.get('predecessor')=={'commit':'909c600e2f822b82be2cfab807c14836991ba0e3','tree':'e12ab142db1a7b3c9dfe063d3db26d83e1cb58a9'})
 scope=a.get('scope',{});ck('scope',scope.get('tracked_markdown_json_count')==447 and scope.get('current_render_target_count')==4 and scope.get('navigation_target_count')==13 and scope.get('physical_moves') is False and scope.get('historical_byte_rewrites') is False);ck('claim_boundary',a.get('claim_boundary')=={'complete_generated_navigation':True,'current_state_single_writer':True,'mixed_document_normalization':False,'physical_document_moves':False,'product_or_experiment_claim_change':False});ck('next_action',a.get('next_action_class')=='execute-document-lifecycle-phase4-mixed-document-correction' and a.get('resume_program_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control')
 ids=a.get('file_identities',{});ok=isinstance(ids,dict) and bool(ids)
 if ok:
  for rel,d in ids.items():
   p=root/rel
   if not p.is_file() or sha(p)!=d:ok=False;break
 ck('file_identities',ok);live={'docs/current/STATE.json','docs/documentation/document-registry.json','README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md','docs/SESSION_ONBOARDING.md'}|set(a.get('generated_targets',[]));ck('live_paths_not_bound',not(set(ids)&live));ck('target_manifest_bound','experiments/document-navigation/navigation-targets.json' in ids);ck('state_schema_v2_bound','docs/current/STATE-v2.schema.json' in ids);ck('registry_schema_v3_bound','docs/documentation/document-registry-v3.schema.json' in ids)
 precomputed=os.environ.get('HW_T_PHASE3_SNAPSHOT_RESULT','')
 if precomputed:
  try:
   q=json.loads(Path(precomputed).read_text(encoding='utf-8'));p2_rc=0 if q.get('pass') is True else 1;p2_detail=json.dumps(q,sort_keys=True)
  except Exception as exc:
   q={};p2_rc=1;p2_detail=str(exc)
 else:
  p2=subprocess.run([sys.executable,str(root/'experiments/document-navigation/verify-frozen-phase2-snapshot.py'),'--root',str(root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  try:q=json.loads(p2.stdout)
  except Exception:q={}
  p2_rc=p2.returncode;p2_detail=p2.stdout+p2.stderr
 ck('phase2_snapshot_preserved',p2_rc==0 and q.get('pass') is True and q.get('check_count')==9,p2_detail)
 ash=sha(root/A) if (root/A).is_file() else '';ck('state_selects_authority',any(x.get('id')=='document-generated-navigation-phase3' and x.get('sha256')==ash for x in state.get('accepted_authorities',[])));ck('audit_identity',u.get('schema_version')==1 and u.get('audit_kind')=='document-generated-navigation-phase3-external-audit');ck('audit_source',u.get('source',{}).get('authority_sha256')==ash);ck('audit_pass',u.get('pass') is True and u.get('check_count')==u.get('pass_count') and u.get('failed_checks')==[] and all(u.get('checks',{}).values()))
 ev=(root/E).read_text(encoding='utf-8') if (root/E).is_file() else '';ho=(root/H).read_text(encoding='utf-8') if (root/H).is_file() else '';ck('evidence_binding',ash in ev and '447/447' in ev and '13/13' in ev);ck('handoff_binding',ash in ho and a.get('next_action_class','') in ho)
 failed=[n for n,v in checks.items() if not v];return {'schema_version':1,'verifier_kind':'document-generated-navigation-authority-phase3','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':errors}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args();r=verify(Path(a.root).resolve());print(json.dumps(r,indent=2,sort_keys=True));return 0 if r['pass'] else 1
if __name__=='__main__':sys.exit(main())
