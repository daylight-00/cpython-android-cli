#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, zipfile
from pathlib import Path
from typing import Any

EXPECTED_CONTROL='6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c'
EXPECTED_ARTIFACT='387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306'
EXPECTED_LOADER='05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2'
EXPECTED_WHEEL_TAG='cp314-cp314-android_24_arm64_v8a'
PRIMARY=[
 'official-extraction-verification.json','runtime-reproduction.json','absolute-path-census.json',
 'normalization-mutations.json','runtime-path-normalization.json','consumer-metadata-normalization.json',
 'native-extension-wheel-evidence.json','sdk-flavor-decision.json','ut3-gate-diagnostics.json'
]

def load(p:Path)->Any:return json.loads(p.read_text())
def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--artifacts',type=Path,required=True);a=ap.parse_args()
 root=a.root.resolve();out=a.output.resolve();art=a.artifacts.resolve();checks={};errors={}
 def ck(name:str,value:bool,detail:Any=None):
  checks[name]=bool(value)
  if not value and detail is not None:errors[name]=detail
 for name in PRIMARY:ck('file_'+name,(out/name).is_file())
 if not all((out/n).is_file() for n in PRIMARY):
  result={'schema_version':1,'audit_kind':'e2-r1-ut3-sysconfig-sdk','pass':False,'checks':checks,'errors':errors,'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':[k for k,v in checks.items() if not v]};(out/'independent-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return 1
 official=load(out/'official-extraction-verification.json');runtime=load(out/'runtime-reproduction.json');base=load(out/'absolute-path-census.json');mut=load(out/'normalization-mutations.json');rp=load(out/'runtime-path-normalization.json');cm=load(out/'consumer-metadata-normalization.json');wh=load(out/'native-extension-wheel-evidence.json');sdk=load(out/'sdk-flavor-decision.json');gate=load(out/'ut3-gate-diagnostics.json')
 ck('authority_control',sha(root/'experiments/epoch2-upstream-thin-control/upstream-control-authority.json')==EXPECTED_CONTROL)
 ck('authority_artifact',sha(root/'experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json')==EXPECTED_ARTIFACT)
 ck('authority_loader',sha(root/'experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json')==EXPECTED_LOADER)
 ck('official_extraction',official.get('verification',{}).get('pass') is True)
 ck('runtime_reproduction',runtime.get('startup',{}).get('startup_pass') is True and runtime.get('startup',{}).get('required_extension_failures')==0)
 ck('runtime_reproduction_lr3',runtime.get('all_exact_mutations') is True and runtime.get('all_16k') is True)
 ck('baseline_census',base.get('phase')=='SC-0' and bool(base.get('text_surfaces',{}).get('rows')))
 ck('baseline_producer_residue',bool(base.get('producer_residue')))
 ck('dynamic_sysconfig',mut.get('sysconfigdata',{}).get('dynamic_prefix') is True)
 ck('relative_sysconfig_json',mut.get('sysconfig_vars_json',{}).get('path_semantics')=='${prefix}-relative')
 ck('dynamic_makefile',mut.get('makefile',{}).get('dynamic_prefix') is True)
 ck('relative_pkgconfig',all(x.get('prefix')=='${pcfiledir}/../..' for x in mut.get('pkgconfig',[])) and bool(mut.get('pkgconfig')))
 ck('relative_build_details',mut.get('build_details',{}).get('path_semantics')=='relative-to-runtime-root')
 ck('runtime_reroot',rp.get('reroot_after_movement') is True)
 ck('runtime_no_stale_a',rp.get('stale_location_a_references')==[])
 ck('runtime_no_producer_residue',rp.get('producer_residue')==[])
 ck('consumer_a',cm.get('location_a',{}).get('pass') is True)
 ck('consumer_b',cm.get('location_b_after_move',{}).get('pass') is True)
 ck('text_unknown_zero',cm.get('text_location_b',{}).get('classification_counts',{}).get('unknown-absolute',0)==0)
 ck('text_stale_zero',cm.get('text_location_b',{}).get('classification_counts',{}).get('stale-install-prefix',0)==0)
 wheel=wh.get('wheel',{});wheel_path=art/wheel.get('filename','')
 ck('wheel_present',wheel_path.is_file())
 ck('wheel_hash',wheel_path.is_file() and sha(wheel_path)==wheel.get('sha256'))
 ck('wheel_filename',wheel.get('filename')=='hw_t_native_probe-0.1.0-cp314-cp314-android_24_arm64_v8a.whl' and wheel.get('filename_ok') is True)
 ck('wheel_tag',wheel.get('tags')==[EXPECTED_WHEEL_TAG] and wheel.get('tag_ok') is True)
 ck('wheel_member',len(wheel.get('extension_members',[]))==1)
 ck('wheel_build',wh.get('returncode')==0)
 ck('wheel_install_a',wh.get('location_a',{}).get('pass') is True)
 ck('wheel_import_relocated',wh.get('location_b_after_base_move_fresh_venv',{}).get('pass') is True and wh.get('relocated_extension_import_pass') is True)
 ext=wh.get('extension_normalization',{});ck('wheel_extension_no_rpath',ext.get('after',{}).get('rpath')==[] and ext.get('after',{}).get('runpath')==[])
 ck('wheel_extension_16k',ext.get('alignment_policy',{}).get('preserved') is True)
 ck('sdk_runtime_only',sdk.get('flavors',{}).get('runtime-only',{}).get('status')=='representationally-required')
 ck('sdk_on_device',sdk.get('flavors',{}).get('on-device-sdk',{}).get('status')=='experimentally-supported')
 ck('sdk_cross_unavailable',sdk.get('flavors',{}).get('cross-build-sdk',{}).get('status')=='unavailable')
 ck('product_unselectable',sdk.get('product_selectable') is False)
 exitc=gate.get('exit_condition',{});gc=gate.get('gate_condition',{})
 ck('exit_unknown_zero',exitc.get('unknown_producer_absolute_paths')==0)
 ck('exit_stale_zero',exitc.get('stale_active_install_prefixes')==0)
 ck('exit_reroot',exitc.get('runtime_paths_reroot_after_movement') is True)
 ck('exit_wheel_build',exitc.get('native_extension_wheel_build') is True)
 ck('exit_wheel_identity',exitc.get('wheel_identity_correct') is True)
 ck('exit_relocated_import',exitc.get('relocated_extension_import') is True)
 ck('gate_all',gate.get('pass') is True and gc and all(v is True for v in gc.values()))
 result={'schema_version':1,'audit_kind':'e2-r1-ut3-sysconfig-sdk','pass':all(checks.values()),'checks':checks,'errors':errors,'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':[k for k,v in checks.items() if not v]}
 (out/'independent-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
