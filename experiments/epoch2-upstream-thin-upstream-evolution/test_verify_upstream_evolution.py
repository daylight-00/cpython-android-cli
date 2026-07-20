#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json,subprocess,sys,tempfile
from pathlib import Path

def run(cmd:list[str],cwd:Path)->subprocess.CompletedProcess[str]:return subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def checkout(root:Path,dst:Path)->None:
 dst.mkdir(parents=True,exist_ok=True);p=subprocess.run(['git','-C',str(root),'checkout-index','--all','--force',f'--prefix={str(dst)}/'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode:raise RuntimeError(p.stderr)
def mutate_json(path:Path,fn):
 d=json.loads(path.read_text());fn(d);path.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();root=a.root.resolve();rel=Path('experiments/epoch2-upstream-thin-upstream-evolution/verify_upstream_evolution.py');checks={};details={}
 def invoke(base:Path):return run([sys.executable,'-B',str(base/rel),'--root',str(base)],base)
 exp_path=root/'experiments/epoch2-upstream-thin-upstream-evolution/run_upstream_evolution_experiment.py'
 spec=importlib.util.spec_from_file_location('ut7_experiment',exp_path);mod=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(mod)
 with tempfile.TemporaryDirectory(prefix='ut7-layout-') as td:
  pkg=Path(td)/'official';prefix=pkg/'prefix';(prefix/'lib/python3.14').mkdir(parents=True);(prefix/'include/python3.14').mkdir(parents=True)
  (prefix/'lib/python3.14/_sysconfigdata_android.py').write_text('build_time_vars = {}\n');(prefix/'lib/libpython3.14.so').write_bytes(b'not-elf');(pkg/'PYTHON.json').write_text('{}\n')
  found=mod.find_prefix(pkg);metadata=mod.find_package_file(pkg,found,'PYTHON.json');facts=mod.prefix_facts(found)
  checks['official-embedded-root-metadata-prefix-layout']=found==prefix.resolve() and metadata==pkg/'PYTHON.json' and facts['lib'] and facts['stdlib'] and facts['sysconfig'] and not facts['bin'] and not facts['launcher']
  details['official-embedded-root-metadata-prefix-layout']={'found':str(found),'metadata':str(metadata),'facts':facts}
  bad=Path(td)/'incomplete/prefix';(bad/'lib').mkdir(parents=True)
  try:mod.find_prefix(bad.parent);rejected=False
  except RuntimeError:rejected=True
  checks['incomplete-prefix-rejected']=rejected;details['incomplete-prefix-rejected']={'rejected':rejected}
  archive=Path(td)/'official.tar.gz'
  import tarfile
  with tarfile.open(archive,'w:gz') as tf:
   tf.add(pkg/'prefix',arcname='prefix');tf.add(pkg/'PYTHON.json',arcname='PYTHON.json')
  snap=mod.snapshot('fixture',archive,{'filename':archive.name},Path(td)/'work','readelf')
  checks['embedded-snapshot-pass-without-console-launcher']=snap['pass'] is True and snap['distribution_mode']=='embedded-android' and snap['console_launcher_expected'] is False and snap['console_launcher_present'] is False
  details['embedded-snapshot-pass-without-console-launcher']={'pass':snap['pass'],'prefix_facts':snap['prefix_facts'],'launchers':snap['launchers']}
 p=invoke(root);checks['positive']=p.returncode==0;details['positive']={'returncode':p.returncode,'stdout':p.stdout[-6000:],'stderr':p.stderr[-6000:]}
 with tempfile.TemporaryDirectory(prefix='ut7-verifier-') as td:
  base=Path(td)
  preview=base/'bad-preview';checkout(root,preview);mutate_json(preview/'experiments/epoch2-upstream-thin-upstream-evolution/python315-preview-delta.json',lambda d:d.update({'release_claim':True,'runtime_support_claim':True}));q=invoke(preview);checks['negative-preview-release']=q.returncode!=0;details['negative-preview-release']={'returncode':q.returncode,'stdout':q.stdout[-6000:],'stderr':q.stderr[-6000:]}
  patch=base/'bad-patch';checkout(root,patch);mutate_json(patch/'experiments/epoch2-upstream-thin-upstream-evolution/patch-update-rehearsal.json',lambda d:d.update({'every_non_identity_delta_recorded':False}));q=invoke(patch);checks['negative-unrecorded-delta']=q.returncode!=0;details['negative-unrecorded-delta']={'returncode':q.returncode,'stdout':q.stdout[-6000:],'stderr':q.stderr[-6000:]}
  sec=base/'bad-security';checkout(root,sec);mutate_json(sec/'experiments/epoch2-upstream-thin-upstream-evolution/security-ownership.json',lambda d:d.update({'ownership':[]}));q=invoke(sec);checks['negative-security-ownership']=q.returncode!=0;details['negative-security-ownership']={'returncode':q.returncode,'stdout':q.stdout[-6000:],'stderr':q.stderr[-6000:]}
  acquisition=base/'bad-acquisition';checkout(root,acquisition)
  def break_acquisition(d):
   d['all_exact_owner_inputs']=False
   for x in d.get('inputs',[]):x['acquisition_scope']='unbounded-or-agent-side'
  mutate_json(acquisition/'experiments/epoch2-upstream-thin-upstream-evolution/input-identities.json',break_acquisition);q=invoke(acquisition);checks['negative-acquisition-boundary']=q.returncode!=0;details['negative-acquisition-boundary']={'returncode':q.returncode,'stdout':q.stdout[-6000:],'stderr':q.stderr[-6000:]}
  gate_type=base/'bad-gate-type';checkout(root,gate_type)
  mutate_json(gate_type/'experiments/epoch2-upstream-thin-upstream-evolution/ut7-gate-diagnostics.json',lambda d:d['gate_condition'].__setitem__('update_burden_explicit',['truthy-but-not-boolean']))
  q=invoke(gate_type);checks['negative-gate-value-type']=q.returncode!=0;details['negative-gate-value-type']={'returncode':q.returncode,'stdout':q.stdout[-6000:],'stderr':q.stderr[-6000:]}
  missing=base/'missing';checkout(root,missing);(missing/'experiments/epoch2-upstream-thin-upstream-evolution/upstream-evolution-authority.json').unlink();q=invoke(missing);checks['missing-authority']=q.returncode!=0;details['missing-authority']={'returncode':q.returncode,'stdout':q.stdout[-6000:],'stderr':q.stderr[-6000:]}
 result={'schema_version':1,'pass':all(checks.values()),'check_count':len(checks),'pass_count':sum(checks.values()),'checks':checks,'details':details};print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
