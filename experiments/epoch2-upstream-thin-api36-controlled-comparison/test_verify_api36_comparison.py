#!/usr/bin/env python3
from __future__ import annotations
import argparse,contextlib,importlib.util,io,json,os,sys
from pathlib import Path
OUT=Path('experiments/epoch2-upstream-thin-api36-controlled-comparison')
def load(p:Path):return json.loads(p.read_text())
def dump(p:Path,o):
 tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');os.replace(tmp,p)
_VERIFIER_CACHE={}
def verify(root:Path)->bool:
 path=root/OUT/'verify_api36_comparison.py'
 key=str(path)
 module=_VERIFIER_CACHE.get(key)
 if module is None:
  spec=importlib.util.spec_from_file_location('api36_focused_verifier',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);_VERIFIER_CACHE[key]=module
 old_argv=sys.argv;sys.argv=[str(path),'--root',str(root)]
 try:
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return module.main()==0
 finally:
  sys.argv=old_argv
def mutate_json(rel:str,fn):
 def apply(root:Path):
  p=root/OUT/rel;d=load(p);fn(d);dump(p,d)
 return apply
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path.cwd());a=ap.parse_args();root=a.root.resolve();results=[]
 results.append({'name':'positive','pass':verify(root)})
 cases=[]
 def case(name,rel,fn):cases.append((name,OUT/rel,fn))
 case('class-b-representative-dependency-retention','control-class-b.json',mutate_json('control-class-b.json',lambda d:d['official_dependency_binary_comparison'][next(iter(d['official_dependency_binary_comparison']))].update(equal=False)))
 case('class-b-manifest-retention','control-class-b.json',mutate_json('control-class-b.json',lambda d:d['official_dependency_manifest_retention'].update({'pass':False})))
 case('class-b-asset-identity-drift','control-class-b.json',mutate_json('control-class-b.json',lambda d:(d['official_dependency_assets']['dependencies'][0].update(exact_identity=False),d['official_dependency_assets']['dependencies'][0]['asset'].update({'sha256':'0'*64,'exact_identity':False}))))
 case('class-b-builder-pin-drift','control-class-b.json',mutate_json('control-class-b.json',lambda d:d['official_dependency_assets']['builder_pin_contract'].update({'pass':False,'tag_counts':{}})))
 case('class-b-official-package-rebuild-surface-drift','control-class-b.json',mutate_json('control-class-b.json',lambda d:d['official_package_rebuild_surface'].update({'pass':False,'incomplete_dependency_names':[]})))
 case('class-c-source-tag-missing','control-class-c.json',mutate_json('control-class-c.json',lambda d:d['source_dependencies']['dependencies'].pop()))
 case('class-c-recipe-archive-identity-drift','control-class-c.json',mutate_json('control-class-c.json',lambda d:d['source_dependencies']['dependencies'][0]['recipe_archive'].update(exact_identity=False)))
 case('class-c-ndk-revision-drift','control-class-c.json',mutate_json('control-class-c.json',lambda d:d['source_dependencies']['dependencies'][0]['ndk_orchestration_patch'].update(effective_ndk_revision='27.2.12479018')))
 case('class-c-api-library-precedence-contract-drift','control-class-c.json',mutate_json('control-class-c.json',lambda d:d['source_dependencies']['dependencies'][0]['ndk_orchestration_patch']['api_library_precedence_patch'].update({'mode':'line-anchor-replacement','script_end_block':False,'shell_syntax_pass':False})))
 case('class-c-prepopulation-flow-drift','control-class-c.json',mutate_json('control-class-c.json',lambda d:d['build']['dependency_prepopulation_contract'].update(source_patch_applied=True)))
 case('class-c-host-isolation-drift','control-class-c.json',mutate_json('control-class-c.json',lambda d:d['source_dependencies'].update(source_dependency_host_isolation_complete=False)))
 case('class-c-libffi-configure-fallback-drift','control-class-c.json',mutate_json('control-class-c.json',lambda d:(d['source_dependencies'].update(libffi_android_configure_fallback_complete=False),next(x for x in d['source_dependencies']['dependencies'] if x['name']=='libffi')['libffi_android_configure_fallback_patch'].update({'pass':False,'forced_cache_values':{}}))))
 case('class-c-libffi-mkstemp-probe-drift','control-class-c.json',mutate_json('control-class-c.json',lambda d:d['source_dependencies']['libffi_android_configure_fallback_probe'].update({'pass':False,'output_exists':False})))
 case('class-c-bzip2-static-archive-drift','control-class-c.json',mutate_json('control-class-c.json',lambda d:next(x for x in d['source_dependencies']['dependencies'] if x['name']=='bzip2')['artifact_closure'].update({'pass':False,'static_archive_pass':False,'static_archive_count':0,'static_object_count':0,'static_archives':[]})))
 case('class-c-sqlite-host-zlib-drift','control-class-c.json',mutate_json('control-class-c.json',lambda d:next(x for x in d['source_dependencies']['dependencies'] if x['name']=='sqlite')['artifact_closure'].update(sqlite_android_zlib_closure=False,forbidden_needed=[{'needed':'libz.so.1'}])))
 case('ndk-target-wrapper-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['ndk_identity'].update(target_macro_api=35)))
 case('ndk-api36-link-capability-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['ndk_identity']['api36_link_probe'].update({'pass':False})))
 case('ndk-api36-crt-inventory-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['ndk_identity']['api36_crt_inventory'].update({'complete':False})))
 case('ndk-system-library-closure-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['ndk_identity']['api36_system_library_probe'].update({'pass':False,'needed':['libz.so.1']})))
 case('ndk-driver-contract-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['ndk_identity']['driver_contract'].update({'pass':False})))
 case('ndk-host-path-argument-filter-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['ndk_identity']['driver_contract']['host_path_argument_filter'].update({'enabled':False,'forbidden_library_paths':[]})))
 case('ndk-host-path-absolute-filter-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['ndk_identity']['driver_contract']['host_path_argument_filter'].update({'raw_absolute_host_paths_filtered':False})))
 case('ndk-host-path-colon-filter-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['ndk_identity']['driver_contract']['host_path_argument_filter'].update({'colon_separated_rpath_lists_filtered':False})))
 case('ndk-selection-policy-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['ndk_identity'].update({'selection_policy':'downloaded-fallback'})))
 case('ndk-platform-max-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['ndk_identity']['platform_metadata'].update({'max':35,'supports_api36':False})))
 case('ndk-prerelease-channel-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['ndk_identity'].update({'release_channel':'stable','prerelease':False})))
 case('class-b-cpython-ndk-revision-drift','control-class-b.json',mutate_json('control-class-b.json',lambda d:d['build']['android_ndk_revision_patch'].update(effective_ndk_revision='0.0.0')))
 case('build-python-bootstrap-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['build_python_bootstrap'].update(version='3.14.5')))
 case('build-python-host-platform-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d['build_python_bootstrap'].update(platform='darwin')))
 case('host-environment-capture-drift','provenance-and-build-burden.json',mutate_json('provenance-and-build-burden.json',lambda d:d.update(host_environment_capture_normalization_complete=False)))
 case('host-environment-capture-anchor-drift','control-class-b.json',mutate_json('control-class-b.json',lambda d:d['build']['host_environment_capture_patch'].update(anchor_scope='unbounded-global')))
 case('unenumerated-additional-delta','controlled-delta-inventory.json',mutate_json('controlled-delta-inventory.json',lambda d:d.update(all_deltas_enumerated=False)))
 case('epoch3-selection','controlled-delta-inventory.json',mutate_json('controlled-delta-inventory.json',lambda d:d.update(epoch3_selection=True,product_decision='select-B')))
 case('gate-non-boolean','api36-gate-diagnostics.json',mutate_json('api36-gate-diagnostics.json',lambda d:d['gate_condition'].__setitem__('no_epoch3_selection',['truthy-not-bool'])))
 case('authority-missing','api36-controlled-comparison-authority.json',lambda r:(r/OUT/'api36-controlled-comparison-authority.json').unlink())
 case('binary-committed','forbidden.so',lambda r:(r/OUT/'forbidden.so').write_bytes(b'\x7fELF'))
 for name,rel,mut in cases:
  print(f'negative-case={name}',file=sys.stderr,flush=True)
  path=root/rel;existed=path.exists();before=path.read_bytes() if existed else None;mode=path.stat().st_mode if existed else None
  try:
   mut(root);results.append({'name':name,'pass':not verify(root)})
  finally:
   if existed:
    path.write_bytes(before);os.chmod(path,mode)
   elif path.exists():
    path.unlink()
 out={'schema_version':2,'test_kind':'api36-verifier-regression','execution_model':'in-place-single-file-mutation-with-finally-restore','case_count':len(results),'pass_count':sum(x['pass'] for x in results),'cases':results,'pass':all(x['pass'] for x in results)};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
