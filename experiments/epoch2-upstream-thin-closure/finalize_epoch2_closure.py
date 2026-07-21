#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from typing import Any
OUT_REL='experiments/epoch2-upstream-thin-closure'
ACTION='evaluate-epoch2-closure-gates'
NEXT_ACTION='initialize-epoch3-from-accepted-evidence-export'
NEXT_TASK='E3-INIT'
TRANSACTION_ID='20260721-e2-closure-v1'
PRIMARY=['closure-gate-matrix.json','producer-independent-evidence-export.json','accepted-product-seed-boundary.json','unresolved-risk-register.json','epoch1-inheritance-matrix.json','reference-hierarchy.json','mandatory-invariants.json','selectable-options.json','reference-deviation-register.json','producer-only-deferred-register.json','epoch3-initialization-contract.json','independent-audit.json']
SCRIPTS=['build_epoch2_closure.py','audit_epoch2_closure.py','finalize_epoch2_closure.py','verify_epoch2_closure.py','test_verify_epoch2_closure.py','run-epoch2-closure.sh']
NEW_DOCS=['README.md',*PRIMARY,'closure-authority.json','evidence-freeze.md']
def load(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def dump(p:Path,o:Any):p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def reg_entry(path:str)->dict[str,Any]:
 n=Path(path).name;ext=Path(path).suffix.removeprefix('.')
 if n=='closure-authority.json':domain='machine_authority'
 elif n=='independent-audit.json':domain='audit'
 elif ext=='md':domain='claim_evidence'
 else:domain='machine_evidence'
 return {'authority_domain':domain,'format':ext,'lifecycle_class':'FROZEN_AUTHORITY','machine_binding_policy':'allowed','migration_action':'e2-closure','mutability':'immutable','onboarding_visibility':'secondary' if ext=='md' else 'machine','owner':'epoch2-closure','path':path,'planned_canonical_parent':'docs/authorities/experiments/INDEX.md' if ext=='md' else 'docs/authorities/machine/INDEX.md','rationale':'','supersession_rule':'Explicit successor authority only.','update_trigger':'Never edit after freeze; create successor authority.'}
def e3_task(authority_sha:str)->dict[str,Any]:
 return {
  'task_id':NEXT_TASK,'title':'Epoch 3 initialization decisions and clean repository contract','action_class':NEXT_ACTION,'work_class':'L',
  'goal':'Consume the accepted Epoch 2 producer-independent export, complete every product selection disposition, define the clean repository boundary, and freeze the Epoch 3 product contract before implementation expands.',
  'activation':{'accepted_authority_path':f'{OUT_REL}/closure-authority.json','accepted_authority_sha256':authority_sha,'prerequisites_satisfied':True,'required_authority_role':'epoch2-closure-and-producer-independent-export','required_predecessor_action_class':ACTION,'status':'ready'},
  'required_reads':[{'path':'docs/epochs/EPOCH3_CHARTER.md','reason':'Epoch 3 mission, producer model, selection boundary, and repository contract.','scope':'full'},{'path':'docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md','reason':'Epoch 3 initialization gates.','scope':'section','section_heading':'## 8. Epoch 3 initialization gates','stop_before_heading':'## 9. Epoch 3 completion gates'},{'path':f'{OUT_REL}/epoch3-initialization-contract.json','reason':'Frozen initialization inputs and no-implementation-before-selection rule.','scope':'full'},{'path':f'{OUT_REL}/reference-hierarchy.json','reason':'Astral primary product reference and Python.org/CPython secondary Android input authority boundary.','scope':'full'}],
  'required_authorities':[{'path':f'{OUT_REL}/closure-authority.json','reason':'Frozen Epoch 2 closure and producer-independent evidence export.','sha256':authority_sha},{'path':f'{OUT_REL}/accepted-product-seed-boundary.json','reason':'Accepted minimal upstream-derived initialization seed.','sha256':sha(Path.cwd()/OUT_REL/'accepted-product-seed-boundary.json') if (Path.cwd()/OUT_REL/'accepted-product-seed-boundary.json').is_file() else ''}],
  'input_routing':{'first_attempt':'repository-local-accepted-evidence-export','fallback':'one bounded owner-run repository initialization runner','forbidden':['reopen-unrelated-epoch2-experiments','import-complete-laboratory-history','start-product-implementation-before-selection-register','network-git-in-assistant-environment']},
  'default_exclusions':['docs/history/**','docs/handoff/**','docs/stages/**','unselected-epoch2-experiments','producer-only-source-build-machinery','past-chat-transcripts'],
  'claim_boundary':{'android_runtime_claim':True,'official_upstream_identity_claim':True,'epoch2_closed_claim':True,'epoch3_initialization_ready_claim':True,'epoch3_selection_claim':False,'product_selectability_claim':False,'device_qualification_claim':False,'publication_claim':False},
  'deliverable':{'class':'epoch3-initialization-authority-and-clean-repository-contract','owner_interface':'one-runner','result':'complete-pass-or-fail-receipt'},
  'completion_contract':{'contract_version':1,'always':{'all_required_verifiers_must_pass':True,'generated_views_must_be_regenerated':True,'new_markdown_or_json_requires_registry_update':True,'one_runner_and_complete_receipt_required':True,'implementation_expansion_before_selection_complete_forbidden':True},'fail':{'complete_receipt_required':True,'allowed_action_policy':'retain-current-action-or-select-cataloged-bounded-correction'},'pass':{'required_output_roles':['epoch3-selection-register','clean-repository-boundary','product-contract-freeze','initialization-independent-audit','initialization-authority'],'required_selection_dispositions':['adopt','adopt-with-redesign','exclude','defer-to-epoch4'],'required_initialization_gates':['E3-I1','E3-I2','E3-I3','E3-I4'],'successor_action_class':'implement-epoch3-clean-upstream-derived-product','successor_must_exist':False,'successor_task_id':'E3-IMPLEMENT'}}
 }
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));ap.add_argument('--predecessor-head',required=True);ap.add_argument('--predecessor-tree',required=True);a=ap.parse_args();root=a.root.resolve();out=root/OUT_REL
 audit=load(out/'independent-audit.json');gate=load(out/'closure-gate-matrix.json');exp=load(out/'producer-independent-evidence-export.json');seed=load(out/'accepted-product-seed-boundary.json');risk=load(out/'unresolved-risk-register.json');sel=load(out/'selectable-options.json');init=load(out/'epoch3-initialization-contract.json')
 if audit.get('pass') is not True or gate.get('all_resolved') is not True:raise SystemExit('closure evidence not PASS')
 if exp.get('epoch3_selection_made') is not False or sel.get('selection_complete') is not False or seed.get('release_product') is not False:raise SystemExit('selection boundary violated')
 file_ids={n:sha(out/n) for n in ['README.md',*PRIMARY,*SCRIPTS]}
 transition_files={p:sha(root/p) for p in ['docs/epochs/EPOCH2_CHARTER.md','docs/epochs/EPOCH3_CHARTER.md','docs/roadmap/EPOCH2_PROGRAM_PLAN.md']}
 authority={'schema_version':1,'authority_kind':'epoch2-closure-and-producer-independent-evidence-export','status':'frozen-pass-epoch2-closed-epoch3-initialization-ready','predecessor':{'commit':a.predecessor_head,'tree':a.predecessor_tree},'closure_gate_matrix':{'path':f'{OUT_REL}/closure-gate-matrix.json','sha256':file_ids['closure-gate-matrix.json'],'resolved_count':8,'gate_count':8},'producer_independent_export':{'path':f'{OUT_REL}/producer-independent-evidence-export.json','sha256':file_ids['producer-independent-evidence-export.json']},'accepted_product_seed':{'path':f'{OUT_REL}/accepted-product-seed-boundary.json','sha256':file_ids['accepted-product-seed-boundary.json'],'seed_id':seed['seed_id'],'release_product':False},'selection_input':{'path':f'{OUT_REL}/selectable-options.json','sha256':file_ids['selectable-options.json'],'item_count':sel['item_count'],'selection_complete':False},'unresolved_risks':{'path':f'{OUT_REL}/unresolved-risk-register.json','sha256':file_ids['unresolved-risk-register.json'],'risk_count':risk['risk_count'],'closure_blocker_count':risk['closure_blocker_count']},'epoch3_initialization_contract':{'path':f'{OUT_REL}/epoch3-initialization-contract.json','sha256':file_ids['epoch3-initialization-contract.json'],'status':init['status']},'source_authority_bindings':gate['authority_bindings'],'file_identities':file_ids,'repository_transition_file_identities':transition_files,'verification':{'independent_audit':f"{audit['pass_count']}/{audit['check_count']}",'focused_verifier':'required-after-finalization','negative_fixtures':'required-before-transaction'},'claim_boundary':{'epoch2_closed':True,'producer_independent_export_complete':True,'accepted_seed_for_initialization':True,'epoch3_initialization_ready':True,'epoch3_selection_started':False,'product_selectability':False,'minimum_android_api_selected':False,'runtime_16k_device_qualified':False,'publication':False},'next_action_class':NEXT_ACTION}
 dump(out/'closure-authority.json',authority);authority_sha=sha(out/'closure-authority.json')
 (out/'evidence-freeze.md').write_text(f'''# Epoch 2 Closure Evidence Freeze\n\n```text\nauthority                  {OUT_REL}/closure-authority.json\nauthority sha256           {authority_sha}\nclosure gates              8/8 resolved\nindependent audit          {audit['pass_count']}/{audit['check_count']} PASS\naccepted seed              {seed['seed_id']}\nselection items            {sel['item_count']} pending Epoch 3\nunresolved risks           {risk['risk_count']} recorded / {risk['closure_blocker_count']} closure blockers\nEpoch 2 status             closed\nEpoch 3 status             ready for initialization; selection not started\nnext action                {NEXT_ACTION}\n```\n\nAccepted: producer-independent evidence export, one minimal upstream-derived initialization seed, explicit mandatory invariants, complete selection inputs, reference hierarchy, reference-deviation reduction review, Epoch 1 inheritance, and Epoch 4 producer deferrals.\n\nNot accepted: a selected Epoch 3 feature surface, a selectable or published product, API 36 as the default input, a minimum Android API, runtime 16 KiB device support, broad Android-context support, or a project-owned full source producer.\n''',encoding='utf-8')
 # Registry additions and Epoch 2 plan retirement.
 regp=root/'docs/documentation/document-registry.json';reg=load(regp);existing={x['path'] for x in reg['documents']}
 for n in NEW_DOCS:
  p=f'{OUT_REL}/{n}'
  if p not in existing:reg['documents'].append(reg_entry(p));existing.add(p)
 for row in reg['documents']:
  if row['path']=='docs/roadmap/EPOCH2_PROGRAM_PLAN.md':
   row['lifecycle_class']='HISTORICAL_SNAPSHOT';row['authority_domain']='historical_plan';row['mutability']='immutable-snapshot';row['onboarding_visibility']='secondary';row['supersession_rule']='Epoch 2 closure authority and Epoch 3 charter control successor work.';row['update_trigger']='Never edit after Epoch 2 closure.'
 reg['documents'].sort(key=lambda x:x['path']);dump(regp,reg)
 # Task catalog: define Epoch 3 initialization before selection starts.
 cp=root/'docs/agent/TASK_CATALOG.json';cat=load(cp)
 cat['tasks']=[x for x in cat['tasks'] if x.get('task_id')!=NEXT_TASK]
 task=e3_task(authority_sha)
 # Correct seed binding using the explicit root rather than cwd.
 task['required_authorities'][1]['sha256']=file_ids['accepted-product-seed-boundary.json']
 cat['tasks'].append(task);dump(cp,cat);catalog_sha=sha(cp)
 # State transition: Epoch 2 is closed; Epoch 3 initialization is ready but not started.
 sp=root/'docs/current/STATE.json';state=load(sp)
 state['state_revision']=16;state['predecessor']={'commit':a.predecessor_head,'tree':a.predecessor_tree}
 state['accepted_authorities'].append({'id':'epoch2-closure-and-producer-independent-evidence-export','path':f'{OUT_REL}/closure-authority.json','role':'Epoch 2 closure, accepted upstream-derived seed, selection inputs, and Epoch 3 initialization boundary','sha256':authority_sha})
 state['program']={'epoch':{'id':'E3','name':'clean upstream-derived Android standalone distribution','status':'ready-not-started'},'gate':{'id':'E3/INIT','name':'Epoch 3 initialization decisions and contract freeze','status':'ready'},'next_action_class':NEXT_ACTION,'status':'ready'}
 state['next_action_class']=NEXT_ACTION;state['control_work']['next_action_class']=NEXT_ACTION;state['control_work']['resume_program_action_class']=NEXT_ACTION;state['active_work_package']=None;state['blockers']=[]
 state['unresolved_risks']=[x['risk'] for x in risk['risks']]
 state['claim_boundaries']['epoch3_feature_selection_started']=False;state['claim_boundaries']['selectable']=False;state['claim_boundaries']['publication_authorized']=False
 state['active_plan']={'path':'docs/epochs/EPOCH3_CHARTER.md','sha256':sha(root/'docs/epochs/EPOCH3_CHARTER.md'),'detail_path':'docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md','detail_sha256':sha(root/'docs/roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md')}
 state['task_catalog']['sha256']=catalog_sha;state['task_completion']['current_action_class']=NEXT_ACTION;state['task_completion']['pass_successor_action_class']='implement-epoch3-clean-upstream-derived-product';state['updated_by_transaction']=TRANSACTION_ID;dump(sp,state)
 # Registry basis after transition.
 reg=load(regp);reg['basis']['next_action_class']=NEXT_ACTION;reg['basis']['predecessor_head']=a.predecessor_head;reg['basis']['predecessor_tree']=a.predecessor_tree;reg['basis']['tracked_document_count']=len(reg['documents']);reg['basis']['canonical_active_plan']='docs/epochs/EPOCH3_CHARTER.md';dump(regp,reg)
 # Regenerate current task and generated views.
 renderer=root/'experiments/agent-task-completion/render-document-views.py';p=subprocess.run([sys.executable,'-B',str(renderer),'--root',str(root)],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode:print(p.stdout);print(p.stderr,file=sys.stderr);raise SystemExit('generated-view renderer failed')
 print(json.dumps({'pass':True,'authority_sha256':authority_sha,'state_revision':16,'next_action_class':NEXT_ACTION,'selection_started':False},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
