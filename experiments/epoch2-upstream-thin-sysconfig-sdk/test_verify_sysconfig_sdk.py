#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shlex, shutil, subprocess, tarfile, tempfile, zipfile
from pathlib import Path

OUTPUT_REL='experiments/epoch2-upstream-thin-sysconfig-sdk'
PRE_HEAD='6ab21000b89f75de66bf9cae8ffe31ebd30b34fd'
PRE_TREE='7d7ef4fbf9b4252d52ae9c2141fd18aa186f211b'
SCRIPTS=['native_probe.c','setup.py','run_sysconfig_sdk_experiment.py','audit_sysconfig_sdk.py','verify_sysconfig_sdk.py','test_verify_sysconfig_sdk.py','finalize_sysconfig_sdk.py','run-ut3-sysconfig-and-native-extension-sdk.sh']
PRIMARY=['official-extraction-verification.json','runtime-reproduction.json','absolute-path-census.json','normalization-mutations.json','runtime-path-normalization.json','consumer-metadata-normalization.json','native-extension-wheel-evidence.json','sdk-flavor-decision.json','ut3-gate-diagnostics.json','independent-audit.json']

def dump(p:Path,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,cwd=None):return subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def run_dead_cwd(cmd):
 script='set -e; d="$(mktemp -d)"; cd "$d"; rmdir "$d"; exec '+ ' '.join(shlex.quote(str(x)) for x in cmd)
 return subprocess.run(['bash','-c',script],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def archive_head(root:Path,dest:Path):
 p=subprocess.Popen(['git','-C',str(root),'archive','--format=tar','HEAD'],stdout=subprocess.PIPE)
 assert p.stdout is not None
 with tarfile.open(fileobj=p.stdout,mode='r|') as tf:tf.extractall(dest)
 if p.wait()!=0:raise RuntimeError('git archive HEAD failed')

def make_fixture(source_root:Path,dest:Path,art:Path):
 archive_head(source_root,dest)
 out=dest/OUTPUT_REL;out.mkdir(parents=True)
 live=source_root/OUTPUT_REL
 for n in SCRIPTS:shutil.copy2(live/n,out/n)
 wheel_name='hw_t_native_probe-0.1.0-cp314-cp314-android_24_arm64_v8a.whl';wheel=art/wheel_name;art.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(wheel,'w') as z:
  z.writestr('hw_t_native_probe.cpython-314-aarch64-linux-android.so',b'fixture-elf')
  z.writestr('hw_t_native_probe-0.1.0.dist-info/WHEEL','Wheel-Version: 1.0\nTag: cp314-cp314-android_24_arm64_v8a\n')
 official={'schema_version':1,'verification':{'pass':True}}
 runtime={'schema_version':1,'startup':{'startup_pass':True,'required_extension_failures':0},'all_exact_mutations':True,'all_16k':True}
 baseline={'schema_version':1,'phase':'SC-0','text_surfaces':{'rows':[{'token':'/usr/local','classification':'stale-install-prefix'}]},'producer_residue':['/usr/local']}
 mutations={'schema_version':1,'sysconfigdata':{'dynamic_prefix':True},'sysconfig_vars_json':{'path_semantics':'${prefix}-relative'},'makefile':{'dynamic_prefix':True},'pkgconfig':[{'prefix':'${pcfiledir}/../..'}],'build_details':{'path_semantics':'relative-to-runtime-root'}}
 rp={'schema_version':1,'reroot_after_movement':True,'producer_residue':[],'stale_location_a_references':[]}
 clean_text={'classification_counts':{'unknown-absolute':0,'stale-install-prefix':0}}
 cm={'schema_version':1,'pass':True,'location_a':{'pass':True},'location_b_after_move':{'pass':True},'text_location_a':clean_text,'text_location_b':clean_text}
 wh={'schema_version':1,'returncode':0,'wheel':{'filename':wheel_name,'sha256':sha(wheel),'size':wheel.stat().st_size,'tags':['cp314-cp314-android_24_arm64_v8a'],'filename_ok':True,'tag_ok':True,'extension_members':['hw_t_native_probe.cpython-314-aarch64-linux-android.so'],'pass':True},'location_a':{'pass':True},'location_b_after_base_move_fresh_venv':{'pass':True},'relocated_extension_import_pass':True,'extension_normalization':{'after':{'rpath':[],'runpath':[]},'alignment_policy':{'preserved':True}}}
 sdk={'schema_version':1,'product_selectable':False,'flavors':{'runtime-only':{'status':'representationally-required'},'on-device-sdk':{'status':'experimentally-supported'},'cross-build-sdk':{'status':'unavailable'}}}
 exitc={'unknown_producer_absolute_paths':0,'stale_active_install_prefixes':0,'runtime_paths_reroot_after_movement':True,'native_extension_wheel_build':True,'wheel_identity_correct':True,'relocated_extension_import':True}
 gatec={'unknown_producer_absolute_paths_zero':True,'stale_active_install_prefixes_zero':True,'runtime_paths_reroot_after_movement':True,'native_extension_wheel_build':True,'wheel_identity_correct':True,'relocated_extension_import':True,'consumer_metadata_location_a':True,'consumer_metadata_location_b':True,'runtime_reproduction':True,'lr3_exact_and_16k':True}
 gate={'schema_version':1,'pass':True,'exit_condition':exitc,'gate_condition':gatec,'failed_gate_conditions':[]}
 audit={'schema_version':1,'pass':True,'check_count':1,'pass_count':1,'checks':{'fixture':True},'failed_checks':[]}
 data={'official-extraction-verification.json':official,'runtime-reproduction.json':runtime,'absolute-path-census.json':baseline,'normalization-mutations.json':mutations,'runtime-path-normalization.json':rp,'consumer-metadata-normalization.json':cm,'native-extension-wheel-evidence.json':wh,'sdk-flavor-decision.json':sdk,'ut3-gate-diagnostics.json':gate,'independent-audit.json':audit}
 for n,o in data.items():dump(out/n,o)
 run(['git','init','-q'],dest);run(['git','-C',str(dest),'add','-A'])
 f=run_dead_cwd(['python3',str(out/'finalize_sysconfig_sdk.py'),'--root',str(dest),'--artifact-dir',str(art),'--predecessor-head',PRE_HEAD,'--predecessor-tree',PRE_TREE])
 if f.returncode:raise RuntimeError('finalizer fixture failed:\n'+f.stdout+'\n'+f.stderr)
 run(['git','-C',str(dest),'add','-A'])
 return out,wheel

def verify(root:Path,art:Path):
 return run_dead_cwd(['python3',str(root/OUTPUT_REL/'verify_sysconfig_sdk.py'),'--root',str(root),'--artifact-dir',str(art),'--expected-predecessor-head',PRE_HEAD,'--expected-predecessor-tree',PRE_TREE])

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=None);a=ap.parse_args();root=(a.root if a.root is not None else Path.cwd()).resolve();results=[]
 with tempfile.TemporaryDirectory(prefix='ut3-verify-') as td:
  base=Path(td)
  pos=base/'positive';pos.mkdir();art=base/'art-positive';make_fixture(root,pos,art);p=verify(pos,art);results.append({'name':'positive','pass':p.returncode==0,'stdout':p.stdout,'stderr':p.stderr})
  neg=base/'negative';shutil.copytree(pos,neg,symlinks=True);state=json.loads((neg/'docs/current/STATE.json').read_text());state['next_action_class']='wrong';dump(neg/'docs/current/STATE.json',state);n=verify(neg,art);results.append({'name':'negative-state-drift','pass':n.returncode!=0,'stdout':n.stdout,'stderr':n.stderr})
  miss=base/'missing';shutil.copytree(pos,miss,symlinks=True);(miss/OUTPUT_REL/'sysconfig-sdk-authority.json').unlink();m=verify(miss,art);results.append({'name':'missing-authority','pass':m.returncode!=0,'stdout':m.stdout,'stderr':m.stderr})
 passed=all(x['pass'] for x in results);print(json.dumps({'schema_version':1,'pass':passed,'tests':results},indent=2,sort_keys=True));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
