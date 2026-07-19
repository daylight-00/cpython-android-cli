#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,subprocess,sys
from pathlib import Path
A=Path('experiments/document-mixed-correction/document-mixed-correction-authority.json');U=Path('experiments/document-mixed-correction/document-mixed-correction-external-audit.json')
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default='.');x=a.parse_args();r=Path(x.root).resolve();checks={};err={}
 def ck(n,v,e=''):checks[n]=bool(v);err.update({n:e} if not v and e else {})
 try:o=load(r/A);u=load(r/U);s=load(r/'docs/current/STATE.json');ck('parse',True)
 except Exception as e:o={};u={};s={};ck('parse',False,str(e))
 ck('identity',o.get('authority_kind')=='document-mixed-correction-phase4' and o.get('schema_version')==1 and o.get('authority_version')==1)
 ck('status',o.get('status')=='frozen-pass-mixed-document-layers-separated')
 ck('predecessor',o.get('predecessor')=={'commit':'38889c8ec1daf26ac029a230bb2281296ef92680','tree':'64a5d860c92235a5a857cc97f473b436fb2db468'})
 scope=o.get('scope',{});ck('scope',scope.get('stable_successor_count')==3 and scope.get('byte_preserved_mixed_path_count')==13 and scope.get('navigation_target_count')==14 and scope.get('physical_moves') is False and scope.get('historical_byte_rewrites') is False)
 cb=o.get('claim_boundary',{});ck('claim_boundary',cb=={'mixed_document_normalization':True,'legacy_authority_decoupling':False,'physical_document_moves':False,'product_or_experiment_claim_change':False})
 ids=o.get('file_identities',{});ok=bool(ids)
 for p,d in ids.items():
  if not (r/p).is_file() or sha(r/p)!=d:ok=False;break
 ck('file_identities',ok)
 forbidden={'README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md','docs/SESSION_ONBOARDING.md','docs/current/STATE.json','docs/documentation/document-registry.json','docs/history/README.md','docs/roadmap/README.md'};ck('live_not_bound',not(set(ids)&forbidden))
 ck('guide_bound','docs/PROJECT_GUIDE.md' in ids);ck('plan_bound','docs/roadmap/EPOCH2_PROGRAM_PLAN.md' in ids);ck('system_bound','docs/documentation/DOCUMENTATION_SYSTEM.md' in ids);ck('manifest_bound','experiments/document-mixed-correction/legacy-mixed-paths.json' in ids and 'experiments/document-mixed-correction/frozen-phase3-snapshot.json' in ids)
 live=subprocess.run([sys.executable,str(r/'experiments/document-mixed-correction/verify-mixed-document-correction.py'),'--root',str(r)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:lj=json.loads(live.stdout)
 except Exception:lj={}
 ck('live_verifier',live.returncode==0 and lj.get('pass') is True and lj.get('check_count')==27,live.stdout+live.stderr)
 snap=subprocess.run([sys.executable,str(r/'experiments/document-mixed-correction/verify-frozen-phase3-snapshot.py'),'--root',str(r)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:sj=json.loads(snap.stdout)
 except Exception:sj={}
 ck('phase3_snapshot',snap.returncode==0 and sj.get('pass') is True and sj.get('check_count')==10,snap.stdout+snap.stderr)
 ah=sha(r/A) if (r/A).is_file() else '';ck('state_selects_authority',any(z.get('id')=='document-mixed-document-correction-phase4' and z.get('sha256')==ah for z in s.get('accepted_authorities',[])))
 ck('state_next_action',s.get('next_action_class')=='execute-document-lifecycle-phase5-legacy-authority-decoupling')
 ck('audit_identity',u.get('audit_kind')=='document-mixed-correction-phase4-external-audit' and u.get('schema_version')==1)
 ck('audit_source',u.get('source',{}).get('authority_sha256')==ah)
 ck('audit_pass',u.get('pass') is True and u.get('check_count')==u.get('pass_count') and u.get('failed_checks')==[] and all(u.get('checks',{}).values()))
 ev=(r/'docs/evidence/DOCUMENT_MIXED_DOCUMENT_CORRECTION_AUTHORITY_FREEZE.md').read_text() if (r/'docs/evidence/DOCUMENT_MIXED_DOCUMENT_CORRECTION_AUTHORITY_FREEZE.md').is_file() else '';ho=(r/'docs/handoff/2026-07-19-document-mixed-document-correction.md').read_text() if (r/'docs/handoff/2026-07-19-document-mixed-document-correction.md').is_file() else '';ck('evidence_binding',ah in ev and 'snapshot-relative' in ev);ck('handoff_binding',ah in ho and o.get('next_action_class','') in ho)
 ck('next_boundary',o.get('next_action_class')=='execute-document-lifecycle-phase5-legacy-authority-decoupling' and o.get('resume_program_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control')
 failed=[k for k,v in checks.items() if not v];out={'schema_version':1,'verifier_kind':'document-mixed-correction-authority-phase4','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':err};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())
