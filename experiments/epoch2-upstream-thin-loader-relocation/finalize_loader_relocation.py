#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from typing import Any

ACTION='execute-e2-r1-ut2-loader-relocation-launcher-getpath'
NEXT_ACTION='execute-e2-r1-ut3-sysconfig-and-native-extension-sdk'
NEXT_TASK='E2-R1-UT-3'
FOLLOWING_ACTION='execute-e2-r1-ut4-android-data-and-writable-state-policy'
FOLLOWING_TASK='E2-R1-UT-4'
OUTPUT_REL='experiments/epoch2-upstream-thin-loader-relocation'
TRANSACTION_ID='20260720-e2-r1-ut2-loader-relocation-launcher-getpath-v5'
PRIMARY=['official-extraction-verification.json','launcher-build-evidence.json','loader-variant-matrix.json','launcher-variant-matrix.json','executable-discovery-matrix.json','native-loader-evidence.json','relocation-results.json','ut2-gate-diagnostics.json','independent-audit.json']
SCRIPTS=['launcher_la0_pyconfig.c','launcher_la1_bytesmain.c','launcher_la2_programs_python.c','launcher_la3_android_signal.c','launcher_lr0_self_reexec.c','run_loader_relocation_experiment.py','audit_loader_relocation.py','verify_loader_relocation.py','test_verify_loader_relocation.py','finalize_loader_relocation.py','run-ut2-loader-relocation-launcher-getpath.sh']
NEW_DOCS=['README.md',*PRIMARY,'loader-relocation-authority.json','evidence-freeze.md']

def load(p:Path)->Any:return json.loads(p.read_text())
def dump(p:Path,o:Any):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def sha(p:Path)->str:
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def completion_contract(current:str, successor:str, successor_task:str)->dict[str,Any]:
 return {
  'contract_version':1,
  'always':{'all_required_verifiers_must_pass':True,'clean_main_and_bundle_export_ready_on_close':True,'forbidden_new_authority_bindings':['docs/current/STATE.json','docs/current/AGENT_TASK.json','README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md'],'generated_views_must_be_regenerated':True,'new_markdown_or_json_requires_registry_update':True,'one_runner_and_complete_receipt_required':True},
  'fail':{'allowed_action_policy':'retain-current-action-or-select-cataloged-bounded-correction','complete_receipt_required':True,'correction_task_must_be_cataloged':True,'correction_task_must_resume_action_class':current,'required_failure_records':['first-meaningful-failure','failure-classification','blocked-downstream','claim-boundary'],'required_state_updates':['state_revision','predecessor','active_work_package','blockers','unresolved_risks','updated_by_transaction']},
  'pass':{'required_catalog_updates':['bind-accepted-authority-into-successor','activate-successor-task','define-successor-completion-contract-before-selection'],'required_output_namespace':'experiments/epoch2-upstream-thin-sysconfig-sdk/','required_output_roles':['absolute-path-census','runtime-path-normalization','consumer-metadata-normalization','native-extension-wheel-evidence','sdk-flavor-decision','independent-audit','machine-authority','evidence-freeze'],'required_state_updates':['state_revision','predecessor','accepted_authorities','program.gate','program.next_action_class','next_action_class','control_work.next_action_class','control_work.resume_program_action_class','unresolved_risks','updated_by_transaction'],'successor_action_class':successor,'successor_must_exist':True,'successor_task_id':successor_task}
 }

def registry_entry(path:str)->dict[str,Any]:
 name=Path(path).name; ext=Path(path).suffix.removeprefix('.')
 domain='machine_authority' if name=='loader-relocation-authority.json' else ('audit' if name=='independent-audit.json' else ('claim_evidence' if ext=='md' else 'machine_evidence'))
 return {'authority_domain':domain,'format':ext,'lifecycle_class':'FROZEN_AUTHORITY','machine_binding_policy':'allowed','migration_action':'e2-r1-ut2-loader-relocation-launcher-getpath','mutability':'immutable','onboarding_visibility':'secondary' if ext=='md' else 'machine','owner':'epoch2-research','path':path,'planned_canonical_parent':'docs/authorities/experiments/INDEX.md' if ext=='md' else 'docs/authorities/machine/INDEX.md','rationale':'','supersession_rule':'Explicit successor experiment or authority only.','update_trigger':'Never edit after freeze; create successor authority.'}

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path.cwd()); ap.add_argument('--output-dir',default=OUTPUT_REL); ap.add_argument('--artifact-dir',type=Path,required=True); ap.add_argument('--predecessor-head',required=True); ap.add_argument('--predecessor-tree',required=True); a=ap.parse_args(); root=a.root.resolve(); out=root/a.output_dir; art=a.artifact_dir.resolve()
 audit=load(out/'independent-audit.json')
 if audit.get('pass') is not True: raise SystemExit('independent audit is not PASS')
 lm=load(out/'loader-variant-matrix.json'); la=load(out/'launcher-variant-matrix.json'); ex=load(out/'executable-discovery-matrix.json'); ne=load(out/'native-loader-evidence.json'); rr=load(out/'relocation-results.json'); candidate=load(art/'selected-candidate.json')
 file_ids={n:sha(out/n) for n in [*PRIMARY,*SCRIPTS]}
 readme=f'''# E2-R1/UT-2 — Loader, relocation, launcher, and getpath

This experiment executes the official CPython 3.14.6 Android package on the owner Android/Termux environment and compares loader variants LR-0 through LR-3, launcher variants LA-0 through LA-3, and a clean LR-4 candidate.

Selected loader input: `{lm['selected_input_variant']}`. Selected launcher: `{la['selected']}`.

The accepted result removes project-required `LD_LIBRARY_PATH` and loader-bootstrap self-reexec, closes every packaged native dependency edge with relative `DT_RUNPATH`, preserves 16 KiB ELF alignment, imports every packaged native extension, passes direct/transitive/dlopen probes, survives whole-prefix movement, and records executable/symlink/venv/getpath boundaries.

The selected launcher binary remains a result artifact, not a committed product. Device qualification, Epoch 3 product selection, product selectability, and publication remain outside this authority.
'''
 (out/'README.md').write_text(readme)
 authority={'schema_version':1,'authority_kind':'e2-r1-ut2-loader-relocation-launcher-getpath','status':'frozen-pass-bounded-android-runtime-and-relocation','predecessor':{'commit':a.predecessor_head,'tree':a.predecessor_tree},'upstream_control_authority':{'path':'experiments/epoch2-upstream-thin-control/upstream-control-authority.json','sha256':'6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c'},'artifact_prototype_authority':{'path':'experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json','sha256':'387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306'},'selection':{'loader_variant':lm['selected_input_variant'],'clean_candidate':'LR-4','launcher_variant':la['selected'],'launcher_sha256':candidate['launcher_sha256'],'exit_condition':lm['exit_condition'],'gate_condition':lm['gate_condition']},'device':ne['device'],'native_loader':{'transformed_elf_count':ne['transformed_elf_count'],'all_exact_mutations':ne['all_exact_mutations'],'all_alignment_preserved':ne['all_alignment_preserved'],'all_16k_compatible':ne['all_16k_compatible'],'alignment_policy':ne.get('alignment_policy'),'patchelf_capabilities':ne.get('patchelf_capabilities'),'bounded_bionic_checks':ne['bounded_bionic_checks']},'executable_boundary':ex['supported_boundary'],'relocation':{'whole_prefix_relocation_pass':rr['whole_prefix_relocation_pass'],'subprocess_child_reentry_pass':rr['subprocess_child_reentry_pass']},'file_identities':file_ids,'verification':{'independent_audit':f"{audit['pass_count']}/{audit['check_count']}",'focused_verifier':'required-after-finalization','negative_fixtures':'required-before-transaction'},'claim_boundary':{'official_upstream_identity':True,'artifact_representation':True,'bounded_android_runtime':True,'relative_native_loader_closure':True,'whole_prefix_relocation':True,'launcher_and_getpath_boundary':True,'device_qualification':False,'epoch3_selection':False,'product_selectability':False,'publication':False},'next_action_class':NEXT_ACTION}
 dump(out/'loader-relocation-authority.json',authority); authority_sha=sha(out/'loader-relocation-authority.json')
 freeze=f'''# E2-R1/UT-2 Evidence Freeze

```text
authority       {OUTPUT_REL}/loader-relocation-authority.json
authority sha   {authority_sha}
loader          {lm['selected_input_variant']} -> LR-4
launcher        {la['selected']}
LD_LIBRARY_PATH absent
self-reexec     absent
internal edges  0
extension fails 0
relocation      PASS
audit           {audit['pass_count']}/{audit['check_count']} PASS
```

Accepted: bounded Android/Bionic execution, relative native loader closure, selected launcher semantics, executable/getpath boundary evidence, whole-prefix relocation, and subprocess re-entry.

Not accepted: broad device qualification, Epoch 3 product selection, product selectability, or publication.
'''; (out/'evidence-freeze.md').write_text(freeze)

 catalog_path=root/'docs/agent/TASK_CATALOG.json'; catalog=load(catalog_path); ut3=next(t for t in catalog['tasks'] if t['task_id']==NEXT_TASK)
 req={'path':f'{OUTPUT_REL}/loader-relocation-authority.json','reason':'Frozen Android/Bionic loader, launcher, getpath, native closure, and whole-prefix relocation authority.','sha256':authority_sha}
 ut3['activation']={'prerequisites_satisfied':True,'accepted_authority_path':req['path'],'accepted_authority_sha256':authority_sha,'required_authority_role':'loader-relocation-launcher-getpath','required_predecessor_action_class':ACTION,'status':'ready'}
 if not any(x.get('path')==req['path'] for x in ut3['required_authorities']):ut3['required_authorities'].append(req)
 ut3['claim_boundary']['android_runtime_claim']=True
 ut3['completion_contract']=completion_contract(NEXT_ACTION,FOLLOWING_ACTION,FOLLOWING_TASK)
 if not any(t.get('task_id')==FOLLOWING_TASK for t in catalog['tasks']):
  catalog['tasks'].append({'action_class':FOLLOWING_ACTION,'activation':{'prerequisites_satisfied':False,'required_authority_role':'sysconfig-and-native-extension-sdk','required_predecessor_action_class':NEXT_ACTION,'status':'blocked-on-predecessor-authority'},'claim_boundary':dict(ut3['claim_boundary']),'default_exclusions':list(ut3['default_exclusions']),'deliverable':dict(ut3['deliverable']),'goal':'Define host-neutral CA, timezone, temporary, cache, bytecode, user-site, venv writable-state, and read-only-install policies for Android.','input_routing':dict(ut3['input_routing']),'required_authorities':list(ut3['required_authorities']),'required_reads':[{'path':'docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md','reason':'Android-mandatory data candidates, writable-state boundaries, negative scans, and exit condition.','scope':'section','section_heading':'## UT-4 — Android-mandatory data and writable-state policy','stop_before_heading':'## UT-5 — Feature capability and product-surface qualification'}],'task_id':FOLLOWING_TASK,'title':'Android-mandatory data and writable-state policy','work_class':'L'})
 dump(catalog_path,catalog); catalog_sha=sha(catalog_path)
 state_path=root/'docs/current/STATE.json'; state=load(state_path); state['state_revision']+=1; state['predecessor']={'commit':a.predecessor_head,'tree':a.predecessor_tree}; state['accepted_authorities'].append({'id':'e2-r1-ut2-loader-relocation-launcher-getpath','path':req['path'],'role':'bounded Android/Bionic loader, launcher, getpath, native closure, and whole-prefix relocation evidence','sha256':authority_sha}); state['program']['gate']={'id':'E2-R1/UT-3','name':'Sysconfig and native-extension SDK','status':'ready'}; state['program']['next_action_class']=NEXT_ACTION; state['next_action_class']=NEXT_ACTION; state['control_work']['next_action_class']=NEXT_ACTION; state['control_work']['resume_program_action_class']=NEXT_ACTION; state['blockers']=[]; state['active_work_package']=None; state['unresolved_risks']=['UT-3 must normalize every active runtime and consumer metadata path and prove a real Android-tagged native-extension wheel build/install/import/relocation path before any SDK or product surface is selectable.']; state['updated_by_transaction']=TRANSACTION_ID; state['task_catalog']['sha256']=catalog_sha; state['task_completion']['current_action_class']=NEXT_ACTION; state['task_completion']['pass_successor_action_class']=FOLLOWING_ACTION; dump(state_path,state)
 registry_path=root/'docs/documentation/document-registry.json'; registry=load(registry_path); existing={d['path'] for d in registry['documents']}
 for n in NEW_DOCS:
  p=f'{OUTPUT_REL}/{n}'
  if p not in existing:registry['documents'].append(registry_entry(p));existing.add(p)
 registry['basis']['next_action_class']=NEXT_ACTION;registry['basis']['predecessor_head']=a.predecessor_head;registry['basis']['predecessor_tree']=a.predecessor_tree;registry['basis']['tracked_document_count']=len(registry['documents']);registry['basis']['task_catalog_schema_version']=catalog['schema_version'];dump(registry_path,registry)
 proc=subprocess.run([sys.executable,str(root/'experiments/agent-task-completion/render-document-views.py'),'--root',str(root)])
 if proc.returncode:return proc.returncode
 print(json.dumps({'pass':True,'authority_sha256':authority_sha,'state_revision':state['state_revision'],'next_action_class':NEXT_ACTION,'selected_loader':lm['selected_input_variant'],'selected_launcher':la['selected']},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
