#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
A=Path('experiments/agent-task-completion/agent-task-completion-authority.json');U=Path('experiments/agent-task-completion/agent-task-completion-external-audit.json')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--live-result');ap.add_argument('--negative-result');ap.add_argument('--snapshot-result');x=ap.parse_args();r=Path(x.root).resolve();checks={};errors={}
 def ck(n,v,e=''):checks[n]=bool(v);errors.update({n:e} if not v and e else {})
 try:o=load(r/A);u=load(r/U);s=load(r/'docs/current/STATE.json');ck('parse',True)
 except Exception as e:o={};u={};s={};ck('parse',False,str(e))
 ck('identity',o.get('authority_kind')=='agent-task-completion-contract-hardening' and o.get('schema_version')==1 and o.get('authority_version')==1)
 ck('status',o.get('status')=='frozen-pass-task-completion-routing-enforced')
 ck('predecessor',o.get('predecessor')=={'commit':'2b5b0b9ef742c36d5a29d4643fb53bf471000415','tree':'e16010a5712c6c098b29887958e1352469436cba'})
 cb=o.get('claim_boundary',{});ck('claim_boundary',cb.get('task_completion_routing_enforced') is True and cb.get('bootstrap_changed') is False and cb.get('device_execution_required') is False and cb.get('product_or_experiment_claim_change') is False)
 ids=o.get('file_identities',{});ok=bool(ids)
 for p,d in ids.items():
  if not (r/p).is_file() or sha(r/p)!=d:ok=False;break
 ck('file_identities',ok)
 forbidden={'docs/current/STATE.json','docs/current/AGENT_TASK.json','docs/documentation/document-registry.json','README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'};ck('live_generated_not_bound',not(set(ids)&forbidden))
 for name,result,path in [('live',x.live_result,'experiments/agent-task-completion/verify-agent-task-completion.py'),('negative',x.negative_result,'experiments/agent-task-completion/test-agent-task-completion.py'),('snapshot',x.snapshot_result,'experiments/agent-task-completion/verify-frozen-agent-bootstrap-snapshot.py')]:
  if result:
   try:z=load(Path(result));ck(name,z.get('pass') is True and z.get('failed_checks')==[])
   except Exception as e:ck(name,False,str(e))
  else:
   p=subprocess.run([sys.executable,str(r/path),'--root',str(r)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);ck(name,p.returncode==0,p.stderr or p.stdout)
 digest=sha(r/A);latest=next((a for a in s.get('accepted_authorities',[]) if a.get('id')=='agent-task-completion-contract-hardening'),{});ck('state_selects_authority',latest.get('path')==str(A) and latest.get('sha256')==digest)
 tc=s.get('task_completion',{});ck('state_completion',tc.get('status')=='enforced' and tc.get('authority_sha256')==digest and tc.get('current_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control')
 ck('audit_identity',u.get('audit_kind')=='agent-task-completion-contract-external-audit' and u.get('source_authority_path')==str(A) and u.get('source_authority_sha256')==digest)
 ck('audit_pass',u.get('pass') is True and u.get('blockers')==[] and all(u.get('checks',{}).values()))
 ev=(r/'docs/evidence/AGENT_TASK_COMPLETION_CONTRACT_AUTHORITY_FREEZE.md').read_text();hist=(r/'docs/history/2026-07-19-agent-task-completion-contract-hardening.md').read_text();ck('evidence_binding',digest in ev);ck('history_binding',digest in hist)
 ck('verification_shape',o.get('verification',{}).get('render')=='20/20' and o.get('verification',{}).get('live')=='25/25' and o.get('verification',{}).get('negative')=='16/16' and o.get('verification',{}).get('bootstrap_snapshot')=='10/10')
 ck('next_action',o.get('next_action_class')=='execute-e2-r1-ut0-exact-official-upstream-control')
 failed=[k for k,v in checks.items() if not v];out={'schema_version':1,'verifier_kind':'agent-task-completion-authority','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':errors};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())
