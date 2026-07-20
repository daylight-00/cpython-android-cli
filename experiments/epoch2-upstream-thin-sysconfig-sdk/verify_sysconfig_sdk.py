#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
from typing import Any

OUTPUT_REL='experiments/epoch2-upstream-thin-sysconfig-sdk'
ACTION='execute-e2-r1-ut3-sysconfig-and-native-extension-sdk'
NEXT_ACTION='execute-e2-r1-ut4-android-data-and-writable-state-policy'
FOLLOWING_ACTION='execute-e2-r1-ut5-feature-capability-and-product-surface-qualification'
PRIMARY=['official-extraction-verification.json','runtime-reproduction.json','absolute-path-census.json','normalization-mutations.json','runtime-path-normalization.json','consumer-metadata-normalization.json','native-extension-wheel-evidence.json','sdk-flavor-decision.json','ut3-gate-diagnostics.json','independent-audit.json']
SCRIPTS=['native_probe.c','setup.py','run_sysconfig_sdk_experiment.py','audit_sysconfig_sdk.py','verify_sysconfig_sdk.py','test_verify_sysconfig_sdk.py','finalize_sysconfig_sdk.py','run-ut3-sysconfig-and-native-extension-sdk.sh']
REQUIRED=['README.md',*PRIMARY,*SCRIPTS,'sysconfig-sdk-authority.json','evidence-freeze.md']

def load(p:Path)->Any:return json.loads(p.read_text())
def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=None);ap.add_argument('--output-dir',default=OUTPUT_REL);ap.add_argument('--artifact-dir',type=Path,required=True);ap.add_argument('--expected-predecessor-head');ap.add_argument('--expected-predecessor-tree');a=ap.parse_args();root=(a.root if a.root is not None else Path.cwd()).resolve();out=root/a.output_dir;art=a.artifact_dir.resolve();checks={};errors={}
 def ck(name:str,value:bool,detail:Any=None):checks[name]=bool(value);errors.setdefault(name,detail) if not value and detail is not None else None
 ck('required_files',all((out/n).is_file() for n in REQUIRED),[n for n in REQUIRED if not (out/n).is_file()])
 docs={}
 for n in REQUIRED:
  p=out/n
  if p.suffix=='.json' and p.is_file():
   try:docs[n]=load(p)
   except Exception as e:errors['json_parse']={n:str(e)}
 ck('json_parse','json_parse' not in errors)
 if not checks['required_files'] or not checks['json_parse']:
  result={'schema_version':1,'verification_kind':'e2-r1-ut3-sysconfig-sdk','pass':False,'checks':checks,'errors':errors,'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':[k for k,v in checks.items() if not v]};print(json.dumps(result,indent=2,sort_keys=True));return 1
 auth=docs['sysconfig-sdk-authority.json'];audit=docs['independent-audit.json'];gate=docs['ut3-gate-diagnostics.json'];rp=docs['runtime-path-normalization.json'];cm=docs['consumer-metadata-normalization.json'];wh=docs['native-extension-wheel-evidence.json'];sdk=docs['sdk-flavor-decision.json']
 auth_sha=sha(out/'sysconfig-sdk-authority.json')
 ck('audit',audit.get('pass') is True and audit.get('pass_count')==audit.get('check_count'))
 ck('gate',gate.get('pass') is True and all(v is True for v in gate.get('gate_condition',{}).values()))
 ck('authority_kind',auth.get('authority_kind')=='e2-r1-ut3-sysconfig-and-native-extension-sdk' and auth.get('status')=='frozen-pass-runtime-and-on-device-sdk-metadata')
 ck('authority_predecessor',(not a.expected_predecessor_head or auth.get('predecessor',{}).get('commit')==a.expected_predecessor_head) and (not a.expected_predecessor_tree or auth.get('predecessor',{}).get('tree')==a.expected_predecessor_tree))
 ids=auth.get('file_identities',{});ck('authority_file_set',set(ids)==set(PRIMARY+SCRIPTS),{'expected':sorted(PRIMARY+SCRIPTS),'actual':sorted(ids)})
 ck('authority_file_identities',all((out/n).is_file() and sha(out/n)==h for n,h in ids.items()))
 claim=auth.get('claim_boundary',{});ck('authority_claims',claim.get('runtime_metadata_normalization') is True and claim.get('consumer_metadata_normalization') is True and claim.get('on_device_native_extension_sdk') is True and claim.get('cross_build_sdk') is False and claim.get('product_selectability') is False and claim.get('publication') is False)
 ck('authority_exit',auth.get('exit_condition')==gate.get('exit_condition') and auth.get('gate_condition')==gate.get('gate_condition'))
 ck('runtime_reroot',rp.get('reroot_after_movement') is True and rp.get('producer_residue')==[] and rp.get('stale_location_a_references')==[])
 ck('consumer_metadata',cm.get('pass') is True and cm.get('location_a',{}).get('pass') is True and cm.get('location_b_after_move',{}).get('pass') is True)
 ck('consumer_text_clean',cm.get('text_location_b',{}).get('classification_counts',{}).get('unknown-absolute',0)==0 and cm.get('text_location_b',{}).get('classification_counts',{}).get('stale-install-prefix',0)==0)
 wheel=wh.get('wheel',{});wheel_path=art/wheel.get('filename','')
 ck('wheel_artifact',wheel_path.is_file() and sha(wheel_path)==wheel.get('sha256'))
 ck('wheel_identity',wheel.get('filename')=='hw_t_native_probe-0.1.0-cp314-cp314-android_24_arm64_v8a.whl' and wheel.get('filename_ok') is True and wheel.get('tags')==['cp314-cp314-android_24_arm64_v8a'] and wheel.get('pass') is True)
 ck('wheel_imports',wh.get('location_a',{}).get('pass') is True and wh.get('location_b_after_base_move_fresh_venv',{}).get('pass') is True and wh.get('relocated_extension_import_pass') is True)
 ck('wheel_extension_surface',wh.get('extension_normalization',{}).get('after',{}).get('rpath')==[] and wh.get('extension_normalization',{}).get('after',{}).get('runpath')==[] and wh.get('extension_normalization',{}).get('alignment_policy',{}).get('preserved') is True)
 flavors=sdk.get('flavors',{});ck('sdk_decision',flavors.get('runtime-only',{}).get('status')=='representationally-required' and flavors.get('on-device-sdk',{}).get('status')=='experimentally-supported' and flavors.get('cross-build-sdk',{}).get('status')=='unavailable' and sdk.get('product_selectable') is False)
 state=load(root/'docs/current/STATE.json');task=load(root/'docs/current/AGENT_TASK.json');catalog=load(root/'docs/agent/TASK_CATALOG.json');registry=load(root/'docs/documentation/document-registry.json')
 ck('state_revision',state.get('state_revision')==10)
 ck('state_next',state.get('next_action_class')==NEXT_ACTION and state.get('program',{}).get('gate',{}).get('id')=='E2-R1/UT-4')
 bindings=[x for x in state.get('accepted_authorities',[]) if x.get('path')==f'{OUTPUT_REL}/sysconfig-sdk-authority.json'];ck('state_binding',len(bindings)==1 and bindings[0].get('sha256')==auth_sha)
 ck('current_task',task.get('task',{}).get('id')=='E2-R1-UT-4' and task.get('task',{}).get('action_class')==NEXT_ACTION and task.get('state_revision')==10)
 ut4=next((t for t in catalog.get('tasks',[]) if t.get('task_id')=='E2-R1-UT-4'),None);ut5=next((t for t in catalog.get('tasks',[]) if t.get('task_id')=='E2-R1-UT-5'),None)
 ck('ut4_activation',isinstance(ut4,dict) and ut4.get('activation',{}).get('status')=='ready' and ut4.get('activation',{}).get('accepted_authority_sha256')==auth_sha)
 ck('ut4_completion_contract',isinstance(ut4,dict) and ut4.get('completion_contract',{}).get('pass',{}).get('successor_task_id')=='E2-R1-UT-5' and ut4.get('completion_contract',{}).get('pass',{}).get('successor_action_class')==FOLLOWING_ACTION)
 ck('ut5_cataloged',isinstance(ut5,dict) and ut5.get('action_class')==FOLLOWING_ACTION and ut5.get('activation',{}).get('status')=='blocked-on-predecessor-authority')
 reg={d.get('path') for d in registry.get('documents',[])};expected_docs={f'{OUTPUT_REL}/{n}' for n in ['README.md',*PRIMARY,'sysconfig-sdk-authority.json','evidence-freeze.md']};ck('registry_coverage',expected_docs<=reg,sorted(expected_docs-reg))
 ck('generated_views',f'execute-e2-r1-ut4-android-data-and-writable-state-policy' in (root/'README.md').read_text() and 'State revision:** 10' in (root/'docs/CURRENT_CONTEXT.md').read_text())
 tracked=subprocess.run(['git','-C',str(root),'ls-files',OUTPUT_REL],text=True,stdout=subprocess.PIPE).stdout.splitlines();ck('no_binary_committed',not any(Path(x).suffix in {'.whl','.so','.a','.o'} for x in tracked),tracked)
 result={'schema_version':1,'verification_kind':'e2-r1-ut3-sysconfig-sdk','authority_sha256':auth_sha,'pass':all(checks.values()),'checks':checks,'errors':{k:v for k,v in errors.items() if k in checks and not checks[k]},'check_count':len(checks),'pass_count':sum(checks.values()),'failed_checks':[k for k,v in checks.items() if not v],'claim_boundary':'Relocation-aware runtime and consumer metadata plus bounded on-device SDK evidence; no cross-build SDK, broad device qualification, product selection, selectability, or publication claim.'}
 print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
