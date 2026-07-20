#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from typing import Any
ACTION='execute-e2-r1-ut7-upstream-evolution-and-maintenance-portability'
NEXT_ACTION='execute-e2-r1-api36-controlled-source-equivalent-comparison'
NEXT_TASK='E2-R1-API36-1'
OUTPUT_REL='experiments/epoch2-upstream-thin-upstream-evolution'
TRANSACTION_ID='20260720-e2-r1-ut7-upstream-evolution-v4'
PRIMARY=['input-identities.json','patch-update-rehearsal.json','configuration-only-delta.json','layout-and-extension-delta.json','runpath-and-sysconfig-delta.json','wheel-and-pip-delta.json','python315-preview-delta.json','security-ownership.json','ut7-gate-diagnostics.json','independent-audit.json']
SCRIPTS=['run_upstream_evolution_experiment.py','audit_upstream_evolution.py','verify_upstream_evolution.py','test_verify_upstream_evolution.py','finalize_upstream_evolution.py','run-ut7-upstream-evolution.sh']
NEW_DOCS=['README.md',*PRIMARY,'upstream-evolution-authority.json','evidence-freeze.md']
AUTH=[
 ('plan_authority','experiments/epoch2-upstream-thin-plan/plan-authority.json','62b3b07f37a90b497747562bb00a9db5a3d78b3b2cb45df8f66db22818f5eafa'),
 ('upstream_control_authority','experiments/epoch2-upstream-thin-control/upstream-control-authority.json','6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c'),
 ('artifact_prototype_authority','experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json','387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306'),
 ('loader_relocation_authority','experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json','05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2'),
 ('sysconfig_sdk_authority','experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json','6cff1984d4601a37e8b57762bb170a57e695cb64d516c1dab0023b7e809dc808'),
 ('android_data_policy_authority','experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json','be25e52aba1d6c9d0b2e25fec2bd1d8a0a0d9eb870436f00e81f347e90d012b7'),
 ('feature_qualification_authority','experiments/epoch2-upstream-thin-feature-qualification/feature-qualification-authority.json','3b56a38898a3a2384cf9419fe3cd124faa8dbf367cdd5532724b3424092a62e5'),
 ('platform_portability_authority','experiments/epoch2-upstream-thin-platform-portability/platform-portability-authority.json','b21eddfee574343772d0875a7b6f26aa7b5dd494ccf0a5f1be9b8c09201276f4')]
def load(p:Path)->Any:return json.loads(p.read_text())
def dump(p:Path,o:Any):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def common_always()->dict[str,Any]:return {'all_required_verifiers_must_pass':True,'clean_main_and_bundle_export_ready_on_close':True,'forbidden_new_authority_bindings':['docs/current/STATE.json','docs/current/AGENT_TASK.json','README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'],'generated_views_must_be_regenerated':True,'new_markdown_or_json_requires_registry_update':True,'one_runner_and_complete_receipt_required':True}
def api36_contract()->dict[str,Any]:
 return {'contract_version':1,'always':common_always(),'fail':{'allowed_action_policy':'retain-current-action-or-select-cataloged-bounded-correction','complete_receipt_required':True,'correction_task_must_be_cataloged':True,'correction_task_must_resume_action_class':NEXT_ACTION,'required_failure_records':['first-meaningful-failure','failure-classification','blocked-downstream','claim-boundary'],'required_state_updates':['state_revision','predecessor','active_work_package','blockers','unresolved_risks','updated_by_transaction']},'pass':{'required_catalog_updates':['record-epoch2-closure-readiness','define-next-program-decision-before-selection'],'required_output_namespace':'experiments/epoch2-upstream-thin-api36-controlled-comparison/','required_output_roles':['control-class-a','control-class-b','control-class-c','controlled-delta-inventory','runtime-and-elf-measurements','benchmark-and-size','wheel-sysconfig-and-symbols','provenance-and-build-burden','independent-audit','machine-authority','evidence-freeze'],'required_state_updates':['state_revision','predecessor','accepted_authorities','program.gate','program.next_action_class','next_action_class','control_work.next_action_class','control_work.resume_program_action_class','unresolved_risks','updated_by_transaction'],'successor_action_class':'evaluate-epoch2-closure-gates','successor_must_exist':False,'successor_task_id':'E2-CLOSURE'}}
def registry_entry(path:str)->dict[str,Any]:
 name=Path(path).name;ext=Path(path).suffix.removeprefix('.');domain='machine_authority' if name=='upstream-evolution-authority.json' else ('audit' if name=='independent-audit.json' else ('claim_evidence' if ext=='md' else 'machine_evidence'))
 return {'authority_domain':domain,'format':ext,'lifecycle_class':'FROZEN_AUTHORITY','machine_binding_policy':'allowed','migration_action':'e2-r1-ut7-upstream-evolution','mutability':'immutable','onboarding_visibility':'secondary' if ext=='md' else 'machine','owner':'epoch2-research','path':path,'planned_canonical_parent':'docs/authorities/experiments/INDEX.md' if ext=='md' else 'docs/authorities/machine/INDEX.md','rationale':'','supersession_rule':'Explicit successor experiment or authority only.','update_trigger':'Never edit after freeze; create successor authority.'}
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=None);ap.add_argument('--output-dir',default=OUTPUT_REL);ap.add_argument('--predecessor-head',required=True);ap.add_argument('--predecessor-tree',required=True);a=ap.parse_args();root=(a.root if a.root is not None else Path.cwd()).resolve();out=root/a.output_dir
 ev={n:load(out/n) for n in PRIMARY};audit=ev['independent-audit.json'];gate=ev['ut7-gate-diagnostics.json'];inputs=ev['input-identities.json'];rehearsal=ev['patch-update-rehearsal.json'];config=ev['configuration-only-delta.json'];layout=ev['layout-and-extension-delta.json'];runsc=ev['runpath-and-sysconfig-delta.json'];wheel=ev['wheel-and-pip-delta.json'];preview=ev['python315-preview-delta.json'];security=ev['security-ownership.json']
 if audit.get('pass') is not True or gate.get('pass') is not True or preview.get('release_claim') is not False:raise SystemExit('UT-7 evidence is not PASS')
 if inputs.get('all_exact_owner_inputs') is not True or not all(x.get('acquisition_scope')=='bounded-owner-local' and x.get('exact_identity_verified') is True and x.get('acquisition_mode') in {'owner-local-cache-reuse','owner-local-bounded-download'} for x in inputs.get('inputs',[])):raise SystemExit('UT-7 input acquisition boundary is not exact bounded owner-local')
 for _,p,h in AUTH:
  if sha(root/p)!=h:raise SystemExit('required authority identity mismatch:'+p)
 protocol_src=out/'SESSION_PROTOCOL.md';contract_src=out/'BOOTSTRAP_CONTRACT.json'
 if not protocol_src.is_file() or not contract_src.is_file():raise SystemExit('operation protocol payload missing')
 protocol_dst=root/'docs/agent/SESSION_PROTOCOL.md';contract_dst=root/'docs/agent/BOOTSTRAP_CONTRACT.json';protocol_dst.write_bytes(protocol_src.read_bytes());contract_dst.write_bytes(contract_src.read_bytes());protocol_binding={'session_protocol_sha256':sha(protocol_dst),'bootstrap_contract_sha256':sha(contract_dst)}
 protocol_src.unlink();contract_src.unlink()
 file_ids={n:sha(out/n) for n in [*PRIMARY,*SCRIPTS]}
 (out/'README.md').write_text('''# E2-R1/UT-7 — Upstream evolution and maintenance portability

This authority records a complete exact-input official CPython 3.14.5 → 3.14.6 Android patch-update rehearsal and a bounded Python 3.15.0b4 Android preview delta. It inventories every normalized change beyond package identity, separates configuration-only candidates from qualification obligations, and assigns security and maintenance ownership.

The Python 3.15 evidence is preview-only. It is not a release claim, runtime-support claim, product selection, minimum-version policy, or publication authorization. A patch update is never accepted by metadata substitution alone: the frozen loader, relocation, sysconfig/SDK, data policy, feature, and platform qualifications must be replayed.

This evidence enables Epoch 3 decisions about supported-version policy, update automation, staffing, and release cadence. It activates the API-36 controlled source-equivalent comparison track without selecting an Epoch 3 product.
''')
 bindings={k:{'path':p,'sha256':h} for k,p,h in AUTH}
 authority={'schema_version':1,'authority_kind':'e2-r1-ut7-upstream-evolution-and-maintenance-portability','status':'frozen-pass-bounded-patch-update-and-preview-delta','predecessor':{'commit':a.predecessor_head,'tree':a.predecessor_tree},**bindings,'official_inputs':inputs['inputs'],'acquisition_boundary':{'scope':'bounded-owner-local','modes':sorted({x['acquisition_mode'] for x in inputs['inputs']}),'network_acquisition_count':inputs.get('owner_network_download_count',0),'exact_identity_required':True,'input_count':len(inputs['inputs'])},'patch_update':{'from_version':rehearsal['from_version'],'to_version':rehearsal['to_version'],'configuration_only_candidate':rehearsal['configuration_only_candidate'],'normalized_file_delta':{k:rehearsal['all_other_normalized_file_changes'][k] for k in ['added_count','removed_count','changed_count']},'qualification_replay_required':rehearsal['qualification_replay_required']},'configuration_boundary':config,'layout_and_extension_delta':layout,'runpath_and_sysconfig_delta':runsc,'wheel_and_pip_delta':wheel,'python315_preview':{'version':preview['preview_version'],'preview_only':preview['preview_only'],'release_claim':preview['release_claim'],'runtime_support_claim':preview['runtime_support_claim'],'product_selection':preview['product_selection'],'pidfd_related_subprocess_behavior':preview['pidfd_related_subprocess_behavior']},'security_ownership':security,'operation_protocol':{'revision':3,'owner_local_network_acquisition_allowed':True,'assistant_network_assumed':False,'single_archive_exchange':True,'embedded_runner_required':True,**protocol_binding},'gate_condition':gate['gate_condition'],'exit_condition':gate['exit_condition'],'file_identities':file_ids,'verification':{'independent_audit':f"{audit['pass_count']}/{audit['check_count']}",'focused_verifier':'required-after-finalization','negative_fixtures':'required-before-transaction'},'claim_boundary':{'official_upstream_identity':True,'official_patch_update_rehearsal':True,'maintenance_delta':True,'python315_preview_evidence':True,'python315_release_support':False,'python315_runtime_qualification':False,'supported_version_policy_selected':False,'release_cadence_selected':False,'epoch3_selection':False,'product_selectability':False,'publication':False},'epoch3_decisions_enabled':['supported version policy','update automation','maintenance staffing','release cadence'],'epoch3_selection_made':False,'next_action_class':NEXT_ACTION}
 dump(out/'upstream-evolution-authority.json',authority);authority_sha=sha(out/'upstream-evolution-authority.json')
 (out/'evidence-freeze.md').write_text(f'''# E2-R1/UT-7 Evidence Freeze

```text
authority                 {OUTPUT_REL}/upstream-evolution-authority.json
authority sha             {authority_sha}
patch rehearsal           3.14.5 -> 3.14.6
patch configuration-only  {rehearsal['configuration_only_candidate']}
patch file deltas         +{gate['exit_condition']['patch_layout_added']} / -{gate['exit_condition']['patch_layout_removed']} / changed {gate['exit_condition']['patch_normalized_changed_count']}
preview                    3.15.0b4 evidence only
preview release claim     false
version-literal files     {gate['exit_condition']['version_literal_file_count']}
audit                     {audit['pass_count']}/{audit['check_count']} PASS
```

Accepted: exact official input bindings acquired or reused by the bounded owner-local runner, complete patch-update delta, explicit update burden, preview delta, and security ownership.

Not accepted: Python 3.15 release/runtime support, automatic update acceptance, supported-version policy, staffing level, release cadence, Epoch 3 product selection, product selectability, or publication.
''')
 # Registry
 regp=root/'docs/documentation/document-registry.json';reg=load(regp);existing={x['path'] for x in reg['documents']}
 for n in NEW_DOCS:
  p=f'{OUTPUT_REL}/{n}'
  if p not in existing:reg['documents'].append(registry_entry(p));existing.add(p)
 reg['documents'].sort(key=lambda x:x['path']);dump(regp,reg)
 # Experiments index
 exp=root/'experiments/README.md';text=exp.read_text();line='- [`epoch2-upstream-thin-upstream-evolution/`](epoch2-upstream-thin-upstream-evolution/) — UT-7 patch-update rehearsal and Python 3.15 preview maintenance delta.\n'
 if line not in text:exp.write_text(text.rstrip()+'\n'+line)
 # State
 sp=root/'docs/current/STATE.json';state=load(sp);state['state_revision']=14;state['predecessor']={'commit':a.predecessor_head,'tree':a.predecessor_tree};state['accepted_authorities'].append({'id':'e2-r1-ut7-upstream-evolution-and-maintenance-portability','path':f'{OUTPUT_REL}/upstream-evolution-authority.json','role':'official patch-update rehearsal, Python 3.15 preview delta, maintenance burden, and security ownership','sha256':authority_sha});state['program']['gate']={'id':'E2-R1/API36-1','name':'API-36 controlled source-equivalent comparison','status':'ready'};state['program']['next_action_class']=NEXT_ACTION;state['next_action_class']=NEXT_ACTION;state['control_work']['next_action_class']=NEXT_ACTION;state['control_work']['resume_program_action_class']=NEXT_ACTION;state['active_work_package']=None;state['blockers']=[];state['agent_onboarding']['session_protocol_revision']=3;state['agent_onboarding']['session_output']='single-self-contained-zst-both-directions-with-out-of-band-sha256';state['session_protocol']={'path':'docs/agent/SESSION_PROTOCOL.md','revision':3,'sha256':protocol_binding['session_protocol_sha256']};state['unresolved_risks']=['The API-36 comparison must keep compile API as the intended changed variable and enumerate every unavoidable additional delta.','Python 3.15.0b4 remains preview-only and requires a successor release/runtime qualification before any support claim.','UT-6 still withholds a minimum release API and runtime 16 KiB support until direct target evidence exists.'];state['updated_by_transaction']=TRANSACTION_ID;dump(sp,state)
 # Task catalog successor activation and completion contract
 cp=root/'docs/agent/TASK_CATALOG.json';cat=load(cp);task=next(x for x in cat['tasks'] if x.get('task_id')==NEXT_TASK);task['activation']={'accepted_authority_path':f'{OUTPUT_REL}/upstream-evolution-authority.json','accepted_authority_sha256':authority_sha,'prerequisites_satisfied':True,'required_authority_role':'upstream-evolution-and-maintenance-portability','required_predecessor_action_class':ACTION,'status':'ready'}
 if not any(x.get('path')==f'{OUTPUT_REL}/upstream-evolution-authority.json' for x in task['required_authorities']):task['required_authorities'].append({'path':f'{OUTPUT_REL}/upstream-evolution-authority.json','reason':'Frozen patch-update and preview maintenance-portability authority.','sha256':authority_sha})
 task['completion_contract']=api36_contract();dump(cp,cat);catalog_sha=sha(cp)
 # Bind current state to the exact successor catalog identity after catalog mutation.
 state=load(sp);state['task_catalog']['sha256']=catalog_sha;state['task_completion']['current_action_class']=NEXT_ACTION;state['task_completion']['pass_successor_action_class']='evaluate-epoch2-closure-gates';dump(sp,state)
 # Refresh document-registry basis after state/catalog transition.
 reg=load(regp);reg['basis']['next_action_class']=NEXT_ACTION;reg['basis']['predecessor_head']=a.predecessor_head;reg['basis']['predecessor_tree']=a.predecessor_tree;reg['basis']['tracked_document_count']=len(reg['documents']);reg['basis']['task_catalog_schema_version']=cat['schema_version'];dump(regp,reg)
 # Regenerate current task/state and navigation views.
 renderer=root/'experiments/agent-task-completion/render-document-views.py';p=subprocess.run([sys.executable,'-B',str(renderer),'--root',str(root)],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode:print(p.stdout);print(p.stderr,file=sys.stderr);raise SystemExit('generated-view renderer failed')
 print(json.dumps({'pass':True,'authority_sha256':authority_sha,'state_revision':14,'next_action_class':NEXT_ACTION},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
