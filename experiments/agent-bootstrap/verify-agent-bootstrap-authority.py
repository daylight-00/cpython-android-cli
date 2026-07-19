#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
A=Path('experiments/agent-bootstrap/agent-bootstrap-authority.json');U=Path('experiments/agent-bootstrap/agent-bootstrap-external-audit.json')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--bootstrap-result');ap.add_argument('--snapshot-result');x=ap.parse_args();r=Path(x.root).resolve();checks={};errors={}
 def ck(n,v,e=''):checks[n]=bool(v);errors.update({n:e} if not v and e else {})
 try:o=load(r/A);u=load(r/U);s=load(r/'docs/current/STATE.json');c=load(r/'docs/agent/BOOTSTRAP_CONTRACT.json');ck('parse',True)
 except Exception as e:o={};u={};s={};c={};ck('parse',False,str(e))
 ck('identity',o.get('authority_kind')=='immutable-agent-bootstrap-and-bundle-session-protocol' and o.get('schema_version')==1 and o.get('authority_version')==1)
 ck('status',o.get('status')=='frozen-pass-agent-bootstrap-established-handoff-loop-retired')
 ck('predecessor',o.get('predecessor')=={'commit':'34695ed741411067302bd7372e3b7024b5fab541','tree':'8537ad0495915491fce158abe1f25851f5149708'})
 cb=o.get('claim_boundary',{});ck('claim_boundary',cb.get('agent_onboarding_system_established') is True and cb.get('drive_connector_first') is True and cb.get('github_connector_or_api_allowed') is False and cb.get('ordinary_handoff_packages_required') is False and cb.get('product_or_experiment_claim_change') is False and cb.get('device_execution_required') is False)
 sc=o.get('scope',{});ck('scope',sc.get('immutable_bootstrap_count')==1 and sc.get('mandatory_stable_module_count')==2 and sc.get('generated_task_manifest_count')==1 and sc.get('mandatory_session_rule_count')==20 and sc.get('predecessor_snapshot_count')==13 and sc.get('navigation_target_count')==16)
 ids=o.get('file_identities',{});ok=bool(ids)
 for p,d in ids.items():
  if not (r/p).is_file() or sha(r/p)!=d:ok=False;break
 ck('file_identities',ok)
 forbidden={'docs/current/STATE.json','docs/current/AGENT_TASK.json','docs/documentation/document-registry.json','README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'};ck('live_generated_not_bound',not(set(ids)&forbidden))
 ck('bootstrap_contract',ids.get('AGENT_BOOTSTRAP.md')==c.get('bootstrap',{}).get('sha256'))
 children=[('bootstrap',x.bootstrap_result,'experiments/agent-bootstrap/verify-agent-bootstrap.py'),('phase5_snapshot',x.snapshot_result,'experiments/agent-bootstrap/verify-frozen-phase5-snapshot.py')]
 for name,result,path in children:
  if result:
   try:z=load(Path(result));ck(name,z.get('pass') is True and z.get('failed_checks')==[])
   except Exception as e:ck(name,False,str(e))
  else:
   p=subprocess.run([sys.executable,str(r/path),'--root',str(r)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);ck(name,p.returncode==0,p.stderr or p.stdout)
 digest=sha(r/A);latest=next((a for a in s.get('accepted_authorities',[]) if a.get('id')=='immutable-agent-bootstrap-bundle-session-protocol'),{});ck('state_selects_authority',latest.get('path')==str(A) and latest.get('sha256')==digest)
 ao=s.get('agent_onboarding',{});ck('state_bootstrap',ao.get('status')=='established' and ao.get('bootstrap_path')=='AGENT_BOOTSTRAP.md' and ao.get('ordinary_handoff_packages_required') is False and ao.get('authority_sha256')==digest)
 ck('state_next_action',s.get('next_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control')
 ck('audit_identity',u.get('audit_kind')=='immutable-agent-bootstrap-external-audit' and u.get('source_authority_path')==str(A) and u.get('source_authority_sha256')==digest)
 ck('audit_pass',u.get('pass') is True and u.get('blockers')==[] and all(u.get('checks',{}).values()))
 ev=(r/'docs/evidence/AGENT_BOOTSTRAP_AND_BUNDLE_SESSION_PROTOCOL_AUTHORITY_FREEZE.md').read_text();hist=(r/'docs/history/2026-07-19-agent-bootstrap-and-bundle-session-transition.md').read_text();ck('evidence_binding',digest in ev);ck('history_binding',digest in hist)
 ck('no_new_handoff',not (r/'docs/handoff/2026-07-19-agent-bootstrap-and-bundle-session-transition.md').exists())
 ck('verification_shape',o.get('verification',{}).get('render')=='20/20' and o.get('verification',{}).get('negative_fixtures')=='15/15' and o.get('verification',{}).get('phase5_snapshot')=='9/9')
 ck('next_action',o.get('next_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control')
 failed=[k for k,v in checks.items() if not v];out={'schema_version':1,'verifier_kind':'agent-bootstrap-authority','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':errors};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())
