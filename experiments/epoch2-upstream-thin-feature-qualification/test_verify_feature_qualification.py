#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys,tempfile
from pathlib import Path

def run(cmd:list[str],cwd:Path)->subprocess.CompletedProcess[str]:
 return subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def checkout(root:Path,dst:Path)->None:
 dst.mkdir(parents=True,exist_ok=True)
 p=subprocess.run(['git','-C',str(root),'checkout-index','--all','--force',f'--prefix={str(dst)}/'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode:raise RuntimeError(p.stderr)

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();root=a.root.resolve();verifier=root/'experiments/epoch2-upstream-thin-feature-qualification/verify_feature_qualification.py'
 checks={};details={}
 p=run([sys.executable,'-B',str(verifier),'--root',str(root)],root);checks['positive']=p.returncode==0;details['positive']={'returncode':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-4000:]}
 with tempfile.TemporaryDirectory(prefix='ut5-verifier-') as td:
  base=Path(td)
  bad=base/'bad';checkout(root,bad)
  core=bad/'experiments/epoch2-upstream-thin-feature-qualification/subprocess-core-matrix.json';data=json.loads(core.read_text());data['cases'][0]['classification']='blanket-pass';core.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
  q=run([sys.executable,'-B',str(bad/'experiments/epoch2-upstream-thin-feature-qualification/verify_feature_qualification.py'),'--root',str(bad)],bad);checks['negative-classification']=q.returncode!=0;details['negative-classification']={'returncode':q.returncode,'stdout':q.stdout[-4000:],'stderr':q.stderr[-4000:]}
  modebad=base/'modebad';checkout(root,modebad)
  vm=modebad/'experiments/epoch2-upstream-thin-feature-qualification/venv-matrix.json';vdata=json.loads(vm.read_text());fresh=next(x for x in vdata['cases'] if x['case']=='base_moved_before_new_venv');fresh['evidence']['mode']='copies';vm.write_text(json.dumps(vdata,indent=2,sort_keys=True)+'\n')
  m=run([sys.executable,'-B',str(modebad/'experiments/epoch2-upstream-thin-feature-qualification/verify_feature_qualification.py'),'--root',str(modebad)],modebad);checks['negative-fresh-mode']=m.returncode!=0;details['negative-fresh-mode']={'returncode':m.returncode,'stdout':m.stdout[-4000:],'stderr':m.stderr[-4000:]}
  missing=base/'missing';checkout(root,missing);(missing/'experiments/epoch2-upstream-thin-feature-qualification/feature-qualification-authority.json').unlink()
  r=run([sys.executable,'-B',str(missing/'experiments/epoch2-upstream-thin-feature-qualification/verify_feature_qualification.py'),'--root',str(missing)],missing);checks['missing-authority']=r.returncode!=0;details['missing-authority']={'returncode':r.returncode,'stdout':r.stdout[-4000:],'stderr':r.stderr[-4000:]}
 result={'schema_version':1,'pass':all(checks.values()),'check_count':len(checks),'pass_count':sum(checks.values()),'checks':checks,'details':details}
 print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
