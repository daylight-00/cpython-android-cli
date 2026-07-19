#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
CORE=Path('experiments/document-legacy-authority-decoupling/verify-legacy-binding-resolution.py');LIVE=Path('experiments/document-legacy-authority-decoupling/verify-legacy-authority-decoupling.py')
def run(root,tool=CORE):return subprocess.run([sys.executable,str(root/tool),'--root',str(root)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def materialize(src,dst):
 subprocess.run(['git','init','-q'],cwd=dst,check=True);subprocess.run(['git','config','gc.auto','0'],cwd=dst,check=True)
 raw=subprocess.check_output(['git','ls-files','-z','--','*.md','*.json','experiments/document-legacy-authority-decoupling/render-document-views.py','experiments/document-legacy-authority-decoupling/verify-legacy-binding-resolution.py','experiments/document-legacy-authority-decoupling/verify-legacy-authority-decoupling.py'],cwd=src)
 subprocess.run(['git','checkout-index','--force',f'--prefix={dst}/','--stdin','-z'],cwd=src,input=raw,check=True);subprocess.run(['git','add','-A'],cwd=dst,check=True,stdout=subprocess.DEVNULL)
def restore(r):subprocess.run(['git','checkout-index','-a','-f'],cwd=r,check=True,stdout=subprocess.DEVNULL);subprocess.run(['git','clean','-fdq'],cwd=r,check=True)
def editj(p,fn):x=json.loads(p.read_text());fn(x);p.write_text(json.dumps(x))
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default='.');x=a.parse_args();src=Path(x.root).resolve();tmp=Path(tempfile.mkdtemp(prefix='doc-phase5-'));r=tmp/'r';r.mkdir();checks={}
 try:
  materialize(src,r)
  # Historical compatibility is independent from live target bytes.
  restore(r);(r/'README.md').write_text((r/'README.md').read_text()+'\nlive mutation\n');checks['live-byte-independent']=run(r,CORE)
  cases=[]
  cases.append(('snapshot-mutation',lambda:(r/json.loads((r/'docs/documentation/legacy-authority-decoupling-map.json').read_text())['bindings'][0]['snapshot_path']).write_text('broken\n')))
  cases.append(('snapshot-delete',lambda:(r/json.loads((r/'docs/documentation/legacy-authority-decoupling-map.json').read_text())['bindings'][1]['snapshot_path']).unlink()))
  cases.append(('map-entry-delete',lambda:editj(r/'docs/documentation/legacy-authority-decoupling-map.json',lambda o:o['bindings'].pop())))
  cases.append(('map-recorded-digest',lambda:editj(r/'docs/documentation/legacy-authority-decoupling-map.json',lambda o:o['bindings'][0].__setitem__('recorded_sha256','0'*64))))
  cases.append(('map-live-snapshot',lambda:editj(r/'docs/documentation/legacy-authority-decoupling-map.json',lambda o:o['bindings'][0].__setitem__('snapshot_path','README.md'))))
  cases.append(('baseline-mutation',lambda:editj(r/'docs/documentation/legacy-live-binding-baseline.json',lambda o:o['bindings'][0].__setitem__('recorded_sha256','0'*64))))
  cases.append(('authority-binding-mutation',lambda:editj(r/json.loads((r/'docs/documentation/legacy-authority-decoupling-map.json').read_text())['bindings'][0]['authority_path'],lambda o:o['file_identities'].__setitem__('README.md','0'*64))))
  cases.append(('new-live-binding',lambda:write_new_binding(r)))
  for n,fn in cases:
   restore(r);fn();subprocess.run(['git','add','-A'],cwd=r,check=True,stdout=subprocess.DEVNULL);checks[n]=not run(r,CORE)
  # Live system mutations.
  restore(r);editj(r/'docs/current/STATE.json',lambda o:o['control_work'].__setitem__('migration_complete',False));checks['migration-not-closed']=not run(r,LIVE)
  restore(r);editj(r/'docs/current/STATE.json',lambda o:o.__setitem__('next_action_class','bad'));checks['wrong-next-action']=not run(r,LIVE)
  restore(r);editj(r/'docs/documentation/document-registry.json',lambda o:next(z for z in o['documents'] if z['path'].startswith('docs/history/legacy-authority-bindings/') and z['path'].endswith('.md') and z['path']!='docs/history/legacy-authority-bindings/README.md').__setitem__('lifecycle_class','GENERATED_VIEW'));checks['snapshot-registry-class']=not run(r,LIVE)
 finally:shutil.rmtree(tmp,ignore_errors=True)
 failed=[k for k,v in checks.items() if not v];o={'schema_version':1,'verifier_kind':'document-legacy-authority-decoupling-negative-fixtures','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks};print(json.dumps(o,indent=2,sort_keys=True));return 0 if o['pass'] else 1
def write_new_binding(r):
 p=r/'new-authority.json';p.write_text(json.dumps({'file_identities':{'README.md':'f'*64}}))
if __name__=='__main__':sys.exit(main())
