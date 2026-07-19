#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

def sha(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def load(p: Path): return json.loads(p.read_text(encoding='utf-8'))

def git(root: Path, *args: str) -> str:
    return subprocess.check_output(['git','-C',str(root),*args],text=True,stderr=subprocess.DEVNULL).strip()

def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');x=ap.parse_args();r=Path(x.root).resolve()
    errors=[]
    try:
        c=load(r/'docs/agent/BOOTSTRAP_CONTRACT.json');s=load(r/'docs/current/STATE.json');t=load(r/'docs/current/AGENT_TASK.json')
    except Exception as e:
        print(json.dumps({'pass':False,'errors':[str(e)]},indent=2));return 1
    if sha(r/c['bootstrap']['path'])!=c['bootstrap']['sha256']: errors.append('bootstrap-sha256')
    if s.get('state_revision')!=t.get('state_revision'): errors.append('state-task-revision')
    if s.get('next_action_class')!=t.get('task',{}).get('action_class'): errors.append('state-task-action')
    try:
        branch=git(r,'branch','--show-current');head=git(r,'rev-parse','HEAD');tree=git(r,'rev-parse','HEAD^{tree}');clean=git(r,'status','--porcelain')=='';refs=git(r,'show-ref')
    except Exception as e:
        branch=head=tree='unknown';clean=False;refs='';errors.append('git-state:'+str(e))
    out={
      'schema_version':1,'certificate_kind':'agent-onboarding-mechanical-certificate','pass':not errors,'errors':errors,
      'repository':{'branch':branch,'head':head,'tree':tree,'clean':clean,'refs':refs.splitlines()},
      'bootstrap':{'path':c['bootstrap']['path'],'sha256':c['bootstrap']['sha256'],'contract_version':c['schema_version']},
      'mandatory_read_order':c['mandatory_read_order'],'state_revision':s.get('state_revision'),'program':s.get('program'),
      'next_action_class':s.get('next_action_class'),'work_class':t.get('task',{}).get('work_class'),
      'required_reads':t.get('required_reads',[]),'required_authorities':t.get('required_authorities',[]),
      'default_exclusions':t.get('default_exclusions',[]),'claim_boundary':t.get('claim_boundary',{}),
      'blockers':s.get('blockers',[]),'unresolved_risks':s.get('unresolved_risks',[]),
      'agent_attestation_required':['mandatory modules read in full','task sections read exactly','additional reads listed with justification']
    }
    print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())
