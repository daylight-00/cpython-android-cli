#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, io, json, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path

OUTPUT='experiments/epoch2-upstream-thin-loader-relocation'
SCRIPTS=['launcher_la0_pyconfig.c','launcher_la1_bytesmain.c','launcher_la2_programs_python.c','launcher_la3_android_signal.c','launcher_lr0_self_reexec.c','run_loader_relocation_experiment.py','audit_loader_relocation.py','verify_loader_relocation.py','test_verify_loader_relocation.py','finalize_loader_relocation.py','run-ut2-loader-relocation-launcher-getpath.sh']
CASES=['direct_real_path','relative_in_tree_symlink','absolute_in_tree_symlink','external_symlink','altered_argv0','copied_executable_without_prefix','venv_symlink_mode','venv_copy_mode','runtime_moved_before_fresh_venv_creation','pre_existing_venv_after_base_move','pre_existing_copy_venv_after_base_move','patch_level_base_replacement']

def dump(p:Path,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def sha(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd):return subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def copy_predecessor_head(source_root:Path,root:Path)->None:
 root.mkdir(parents=True,exist_ok=False)
 p=subprocess.run(['git','-C',str(source_root),'archive','--format=tar','HEAD'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode!=0:
  raise RuntimeError(f'hermetic predecessor archive failed: {p.stderr.decode(errors="replace").strip()}')
 with tarfile.open(fileobj=io.BytesIO(p.stdout),mode='r:') as tf:
  for member in tf.getmembers():
   parts=Path(member.name).parts
   if member.name.startswith('/') or '..' in parts:
    raise RuntimeError(f'unsafe predecessor archive member: {member.name}')
  tf.extractall(root,filter='fully_trusted')
 if not any(root.iterdir()):
  raise RuntimeError('hermetic predecessor archive is empty')

def fixture(source_root:Path, sibling:Path, base:Path)->tuple[Path,Path]:
 root=base/'repo';copy_predecessor_head(source_root,root)
 out=root/OUTPUT;out.mkdir(parents=True,exist_ok=True)
 for n in SCRIPTS:shutil.copy2(sibling/n,out/n)
 art=base/'artifacts';art.mkdir();(art/'selected-launcher').write_bytes(b'\x7fELFsynthetic-selected-launcher')
 exit_condition={'project_required_LD_LIBRARY_PATH_absent':True,'loader_bootstrap_self_reexec_absent':True,'unresolved_internal_edges':0,'required_extension_failures':0,'whole_prefix_relocation_pass':True,'subprocess_child_reentry_pass':True}
 gate_condition={'project_required_LD_LIBRARY_PATH_absent':True,'loader_bootstrap_self_reexec_absent':True,'unresolved_internal_edges_zero':True,'required_extension_failures_zero':True,'whole_prefix_relocation_pass':True,'subprocess_child_reentry_pass':True,'all_exact_mutations':True,'all_alignment_preserved':True,'all_16k_compatible':True,'android_api_compatible':True}
 cand={'schema_version':1,'selected_loader':'LR-3','selected_launcher':'LA-2','launcher_sha256':sha(art/'selected-launcher'),'exit_condition':exit_condition,'gate_condition':gate_condition,'product_selectable':False};dump(art/'selected-candidate.json',cand)
 probe={'startup_pass':True,'required_extension_failures':0,'dlopen_pass':True,'child_reentry_pass':True,'ld_library_path_absent':True,'self_reexec_absent':True,'data':{},'returncode':0,'stdout':'','stderr':'','command':[]}
 dump(out/'official-extraction-verification.json',{'schema_version':1,'prefix_verification':{'pass':True}})
 launchers={k:{'surface':{'runpath':['$ORIGIN/../lib'],'rpath':[]},'runpath_normalization':{'action':'none','command':None,'exact_normalization_check':True,'alignment_policy':{'preserved':True},'classification':{'requires_normalization':False,'toolchain_default_entries':[]}}} for k in ('LA-0','LA-1','LA-2','LA-3','LR-0')}
 dump(out/'launcher-build-evidence.json',{'schema_version':1,'patchelf_capabilities':{'page_size_supported':True},'variants':launchers})
 dump(out/'loader-variant-matrix.json',{'schema_version':1,'variants':[],'selected_input_variant':'LR-3','lr4':{'pass':True,'probe':probe,'selected_from':'LR-3','launcher':'LA-2'},'exit_condition':exit_condition,'gate_condition':gate_condition,'pass':True})
 dump(out/'launcher-variant-matrix.json',{'schema_version':1,'variants':[{'variant':'LA-2','pass':True}],'selected':'LA-2','selection_order':['LA-2','LA-1','LA-0','LA-3']})
 cases={k:{'pass':k not in {'copied_executable_without_prefix','venv_copy_mode','pre_existing_venv_after_base_move','pre_existing_copy_venv_after_base_move'}} for k in CASES}
 cases['pre_existing_venv_after_base_move']={'pass':False,'venv_mode':'symlinks','path_state':{'lexists':True,'exists':False,'is_symlink':True,'symlink_target':'/old/prefix/bin/python3.14','resolved_target':'/old/prefix/bin/python3.14'},'execution_error':{'type':'FileNotFoundError','errno':2,'message':'missing','filename':'venv/bin/python'}}
 cases['pre_existing_copy_venv_after_base_move']={'pass':False,'venv_mode':'copies','path_state':{'lexists':True,'exists':True,'is_symlink':False,'symlink_target':None,'resolved_target':'venv-copy/bin/python'},'returncode':1}
 dump(out/'executable-discovery-matrix.json',{'schema_version':1,'cases':cases,'supported_boundary':{k:bool(v.get('pass')) for k,v in cases.items()}})
 object_row={'path':'prefix/lib/python3.14/lib-dynload/_ssl.cpython-314-aarch64-linux-android.so','mutated':True,'mutation_command':['patchelf','--page-size','16384','--set-rpath','$ORIGIN/../../..','x.so'],'alignment_policy':{'before_load_count':3,'after_load_count':4,'before_all_16k':True,'after_all_16k':True,'load_count_not_reduced':True,'preserved':True},'alignment_preserved':True,'alignment_16k_compatible':True,'exact_mutation_check':True}
 dump(out/'native-loader-evidence.json',{'schema_version':1,'selected_loader_variant':'LR-3','selected_launcher_variant':'LA-2','patchelf_capabilities':{'page_size_supported':True},'device':{'android_api':35,'minimum_package_api':24,'api_compatible':True,'api_probe':{'parsed_android_api':35},'uname':'synthetic','execution_context':'synthetic Termux'},'transformed_elf_count':1,'all_exact_mutations':True,'all_alignment_preserved':True,'all_16k_compatible':True,'alignment_policy':'synthetic','bounded_bionic_checks':{'origin_direct_lookup':True,'transitive_extension_lookup':True,'dlopen':True,'minimum_api':True,'modern_linker_namespace':True},'objects':[object_row]})
 dump(out/'relocation-results.json',{'schema_version':1,'whole_prefix_relocation_pass':True,'subprocess_child_reentry_pass':True,'exit_condition':exit_condition,'gate_condition':gate_condition})
 dump(out/'ut2-gate-diagnostics.json',{'schema_version':1,'pass':True,'exit_condition':exit_condition,'gate_condition':gate_condition,'failed_gate_conditions':[]})
 checks={f'c{i}':True for i in range(23)};dump(out/'independent-audit.json',{'schema_version':1,'checks':checks,'check_count':23,'pass_count':23,'failed_checks':[],'pass':True})
 return root,art

def finalize(root:Path,art:Path,sibling:Path):
 return run([sys.executable,str(sibling/'finalize_loader_relocation.py'),'--root',str(root),'--artifact-dir',str(art),'--predecessor-head','ffdc2ebe65cf2e11a74c08bbdaab5cba1a54351f','--predecessor-tree','bec2af6ce3894d34b109cf5ea532364843404c15'])
def verify(root:Path,art:Path,sibling:Path):return run([sys.executable,str(sibling/'verify_loader_relocation.py'),'--root',str(root),'--artifact-dir',str(art)])

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();source=a.root.resolve();sibling=Path(__file__).resolve().parent
 results={}
 spec=importlib.util.spec_from_file_location('ut2_experiment',sibling/'run_loader_relocation_experiment.py');mod=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(mod)
 compiler='/data/data/com.termux/files/usr/bin/clang';desired='$ORIGIN/../lib'
 exact=mod.classify_launcher_runpath([desired],desired,compiler)
 injected=mod.classify_launcher_runpath(['/data/data/com.termux/files/usr/bin/../../usr/lib:'+desired],desired,compiler)
 rejected=[]
 for bad in (['/unexpected/lib:'+desired],[desired+':$ORIGIN/else'],['/data/data/com.termux/files/usr/lib']):
  try:mod.classify_launcher_runpath(bad,desired,compiler)
  except ValueError:rejected.append(True)
  else:rejected.append(False)
 results['runpath_classifier']={'exact_noop':exact['requires_normalization'] is False,'termux_default_detected':injected['requires_normalization'] is True and injected['toolchain_default_entries']==['/data/data/com.termux/files/usr/bin/../../usr/lib'],'unexpected_rejected':all(rejected)}
 align_exact=mod.alignment_policy([0x4000,0x4000,0x4000],[0x4000,0x4000,0x4000])
 align_added=mod.alignment_policy([0x4000,0x4000,0x4000],[0x4000,0x4000,0x4000,0x4000])
 align_bad=mod.alignment_policy([0x4000,0x4000,0x4000],[0x4000,0x4000,0x1000,0x4000])
 align_dropped=mod.alignment_policy([0x4000,0x4000,0x4000],[0x4000,0x4000])
 pcmd=mod.patchelf_set_runpath_command('patchelf','$ORIGIN/../lib',Path('/tmp/x'))
 results['alignment_policy']={'exact':align_exact['preserved'] is True,'added_16k_segment':align_added['preserved'] is True,'four_k_rejected':align_bad['preserved'] is False,'load_drop_rejected':align_dropped['preserved'] is False,'page_size_command':pcmd[:3]==['patchelf','--page-size','16384']}
 with tempfile.TemporaryDirectory(prefix='ut2-dangling-venv-test-') as dd:
  base=Path(dd);missing=base/'old-prefix'/'bin'/'python3.14';link=base/'venv'/'bin'/'python';link.parent.mkdir(parents=True);link.symlink_to(missing)
  observed=mod.execute_getpath(link,base/'moved-prefix',base,record_exec_error=True)
  results['dangling_symlink_boundary']={'pass_false':observed.get('pass') is False,'errno_2':observed.get('execution_error',{}).get('errno')==2,'lexists':observed.get('path_state',{}).get('lexists') is True,'exists_false':observed.get('path_state',{}).get('exists') is False,'is_symlink':observed.get('path_state',{}).get('is_symlink') is True}
 with tempfile.TemporaryDirectory(prefix='ut2-verify-test-') as td:
  base=Path(td)
  r,art=fixture(source,sibling,base/'positive');f=finalize(r,art,sibling);v=verify(r,art,sibling);results['positive']={'finalize_rc':f.returncode,'verify_rc':v.returncode,'stdout':v.stdout[-2000:],'stderr':v.stderr[-1000:]}
  r2,art2=fixture(source,sibling,base/'negative');f2=finalize(r2,art2,sibling);lm=json.loads((r2/OUTPUT/'loader-variant-matrix.json').read_text());lm['exit_condition']['unresolved_internal_edges']=1;dump(r2/OUTPUT/'loader-variant-matrix.json',lm);v2=verify(r2,art2,sibling);results['negative']={'finalize_rc':f2.returncode,'verify_rc':v2.returncode}
  r3,art3=fixture(source,sibling,base/'missing');f3=finalize(r3,art3,sibling);(r3/OUTPUT/'native-loader-evidence.json').unlink();v3=verify(r3,art3,sibling);results['missing']={'finalize_rc':f3.returncode,'verify_rc':v3.returncode}
 ok=all(results['runpath_classifier'].values()) and all(results['alignment_policy'].values()) and all(results['dangling_symlink_boundary'].values()) and results['positive']['finalize_rc']==0 and results['positive']['verify_rc']==0 and results['negative']['verify_rc']!=0 and results['missing']['verify_rc']!=0
 print(json.dumps({'pass':ok,'results':results},indent=2,sort_keys=True));return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
