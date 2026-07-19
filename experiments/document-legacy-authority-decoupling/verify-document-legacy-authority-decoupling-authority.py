#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,subprocess,sys
from pathlib import Path
A=Path('experiments/document-legacy-authority-decoupling/legacy-authority-decoupling-authority.json');U=Path('experiments/document-legacy-authority-decoupling/legacy-authority-decoupling-external-audit.json')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--binding-result');ap.add_argument('--live-result');ap.add_argument('--snapshot-result');x=ap.parse_args();r=Path(x.root).resolve();checks={};err={}
 def ck(n,v,e=''):checks[n]=bool(v);err.update({n:e} if not v and e else {})
 try:o=load(r/A);u=load(r/U);s=load(r/'docs/current/STATE.json');ck('parse',True)
 except Exception as e:o={};u={};s={};ck('parse',False,str(e))
 ck('identity',o.get('authority_kind')=='document-legacy-authority-decoupling-phase5' and o.get('schema_version')==1 and o.get('authority_version')==1)
 ck('status',o.get('status')=='frozen-pass-legacy-authority-decoupled-document-migration-complete')
 ck('predecessor',o.get('predecessor')=={'commit':'d201957a11861147bdbe11b6a91bf68fb6714a4d','tree':'1c0c692d7763487ad2ba0d91a7f2bf04b6e0b423'})
 cb=o.get('claim_boundary',{});ck('claim_boundary',cb=={'legacy_authority_decoupling':True,'historical_authority_bytes_rewritten':False,'live_paths_bound_to_historical_digests':False,'new_live_generated_bindings_allowed':False,'physical_document_moves':False,'documentation_lifecycle_migration_complete':True,'product_or_experiment_claim_change':False})
 sc=o.get('scope',{});ck('scope',sc.get('legacy_binding_count')==sc.get('compatibility_snapshot_count')==24 and sc.get('original_authority_count')==6 and sc.get('navigation_target_count')==15 and sc.get('tracked_markdown_json_count')>463)
 ids=o.get('file_identities',{});ok=bool(ids)
 for p,d in ids.items():
  if not (r/p).is_file() or sha(r/p)!=d:ok=False;break
 ck('file_identities',ok)
 live={'README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md','docs/SESSION_ONBOARDING.md','docs/current/STATE.json','docs/documentation/document-registry.json','docs/history/legacy-authority-bindings/README.md'};ck('live_not_bound',not(set(ids)&live))
 children=[('binding_resolution',x.binding_result,'experiments/document-legacy-authority-decoupling/verify-legacy-binding-resolution.py',12),('live_verifier',x.live_result,'experiments/document-legacy-authority-decoupling/verify-legacy-authority-decoupling.py',21),('phase4_snapshot',x.snapshot_result,'experiments/document-legacy-authority-decoupling/verify-frozen-phase4-snapshot.py',9)]
 for name,result,path,count in children:
  if result:
   try:z=load(Path(result));ck(name,z.get('pass') is True and z.get('check_count')==count and z.get('pass_count')==count)
   except Exception as e:ck(name,False,str(e))
  else:
   p=subprocess.run([sys.executable,str(r/path),'--root',str(r)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);ck(name,p.returncode==0,p.stderr or p.stdout)
 ck('verification_shape',o.get('verification')=={'binding_resolution':'12/12','phase5_live':'21/21','negative_fixtures':'12/12','phase4_snapshot':'9/9','phase5_authority':'21/21'})
 ck('completion_decision',o.get('completion_decision',{}).get('phase6_physical_relocation_required') is False)
 ck('next_action',o.get('next_action_class')==o.get('resume_program_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control')
 digest=sha(r/A);latest=next((a for a in s.get('accepted_authorities',[]) if a.get('id')=='document-legacy-authority-decoupling-phase5'),{});ck('state_selects_authority',latest.get('sha256')==digest and latest.get('path')==str(A))
 ck('state_next_action',s.get('next_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control' and s.get('control_work',{}).get('migration_complete') is True)
 ck('audit_identity',u.get('audit_kind')=='document-legacy-authority-decoupling-external-audit' and u.get('source_authority_sha256')==digest)
 ck('audit_pass',u.get('pass') is True and u.get('blockers')==[])
 ck('audit_source',u.get('source_authority_path')==str(A))
 ev=(r/'docs/evidence/DOCUMENT_LEGACY_AUTHORITY_DECOUPLING_AUTHORITY_FREEZE.md').read_text();ho=(r/'docs/handoff/2026-07-19-document-legacy-authority-decoupling.md').read_text();ck('evidence_binding',digest in ev);ck('handoff_binding',digest in ho)
 failed=[k for k,v in checks.items() if not v];out={'schema_version':1,'verifier_kind':'document-legacy-authority-decoupling-authority-phase5','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':err};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())
