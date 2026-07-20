#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def load(p:Path): return json.loads(p.read_text())
def sha(p:Path):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def dump(p:Path,o): p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',type=Path,required=True); ap.add_argument('--artifact-dir',type=Path,required=True); a=ap.parse_args(); o=a.output_dir; art=a.artifact_dir
 lb=load(o/'launcher-build-evidence.json'); lm=load(o/'loader-variant-matrix.json'); la=load(o/'launcher-variant-matrix.json'); ex=load(o/'executable-discovery-matrix.json'); ne=load(o/'native-loader-evidence.json'); rr=load(o/'relocation-results.json'); diag=load(o/'ut2-gate-diagnostics.json'); cand=load(art/'selected-candidate.json')
 checks={}
 checks['loader_matrix_pass']=lm.get('pass') is True
 checks['gate_diagnostics_pass']=diag.get('pass') is True and all(diag.get('gate_condition',{}).values()) and lm.get('gate_condition')==diag.get('gate_condition')
 checks['lr4_pass']=lm.get('lr4',{}).get('pass') is True
 checks['selected_loader_consistent']=lm.get('selected_input_variant')==ne.get('selected_loader_variant')==cand.get('selected_loader')
 checks['selected_launcher_consistent']=la.get('selected')==ne.get('selected_launcher_variant')==cand.get('selected_launcher')
 checks['selected_launcher_variant_pass']=any(x.get('variant')==la.get('selected') and x.get('pass') is True for x in la.get('variants',[]))
 expected_launchers={'LA-0','LA-1','LA-2','LA-3','LR-0'}; built=lb.get('variants',{})
 checks['launcher_build_complete']=set(built)==expected_launchers
 checks['launcher_runpath_exact']=checks['launcher_build_complete'] and all(v.get('surface',{}).get('runpath')==['$ORIGIN/../lib'] and not v.get('surface',{}).get('rpath') for v in built.values())
 checks['launcher_normalization_exact']=checks['launcher_build_complete'] and all(v.get('runpath_normalization',{}).get('exact_normalization_check') is True for v in built.values())
 checks['patchelf_page_size_supported']=lb.get('patchelf_capabilities',{}).get('page_size_supported') is True and ne.get('patchelf_capabilities',{}).get('page_size_supported') is True
 checks['launcher_patchelf_page_size']=checks['launcher_build_complete'] and all((v.get('runpath_normalization',{}).get('action')=='none' or '--page-size' in (v.get('runpath_normalization',{}).get('command') or []) and '16384' in (v.get('runpath_normalization',{}).get('command') or [])) for v in built.values())
 checks['launcher_absolute_runpath_absent']=checks['launcher_build_complete'] and all(not any(x.startswith('/') for g in v.get('surface',{}).get('runpath',[]) for x in g.split(':')) for v in built.values())
 ec=lm.get('exit_condition',{})
 checks['ld_library_path_absent']=ec.get('project_required_LD_LIBRARY_PATH_absent') is True
 checks['self_reexec_absent']=ec.get('loader_bootstrap_self_reexec_absent') is True
 checks['internal_edges_zero']=ec.get('unresolved_internal_edges')==0
 checks['extension_failures_zero']=ec.get('required_extension_failures')==0
 checks['whole_prefix_relocation']=ec.get('whole_prefix_relocation_pass') is True and rr.get('whole_prefix_relocation_pass') is True
 checks['subprocess_reentry']=ec.get('subprocess_child_reentry_pass') is True and rr.get('subprocess_child_reentry_pass') is True
 checks['exact_mutations']=ne.get('all_exact_mutations') is True
 checks['alignment_preserved']=ne.get('all_alignment_preserved') is True
 checks['alignment_16k']=ne.get('all_16k_compatible') is True
 objs=ne.get('objects',[])
 checks['object_alignment_policy']=bool(objs) and all(x.get('alignment_policy',{}).get('preserved') is True for x in objs)
 mutated=[x for x in objs if x.get('mutated') is True]
 checks['mutated_patchelf_page_size']=all('--page-size' in (x.get('mutation_command') or []) and '16384' in (x.get('mutation_command') or []) for x in mutated)
 checks['android_api_compatible']=ne.get('device',{}).get('api_compatible') is True
 b=ne.get('bounded_bionic_checks',{})
 checks['origin_direct_lookup']=b.get('origin_direct_lookup') is True
 checks['transitive_lookup']=b.get('transitive_extension_lookup') is True
 checks['dlopen']=b.get('dlopen') is True
 required={'direct_real_path','relative_in_tree_symlink','absolute_in_tree_symlink','external_symlink','altered_argv0','copied_executable_without_prefix','venv_symlink_mode','venv_copy_mode','runtime_moved_before_fresh_venv_creation','pre_existing_venv_after_base_move','pre_existing_copy_venv_after_base_move','patch_level_base_replacement'}
 checks['discovery_matrix_complete']=required.issubset(set(ex.get('cases',{})))
 moved_symlink=ex.get('cases',{}).get('pre_existing_venv_after_base_move',{})
 ps=moved_symlink.get('path_state',{})
 ee=moved_symlink.get('execution_error',{})
 checks['moved_symlink_venv_boundary_recorded']=moved_symlink.get('pass') is False and moved_symlink.get('venv_mode')=='symlinks' and ps.get('lexists') is True and ps.get('exists') is False and ps.get('is_symlink') is True and ee.get('errno')==2
 moved_copy=ex.get('cases',{}).get('pre_existing_copy_venv_after_base_move',{})
 checks['moved_copy_venv_boundary_recorded']=moved_copy.get('venv_mode')=='copies' and isinstance(moved_copy.get('pass'),bool)
 checks['selected_launcher_present']=(art/'selected-launcher').is_file()
 checks['selected_launcher_hash']=checks['selected_launcher_present'] and sha(art/'selected-launcher')==cand.get('launcher_sha256')
 checks['candidate_unselectable']=cand.get('product_selectable') is False
 failed=[k for k,v in checks.items() if not v]
 result={'schema_version':1,'audit_kind':'e2-r1-ut2-loader-relocation-launcher-getpath','checks':checks,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'pass':not failed,'claim_boundary':'Bounded Android/Termux loader, launcher, getpath, and whole-prefix relocation evidence only; no device qualification, Epoch 3 product selection, or publication claim.'}
 dump(o/'independent-audit.json',result); print(json.dumps(result,indent=2,sort_keys=True)); return 0 if not failed else 1
if __name__=='__main__': raise SystemExit(main())
