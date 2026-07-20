#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
from typing import Any

OUTPUT_REL='experiments/epoch2-upstream-thin-feature-qualification'
NEXT_ACTION='execute-e2-r1-ut6-platform-portability'
NEXT_TASK='E2-R1-UT-6'
AUTHORITY='feature-qualification-authority.json'
CLASSIFICATIONS={'pass','android-mandatory-adaptation','missing-bionic-primitive','upstream-build-decision','inadequate-environment'}
CORE=['run_text_capture','popen_binary_pipes','cwd','custom_env','executable_lookup','absolute_execution','poll_wait_communicate','timeout','terminate','kill','large_output','nested_python','child_native_imports','relocated_base_execution','venv_execution','asyncio_subprocess_exec','asyncio_subprocess_shell']
SECONDARY=['shell_default','shell_explicit_system','explicit_shell_argv','start_new_session','process_group','signal_forwarding','pass_fds','close_fds','preexec_fn','pty','background_reap']
VENV=['symlink_mode','copy_mode','base_moved_before_new_venv','pre_existing_symlink_venv_after_base_move','pre_existing_copy_venv_after_base_move','venv_moved_without_base','patch_level_base_replacement_same_path','native_extension_in_venv','uv_created_venv','pip_generated_console_script_after_venv_relocation']
PIP=['PIP-0','PIP-1','PIP-2','PIP-3','PIP-X']
MP=['start_method:fork','start_method:spawn','start_method:forkserver','pipes_connections','queues','pools','locks','semaphores','events','conditions','shared_values_arrays','manager','process_pool_executor','resource_tracker','shared_memory','termination_cleanup']
PRIMARY=['runtime-sdk-reproduction.json','subprocess-core-matrix.json','subprocess-secondary-matrix.json','venv-matrix.json','base-pip-variants.json','multiprocessing-matrix.json','feature-surface-decision.json','ut5-gate-diagnostics.json','independent-audit.json']
SCRIPTS=['run_feature_qualification_experiment.py','audit_feature_qualification.py','verify_feature_qualification.py','test_verify_feature_qualification.py','finalize_feature_qualification.py','run-ut5-feature-capability-and-product-surface-qualification.sh']
NEW_DOCS=['README.md',*PRIMARY,AUTHORITY,'evidence-freeze.md']

def load(p:Path)->Any:return json.loads(p.read_text())
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=None);ap.add_argument('--output-dir',default=OUTPUT_REL);ap.add_argument('--expected-predecessor-head');ap.add_argument('--expected-predecessor-tree');a=ap.parse_args();root=(a.root if a.root is not None else Path.cwd()).resolve();out=root/a.output_dir
 checks:dict[str,bool]={};errors:dict[str,str]={}
 def ck(name:str,value:bool,detail:str=''):
  checks[name]=bool(value)
  if not value:errors[name]=detail or 'failed'
 try:
  core=load(out/'subprocess-core-matrix.json');secondary=load(out/'subprocess-secondary-matrix.json');venv=load(out/'venv-matrix.json');pip=load(out/'base-pip-variants.json');mp=load(out/'multiprocessing-matrix.json');decision=load(out/'feature-surface-decision.json');gate=load(out/'ut5-gate-diagnostics.json');audit=load(out/'independent-audit.json');runtime=load(out/'runtime-sdk-reproduction.json');authority=load(out/AUTHORITY);state=load(root/'docs/current/STATE.json');task=load(root/'docs/current/AGENT_TASK.json');catalog=load(root/'docs/agent/TASK_CATALOG.json');registry=load(root/'docs/documentation/document-registry.json')
 except Exception as e:
  print(json.dumps({'pass':False,'check_count':0,'pass_count':0,'failed_checks':['load'],'errors':{'load':repr(e)},'checks':{}},indent=2,sort_keys=True));return 1
 def matrix(name:str,obj:dict[str,Any],required:list[str],field:str='cases'):
  rows=obj.get(field,[]);names=[x.get('case') for x in rows]
  ck(f'{name}-pass',obj.get('pass') is True)
  ck(f'{name}-case-set-exact',names==required,repr(names))
  ck(f'{name}-classification-vocabulary',all(x.get('classification') in CLASSIFICATIONS for x in rows))
  ck(f'{name}-evidence-present',all(isinstance(x.get('evidence'),dict) and x['evidence'] for x in rows))
  return rows
 core_rows=matrix('core',core,CORE);sec_rows=matrix('secondary',secondary,SECONDARY);venv_rows=matrix('venv',venv,VENV);pip_rows=matrix('pip',pip,PIP,'variants');mp_rows=matrix('multiprocessing',mp,MP)
 symlink=next(x for x in venv_rows if x['case']=='symlink_mode');copy=next(x for x in venv_rows if x['case']=='copy_mode');fresh=next(x for x in venv_rows if x['case']=='base_moved_before_new_venv');native=next(x for x in venv_rows if x['case']=='native_extension_in_venv')
 ck('venv-symlink-anchor',symlink.get('pass') is True)
 ck('venv-copy-boundary',copy.get('pass') is False and copy.get('classification') in {'inadequate-environment','android-mandatory-adaptation'} and copy.get('support_candidate') is False)
 ck('venv-fresh-after-move-anchor',fresh.get('pass') is True and fresh.get('evidence',{}).get('mode')=='symlinks')
 ck('venv-native-extension-anchor',native.get('pass') is True)
 ck('gate-fresh-mode',gate.get('exit_condition',{}).get('fresh_venv_mode')=='symlinks')
 ck('runtime-reproduction-pass',runtime.get('pass') is True)
 ck('gate-pass',gate.get('pass') is True)
 ck('gate-failed-empty',gate.get('failed_gate_conditions')==[])
 ck('audit-pass',audit.get('pass') is True and audit.get('pass_count')==audit.get('check_count'))
 ck('decision-pass',decision.get('pass') is True)
 ck('decision-no-selection',decision.get('epoch3_selection_made') is False)
 ck('decision-no-blanket',all(v is False for v in decision.get('blanket_claims',{}).values()))
 ck('decision-negative-scan',decision.get('negative_contract_scan',{}).get('pass') is True)
 ck('authority-kind',authority.get('authority_kind')=='e2-r1-ut5-feature-capability-and-product-surface-qualification')
 ck('authority-status',authority.get('status')=='frozen-pass-explicit-feature-support-boundaries')
 ck('authority-no-selection',authority.get('epoch3_selection_made') is False)
 ck('authority-next-action',authority.get('next_action_class')==NEXT_ACTION)
 ck('authority-vocabulary',set(authority.get('classification_vocabulary',[]))==CLASSIFICATIONS)
 if a.expected_predecessor_head:ck('authority-predecessor-head',authority.get('predecessor',{}).get('commit')==a.expected_predecessor_head)
 if a.expected_predecessor_tree:ck('authority-predecessor-tree',authority.get('predecessor',{}).get('tree')==a.expected_predecessor_tree)
 for n in [*PRIMARY,*SCRIPTS]:
  p=out/n;ck(f'file-present:{n}',p.is_file())
  if p.is_file():ck(f'file-identity:{n}',authority.get('file_identities',{}).get(n)==sha(p),f'{authority.get("file_identities",{}).get(n)} != {sha(p)}')
 ck('state-revision',state.get('state_revision')==12,str(state.get('state_revision')))
 ck('state-next-action',state.get('next_action_class')==NEXT_ACTION)
 ck('state-program-gate',state.get('program',{}).get('gate',{}).get('id')=='E2-R1/UT-6' and state.get('program',{}).get('gate',{}).get('status')=='ready')
 ck('state-program-action',state.get('program',{}).get('next_action_class')==NEXT_ACTION)
 auth_sha=sha(out/AUTHORITY)
 accepted=[x for x in state.get('accepted_authorities',[]) if x.get('path')==f'{OUTPUT_REL}/{AUTHORITY}']
 ck('state-authority-binding',len(accepted)==1 and accepted[0].get('sha256')==auth_sha)
 ck('state-unresolved-risk-ut6',any('UT-6' in x for x in state.get('unresolved_risks',[])))
 ck('task-state-revision',task.get('state_revision')==12)
 ck('task-id',task.get('task',{}).get('id')==NEXT_TASK)
 ck('task-action',task.get('task',{}).get('action_class')==NEXT_ACTION)
 ck('task-gate-ready',task.get('program_gate',{}).get('id')=='E2-R1/UT-6' and task.get('program_gate',{}).get('status')=='ready')
 req=[x for x in task.get('required_authorities',[]) if x.get('path')==f'{OUTPUT_REL}/{AUTHORITY}']
 ck('task-authority-binding',len(req)==1 and req[0].get('sha256')==auth_sha)
 ut6=next((x for x in catalog.get('tasks',[]) if x.get('task_id')==NEXT_TASK),None)
 ck('catalog-ut6-exists',ut6 is not None)
 if ut6:
  ck('catalog-ut6-ready',ut6.get('activation',{}).get('status')=='ready' and ut6.get('activation',{}).get('accepted_authority_sha256')==auth_sha)
  ck('catalog-ut6-contract',ut6.get('completion_contract',{}).get('pass',{}).get('successor_task_id')=='E2-R1-UT-7')
 ck('catalog-ut7-exists',any(x.get('task_id')=='E2-R1-UT-7' for x in catalog.get('tasks',[])))
 docs={x.get('path') for x in registry.get('documents',[])}
 for n in NEW_DOCS:ck(f'registry:{n}',f'{OUTPUT_REL}/{n}' in docs)
 ck('registry-next-action',registry.get('basis',{}).get('next_action_class')==NEXT_ACTION)
 total=len(checks);passed=sum(checks.values());failed=[k for k,v in checks.items() if not v]
 result={'schema_version':1,'verifier_kind':'ut5-focused','pass':not failed,'check_count':total,'pass_count':passed,'failed_checks':failed,'errors':errors,'checks':checks}
 print(json.dumps(result,indent=2,sort_keys=True));return 0 if not failed else 1
if __name__=='__main__':raise SystemExit(main())
