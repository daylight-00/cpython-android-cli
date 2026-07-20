#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from typing import Any

ACTION='execute-e2-r1-ut5-feature-capability-and-product-surface-qualification'
NEXT_ACTION='execute-e2-r1-ut6-platform-portability'
NEXT_TASK='E2-R1-UT-6'
FOLLOWING_ACTION='execute-e2-r1-ut7-upstream-evolution-and-maintenance-portability'
FOLLOWING_TASK='E2-R1-UT-7'
OUTPUT_REL='experiments/epoch2-upstream-thin-feature-qualification'
TRANSACTION_ID='20260720-e2-r1-ut5-feature-capability-and-product-surface-qualification-v2'
PRIMARY=['runtime-sdk-reproduction.json','subprocess-core-matrix.json','subprocess-secondary-matrix.json','venv-matrix.json','base-pip-variants.json','multiprocessing-matrix.json','feature-surface-decision.json','ut5-gate-diagnostics.json','independent-audit.json']
SCRIPTS=['run_feature_qualification_experiment.py','audit_feature_qualification.py','verify_feature_qualification.py','test_verify_feature_qualification.py','finalize_feature_qualification.py','run-ut5-feature-capability-and-product-surface-qualification.sh']
NEW_DOCS=['README.md',*PRIMARY,'feature-qualification-authority.json','evidence-freeze.md']

def load(p:Path)->Any:return json.loads(p.read_text())
def dump(p:Path,o:Any):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def completion_contract(current:str,successor:str,successor_task:str)->dict[str,Any]:
 return {'contract_version':1,'always':{'all_required_verifiers_must_pass':True,'clean_main_and_bundle_export_ready_on_close':True,'forbidden_new_authority_bindings':['docs/current/STATE.json','docs/current/AGENT_TASK.json','README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'],'generated_views_must_be_regenerated':True,'new_markdown_or_json_requires_registry_update':True,'one_runner_and_complete_receipt_required':True},'fail':{'allowed_action_policy':'retain-current-action-or-select-cataloged-bounded-correction','complete_receipt_required':True,'correction_task_must_be_cataloged':True,'correction_task_must_resume_action_class':current,'required_failure_records':['first-meaningful-failure','failure-classification','blocked-downstream','claim-boundary'],'required_state_updates':['state_revision','predecessor','active_work_package','blockers','unresolved_risks','updated_by_transaction']},'pass':{'required_catalog_updates':['bind-accepted-authority-into-successor','activate-successor-task','define-successor-completion-contract-before-selection'],'required_output_namespace':'experiments/epoch2-upstream-thin-platform-portability/','required_output_roles':['environment-matrix','static-16k-matrix','runtime-platform-matrix','minimum-api-claim','supported-contexts','withheld-claims','independent-audit','machine-authority','evidence-freeze'],'required_state_updates':['state_revision','predecessor','accepted_authorities','program.gate','program.next_action_class','next_action_class','control_work.next_action_class','control_work.resume_program_action_class','unresolved_risks','updated_by_transaction'],'successor_action_class':successor,'successor_must_exist':True,'successor_task_id':successor_task}}

def registry_entry(path:str)->dict[str,Any]:
 name=Path(path).name;ext=Path(path).suffix.removeprefix('.');domain='machine_authority' if name=='feature-qualification-authority.json' else ('audit' if name=='independent-audit.json' else ('claim_evidence' if ext=='md' else 'machine_evidence'))
 return {'authority_domain':domain,'format':ext,'lifecycle_class':'FROZEN_AUTHORITY','machine_binding_policy':'allowed','migration_action':'e2-r1-ut5-feature-capability-and-product-surface-qualification','mutability':'immutable','onboarding_visibility':'secondary' if ext=='md' else 'machine','owner':'epoch2-research','path':path,'planned_canonical_parent':'docs/authorities/experiments/INDEX.md' if ext=='md' else 'docs/authorities/machine/INDEX.md','rationale':'','supersession_rule':'Explicit successor experiment or authority only.','update_trigger':'Never edit after freeze; create successor authority.'}

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=None);ap.add_argument('--output-dir',default=OUTPUT_REL);ap.add_argument('--predecessor-head',required=True);ap.add_argument('--predecessor-tree',required=True);a=ap.parse_args();root=(a.root if a.root is not None else Path.cwd()).resolve();out=root/a.output_dir
 audit=load(out/'independent-audit.json');gate=load(out/'ut5-gate-diagnostics.json');core=load(out/'subprocess-core-matrix.json');secondary=load(out/'subprocess-secondary-matrix.json');venv=load(out/'venv-matrix.json');pip=load(out/'base-pip-variants.json');mp=load(out/'multiprocessing-matrix.json');decision=load(out/'feature-surface-decision.json')
 if audit.get('pass') is not True or gate.get('pass') is not True or decision.get('pass') is not True:raise SystemExit('UT-5 audit/gate/decision is not PASS')
 file_ids={n:sha(out/n) for n in [*PRIMARY,*SCRIPTS]}
 (out/'README.md').write_text('''# E2-R1/UT-5 — Feature capability and product-surface qualification

This experiment classifies subprocess, venv, base-pip, uv-coexistence, console-script, and multiprocessing behavior on the selected official Android runtime. Every matrix entry has an evidence-backed disposition: `pass`, `android-mandatory-adaptation`, `missing-bionic-primitive`, `upstream-build-decision`, or `inadequate-environment`.

Passing probes are technical support candidates only. They do not select Epoch 3 inclusion. In particular, base pip, pip command wrappers, external uv, pre-existing venv relocation, `preexec_fn`, and multiprocessing primitives remain individually bounded. Default `/bin/sh` is not assumed; explicit Android shell behavior is recorded separately.

This authority enables feature-surface selection and platform qualification. It does not qualify broad devices, select an Epoch 3 product, make the product selectable, or publish artifacts.
''')
 def summary(rows:list[dict[str,Any]])->dict[str,Any]:
  return {'classified':len(rows),'technically_passing':[x['case'] for x in rows if x.get('pass') is True],'adaptation_required':[x['case'] for x in rows if x.get('classification')=='android-mandatory-adaptation'],'missing_bionic_primitive':[x['case'] for x in rows if x.get('classification')=='missing-bionic-primitive'],'upstream_build_decision':[x['case'] for x in rows if x.get('classification')=='upstream-build-decision'],'inadequate_environment':[x['case'] for x in rows if x.get('classification')=='inadequate-environment'],'support_candidates':[x['case'] for x in rows if x.get('support_candidate') is True]}
 authority={'schema_version':1,'authority_kind':'e2-r1-ut5-feature-capability-and-product-surface-qualification','status':'frozen-pass-explicit-feature-support-boundaries','predecessor':{'commit':a.predecessor_head,'tree':a.predecessor_tree},'upstream_control_authority':{'path':'experiments/epoch2-upstream-thin-control/upstream-control-authority.json','sha256':'6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c'},'artifact_prototype_authority':{'path':'experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json','sha256':'387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306'},'loader_relocation_authority':{'path':'experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json','sha256':'05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2'},'sysconfig_sdk_authority':{'path':'experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json','sha256':'6cff1984d4601a37e8b57762bb170a57e695cb64d516c1dab0023b7e809dc808'},'android_data_policy_authority':{'path':'experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json','sha256':'be25e52aba1d6c9d0b2e25fec2bd1d8a0a0d9eb870436f00e81f347e90d012b7'},'classification_vocabulary':['pass','android-mandatory-adaptation','missing-bionic-primitive','upstream-build-decision','inadequate-environment'],'feature_surface':{'subprocess_core':summary(core['cases']),'subprocess_secondary':summary(secondary['cases']),'venv':summary(venv['cases']),'base_pip':summary(pip['variants']),'multiprocessing':summary(mp['cases'])},'policy_boundaries':decision['policy_boundaries'],'epoch3_selection_made':False,'blanket_claims':decision['blanket_claims'],'exit_condition':gate['exit_condition'],'gate_condition':gate['gate_condition'],'file_identities':file_ids,'verification':{'independent_audit':f"{audit['pass_count']}/{audit['check_count']}",'focused_verifier':'required-after-finalization','negative_fixtures':'required-before-transaction'},'claim_boundary':{'official_upstream_identity':True,'artifact_representation':True,'bounded_android_runtime':True,'runtime_metadata_normalization':True,'android_data_policy':True,'feature_capability_qualification':True,'product_surface_selection_input':True,'device_qualification':False,'epoch3_selection':False,'product_selectability':False,'publication':False},'next_action_class':NEXT_ACTION}
 dump(out/'feature-qualification-authority.json',authority);authority_sha=sha(out/'feature-qualification-authority.json')
 (out/'evidence-freeze.md').write_text(f'''# E2-R1/UT-5 Evidence Freeze

```text
authority         {OUTPUT_REL}/feature-qualification-authority.json
authority sha     {authority_sha}
classified cases  {gate['exit_condition']['total_classified_cases']}
unclassified      {gate['exit_condition']['unclassified_cases']}
complete matrices {gate['exit_condition']['complete_matrix_count']}/{gate['exit_condition']['required_matrix_count']}
blanket claims    {gate['exit_condition']['blanket_claim_count']}
negative hits     {gate['exit_condition']['negative_contract_hits']}
audit             {audit['pass_count']}/{audit['check_count']} PASS
```

Accepted: evidence-backed per-case feasibility and support boundaries for subprocess, venv, pip variants, uv coexistence, console-script relocation, and multiprocessing.

Not accepted: automatic inclusion of any passing capability, broad device qualification, Epoch 3 product selection, product selectability, or publication.
''')
 catalog_path=root/'docs/agent/TASK_CATALOG.json';catalog=load(catalog_path);ut6=next(t for t in catalog['tasks'] if t['task_id']==NEXT_TASK)
 req={'path':f'{OUTPUT_REL}/feature-qualification-authority.json','reason':'Frozen feature capability and product-surface qualification authority.','sha256':authority_sha}
 ut6['activation']={'prerequisites_satisfied':True,'accepted_authority_path':req['path'],'accepted_authority_sha256':authority_sha,'required_authority_role':'feature-capability-and-product-surface-qualification','required_predecessor_action_class':ACTION,'status':'ready'}
 if not any(x.get('path')==req['path'] for x in ut6['required_authorities']):ut6['required_authorities'].append(req)
 ut6['completion_contract']=completion_contract(NEXT_ACTION,FOLLOWING_ACTION,FOLLOWING_TASK)
 if not any(t.get('task_id')==FOLLOWING_TASK for t in catalog['tasks']):
  catalog['tasks'].append({'action_class':FOLLOWING_ACTION,'activation':{'prerequisites_satisfied':False,'required_authority_role':'platform-portability','required_predecessor_action_class':NEXT_ACTION,'status':'blocked-on-predecessor-authority'},'claim_boundary':dict(ut6['claim_boundary']),'completion_contract':None,'default_exclusions':list(ut6['default_exclusions']),'deliverable':dict(ut6['deliverable']),'goal':'Bound patch-update and Python 3.15 evolution burden without turning preview evidence into a release claim.','input_routing':dict(ut6['input_routing']),'required_authorities':list(ut6['required_authorities']),'required_reads':[{'path':'docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md','reason':'Patch update and Python 3.15 preview maintenance portability.','scope':'section','section_heading':'## UT-7 — Upstream evolution and maintenance portability','stop_before_heading':'## API-36 controlled source-equivalent comparison track'}],'task_id':FOLLOWING_TASK,'title':'Upstream evolution and maintenance portability','work_class':'L'})
 dump(catalog_path,catalog);catalog_sha=sha(catalog_path)
 state_path=root/'docs/current/STATE.json';state=load(state_path);state['state_revision']+=1;state['predecessor']={'commit':a.predecessor_head,'tree':a.predecessor_tree};state['accepted_authorities'].append({'id':'e2-r1-ut5-feature-capability-and-product-surface-qualification','path':req['path'],'role':'explicit evidence-backed subprocess, venv, pip, uv, console-script, and multiprocessing support boundaries','sha256':authority_sha});state['program']['gate']={'id':'E2-R1/UT-6','name':'Platform portability','status':'ready'};state['program']['next_action_class']=NEXT_ACTION;state['next_action_class']=NEXT_ACTION;state['control_work']['next_action_class']=NEXT_ACTION;state['control_work']['resume_program_action_class']=NEXT_ACTION;state['blockers']=[];state['active_work_package']=None;state['unresolved_risks']=['UT-6 must bind every public Android platform claim to target evidence or explicitly withhold it; modern-device success is not minimum-API proof.'];state['updated_by_transaction']=TRANSACTION_ID;state['task_catalog']['sha256']=catalog_sha;state['task_completion']['current_action_class']=NEXT_ACTION;state['task_completion']['pass_successor_action_class']=FOLLOWING_ACTION;dump(state_path,state)
 registry_path=root/'docs/documentation/document-registry.json';registry=load(registry_path);existing={d['path'] for d in registry['documents']}
 for n in NEW_DOCS:
  p=f'{OUTPUT_REL}/{n}'
  if p not in existing:registry['documents'].append(registry_entry(p));existing.add(p)
 registry['basis']['next_action_class']=NEXT_ACTION;registry['basis']['predecessor_head']=a.predecessor_head;registry['basis']['predecessor_tree']=a.predecessor_tree;registry['basis']['tracked_document_count']=len(registry['documents']);registry['basis']['task_catalog_schema_version']=catalog['schema_version'];dump(registry_path,registry)
 proc=subprocess.run([sys.executable,str(root/'experiments/agent-task-completion/render-document-views.py'),'--root',str(root)],cwd=root)
 if proc.returncode:return proc.returncode
 print(json.dumps({'pass':True,'authority_sha256':authority_sha,'state_revision':state['state_revision'],'next_action_class':NEXT_ACTION},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
