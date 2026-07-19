#!/usr/bin/env python3
"""Negative fixtures for Phase 3 navigation and registry contracts."""
from __future__ import annotations
import json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; VERIFY=Path('experiments/document-navigation/verify-document-navigation.py')
SELECT=['*.md','*.json','experiments/document-navigation/render-document-views.py','experiments/document-navigation/verify-document-navigation.py']
def run(root:Path)->bool:return subprocess.run([sys.executable,str(root/VERIFY),'--root',str(root)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def materialize(dst:Path):
 data=subprocess.run(['git','ls-files','-z','--','*.md','*.json','experiments/document-navigation/render-document-views.py','experiments/document-navigation/verify-document-navigation.py'],cwd=ROOT,check=True,stdout=subprocess.PIPE).stdout
 prefix=str(dst.resolve())+'/'
 subprocess.run(['git','checkout-index','--force','--prefix='+prefix,'--stdin','-z'],cwd=ROOT,check=True,input=data)
 subprocess.run(['git','init','-q'],cwd=dst,check=True);subprocess.run(['git','config','gc.auto','0'],cwd=dst,check=True);subprocess.run(['git','add','-A'],cwd=dst,check=True)
MUTABLE=[
 'docs/evidence/README.md','docs/navigation/README.md','docs/current/STATE.json','docs/documentation/document-registry.json',
 'experiments/document-navigation/document-navigation-external-audit.json','experiments/document-navigation/navigation-targets.json',
 'docs/handoff/2026-07-16-stage3f-successor-session-reading-path-snapshot.md'
]
def snapshot_mutable(dst:Path):
 return {q:(dst/q).read_bytes() for q in MUTABLE}
def restore(dst:Path,pristine:dict[str,bytes]):
 subprocess.run(['git','rm','--cached','--ignore-unmatch','-q','docs/UNREGISTERED.json'],cwd=dst,check=False)
 try:(dst/'docs/UNREGISTERED.json').unlink()
 except FileNotFoundError:pass
 for q,b in pristine.items():
  p=dst/q;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)

def mutate(root:Path,name:str):
 if name=='missing-navigation-target':(root/'docs/evidence/README.md').unlink()
 elif name=='generated-navigation-drift':(root/'docs/navigation/README.md').write_text('drift\n')
 elif name=='wrong-phase':
  p=root/'docs/current/STATE.json';d=json.loads(p.read_text());d['control_work']['completed_phase']=2;p.write_text(json.dumps(d))
 elif name=='duplicate-current-source':
  p=root/'docs/documentation/document-registry.json';d=json.loads(p.read_text());e=next(x.copy() for x in d['documents'] if x['path']=='docs/CURRENT_CONTEXT.md');e['lifecycle_class']='CURRENT_SOURCE';d['documents'].append(e);p.write_text(json.dumps(d))
 elif name=='unregistered-document':
  (root/'docs/UNREGISTERED.json').write_text('{}\n');subprocess.run(['git','add','docs/UNREGISTERED.json'],cwd=root,check=True)
 elif name=='target-misclassified':
  p=root/'docs/documentation/document-registry.json';d=json.loads(p.read_text());next(x for x in d['documents'] if x['path']=='docs/evidence/README.md')['lifecycle_class']='STABLE';p.write_text(json.dumps(d))
 elif name=='new-live-binding':
  p=root/'experiments/document-navigation/document-navigation-external-audit.json';d=json.loads(p.read_text());d['file_identities']={'docs/navigation/README.md':'0'*64};p.write_text(json.dumps(d))
 elif name=='broken-generated-link':(root/'docs/navigation/README.md').write_text((root/'docs/navigation/README.md').read_text()+'\n[bad](MISSING.md)\n')
 elif name=='wrong-authority-id':
  p=root/'docs/current/STATE.json';d=json.loads(p.read_text());d['accepted_authorities'][-1]['sha256']='0'*64;p.write_text(json.dumps(d))
 elif name=='missing-handoff-snapshot':(root/'docs/handoff/2026-07-16-stage3f-successor-session-reading-path-snapshot.md').unlink()
 elif name=='manifest-count-drift':
  p=root/'experiments/document-navigation/navigation-targets.json';d=json.loads(p.read_text());d['targets']=d['targets'][:-1];p.write_text(json.dumps(d))
def main()->int:
 names=['valid','missing-navigation-target','generated-navigation-drift','wrong-phase','duplicate-current-source','unregistered-document','target-misclassified','new-live-binding','broken-generated-link','wrong-authority-id','missing-handoff-snapshot','manifest-count-drift'];expected={n:(n=='valid') for n in names};tmp=Path(tempfile.mkdtemp(prefix='document-navigation-fixtures-'));repo=tmp/'r';repo.mkdir();results=[]
 try:
  materialize(repo);pristine=snapshot_mutable(repo)
  for n in names:
   restore(repo,pristine);mutate(repo,n) if n!='valid' else None;actual=run(repo);results.append({'name':n,'expected':expected[n],'actual':actual,'pass':actual==expected[n]})
 finally:
  # Fixture cleanup is deliberately non-authoritative. Temporary roots are left
  # for the platform temporary-directory lifecycle rather than risking a Git
  # metadata cleanup race after a completed verdict.
  pass
 failed=[x['name'] for x in results if not x['pass']];out={'schema_version':1,'test_kind':'document-generated-navigation-negative-fixtures','pass':not failed,'check_count':len(results),'pass_count':len(results)-len(failed),'failed_checks':failed,'checks':results,'fixture_materialization':{'source':'staged-index','repository_count':1,'git_commit_created':False,'cleanup_affects_verdict':False}};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())
