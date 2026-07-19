#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
VERIFY=Path('experiments/document-mixed-correction/verify-mixed-document-correction.py')
def run(root):
 e=os.environ.copy();e['HW_T_PHASE4_FIXTURE_FAST']='1';return subprocess.run([sys.executable,str(root/VERIFY),'--root',str(root)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=e).returncode==0
def materialize(src,dst):
 subprocess.run(['git','init','-q'],cwd=dst,check=True);subprocess.run(['git','config','gc.auto','0'],cwd=dst,check=True)
 raw=subprocess.check_output(['git','ls-files','-z','--','*.md','*.json','experiments/document-mixed-correction/render-document-views.py','experiments/document-mixed-correction/verify-mixed-document-correction.py'],cwd=src)
 subprocess.run(['git','checkout-index','--force',f'--prefix={str(dst)}/','--stdin','-z'],cwd=src,input=raw,check=True)
 subprocess.run(['git','add','-A'],cwd=dst,check=True,stdout=subprocess.DEVNULL)
def restore(dst):subprocess.run(['git','checkout-index','-a','-f'],cwd=dst,check=True,stdout=subprocess.DEVNULL);subprocess.run(['git','clean','-fdq'],cwd=dst,check=True)
def mutate(r,n):
 if n=='guide-temporal':(r/'docs/PROJECT_GUIDE.md').write_text((r/'docs/PROJECT_GUIDE.md').read_text()+'\nnext action: bad\n')
 elif n=='plan-status':(r/'docs/roadmap/EPOCH2_PROGRAM_PLAN.md').write_text((r/'docs/roadmap/EPOCH2_PROGRAM_PLAN.md').read_text()+'\ncurrent disposition: bad\n')
 elif n=='orientation-byte':(r/'docs/PROJECT_ORIENTATION.md').write_text((r/'docs/PROJECT_ORIENTATION.md').read_text()+'\nmutation\n')
 elif n=='old-roadmap-byte':(r/'docs/roadmap/EPOCH2_ROADMAP.md').write_text((r/'docs/roadmap/EPOCH2_ROADMAP.md').read_text()+'\nmutation\n')
 elif n=='state-old-plan':
  import json;p=r/'docs/current/STATE.json';x=json.loads(p.read_text());x['active_plan']['path']='docs/roadmap/EPOCH2_ROADMAP.md';p.write_text(json.dumps(x))
 elif n=='registry-orientation-stable':
  import json;p=r/'docs/documentation/document-registry.json';x=json.loads(p.read_text());next(e for e in x['documents'] if e['path']=='docs/PROJECT_ORIENTATION.md')['lifecycle_class']='STABLE';p.write_text(json.dumps(x))
 elif n=='registry-old-plan-active':
  import json;p=r/'docs/documentation/document-registry.json';x=json.loads(p.read_text());next(e for e in x['documents'] if e['path']=='docs/roadmap/EPOCH2_ROADMAP.md')['lifecycle_class']='ACTIVE_PLAN';p.write_text(json.dumps(x))
 elif n=='history-warning':(r/'docs/history/README.md').write_text('# broken\n')
 elif n=='readme-snapshot':(r/'docs/history/2026-07-19-pre-phase4-root-readme-snapshot.md').write_text('broken\n')
 elif n=='phase-contract-class':
  import json;p=r/'docs/documentation/document-registry.json';x=json.loads(p.read_text());next(e for e in x['documents'] if e['path']=='docs/documentation/DOCUMENT_LIFECYCLE.md')['lifecycle_class']='STABLE';p.write_text(json.dumps(x))
 elif n=='claim':
  import json;p=r/'docs/current/STATE.json';x=json.loads(p.read_text());x['claim_boundaries']['selectable']=True;p.write_text(json.dumps(x))
 elif n=='authority-live-binding':
  import json;p=r/'experiments/document-mixed-correction/document-mixed-correction-authority.json';x=json.loads(p.read_text());x.setdefault('file_identities',{})['docs/current/STATE.json']='0'*64;p.write_text(json.dumps(x))
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default='.');x=a.parse_args();src=Path(x.root).resolve();names=['guide-temporal','plan-status','orientation-byte','old-roadmap-byte','state-old-plan','registry-orientation-stable','registry-old-plan-active','history-warning','readme-snapshot','phase-contract-class','claim','authority-live-binding'];tmp=Path(tempfile.mkdtemp(prefix='doc-phase4-'));r=tmp/'r';r.mkdir();checks={}
 try:
  materialize(src,r)
  for n in names:
   restore(r);mutate(r,n);subprocess.run(['git','add','-A'],cwd=r,check=True,stdout=subprocess.DEVNULL);checks[n]=not run(r)
 finally:shutil.rmtree(tmp,ignore_errors=True)
 failed=[k for k,v in checks.items() if not v];o={'schema_version':1,'verifier_kind':'document-mixed-correction-negative-fixtures','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks};print(json.dumps(o,indent=2,sort_keys=True));return 0 if o['pass'] else 1
if __name__=='__main__':sys.exit(main())
