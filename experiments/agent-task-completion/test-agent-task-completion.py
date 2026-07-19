#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil,subprocess,sys,tempfile
from pathlib import Path
V='experiments/agent-task-completion/verify-agent-task-completion.py'
def run(r,rr):return subprocess.run([sys.executable,V,'--root',str(r),'--render-result',str(rr)],cwd=r,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def editj(p,fn):o=json.loads(p.read_text());fn(o);p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');x=ap.parse_args();src=Path(x.root).resolve();tmp=Path(tempfile.mkdtemp());r=tmp/'r';r.mkdir();rr=tmp/'render.json';rr.write_text(json.dumps({'pass':True,'target_count':20,'mismatched_targets':[]})+'\n')
 try:
  files=subprocess.check_output(['git','-C',str(src),'ls-files','-z'],text=False).split(b'\0');files=[f.decode() for f in files if f]
  for rel in files:
   p=src/rel
   if p.is_file():q=r/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  subprocess.run(['git','init','-q'],cwd=r,check=True);subprocess.run(['git','add','-f','-A'],cwd=r,check=True)
  restore_paths=['docs/current/STATE.json','docs/agent/TASK_CATALOG.json','docs/current/AGENT_TASK.json','docs/documentation/document-registry.json','experiments/agent-task-completion/agent-task-completion-authority.json']
  def restore():subprocess.run(['git','checkout-index','-f','--',*restore_paths],cwd=r,check=True,stdout=subprocess.DEVNULL)
  checks={'baseline-pass':run(r,rr)};cases=[]
  cases.append(('state-action-mismatch',lambda:editj(r/'docs/current/STATE.json',lambda o:o['program'].__setitem__('next_action_class','bad'))))
  cases.append(('model-revision',lambda:editj(r/'docs/current/STATE.json',lambda o:o['agent_onboarding'].__setitem__('project_model_revision',99))))
  cases.append(('protocol-revision',lambda:editj(r/'docs/current/STATE.json',lambda o:o['agent_onboarding'].__setitem__('session_protocol_revision',99))))
  cases.append(('plan-digest',lambda:editj(r/'docs/current/STATE.json',lambda o:o['active_plan'].__setitem__('detail_sha256','0'*64))))
  cases.append(('catalog-digest',lambda:editj(r/'docs/current/STATE.json',lambda o:o['task_catalog'].__setitem__('sha256','0'*64))))
  cases.append(('missing-contract',lambda:editj(r/'docs/agent/TASK_CATALOG.json',lambda o:o['tasks'][0].pop('completion_contract'))))
  cases.append(('manifest-contract',lambda:editj(r/'docs/current/AGENT_TASK.json',lambda o:o['completion_contract']['contract_version'].__class__ and o['completion_contract'].__setitem__('contract_version',9))))
  cases.append(('missing-pass-update',lambda:editj(r/'docs/agent/TASK_CATALOG.json',lambda o:o['tasks'][0]['completion_contract']['pass'].__setitem__('required_state_updates',[]))))
  cases.append(('missing-fail-update',lambda:editj(r/'docs/agent/TASK_CATALOG.json',lambda o:o['tasks'][0]['completion_contract']['fail'].__setitem__('required_state_updates',[]))))
  cases.append(('missing-successor',lambda:editj(r/'docs/agent/TASK_CATALOG.json',lambda o:o.__setitem__('tasks',o['tasks'][:1]))))
  cases.append(('duplicate-successor',lambda:editj(r/'docs/agent/TASK_CATALOG.json',lambda o:o['tasks'].append(dict(o['tasks'][1])))))
  cases.append(('successor-ready-too-early',lambda:editj(r/'docs/agent/TASK_CATALOG.json',lambda o:o['tasks'][1]['activation'].__setitem__('status','ready'))))
  cases.append(('successor-section',lambda:editj(r/'docs/agent/TASK_CATALOG.json',lambda o:o['tasks'][1]['required_reads'][0].__setitem__('section_heading','## missing'))))
  cases.append(('registry-coverage',lambda:editj(r/'docs/documentation/document-registry.json',lambda o:o.__setitem__('documents',o['documents'][1:]))))
  cases.append(('authority-live-binding',lambda:editj(r/'experiments/agent-task-completion/agent-task-completion-authority.json',lambda o:o['file_identities'].__setitem__('docs/current/STATE.json','0'*64))))
  for n,fn in cases:restore();fn();checks[n]=not run(r,rr)
 finally:shutil.rmtree(tmp,ignore_errors=True)
 failed=[k for k,v in checks.items() if not v];o={'schema_version':1,'verifier_kind':'agent-task-completion-negative-fixtures','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks};print(json.dumps(o,indent=2,sort_keys=True));return 0 if o['pass'] else 1
if __name__=='__main__':sys.exit(main())
