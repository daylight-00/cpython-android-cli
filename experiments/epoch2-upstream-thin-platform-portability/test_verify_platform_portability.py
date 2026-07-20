#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys,tempfile
from pathlib import Path

def run(cmd:list[str],cwd:Path)->subprocess.CompletedProcess[str]:return subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def checkout(root:Path,dst:Path)->None:
 dst.mkdir(parents=True,exist_ok=True);p=subprocess.run(['git','-C',str(root),'checkout-index','--all','--force',f'--prefix={str(dst)}/'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode:raise RuntimeError(p.stderr)
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();root=a.root.resolve();verifier=root/'experiments/epoch2-upstream-thin-platform-portability/verify_platform_portability.py';checks={};details={}
 p=run([sys.executable,'-B',str(verifier),'--root',str(root)],root);checks['positive']=p.returncode==0;details['positive']={'returncode':p.returncode,'stdout':p.stdout[-5000:],'stderr':p.stderr[-5000:]}
 with tempfile.TemporaryDirectory(prefix='ut6-verifier-') as td:
  base=Path(td)
  bad=base/'bad-minimum';checkout(root,bad);m=bad/'experiments/epoch2-upstream-thin-platform-portability/minimum-api-claim.json';d=json.loads(m.read_text());d['public_minimum_release_api']=24;d['status']='claimed';d['modern_device_used_as_minimum_proof']=True;m.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');q=run([sys.executable,'-B',str(bad/'experiments/epoch2-upstream-thin-platform-portability/verify_platform_portability.py'),'--root',str(bad)],bad);checks['negative-minimum-inference']=q.returncode!=0;details['negative-minimum-inference']={'returncode':q.returncode,'stdout':q.stdout[-5000:],'stderr':q.stderr[-5000:]}
  broad=base/'bad-broad';checkout(root,broad);s=broad/'experiments/epoch2-upstream-thin-platform-portability/supported-contexts.json';sd=json.loads(s.read_text());sd['public_claims'][0]={'claim':'All Android devices are supported.','evidence':'none'};s.write_text(json.dumps(sd,indent=2,sort_keys=True)+'\n');r=run([sys.executable,'-B',str(broad/'experiments/epoch2-upstream-thin-platform-portability/verify_platform_portability.py'),'--root',str(broad)],broad);checks['negative-broad-claim']=r.returncode!=0;details['negative-broad-claim']={'returncode':r.returncode,'stdout':r.stdout[-5000:],'stderr':r.stderr[-5000:]}
  alias=base/'bad-alias';checkout(root,alias);m=alias/'experiments/epoch2-upstream-thin-platform-portability/static-16k-matrix.json';d=json.loads(m.read_text());d['symlink_aliases'][0]['target_identity_match']=False;d['summary']['symlink_alias_inventory_complete']=False;m.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');u=run([sys.executable,'-B',str(alias/'experiments/epoch2-upstream-thin-platform-portability/verify_platform_portability.py'),'--root',str(alias)],alias);checks['negative-static-alias']=u.returncode!=0;details['negative-static-alias']={'returncode':u.returncode,'stdout':u.stdout[-5000:],'stderr':u.stderr[-5000:]}
  missing=base/'missing';checkout(root,missing);(missing/'experiments/epoch2-upstream-thin-platform-portability/platform-portability-authority.json').unlink();z=run([sys.executable,'-B',str(missing/'experiments/epoch2-upstream-thin-platform-portability/verify_platform_portability.py'),'--root',str(missing)],missing);checks['missing-authority']=z.returncode!=0;details['missing-authority']={'returncode':z.returncode,'stdout':z.stdout[-5000:],'stderr':z.stderr[-5000:]}
 result={'schema_version':1,'pass':all(checks.values()),'check_count':len(checks),'pass_count':sum(checks.values()),'checks':checks,'details':details};print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
