#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil,subprocess,sys,tempfile
from pathlib import Path
V='experiments/agent-bootstrap/verify-agent-bootstrap.py'
def run(r,rr):return subprocess.run([sys.executable,V,'--root',str(r),'--render-result',str(rr)],cwd=r,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def editj(p,fn):o=json.loads(p.read_text());fn(o);p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');x=ap.parse_args();src=Path(x.root).resolve();tmp=Path(tempfile.mkdtemp());r=tmp/'r';r.mkdir();rr=tmp/'render-result.json';rr.write_text(json.dumps({'pass':True,'target_count':20,'mismatched_targets':[]})+'\n')
 try:
  files=subprocess.check_output(['git','-C',str(src),'ls-files','-z'],text=False).split(b'\0');files=[f.decode() for f in files if f]
  for rel in files:
   p=src/rel
   if p.is_file():q=r/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  subprocess.run(['git','init','-q'],cwd=r,check=True);subprocess.run(['git','add','-A'],cwd=r,check=True)
  def restore():subprocess.run(['git','checkout-index','-a','-f'],cwd=r,check=True,stdout=subprocess.DEVNULL);subprocess.run(['git','clean','-fdx'],cwd=r,check=True,stdout=subprocess.DEVNULL)
  checks={};checks['baseline-pass']=run(r,rr)
  cases=[]
  cases.append(('bootstrap-mutation',lambda:(r/'AGENT_BOOTSTRAP.md').write_text((r/'AGENT_BOOTSTRAP.md').read_text()+'x')))
  cases.append(('contract-digest',lambda:editj(r/'docs/agent/BOOTSTRAP_CONTRACT.json',lambda o:o['bootstrap'].__setitem__('sha256','0'*64))))
  cases.append(('missing-project-model',lambda:(r/'docs/agent/PROJECT_MODEL.md').unlink()))
  cases.append(('missing-protocol-rule',lambda:(r/'docs/agent/SESSION_PROTOCOL.md').write_text((r/'docs/agent/SESSION_PROTOCOL.md').read_text().replace('SP-03','SP-X3'))))
  cases.append(('state-task-revision',lambda:editj(r/'docs/current/AGENT_TASK.json',lambda o:o.__setitem__('state_revision',999))))
  cases.append(('task-action',lambda:editj(r/'docs/current/AGENT_TASK.json',lambda o:o['task'].__setitem__('action_class','bad'))))
  cases.append(('task-section',lambda:editj(r/'docs/current/AGENT_TASK.json',lambda o:o['required_reads'][0].__setitem__('section_heading','## missing'))))
  cases.append(('historical-task-read',lambda:editj(r/'docs/current/AGENT_TASK.json',lambda o:o['required_reads'][0].__setitem__('path','docs/history/README.md'))))
  cases.append(('missing-exclusion',lambda:editj(r/'docs/current/AGENT_TASK.json',lambda o:o.__setitem__('default_exclusions',[]))))
  cases.append(('catalog-no-current-action',lambda:editj(r/'docs/agent/TASK_CATALOG.json',lambda o:o['tasks'][0].__setitem__('action_class','bad'))))
  cases.append(('authority-digest',lambda:editj(r/'docs/current/AGENT_TASK.json',lambda o:o['required_authorities'][0].__setitem__('sha256','0'*64))))
  cases.append(('onboarding-not-redirect',lambda:(r/'docs/SESSION_ONBOARDING.md').write_text('# Session Onboarding\nmandatory handoff package\n')))
  cases.append(('registry-bootstrap-class',lambda:editj(r/'docs/documentation/document-registry.json',lambda o:next(d for d in o['documents'] if d['path']=='AGENT_BOOTSTRAP.md').__setitem__('lifecycle_class','STABLE'))))
  cases.append(('state-bootstrap-path',lambda:editj(r/'docs/current/STATE.json',lambda o:o['agent_onboarding'].__setitem__('bootstrap_path','README.md'))))
  for n,fn in cases:
   restore();fn();checks[n]=not run(r,rr)
 finally:shutil.rmtree(tmp,ignore_errors=True)
 failed=[k for k,v in checks.items() if not v];o={'schema_version':1,'verifier_kind':'agent-bootstrap-negative-fixtures','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks};print(json.dumps(o,indent=2,sort_keys=True));return 0 if o['pass'] else 1
if __name__=='__main__':sys.exit(main())
