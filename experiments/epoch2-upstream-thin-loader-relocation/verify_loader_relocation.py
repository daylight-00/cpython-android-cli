#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

def load(p:Path):return json.loads(p.read_text())
def sha(p:Path):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--artifact-dir',type=Path,required=True);a=ap.parse_args();root=a.root.resolve();out=root/'experiments/epoch2-upstream-thin-loader-relocation';art=a.artifact_dir.resolve()
 required=['README.md','official-extraction-verification.json','launcher-build-evidence.json','loader-variant-matrix.json','launcher-variant-matrix.json','executable-discovery-matrix.json','native-loader-evidence.json','relocation-results.json','ut2-gate-diagnostics.json','independent-audit.json','loader-relocation-authority.json','evidence-freeze.md','launcher_la0_pyconfig.c','launcher_la1_bytesmain.c','launcher_la2_programs_python.c','launcher_la3_android_signal.c','launcher_lr0_self_reexec.c','run_loader_relocation_experiment.py','audit_loader_relocation.py','verify_loader_relocation.py','test_verify_loader_relocation.py','finalize_loader_relocation.py','run-ut2-loader-relocation-launcher-getpath.sh']
 checks={};errors={}
 checks['required_files']=all((out/x).is_file() for x in required)
 try:
  lb=load(out/'launcher-build-evidence.json');lm=load(out/'loader-variant-matrix.json');la=load(out/'launcher-variant-matrix.json');ex=load(out/'executable-discovery-matrix.json');ne=load(out/'native-loader-evidence.json');rr=load(out/'relocation-results.json');diag=load(out/'ut2-gate-diagnostics.json');audit=load(out/'independent-audit.json');auth=load(out/'loader-relocation-authority.json');state=load(root/'docs/current/STATE.json');task=load(root/'docs/current/AGENT_TASK.json');catalog=load(root/'docs/agent/TASK_CATALOG.json');registry=load(root/'docs/documentation/document-registry.json');cand=load(art/'selected-candidate.json')
  checks['json_parse']=True
 except Exception as e:
  checks['json_parse']=False;errors['json_parse']=str(e);print(json.dumps({'pass':False,'checks':checks,'errors':errors},indent=2));return 1
 checks['loader_matrix_pass']=lm.get('pass') is True and lm.get('lr4',{}).get('pass') is True
 checks['gate_diagnostics']=diag.get('pass') is True and all(diag.get('gate_condition',{}).values()) and lm.get('gate_condition')==diag.get('gate_condition')
 ec=lm.get('exit_condition',{})
 checks['exit_condition']=ec.get('project_required_LD_LIBRARY_PATH_absent') is True and ec.get('loader_bootstrap_self_reexec_absent') is True and ec.get('unresolved_internal_edges')==0 and ec.get('required_extension_failures')==0 and ec.get('whole_prefix_relocation_pass') is True and ec.get('subprocess_child_reentry_pass') is True
 checks['launcher_selection']=la.get('selected') in {'LA-0','LA-1','LA-2','LA-3'} and any(x.get('variant')==la.get('selected') and x.get('pass') is True for x in la.get('variants',[]))
 expected_launchers={'LA-0','LA-1','LA-2','LA-3','LR-0'};built=lb.get('variants',{})
 checks['launcher_build_complete']=set(built)==expected_launchers
 checks['launcher_runpath_exact']=checks['launcher_build_complete'] and all(v.get('surface',{}).get('runpath')==['$ORIGIN/../lib'] and not v.get('surface',{}).get('rpath') for v in built.values())
 checks['launcher_normalization_exact']=checks['launcher_build_complete'] and all(v.get('runpath_normalization',{}).get('exact_normalization_check') is True for v in built.values())
 checks['patchelf_page_size_supported']=lb.get('patchelf_capabilities',{}).get('page_size_supported') is True and ne.get('patchelf_capabilities',{}).get('page_size_supported') is True
 checks['launcher_patchelf_page_size']=checks['launcher_build_complete'] and all((v.get('runpath_normalization',{}).get('action')=='none' or '--page-size' in (v.get('runpath_normalization',{}).get('command') or []) and '16384' in (v.get('runpath_normalization',{}).get('command') or [])) for v in built.values())
 checks['launcher_absolute_runpath_absent']=checks['launcher_build_complete'] and all(not any(x.startswith('/') for g in v.get('surface',{}).get('runpath',[]) for x in g.split(':')) for v in built.values())
 checks['loader_selection']=lm.get('selected_input_variant') in {'LR-1','LR-2','LR-3'}
 checks['candidate_consistency']=cand.get('selected_loader')==lm.get('selected_input_variant') and cand.get('selected_launcher')==la.get('selected') and cand.get('product_selectable') is False
 checks['candidate_bytes']=(art/'selected-launcher').is_file() and sha(art/'selected-launcher')==cand.get('launcher_sha256')
 checks['native_exact']=ne.get('all_exact_mutations') is True and ne.get('all_alignment_preserved') is True and ne.get('all_16k_compatible') is True
 objs=ne.get('objects',[])
 checks['native_alignment_policy']=bool(objs) and all(x.get('alignment_policy',{}).get('preserved') is True for x in objs)
 mutated=[x for x in objs if x.get('mutated') is True]
 checks['native_patchelf_page_size']=all('--page-size' in (x.get('mutation_command') or []) and '16384' in (x.get('mutation_command') or []) for x in mutated)
 checks['native_api']=ne.get('device',{}).get('api_compatible') is True
 checks['native_bionic']=all(ne.get('bounded_bionic_checks',{}).get(k) is True for k in ('origin_direct_lookup','transitive_extension_lookup','dlopen','minimum_api','modern_linker_namespace'))
 checks['relocation']=rr.get('whole_prefix_relocation_pass') is True and rr.get('subprocess_child_reentry_pass') is True
 reqcases={'direct_real_path','relative_in_tree_symlink','absolute_in_tree_symlink','external_symlink','altered_argv0','copied_executable_without_prefix','venv_symlink_mode','venv_copy_mode','runtime_moved_before_fresh_venv_creation','pre_existing_venv_after_base_move','pre_existing_copy_venv_after_base_move','patch_level_base_replacement'}
 checks['discovery_complete']=reqcases.issubset(set(ex.get('cases',{})))
 moved_symlink=ex.get('cases',{}).get('pre_existing_venv_after_base_move',{});ps=moved_symlink.get('path_state',{});ee=moved_symlink.get('execution_error',{})
 checks['moved_symlink_venv_boundary']=moved_symlink.get('pass') is False and moved_symlink.get('venv_mode')=='symlinks' and ps.get('lexists') is True and ps.get('exists') is False and ps.get('is_symlink') is True and ee.get('errno')==2
 moved_copy=ex.get('cases',{}).get('pre_existing_copy_venv_after_base_move',{})
 checks['moved_copy_venv_boundary']=moved_copy.get('venv_mode')=='copies' and isinstance(moved_copy.get('pass'),bool)
 checks['independent_audit']=audit.get('pass') is True and audit.get('pass_count')==audit.get('check_count')
 ids=auth.get('file_identities',{});checks['authority_file_set']=set(ids)==set(required)-{'README.md','loader-relocation-authority.json','evidence-freeze.md'}
 checks['authority_file_identities']=checks['authority_file_set'] and all(sha(out/k)==v for k,v in ids.items())
 checks['authority_selection']=auth.get('selection',{}).get('loader_variant')==lm.get('selected_input_variant') and auth.get('selection',{}).get('launcher_variant')==la.get('selected') and auth.get('selection',{}).get('launcher_sha256')==cand.get('launcher_sha256')
 checks['authority_claims']=auth.get('claim_boundary',{}).get('bounded_android_runtime') is True and auth.get('claim_boundary',{}).get('relative_native_loader_closure') is True and auth.get('claim_boundary',{}).get('device_qualification') is False and auth.get('claim_boundary',{}).get('product_selectability') is False and auth.get('claim_boundary',{}).get('publication') is False
 authsha=sha(out/'loader-relocation-authority.json')
 checks['state_binding']=any(x.get('path')=='experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json' and x.get('sha256')==authsha for x in state.get('accepted_authorities',[]))
 checks['state_next']=state.get('state_revision')==9 and state.get('next_action_class')=='execute-e2-r1-ut3-sysconfig-and-native-extension-sdk' and state.get('program',{}).get('gate',{}).get('id')=='E2-R1/UT-3'
 checks['current_task']=task.get('task',{}).get('id')=='E2-R1-UT-3' and task.get('task',{}).get('action_class')=='execute-e2-r1-ut3-sysconfig-and-native-extension-sdk'
 ut3=next((x for x in catalog.get('tasks',[]) if x.get('task_id')=='E2-R1-UT-3'),{})
 checks['catalog_binding']=ut3.get('activation',{}).get('accepted_authority_sha256')==authsha and ut3.get('activation',{}).get('status')=='ready'
 checks['ut3_completion_contract']=ut3.get('completion_contract',{}).get('pass',{}).get('successor_task_id')=='E2-R1-UT-4'
 checks['ut4_cataloged']=any(x.get('task_id')=='E2-R1-UT-4' for x in catalog.get('tasks',[]))
 docs={x.get('path') for x in registry.get('documents',[])}
 checks['registry_coverage']=all(f'experiments/epoch2-upstream-thin-loader-relocation/{x}' in docs for x in ['README.md','official-extraction-verification.json','launcher-build-evidence.json','loader-variant-matrix.json','launcher-variant-matrix.json','executable-discovery-matrix.json','native-loader-evidence.json','relocation-results.json','ut2-gate-diagnostics.json','independent-audit.json','loader-relocation-authority.json','evidence-freeze.md'])
 checks['no_binary_committed']=not any(p.is_file() and p.suffix not in {'.md','.json','.py','.sh','.c'} for p in out.rglob('*'))
 failed=[k for k,v in checks.items() if not v]
 result={'schema_version':1,'verification_kind':'e2-r1-ut2-loader-relocation-launcher-getpath','checks':checks,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'errors':errors,'authority_sha256':authsha,'claim_boundary':'Bounded Android runtime/loader/relocation authority; no device qualification, product selection, selectability, or publication claim.','pass':not failed}
 print(json.dumps(result,indent=2,sort_keys=True));return 0 if not failed else 1
if __name__=='__main__':raise SystemExit(main())
