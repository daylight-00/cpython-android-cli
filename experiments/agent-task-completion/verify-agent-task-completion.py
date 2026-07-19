#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
S=Path('docs/current/STATE.json');T=Path('docs/current/AGENT_TASK.json');K=Path('docs/agent/TASK_CATALOG.json');R=Path('docs/documentation/document-registry.json')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def rev(text):
 m=re.search(r'^> \*\*Revision:\*\* (\d+)\s*$',text,re.M);return int(m.group(1)) if m else None
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--render-result');x=ap.parse_args();r=Path(x.root).resolve();checks={};errors={}
 def ck(n,v,e=''):checks[n]=bool(v);errors.update({n:e} if not v and e else {})
 try:s=load(r/S);t=load(r/T);k=load(r/K);reg=load(r/R);ck('parse',True)
 except Exception as e:s={};t={};k={};reg={};ck('parse',False,str(e))
 ck('state_schema',s.get('schema_version')==6 and s.get('schema_path')=='docs/current/STATE-v6.schema.json' and s.get('state_revision')==6)
 actions=[s.get('next_action_class'),s.get('program',{}).get('next_action_class'),s.get('control_work',{}).get('next_action_class'),s.get('control_work',{}).get('resume_program_action_class')]
 ck('state_action_equality',len(set(actions))==1 and actions[0]=='execute-e2-r1-ut0-exact-official-upstream-control')
 pm=r/s.get('project_model',{}).get('path','');sp=r/s.get('session_protocol',{}).get('path','');tc=r/s.get('task_catalog',{}).get('path','')
 ck('project_model_identity',pm.is_file() and sha(pm)==s.get('project_model',{}).get('sha256') and rev(pm.read_text())==s.get('agent_onboarding',{}).get('project_model_revision'))
 ck('session_protocol_identity',sp.is_file() and sha(sp)==s.get('session_protocol',{}).get('sha256') and rev(sp.read_text())==s.get('agent_onboarding',{}).get('session_protocol_revision')==s.get('session_protocol',{}).get('revision'))
 ck('task_catalog_identity',tc.is_file() and sha(tc)==s.get('task_catalog',{}).get('sha256') and k.get('schema_version')==s.get('task_catalog',{}).get('schema_version')==2)
 apath=r/s.get('active_plan',{}).get('path','');dpath=r/s.get('active_plan',{}).get('detail_path','')
 ck('active_plan_identity',apath.is_file() and dpath.is_file() and sha(apath)==s.get('active_plan',{}).get('sha256') and sha(dpath)==s.get('active_plan',{}).get('detail_sha256'))
 current=[q for q in k.get('tasks',[]) if q.get('action_class')==actions[0]];ck('current_catalog_resolution',len(current)==1)
 cur=current[0] if current else {};ck('current_activation',cur.get('activation',{}).get('status')=='ready' and cur.get('activation',{}).get('prerequisites_satisfied') is True)
 ck('manifest_alignment',t.get('schema_version')==2 and t.get('state_revision')==s.get('state_revision') and t.get('program_gate')==s.get('program',{}).get('gate') and t.get('task',{}).get('action_class')==actions[0] and t.get('task',{}).get('id')==cur.get('task_id'))
 ck('completion_contract_exact',bool(cur.get('completion_contract')) and t.get('completion_contract')==cur.get('completion_contract'))
 c=cur.get('completion_contract',{});ck('completion_contract_version',c.get('contract_version')==1)
 always=c.get('always',{});ck('always_contract',all(always.get(x) is True for x in ['new_markdown_or_json_requires_registry_update','generated_views_must_be_regenerated','all_required_verifiers_must_pass','one_runner_and_complete_receipt_required','clean_main_and_bundle_export_ready_on_close']))
 ps=c.get('pass',{});required_pass={'state_revision','predecessor','accepted_authorities','program.gate','program.next_action_class','next_action_class','control_work.next_action_class','control_work.resume_program_action_class','unresolved_risks','updated_by_transaction'}
 ck('pass_state_updates',required_pass.issubset(set(ps.get('required_state_updates',[]))))
 roles={'gate-contract','upstream-input-manifest','package-and-file-hashes','elf-and-extension-inventory','dependency-provider-map','sysconfig-census','package-layout-map','provenance-map','producer-delta','independent-audit','machine-authority','evidence-freeze'}
 ck('pass_output_roles',set(ps.get('required_output_roles',[]))==roles and ps.get('required_output_namespace')=='experiments/epoch2-upstream-thin-control/')
 successor=[q for q in k.get('tasks',[]) if q.get('action_class')==ps.get('successor_action_class')];ck('successor_resolution',ps.get('successor_must_exist') is True and len(successor)==1 and successor[0].get('task_id')==ps.get('successor_task_id'))
 suc=successor[0] if successor else {};ck('successor_blocked',suc.get('activation',{}).get('status')=='blocked-on-predecessor-authority' and suc.get('activation',{}).get('prerequisites_satisfied') is False and suc.get('activation',{}).get('required_predecessor_action_class')==actions[0])
 fail=c.get('fail',{});required_fail={'state_revision','predecessor','active_work_package','blockers','unresolved_risks','updated_by_transaction'}
 ck('fail_state_updates',required_fail.issubset(set(fail.get('required_state_updates',[]))) and fail.get('complete_receipt_required') is True)
 ck('fail_routing',fail.get('allowed_action_policy')=='retain-current-action-or-select-cataloged-bounded-correction' and fail.get('correction_task_must_be_cataloged') is True and fail.get('correction_task_must_resume_action_class')==actions[0])
 sections=True
 for q in t.get('required_reads',[])+suc.get('required_reads',[]):
  p=r/q.get('path','');a=q.get('section_heading');b=q.get('stop_before_heading');text=p.read_text(encoding='utf-8') if p.is_file() else ''
  if q.get('scope')=='section' and (not a or not b or text.count(a)!=1 or text.count(b)!=1 or text.index(a)>=text.index(b)):sections=False;break
 ck('section_boundaries',sections)
 auth=True
 for q in t.get('required_authorities',[]):
  p=r/q.get('path','')
  if not p.is_file() or sha(p)!=q.get('sha256'):auth=False;break
 ck('current_authorities',auth)
 tracked=subprocess.check_output(['git','-C',str(r),'ls-files','--','*.md','*.json'],text=True).splitlines();paths=[d.get('path') for d in reg.get('documents',[])];ck('registry_coverage',sorted(tracked)==sorted(paths) and len(paths)==len(set(paths)))
 ck('task_completion_state',s.get('task_completion',{}).get('status')=='enforced' and s.get('task_completion',{}).get('contract_version')==1 and s.get('task_completion',{}).get('current_action_class')==actions[0] and s.get('task_completion',{}).get('pass_successor_action_class')==ps.get('successor_action_class'))
 if x.render_result:
  try:z=load(Path(x.render_result));ck('render',z.get('pass') is True and z.get('target_count')==20 and z.get('mismatched_targets')==[])
  except Exception as e:ck('render',False,str(e))
 else:
  p=subprocess.run([sys.executable,str(r/'experiments/agent-task-completion/render-document-views.py'),'--root',str(r),'--check'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);ck('render',p.returncode==0,p.stderr or p.stdout)
 forbidden={'docs/current/STATE.json','docs/current/AGENT_TASK.json','README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'}
 newa=load(r/'experiments/agent-task-completion/agent-task-completion-authority.json') if (r/'experiments/agent-task-completion/agent-task-completion-authority.json').is_file() else {}
 ck('new_authority_no_live_binding',not(set(newa.get('file_identities',{}))&forbidden))
 failed=[k for k,v in checks.items() if not v];out={'schema_version':1,'verifier_kind':'agent-task-completion-contract','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':errors};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())
