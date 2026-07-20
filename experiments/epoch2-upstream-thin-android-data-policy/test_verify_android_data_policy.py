#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json,os,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path
OUTREL=Path('experiments/epoch2-upstream-thin-android-data-policy')
SCRIPTS=['run_android_data_policy_experiment.py','audit_android_data_policy.py','verify_android_data_policy.py','test_verify_android_data_policy.py','finalize_android_data_policy.py','run-ut4-android-data-and-writable-state-policy.sh']
def dump(p:Path,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def run(cmd,cwd=None):return subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def evidence(out:Path):
 contract={'provenance':'probe','update_owner':'owner','relocation':'independent','failure_mode':'fail closed','host_neutral':True}
 rr={'startup':{'startup_pass':True,'required_extension_failures':0,'ld_library_path_absent':True,'self_reexec_absent':True},'lr3_exact_and_16k':True}
 ca={'selected':'bundled-default-with-caller-override','contract':contract,'probe':{'default':{'client':{'pass':True}},'invalid_override':{'client':{'pass':False}},'valid_external_override':{'client':{'pass':True}}},'pass':True}
 tz={'selected':'bundled-raw-zoneinfo-tree','contract':contract,'probe':{'v1':{'json':{'offset_seconds':3600}},'v2':{'json':{'offset_seconds':7200}},'host_discovery_disabled':{'json':{'pass':False}}},'pass':True}
 tmp={'contract':contract,'pass':True};cache={'contract':contract,'pass':True};venv={'contract':contract,'probe':{'fresh_after_move':{'json':{'pass':True}}},'pass':True};ro={'contract':contract,'prefix_unchanged':True,'pass':True};upd={'python_update_required':False,'pass':True};scan={'hit_count':0,'active_metadata_unknown_absolute_zero':True,'active_metadata_stale_install_zero':True,'pass':True}
 gatecond={'ca_policy':True,'timezone_policy':True,'temporary_policy':True,'cache_bytecode_user_site_policy':True,'venv_policy':True,'read_only_installation':True,'data_update_independent':True,'subprocess_inheritance':True,'negative_path_scans':True,'policy_completeness':True,'runtime_reproduction':True,'lr3_exact_and_16k':True};gate={'pass':True,'exit_condition':{'required_policy_count':6,'complete_policy_count':6,'negative_path_hits':0,'read_only_prefix_unchanged':True,'relocated_runtime_pass':True,'fresh_venv_after_move_pass':True,'data_update_without_python_update':True},'gate_condition':gatecond,'failed_gate_conditions':[]}
 for n,o in [('runtime-reproduction.json',rr),('ca-trust-candidates.json',ca),('timezone-candidates.json',tz),('temporary-directory-policy.json',tmp),('cache-bytecode-and-user-site-policy.json',cache),('venv-writable-state-policy.json',venv),('read-only-installation-behavior.json',ro),('data-update-evidence.json',upd),('negative-path-scans.json',scan),('ut4-gate-diagnostics.json',gate)]:dump(out/n,o)
def relocation_helper(experiment:Path,td:Path):
 spec=importlib.util.spec_from_file_location('ut4_experiment_regression',experiment)
 if spec is None or spec.loader is None:return {'name':'read-only-relocation-helper','pass':False,'error':'module-load-failed'}
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 source=td/'read-only-source';destination=td/'read-only-destination'
 (source/'bin').mkdir(parents=True);(source/'lib').mkdir()
 executable=source/'bin/python3.14-config';executable.write_text('#!/bin/sh\nexit 0\n');executable.chmod(0o755)
 data=source/'lib/data.txt';data.write_text('stable\n')
 (source/'bin/python').symlink_to('python3.14-config')
 m.make_read_only(source);before=m.tree_snapshot(source)
 m.relocate_read_only_tree(source,destination);after=m.tree_snapshot(destination)
 readonly=all(p.is_symlink() or not (p.stat().st_mode & 0o222) for p in [destination,*destination.rglob('*')])
 passed=(not source.exists() and destination.is_dir() and before['sha256']==after['sha256'] and readonly)
 m.make_writable(destination);shutil.rmtree(destination)
 return {'name':'read-only-relocation-helper','pass':passed,'before':before['sha256'],'after':after['sha256'],'readonly':readonly}
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();root=a.root.resolve();src=root/OUTREL;results=[]
 with tempfile.TemporaryDirectory(prefix='ut4-verify-') as td:
  td=Path(td);results.append(relocation_helper(src/'run_android_data_policy_experiment.py',td))
  base=td/'base';base.mkdir();p=subprocess.Popen(['git','-C',str(root),'archive','HEAD'],stdout=subprocess.PIPE);subprocess.run(['tar','-xf','-','-C',str(base)],stdin=p.stdout,check=True);p.stdout.close();p.wait()
  out=base/OUTREL;out.mkdir(parents=True,exist_ok=True)
  for n in SCRIPTS:shutil.copy2(src/n,out/n)
  evidence(out)
  ar=run([sys.executable,str(out/'audit_android_data_policy.py'),'--root',str(base),'--output',str(out)])
  fi=run([sys.executable,str(out/'finalize_android_data_policy.py'),'--root',str(base),'--predecessor-head','a1fdd7ea96f282504287abb864aaea8dbbe1aa54','--predecessor-tree','a6d8e2da095cdd2fd6e9dfbfb3b220686a4fe093'])
  vr=run([sys.executable,str(out/'verify_android_data_policy.py'),'--root',str(base),'--expected-predecessor-head','a1fdd7ea96f282504287abb864aaea8dbbe1aa54','--expected-predecessor-tree','a6d8e2da095cdd2fd6e9dfbfb3b220686a4fe093'])
  positive=ar.returncode==fi.returncode==vr.returncode==0;results.append({'name':'positive','pass':positive,'audit':ar.stdout[-2000:],'finalize':fi.stdout[-2000:]+fi.stderr[-1000:],'verify':vr.stdout[-3000:]})
  neg=Path(td)/'negative';shutil.copytree(base,neg);g=json.loads((neg/OUTREL/'ut4-gate-diagnostics.json').read_text());g['pass']=False;dump(neg/OUTREL/'ut4-gate-diagnostics.json',g);nv=run([sys.executable,str(neg/OUTREL/'verify_android_data_policy.py'),'--root',str(neg),'--expected-predecessor-head','a1fdd7ea96f282504287abb864aaea8dbbe1aa54','--expected-predecessor-tree','a6d8e2da095cdd2fd6e9dfbfb3b220686a4fe093']);results.append({'name':'negative-gate','pass':nv.returncode!=0,'stdout':nv.stdout[-3000:]})
  miss=Path(td)/'missing';shutil.copytree(base,miss);(miss/OUTREL/'android-data-policy-authority.json').unlink();mv=run([sys.executable,str(miss/OUTREL/'verify_android_data_policy.py'),'--root',str(miss),'--expected-predecessor-head','a1fdd7ea96f282504287abb864aaea8dbbe1aa54','--expected-predecessor-tree','a6d8e2da095cdd2fd6e9dfbfb3b220686a4fe093']);results.append({'name':'missing-authority','pass':mv.returncode!=0,'stdout':mv.stdout[-2000:]})
 result={'schema_version':1,'pass':all(x['pass'] for x in results),'results':results};print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
