#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True,stderr=subprocess.DEVNULL).strip()
def rev(p):
 m=re.search(r'^> \*\*Revision:\*\* (\d+)\s*$',p.read_text(encoding='utf-8'),re.M);return int(m.group(1)) if m else None
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');x=ap.parse_args();r=Path(x.root).resolve();errors=[]
 try:c=load(r/'docs/agent/BOOTSTRAP_CONTRACT.json');s=load(r/'docs/current/STATE.json');t=load(r/'docs/current/AGENT_TASK.json');k=load(r/'docs/agent/TASK_CATALOG.json')
 except Exception as e:print(json.dumps({'pass':False,'errors':[str(e)]},indent=2));return 1
 if sha(r/c['bootstrap']['path'])!=c['bootstrap']['sha256']:errors.append('bootstrap-sha256')
 actions=[s.get('next_action_class'),s.get('program',{}).get('next_action_class'),s.get('control_work',{}).get('next_action_class'),s.get('control_work',{}).get('resume_program_action_class')]
 if len(set(actions))!=1:errors.append('state-action-equality')
 if s.get('state_revision')!=t.get('state_revision'):errors.append('state-task-revision')
 if actions[0]!=t.get('task',{}).get('action_class'):errors.append('state-task-action')
 pm=r/s['project_model']['path'];sp=r/s['session_protocol']['path'];tc=r/s['task_catalog']['path']
 if rev(pm)!=s['agent_onboarding']['project_model_revision'] or sha(pm)!=s['project_model']['sha256']:errors.append('project-model-identity')
 if rev(sp)!=s['agent_onboarding']['session_protocol_revision'] or sha(sp)!=s['session_protocol']['sha256']:errors.append('session-protocol-identity')
 if sha(tc)!=s['task_catalog']['sha256'] or k.get('schema_version')!=s['task_catalog']['schema_version']:errors.append('task-catalog-identity')
 matches=[q for q in k.get('tasks',[]) if q.get('action_class')==actions[0]]
 if len(matches)!=1 or t.get('completion_contract')!=matches[0].get('completion_contract'):errors.append('completion-contract')
 try:branch=git(r,'branch','--show-current');head=git(r,'rev-parse','HEAD');tree=git(r,'rev-parse','HEAD^{tree}');clean=git(r,'status','--porcelain')=='';refs=git(r,'show-ref')
 except Exception as e:branch=head=tree='unknown';clean=False;refs='';errors.append('git-state:'+str(e))
 out={'schema_version':2,'certificate_kind':'agent-onboarding-mechanical-certificate','pass':not errors,'errors':errors,'repository':{'branch':branch,'head':head,'tree':tree,'clean':clean,'refs':refs.splitlines()},'bootstrap':{'path':c['bootstrap']['path'],'sha256':c['bootstrap']['sha256'],'contract_version':c['schema_version']},'mandatory_read_order':c['mandatory_read_order'],'module_revisions':{'project_model':rev(pm),'session_protocol':rev(sp)},'state_revision':s.get('state_revision'),'program':s.get('program'),'next_action_class':actions[0],'work_class':t.get('task',{}).get('work_class'),'required_reads':t.get('required_reads',[]),'required_authorities':t.get('required_authorities',[]),'completion_contract':t.get('completion_contract',{}),'default_exclusions':t.get('default_exclusions',[]),'claim_boundary':t.get('claim_boundary',{}),'blockers':s.get('blockers',[]),'unresolved_risks':s.get('unresolved_risks',[]),'agent_attestation_required':['mandatory modules read in full','task sections read exactly','completion contract understood','additional reads listed with justification']}
 print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())
