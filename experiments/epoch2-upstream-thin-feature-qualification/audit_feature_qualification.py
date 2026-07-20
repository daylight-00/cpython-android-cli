#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any

CLASSIFICATIONS={'pass','android-mandatory-adaptation','missing-bionic-primitive','upstream-build-decision','inadequate-environment'}
CORE=['run_text_capture','popen_binary_pipes','cwd','custom_env','executable_lookup','absolute_execution','poll_wait_communicate','timeout','terminate','kill','large_output','nested_python','child_native_imports','relocated_base_execution','venv_execution','asyncio_subprocess_exec','asyncio_subprocess_shell']
SECONDARY=['shell_default','shell_explicit_system','explicit_shell_argv','start_new_session','process_group','signal_forwarding','pass_fds','close_fds','preexec_fn','pty','background_reap']
VENV=['symlink_mode','copy_mode','base_moved_before_new_venv','pre_existing_symlink_venv_after_base_move','pre_existing_copy_venv_after_base_move','venv_moved_without_base','patch_level_base_replacement_same_path','native_extension_in_venv','uv_created_venv','pip_generated_console_script_after_venv_relocation']
PIP=['PIP-0','PIP-1','PIP-2','PIP-3','PIP-X']
MP=['start_method:fork','start_method:spawn','start_method:forkserver','pipes_connections','queues','pools','locks','semaphores','events','conditions','shared_values_arrays','manager','process_pool_executor','resource_tracker','shared_memory','termination_cleanup']

def load(p:Path)->Any:return json.loads(p.read_text())
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();o=a.output
 checks:dict[str,bool]={};errors:dict[str,str]={}
 def ck(name:str,value:bool,detail:str=''):
  checks[name]=bool(value)
  if not value:errors[name]=detail or 'failed'
 try:
  core=load(o/'subprocess-core-matrix.json');secondary=load(o/'subprocess-secondary-matrix.json');venv=load(o/'venv-matrix.json');pip=load(o/'base-pip-variants.json');mp=load(o/'multiprocessing-matrix.json');decision=load(o/'feature-surface-decision.json');gate=load(o/'ut5-gate-diagnostics.json');runtime=load(o/'runtime-sdk-reproduction.json')
 except Exception as e:
  print(json.dumps({'schema_version':1,'audit_kind':'ut5-independent','pass':False,'check_count':0,'pass_count':0,'failed_checks':['load'],'errors':{'load':repr(e)},'checks':{}},indent=2,sort_keys=True));return 1
 ck('runtime-reproduction-pass',runtime.get('pass') is True)
 def matrix(name:str,obj:dict[str,Any],required:list[str],field:str='cases'):
  rows=obj.get(field,[]);names=[x.get('case') for x in rows]
  ck(f'{name}-matrix-pass',obj.get('pass') is True)
  ck(f'{name}-case-set-exact',names==required,repr(names))
  ck(f'{name}-classifications-valid',all(x.get('classification') in CLASSIFICATIONS for x in rows))
  ck(f'{name}-evidence-present',all(isinstance(x.get('evidence'),dict) and x['evidence'] for x in rows))
  ck(f'{name}-counts-consistent',obj.get('classified_case_count',len(rows))==len(required))
  return rows
 core_rows=matrix('core',core,CORE)
 sec_rows=matrix('secondary',secondary,SECONDARY)
 venv_rows=matrix('venv',venv,VENV)
 pip_rows=matrix('pip',pip,PIP,'variants')
 mp_rows=matrix('multiprocessing',mp,MP)
 core_pass={x['case'] for x in core_rows if x.get('pass') is True}
 ck('core-anchor-run','run_text_capture' in core_pass)
 ck('core-anchor-popen','popen_binary_pipes' in core_pass)
 ck('core-anchor-native-import','child_native_imports' in core_pass)
 ck('core-anchor-async-exec','asyncio_subprocess_exec' in core_pass)
 vpass={x['case'] for x in venv_rows if x.get('pass') is True}
 symlink=next(x for x in venv_rows if x['case']=='symlink_mode')
 copy=next(x for x in venv_rows if x['case']=='copy_mode')
 fresh=next(x for x in venv_rows if x['case']=='base_moved_before_new_venv')
 native=next(x for x in venv_rows if x['case']=='native_extension_in_venv')
 ck('venv-symlink-pass',symlink.get('pass') is True)
 ck('venv-copy-boundary-explicit',copy.get('pass') is False and copy.get('classification') in {'inadequate-environment','android-mandatory-adaptation'} and copy.get('support_candidate') is False)
 ck('venv-fresh-after-move-pass',fresh.get('pass') is True and fresh.get('evidence',{}).get('mode')=='symlinks')
 ck('venv-native-extension-pass',native.get('pass') is True)
 shell_default=next(x for x in sec_rows if x['case']=='shell_default');shell_explicit=next(x for x in sec_rows if x['case']=='shell_explicit_system')
 ck('explicit-shell-evidenced',shell_explicit.get('pass') is True)
 ck('default-shell-boundary-explicit',shell_default.get('pass') is True or shell_default.get('classification')=='android-mandatory-adaptation')
 preexec=next(x for x in sec_rows if x['case']=='preexec_fn')
 ck('preexec-not-default-support',preexec.get('support_candidate') is False)
 old_symlink=next(x for x in venv_rows if x['case']=='pre_existing_symlink_venv_after_base_move')
 ck('old-symlink-venv-explicit',old_symlink.get('classification') in CLASSIFICATIONS)
 console=next(x for x in venv_rows if x['case']=='pip_generated_console_script_after_venv_relocation')
 ck('console-script-relocation-explicit',console.get('classification') in {'pass','android-mandatory-adaptation'})
 ck('pip-required-variants',pip.get('required_variants')==PIP)
 ck('pip-no-selection',pip.get('selection_boundary',{}).get('epoch3_selection_made') is False)
 ck('pip-pass-does-not-require-inclusion',pip.get('selection_boundary',{}).get('passing_probe_requires_inclusion') is False)
 ck('multiprocessing-no-blanket',mp.get('support_boundary',{}).get('blanket_multiprocessing_claim') is False)
 ck('decision-pass',decision.get('pass') is True)
 ck('decision-no-epoch3-selection',decision.get('epoch3_selection_made') is False)
 ck('decision-no-blanket-claims',all(v is False for v in decision.get('blanket_claims',{}).values()))
 ck('decision-negative-scan',decision.get('negative_contract_scan',{}).get('pass') is True)
 ck('decision-unclassified-zero',decision.get('exit_condition',{}).get('unclassified_count')==0)
 ck('gate-pass',gate.get('pass') is True)
 ck('gate-failed-list-empty',gate.get('failed_gate_conditions')==[])
 ck('gate-matrices-complete',gate.get('exit_condition',{}).get('complete_matrix_count')==5)
 ck('gate-selection-not-made',gate.get('exit_condition',{}).get('epoch3_selection_made') is False)
 ck('gate-blanket-zero',gate.get('exit_condition',{}).get('blanket_claim_count')==0)
 ck('gate-negative-hits-zero',gate.get('exit_condition',{}).get('negative_contract_hits')==0)
 total=len(checks);passed=sum(checks.values());failed=[k for k,v in checks.items() if not v]
 result={'schema_version':1,'audit_kind':'ut5-independent','pass':not failed,'check_count':total,'pass_count':passed,'failed_checks':failed,'errors':errors,'checks':checks}
 (o/'independent-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if not failed else 1
if __name__=='__main__':raise SystemExit(main())
