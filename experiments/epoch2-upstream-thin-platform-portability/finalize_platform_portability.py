#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from typing import Any
ACTION='execute-e2-r1-ut6-platform-portability'
NEXT_ACTION='execute-e2-r1-ut7-upstream-evolution-and-maintenance-portability'
NEXT_TASK='E2-R1-UT-7'
FOLLOWING_ACTION='execute-e2-r1-api36-controlled-source-equivalent-comparison'
FOLLOWING_TASK='E2-R1-API36-1'
OUTPUT_REL='experiments/epoch2-upstream-thin-platform-portability'
TRANSACTION_ID='20260720-e2-r1-ut6-platform-portability-v2'
PRIMARY=['current-device-probe.json','runtime-reproduction.json','environment-matrix.json','static-16k-matrix.json','runtime-platform-matrix.json','minimum-api-claim.json','supported-contexts.json','withheld-claims.json','ut6-gate-diagnostics.json','independent-audit.json']
SCRIPTS=['run_platform_portability_experiment.py','audit_platform_portability.py','verify_platform_portability.py','test_verify_platform_portability.py','finalize_platform_portability.py','run-ut6-platform-portability.sh']
NEW_DOCS=['README.md',*PRIMARY,'platform-portability-authority.json','evidence-freeze.md']
AUTH=[
 ('upstream_control_authority','experiments/epoch2-upstream-thin-control/upstream-control-authority.json','6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c'),
 ('artifact_prototype_authority','experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json','387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306'),
 ('loader_relocation_authority','experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json','05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2'),
 ('sysconfig_sdk_authority','experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json','6cff1984d4601a37e8b57762bb170a57e695cb64d516c1dab0023b7e809dc808'),
 ('android_data_policy_authority','experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json','be25e52aba1d6c9d0b2e25fec2bd1d8a0a0d9eb870436f00e81f347e90d012b7'),
 ('feature_qualification_authority','experiments/epoch2-upstream-thin-feature-qualification/feature-qualification-authority.json','3b56a38898a3a2384cf9419fe3cd124faa8dbf367cdd5532724b3424092a62e5')]
def load(p:Path)->Any:return json.loads(p.read_text())
def dump(p:Path,o:Any):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def completion_contract(current:str,successor:str,successor_task:str)->dict[str,Any]:
 return {'contract_version':1,'always':{'all_required_verifiers_must_pass':True,'clean_main_and_bundle_export_ready_on_close':True,'forbidden_new_authority_bindings':['docs/current/STATE.json','docs/current/AGENT_TASK.json','README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'],'generated_views_must_be_regenerated':True,'new_markdown_or_json_requires_registry_update':True,'one_runner_and_complete_receipt_required':True},'fail':{'allowed_action_policy':'retain-current-action-or-select-cataloged-bounded-correction','complete_receipt_required':True,'correction_task_must_be_cataloged':True,'correction_task_must_resume_action_class':current,'required_failure_records':['first-meaningful-failure','failure-classification','blocked-downstream','claim-boundary'],'required_state_updates':['state_revision','predecessor','active_work_package','blockers','unresolved_risks','updated_by_transaction']},'pass':{'required_catalog_updates':['bind-accepted-authority-into-successor','activate-successor-task','define-successor-completion-contract-before-selection'],'required_output_namespace':'experiments/epoch2-upstream-thin-upstream-evolution/','required_output_roles':['patch-update-rehearsal','configuration-only-delta','layout-and-extension-delta','runpath-and-sysconfig-delta','wheel-and-pip-delta','python315-preview-delta','security-ownership','independent-audit','machine-authority','evidence-freeze'],'required_state_updates':['state_revision','predecessor','accepted_authorities','program.gate','program.next_action_class','next_action_class','control_work.next_action_class','control_work.resume_program_action_class','unresolved_risks','updated_by_transaction'],'successor_action_class':successor,'successor_must_exist':True,'successor_task_id':successor_task}}
def registry_entry(path:str)->dict[str,Any]:
 name=Path(path).name;ext=Path(path).suffix.removeprefix('.');domain='machine_authority' if name=='platform-portability-authority.json' else ('audit' if name=='independent-audit.json' else ('claim_evidence' if ext=='md' else 'machine_evidence'))
 return {'authority_domain':domain,'format':ext,'lifecycle_class':'FROZEN_AUTHORITY','machine_binding_policy':'allowed','migration_action':'e2-r1-ut6-platform-portability','mutability':'immutable','onboarding_visibility':'secondary' if ext=='md' else 'machine','owner':'epoch2-research','path':path,'planned_canonical_parent':'docs/authorities/experiments/INDEX.md' if ext=='md' else 'docs/authorities/machine/INDEX.md','rationale':'','supersession_rule':'Explicit successor experiment or authority only.','update_trigger':'Never edit after freeze; create successor authority.'}
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=None);ap.add_argument('--output-dir',default=OUTPUT_REL);ap.add_argument('--predecessor-head',required=True);ap.add_argument('--predecessor-tree',required=True);a=ap.parse_args();root=(a.root if a.root is not None else Path.cwd()).resolve();out=root/a.output_dir
 audit=load(out/'independent-audit.json');gate=load(out/'ut6-gate-diagnostics.json');env=load(out/'environment-matrix.json');static=load(out/'static-16k-matrix.json');runtime=load(out/'runtime-platform-matrix.json');minimum=load(out/'minimum-api-claim.json');supported=load(out/'supported-contexts.json');withheld=load(out/'withheld-claims.json');device=load(out/'current-device-probe.json')
 if audit.get('pass') is not True or gate.get('pass') is not True or runtime.get('pass') is not True or static.get('pass') is not True:raise SystemExit('UT-6 evidence is not PASS')
 for _,p,h in AUTH:
  if sha(root/p)!=h:raise SystemExit('required authority identity mismatch:'+p)
 file_ids={n:sha(out/n) for n in [*PRIMARY,*SCRIPTS]}
 (out/'README.md').write_text('''# E2-R1/UT-6 — Platform portability

This authority separates directly tested platform behavior, static 16 KiB ELF compatibility, related historical evidence, and explicitly withheld claims. The current assembled product is directly qualified only in the recorded Termux/aarch64 Android target context.

The official package's API-24 identity is not treated as runtime proof. The minimum release API remains withheld because no direct current-assembly lower-API target was available. Static 16 KiB-compatible PT_LOAD layout is accepted; runtime operation on a 16 KiB device is accepted only when directly observed. Non-Termux app namespaces, ADB, root, emulator, other ABIs, and broad device/version claims remain withheld.

This evidence enables Epoch 3 platform decisions. It does not select a minimum API, make a broad device claim, select an Epoch 3 product, make the product selectable, or authorize publication.
''')
 bindings={k:{'path':p,'sha256':h} for k,p,h in AUTH}
 authority={'schema_version':1,'authority_kind':'e2-r1-ut6-platform-portability','status':'frozen-pass-bounded-platform-claims-and-explicit-withholding','predecessor':{'commit':a.predecessor_head,'tree':a.predecessor_tree},**bindings,'direct_current_environment':env['current_assembly'][0],'related_historical_environments':env['related_historical_evidence'],'static_16k':static['summary'],'runtime_platform':{'pass':runtime['pass'],'cases':[{'case':x['case'],'status':x['status']} for x in runtime['cases']]},'minimum_api':minimum,'supported_contexts':supported,'withheld_claims':withheld,'gate_condition':gate['gate_condition'],'exit_condition':gate['exit_condition'],'file_identities':file_ids,'verification':{'independent_audit':f"{audit['pass_count']}/{audit['check_count']}",'focused_verifier':'required-after-finalization','negative_fixtures':'required-before-transaction'},'claim_boundary':{'official_upstream_identity':True,'bounded_android_runtime':True,'direct_termux_aarch64_api_target':True,'static_16k_compatibility':True,'runtime_16k_device_qualification':device.get('page_size')==16384,'minimum_release_api':False,'non_termux_context':False,'adb_context':False,'root_context':False,'emulator':False,'other_abis':False,'broad_device_qualification':False,'epoch3_selection':False,'product_selectability':False,'publication':False},'epoch3_decisions_enabled':['minimum release API','supported page-size claim','supported contexts','withheld claims'],'epoch3_selection_made':False,'next_action_class':NEXT_ACTION}
 dump(out/'platform-portability-authority.json',authority);authority_sha=sha(out/'platform-portability-authority.json')
 (out/'evidence-freeze.md').write_text(f'''# E2-R1/UT-6 Evidence Freeze

```text
authority            {OUTPUT_REL}/platform-portability-authority.json
authority sha        {authority_sha}
direct API           {device.get('android_api')}
direct page size     {device.get('page_size')}
runtime cases        {gate['exit_condition']['direct_runtime_pass_count']}/{gate['exit_condition']['runtime_case_count']} direct PASS/complete
runtime ELF          {gate['exit_condition']['static_runtime_elf_count']}
wheel ELF            {gate['exit_condition']['static_wheel_elf_count']}
public claims        {gate['exit_condition']['public_claim_count']}
withheld claims      {gate['exit_condition']['withheld_claim_count']}
minimum API claimed  {gate['exit_condition']['minimum_release_api_claimed']}
runtime 16K tested   {gate['exit_condition']['runtime_16k_device_tested']}
audit                 {audit['pass_count']}/{audit['check_count']} PASS
```

Accepted: exact current-target runtime evidence and static final-ELF 16 KiB compatibility.

Withheld: minimum API, untested page-size runtime, non-Termux, ADB, root, emulator, other ABI, broad device/version, and unselected pip/uv claims.
''')
 catalog_path=root/'docs/agent/TASK_CATALOG.json';catalog=load(catalog_path);ut7=next(t for t in catalog['tasks'] if t['task_id']==NEXT_TASK);req={'path':f'{OUTPUT_REL}/platform-portability-authority.json','reason':'Frozen bounded platform portability and explicit withheld-claim authority.','sha256':authority_sha};ut7['activation']={'prerequisites_satisfied':True,'accepted_authority_path':req['path'],'accepted_authority_sha256':authority_sha,'required_authority_role':'platform-portability','required_predecessor_action_class':ACTION,'status':'ready'}
 if not any(x.get('path')==req['path'] for x in ut7['required_authorities']):ut7['required_authorities'].append(req)
 ut7['completion_contract']=completion_contract(NEXT_ACTION,FOLLOWING_ACTION,FOLLOWING_TASK)
 if not any(t.get('task_id')==FOLLOWING_TASK for t in catalog['tasks']):
  catalog['tasks'].append({'action_class':FOLLOWING_ACTION,'activation':{'prerequisites_satisfied':False,'required_authority_role':'upstream-evolution-and-maintenance-portability','required_predecessor_action_class':NEXT_ACTION,'status':'blocked-on-predecessor-authority'},'claim_boundary':dict(ut7['claim_boundary']),'completion_contract':None,'default_exclusions':list(ut7['default_exclusions']),'deliverable':dict(ut7['deliverable']),'goal':'Compare API-36 source-equivalent control classes while enumerating every delta beyond the compile API.','input_routing':dict(ut7['input_routing']),'required_authorities':list(ut7['required_authorities']),'required_reads':[{'path':'docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md','reason':'API-36 controlled source-equivalent comparison track.','scope':'section','section_heading':'## API-36 controlled source-equivalent comparison track','stop_before_heading':'## 7. Epoch 2 closure gates'}],'task_id':FOLLOWING_TASK,'title':'API-36 controlled source-equivalent comparison','work_class':'L'})
 dump(catalog_path,catalog);catalog_sha=sha(catalog_path)
 state_path=root/'docs/current/STATE.json';state=load(state_path);state['state_revision']+=1;state['predecessor']={'commit':a.predecessor_head,'tree':a.predecessor_tree};state['accepted_authorities'].append({'id':'e2-r1-ut6-platform-portability','path':req['path'],'role':'bounded current-target platform evidence, static 16 KiB compatibility, and explicit withheld claims','sha256':authority_sha});state['program']['gate']={'id':'E2-R1/UT-7','name':'Upstream evolution and maintenance portability','status':'ready'};state['program']['next_action_class']=NEXT_ACTION;state['next_action_class']=NEXT_ACTION;state['control_work']['next_action_class']=NEXT_ACTION;state['control_work']['resume_program_action_class']=NEXT_ACTION;state['blockers']=[];state['active_work_package']=None;state['unresolved_risks']=['UT-7 must rehearse an official 3.14 patch update and bound Python 3.15 preview deltas without converting preview evidence into a release claim.','UT-6 withholds a minimum release API and runtime 16 KiB support until direct target evidence exists.'];state['updated_by_transaction']=TRANSACTION_ID;state['task_catalog']['sha256']=catalog_sha;state['task_completion']['current_action_class']=NEXT_ACTION;state['task_completion']['pass_successor_action_class']=FOLLOWING_ACTION;dump(state_path,state)
 registry_path=root/'docs/documentation/document-registry.json';registry=load(registry_path);existing={d['path'] for d in registry['documents']}
 for n in NEW_DOCS:
  p=f'{OUTPUT_REL}/{n}'
  if p not in existing:registry['documents'].append(registry_entry(p));existing.add(p)
 registry['basis']['next_action_class']=NEXT_ACTION;registry['basis']['predecessor_head']=a.predecessor_head;registry['basis']['predecessor_tree']=a.predecessor_tree;registry['basis']['tracked_document_count']=len(registry['documents']);registry['basis']['task_catalog_schema_version']=catalog['schema_version'];dump(registry_path,registry)
 proc=subprocess.run([sys.executable,str(root/'experiments/agent-task-completion/render-document-views.py'),'--root',str(root)],cwd=root)
 if proc.returncode:return proc.returncode
 print(json.dumps({'pass':True,'authority_sha256':authority_sha,'state_revision':state['state_revision'],'next_action_class':NEXT_ACTION},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
