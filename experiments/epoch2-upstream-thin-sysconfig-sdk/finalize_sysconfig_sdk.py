#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from typing import Any

ACTION='execute-e2-r1-ut3-sysconfig-and-native-extension-sdk'
NEXT_ACTION='execute-e2-r1-ut4-android-data-and-writable-state-policy'
NEXT_TASK='E2-R1-UT-4'
FOLLOWING_ACTION='execute-e2-r1-ut5-feature-capability-and-product-surface-qualification'
FOLLOWING_TASK='E2-R1-UT-5'
OUTPUT_REL='experiments/epoch2-upstream-thin-sysconfig-sdk'
TRANSACTION_ID='20260720-e2-r1-ut3-sysconfig-and-native-extension-sdk-v2'
PRIMARY=['official-extraction-verification.json','runtime-reproduction.json','absolute-path-census.json','normalization-mutations.json','runtime-path-normalization.json','consumer-metadata-normalization.json','native-extension-wheel-evidence.json','sdk-flavor-decision.json','ut3-gate-diagnostics.json','independent-audit.json']
SCRIPTS=['native_probe.c','setup.py','run_sysconfig_sdk_experiment.py','audit_sysconfig_sdk.py','verify_sysconfig_sdk.py','test_verify_sysconfig_sdk.py','finalize_sysconfig_sdk.py','run-ut3-sysconfig-and-native-extension-sdk.sh']
NEW_DOCS=['README.md',*PRIMARY,'sysconfig-sdk-authority.json','evidence-freeze.md']

def load(p:Path)->Any:return json.loads(p.read_text())
def dump(p:Path,o:Any):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def completion_contract(current:str,successor:str,successor_task:str)->dict[str,Any]:
 return {
  'contract_version':1,
  'always':{'all_required_verifiers_must_pass':True,'clean_main_and_bundle_export_ready_on_close':True,'forbidden_new_authority_bindings':['docs/current/STATE.json','docs/current/AGENT_TASK.json','README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'],'generated_views_must_be_regenerated':True,'new_markdown_or_json_requires_registry_update':True,'one_runner_and_complete_receipt_required':True},
  'fail':{'allowed_action_policy':'retain-current-action-or-select-cataloged-bounded-correction','complete_receipt_required':True,'correction_task_must_be_cataloged':True,'correction_task_must_resume_action_class':current,'required_failure_records':['first-meaningful-failure','failure-classification','blocked-downstream','claim-boundary'],'required_state_updates':['state_revision','predecessor','active_work_package','blockers','unresolved_risks','updated_by_transaction']},
  'pass':{'required_catalog_updates':['bind-accepted-authority-into-successor','activate-successor-task','define-successor-completion-contract-before-selection'],'required_output_namespace':'experiments/epoch2-upstream-thin-android-data-policy/','required_output_roles':['ca-trust-candidates','timezone-candidates','temporary-directory-policy','cache-bytecode-and-user-site-policy','venv-writable-state-policy','read-only-installation-behavior','negative-path-scans','independent-audit','machine-authority','evidence-freeze'],'required_state_updates':['state_revision','predecessor','accepted_authorities','program.gate','program.next_action_class','next_action_class','control_work.next_action_class','control_work.resume_program_action_class','unresolved_risks','updated_by_transaction'],'successor_action_class':successor,'successor_must_exist':True,'successor_task_id':successor_task}
 }

def registry_entry(path:str)->dict[str,Any]:
 name=Path(path).name;ext=Path(path).suffix.removeprefix('.')
 domain='machine_authority' if name=='sysconfig-sdk-authority.json' else ('audit' if name=='independent-audit.json' else ('claim_evidence' if ext=='md' else 'machine_evidence'))
 return {'authority_domain':domain,'format':ext,'lifecycle_class':'FROZEN_AUTHORITY','machine_binding_policy':'allowed','migration_action':'e2-r1-ut3-sysconfig-and-native-extension-sdk','mutability':'immutable','onboarding_visibility':'secondary' if ext=='md' else 'machine','owner':'epoch2-research','path':path,'planned_canonical_parent':'docs/authorities/experiments/INDEX.md' if ext=='md' else 'docs/authorities/machine/INDEX.md','rationale':'','supersession_rule':'Explicit successor experiment or authority only.','update_trigger':'Never edit after freeze; create successor authority.'}

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=None);ap.add_argument('--output-dir',default=OUTPUT_REL);ap.add_argument('--artifact-dir',type=Path,required=True);ap.add_argument('--predecessor-head',required=True);ap.add_argument('--predecessor-tree',required=True);a=ap.parse_args();root=(a.root if a.root is not None else Path.cwd()).resolve();out=root/a.output_dir;art=a.artifact_dir.resolve()
 audit=load(out/'independent-audit.json');gate=load(out/'ut3-gate-diagnostics.json');rp=load(out/'runtime-path-normalization.json');cm=load(out/'consumer-metadata-normalization.json');wheel=load(out/'native-extension-wheel-evidence.json');sdk=load(out/'sdk-flavor-decision.json')
 if audit.get('pass') is not True or gate.get('pass') is not True:raise SystemExit('UT-3 audit/gate is not PASS')
 wheel_name=wheel['wheel']['filename'];wheel_path=art/wheel_name
 if not wheel_path.is_file() or sha(wheel_path)!=wheel['wheel']['sha256']:raise SystemExit('wheel artifact identity mismatch')
 file_ids={n:sha(out/n) for n in [*PRIMARY,*SCRIPTS]}
 readme=f'''# E2-R1/UT-3 — Sysconfig and native-extension SDK

This experiment converts the official binary-derived CPython 3.14.6 Android metadata from producer records into a relocation-aware consumer view and proves a real Android native-extension wheel build, venv installation, import, whole-prefix movement, fresh relocated venv installation, and import.

The active sysconfig module derives runtime paths from its own location. The installed Makefile derives `prefix` from `MAKEFILE_LIST`; pkg-config files derive it from `pcfiledir`; build-details and the auxiliary sysconfig JSON use explicit relative path semantics. Producer NDK, workspace, and `/usr/local` values are frozen in the baseline census and removed from active consumer metadata.

The accepted on-device SDK profile uses `clang`, `clang++`, and `llvm-ar` in the Android/Termux execution context. A separate runtime-only representation is required. A workstation cross-build SDK remains unavailable until an explicit relocatable NDK/sysroot authority exists.

The wheel artifact remains in the result receipt and is not committed. This authority does not select an Epoch 3 product, qualify broad devices, make the product selectable, or publish artifacts.
''';(out/'README.md').write_text(readme)
 authority={'schema_version':1,'authority_kind':'e2-r1-ut3-sysconfig-and-native-extension-sdk','status':'frozen-pass-runtime-and-on-device-sdk-metadata','predecessor':{'commit':a.predecessor_head,'tree':a.predecessor_tree},'upstream_control_authority':{'path':'experiments/epoch2-upstream-thin-control/upstream-control-authority.json','sha256':'6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c'},'artifact_prototype_authority':{'path':'experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json','sha256':'387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306'},'loader_relocation_authority':{'path':'experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json','sha256':'05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2'},'normalization':{'runtime_paths_reroot_after_movement':rp['reroot_after_movement'],'producer_residue':rp['producer_residue'],'stale_location_references':rp['stale_location_a_references'],'consumer_location_a_pass':cm['location_a']['pass'],'consumer_location_b_pass':cm['location_b_after_move']['pass']},'native_extension_wheel':{'filename':wheel_name,'sha256':wheel['wheel']['sha256'],'size':wheel['wheel']['size'],'tags':wheel['wheel']['tags'],'build_pass':wheel['returncode']==0,'venv_install_import_pass':wheel['location_a']['pass'],'relocated_fresh_venv_install_import_pass':wheel['location_b_after_base_move_fresh_venv']['pass'],'extension_normalization':wheel['extension_normalization']},'sdk_flavor_decision':sdk['flavors'],'exit_condition':gate['exit_condition'],'gate_condition':gate['gate_condition'],'file_identities':file_ids,'verification':{'independent_audit':f"{audit['pass_count']}/{audit['check_count']}",'focused_verifier':'required-after-finalization','negative_fixtures':'required-before-transaction'},'claim_boundary':{'official_upstream_identity':True,'artifact_representation':True,'bounded_android_runtime':True,'runtime_metadata_normalization':True,'consumer_metadata_normalization':True,'on_device_native_extension_sdk':True,'cross_build_sdk':False,'device_qualification':False,'epoch3_selection':False,'product_selectability':False,'publication':False},'next_action_class':NEXT_ACTION}
 dump(out/'sysconfig-sdk-authority.json',authority);authority_sha=sha(out/'sysconfig-sdk-authority.json')
 freeze=f'''# E2-R1/UT-3 Evidence Freeze

```text
authority       {OUTPUT_REL}/sysconfig-sdk-authority.json
authority sha   {authority_sha}
producer paths  0 active
stale prefixes  0
runtime reroot  PASS
wheel tag       {wheel['wheel']['tags'][0]}
wheel sha       {wheel['wheel']['sha256']}
venv import A   PASS
venv import B   PASS
audit           {audit['pass_count']}/{audit['check_count']} PASS
```

Accepted: relocation-aware runtime sysconfig, normalized consumer metadata, an on-device Android native-extension SDK profile, canonical Android wheel identity, and supported relocated fresh-venv import.

Not accepted: a workstation cross-build SDK, broad device qualification, Epoch 3 product selection, product selectability, or publication.
''';(out/'evidence-freeze.md').write_text(freeze)

 catalog_path=root/'docs/agent/TASK_CATALOG.json';catalog=load(catalog_path);ut4=next(t for t in catalog['tasks'] if t['task_id']==NEXT_TASK)
 req={'path':f'{OUTPUT_REL}/sysconfig-sdk-authority.json','reason':'Frozen relocation-aware sysconfig, consumer metadata, on-device native-extension SDK, and Android wheel authority.','sha256':authority_sha}
 ut4['activation']={'prerequisites_satisfied':True,'accepted_authority_path':req['path'],'accepted_authority_sha256':authority_sha,'required_authority_role':'sysconfig-and-native-extension-sdk','required_predecessor_action_class':ACTION,'status':'ready'}
 if not any(x.get('path')==req['path'] for x in ut4['required_authorities']):ut4['required_authorities'].append(req)
 ut4['completion_contract']=completion_contract(NEXT_ACTION,FOLLOWING_ACTION,FOLLOWING_TASK)
 if not any(t.get('task_id')==FOLLOWING_TASK for t in catalog['tasks']):
  catalog['tasks'].append({'action_class':FOLLOWING_ACTION,'activation':{'prerequisites_satisfied':False,'required_authority_role':'android-data-and-writable-state-policy','required_predecessor_action_class':NEXT_ACTION,'status':'blocked-on-predecessor-authority'},'claim_boundary':dict(ut4['claim_boundary']),'default_exclusions':list(ut4['default_exclusions']),'deliverable':dict(ut4['deliverable']),'goal':'Classify subprocess, venv, pip, and multiprocessing feasibility and bound the technically supportable Epoch 3 feature surface.','input_routing':dict(ut4['input_routing']),'required_authorities':list(ut4['required_authorities']),'required_reads':[{'path':'docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md','reason':'Subprocess, venv, pip, multiprocessing matrices and explicit feature support boundary.','scope':'section','section_heading':'## UT-5 — Feature capability and product-surface qualification','stop_before_heading':'## UT-6 — Dependency and provenance closure'}],'task_id':FOLLOWING_TASK,'title':'Feature capability and product-surface qualification','work_class':'L'})
 dump(catalog_path,catalog);catalog_sha=sha(catalog_path)
 state_path=root/'docs/current/STATE.json';state=load(state_path);state['state_revision']+=1;state['predecessor']={'commit':a.predecessor_head,'tree':a.predecessor_tree};state['accepted_authorities'].append({'id':'e2-r1-ut3-sysconfig-and-native-extension-sdk','path':req['path'],'role':'relocation-aware sysconfig, consumer metadata, on-device native-extension SDK, and Android wheel evidence','sha256':authority_sha});state['program']['gate']={'id':'E2-R1/UT-4','name':'Android-mandatory data and writable-state policy','status':'ready'};state['program']['next_action_class']=NEXT_ACTION;state['next_action_class']=NEXT_ACTION;state['control_work']['next_action_class']=NEXT_ACTION;state['control_work']['resume_program_action_class']=NEXT_ACTION;state['blockers']=[];state['active_work_package']=None;state['unresolved_risks']=['UT-4 must define host-neutral CA, timezone, temporary, cache, bytecode, user-site, venv writable-state, and read-only-install policies without importing Termux-private paths into the product contract.'];state['updated_by_transaction']=TRANSACTION_ID;state['task_catalog']['sha256']=catalog_sha;state['task_completion']['current_action_class']=NEXT_ACTION;state['task_completion']['pass_successor_action_class']=FOLLOWING_ACTION;dump(state_path,state)
 registry_path=root/'docs/documentation/document-registry.json';registry=load(registry_path);existing={d['path'] for d in registry['documents']}
 for n in NEW_DOCS:
  p=f'{OUTPUT_REL}/{n}'
  if p not in existing:registry['documents'].append(registry_entry(p));existing.add(p)
 registry['basis']['next_action_class']=NEXT_ACTION;registry['basis']['predecessor_head']=a.predecessor_head;registry['basis']['predecessor_tree']=a.predecessor_tree;registry['basis']['tracked_document_count']=len(registry['documents']);registry['basis']['task_catalog_schema_version']=catalog['schema_version'];dump(registry_path,registry)
 proc=subprocess.run([sys.executable,str(root/'experiments/agent-task-completion/render-document-views.py'),'--root',str(root)],cwd=root)
 if proc.returncode:return proc.returncode
 print(json.dumps({'pass':True,'authority_sha256':authority_sha,'state_revision':state['state_revision'],'next_action_class':NEXT_ACTION,'wheel_sha256':wheel['wheel']['sha256']},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
