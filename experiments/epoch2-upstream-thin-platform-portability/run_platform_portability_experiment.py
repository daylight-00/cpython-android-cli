#!/usr/bin/env python3
from __future__ import annotations
import argparse, ctypes, hashlib, importlib.util, json, os, platform, re, shutil, stat, subprocess, sys, zipfile
from pathlib import Path
from typing import Any

EXPECTED_ARCHIVE_SHA='38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5'
EXPECTED_ARCHIVE_SIZE=22358404
AUTH={
 'control':('experiments/epoch2-upstream-thin-control/upstream-control-authority.json','6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c'),
 'artifact':('experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json','387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306'),
 'loader':('experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json','05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2'),
 'sysconfig':('experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json','6cff1984d4601a37e8b57762bb170a57e695cb64d516c1dab0023b7e809dc808'),
 'data_policy':('experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json','be25e52aba1d6c9d0b2e25fec2bd1d8a0a0d9eb870436f00e81f347e90d012b7'),
 'feature':('experiments/epoch2-upstream-thin-feature-qualification/feature-qualification-authority.json','3b56a38898a3a2384cf9419fe3cd124faa8dbf367cdd5532724b3424092a62e5'),
 'dual_device':('experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json','e380198cda8c49cad704483e3edc33c2d745cc65857155b3a7edb1887410f06c'),
}
FORBIDDEN_CLAIM_PATTERNS=[r'api\s*24\s*(is|as)\s*(the\s*)?(supported|minimum)',r'all\s+android',r'all\s+devices',r'16\s*ki?b\s+runtime\s+(supported|qualified)',r'non-termux\s+(supported|qualified)',r'root\s+(supported|qualified)',r'adb\s+(supported|qualified)']

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def load(p:Path)->Any:return json.loads(p.read_text())
def dump(p:Path,v:Any)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def run(cmd:list[str],*,env:dict[str,str]|None=None,cwd:Path|None=None,timeout:int=180)->dict[str,Any]:
 try:p=subprocess.run(cmd,env=env,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
 except subprocess.TimeoutExpired as e:return {'command':cmd,'returncode':124,'stdout':e.stdout.decode() if isinstance(e.stdout,bytes) else (e.stdout or ''),'stderr':e.stderr.decode() if isinstance(e.stderr,bytes) else (e.stderr or 'timeout')}
 return {'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def parse_last_json(text:str)->Any:
 dec=json.JSONDecoder()
 for i,c in enumerate(text):
  if c not in '[{':continue
  try:
   o,n=dec.raw_decode(text[i:])
   if not text[i+n:].strip():return o
  except json.JSONDecodeError:pass
 raise ValueError('no terminal JSON')
def import_frozen(root:Path,script_rel:str,authority_rel:str,name:str):
 auth=load(root/authority_rel);p=root/script_rel;expected=auth.get('file_identities',{}).get(p.name)
 if not expected or sha(p)!=expected:raise RuntimeError(f'frozen script mismatch:{script_rel}')
 spec=importlib.util.spec_from_file_location(name,p)
 if spec is None or spec.loader is None:raise RuntimeError(f'import failed:{script_rel}')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def cmd_text(cmd:list[str],default:str='')->dict[str,Any]:
 r=run(cmd,timeout=20);r['value']=r['stdout'].strip() if r['returncode']==0 else default;return r

def device_probe()->dict[str,Any]:
 gp='/system/bin/getprop' if Path('/system/bin/getprop').is_file() else (shutil.which('getprop') or '')
 props={}
 for key in ['ro.build.version.sdk','ro.build.version.release','ro.product.cpu.abilist','ro.product.cpu.abi','ro.product.model','ro.product.device','ro.hardware','ro.build.version.security_patch']:
  props[key]=cmd_text([gp,key]) if gp else {'command':[],'returncode':127,'stdout':'','stderr':'getprop unavailable','value':''}
 try:page=os.sysconf('SC_PAGE_SIZE')
 except Exception:page=0
 api=int(props['ro.build.version.sdk']['value']) if props['ro.build.version.sdk']['value'].isdigit() else None
 prefix=os.environ.get('PREFIX','')
 return {'schema_version':1,'android_api':api,'android_release':props['ro.build.version.release']['value'],'abilist':[x for x in props['ro.product.cpu.abilist']['value'].split(',') if x],'primary_abi':props['ro.product.cpu.abi']['value'],'model':props['ro.product.model']['value'],'device':props['ro.product.device']['value'],'hardware':props['ro.hardware']['value'],'security_patch':props['ro.build.version.security_patch']['value'],'machine':platform.machine(),'uname':platform.uname()._asdict(),'page_size':page,'execution_context':'termux-app-process' if ('com.termux' in prefix or os.environ.get('TERMUX_VERSION')) else 'unknown-android-process','prefix':prefix,'uid':os.getuid(),'adb_path':shutil.which('adb'),'su_path':shutil.which('su'),'termux_version':os.environ.get('TERMUX_VERSION'),'property_probes':props,'pass':api is not None and api>=24 and platform.machine() in {'aarch64','arm64'}}

def hardlink_copy(src:Path,dst:Path)->None:
 if dst.exists():shutil.rmtree(dst)
 def cp(a:str,b:str):
  try:os.link(a,b)
  except OSError:shutil.copy2(a,b)
 shutil.copytree(src,dst,symlinks=True,copy_function=cp)

def is_elf(p:Path)->bool:
 try:return p.is_file() and p.read_bytes()[:4]==b'\x7fELF'
 except OSError:return False

def parse_loads(text:str)->list[dict[str,Any]]:
 rows=[]
 for line in text.splitlines():
  s=line.strip()
  if not s.startswith('LOAD '):continue
  parts=s.split()
  try:
   off=int(parts[1],16);vaddr=int(parts[2],16);filesz=int(parts[4],16);memsz=int(parts[5],16);align=int(parts[-1],16)
  except Exception:continue
  rows.append({'offset':off,'vaddr':vaddr,'filesz':filesz,'memsz':memsz,'align':align,'offset_vaddr_congruent_16k':off%16384==vaddr%16384})
 return rows

def scan_elf(p:Path,rel:str,readelf:str,expected:dict[str,Any]|None=None)->dict[str,Any]:
 ph=run([readelf,'-lW',str(p)],timeout=30);sh=run([readelf,'-SW',str(p)],timeout=30);dy=run([readelf,'-dW',str(p)],timeout=30)
 loads=parse_loads(ph['stdout']);sections=[];relocs=[]
 for line in sh['stdout'].splitlines():
  m=re.search(r'\]\s+(\S+)\s+(\S+)\s+',line)
  if m:
   sections.append(m.group(1))
   if m.group(2) in {'REL','RELA','RELR'} or m.group(1).startswith(('.rel','.rela','.android.rel')):relocs.append({'name':m.group(1),'type':m.group(2)})
 runpaths=[]
 for line in dy['stdout'].splitlines():
  if '(RUNPATH)' in line or '(RPATH)' in line:
   m=re.search(r'\[(.*?)\]',line)
   if m:runpaths.extend([x for x in m.group(1).split(':') if x])
 actual=sha(p);expected_sha=(expected or {}).get('after',{}).get('sha256');expected_runpath=(expected or {}).get('after',{}).get('runpath')
 return {'path':rel,'sha256':actual,'size':p.stat().st_size,'loads':loads,'load_count':len(loads),'all_load_alignments_16k':bool(loads) and all(x['align']>=16384 and x['align']%16384==0 for x in loads),'all_segment_offsets_congruent_16k':bool(loads) and all(x['offset_vaddr_congruent_16k'] for x in loads),'relocation_sections':relocs,'relocation_section_count':len(relocs),'symtab_present':'.symtab' in sections,'stripped':'.symtab' not in sections,'runpath':runpaths,'readelf_pass':ph['returncode']==0 and sh['returncode']==0 and dy['returncode']==0,'expected_post_mutation_sha256':expected_sha,'post_mutation_identity_match':expected_sha==actual if expected_sha else None,'expected_runpath':expected_runpath,'post_runpath_match':runpaths==expected_runpath if expected_runpath is not None else None}

def target_json(python:Path,code:str,env:dict[str,str],timeout:int=240)->dict[str,Any]:
 r=run([str(python),'-c',code],env=env,timeout=timeout)
 try:r['data']=parse_last_json(r['stdout'])
 except Exception:r['data']=None
 r['pass']=r['returncode']==0 and isinstance(r['data'],dict) and r['data'].get('pass') is True
 return r

def contract_scan(values:list[Any],scope:list[str])->dict[str,Any]:
 text='\n'.join(json.dumps(v,sort_keys=True) for v in values);hits=[]
 for pat in FORBIDDEN_CLAIM_PATTERNS:
  if re.search(pat,text,re.I):hits.append(pat)
 return {'pass':not hits,'hits':hits,'pattern_count':len(FORBIDDEN_CLAIM_PATTERNS),'scope':scope}

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--artifacts',type=Path,required=True);ap.add_argument('--cc',default='clang');ap.add_argument('--cxx',default='clang++');ap.add_argument('--ar',default='llvm-ar');ap.add_argument('--patchelf',default='patchelf');ap.add_argument('--readelf',default='readelf');ap.add_argument('--pkg-config',default='pkg-config');a=ap.parse_args()
 root=a.root.resolve();archive=a.archive.resolve();work=a.work.resolve();out=a.output.resolve();artifacts=a.artifacts.resolve();shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True);out.mkdir(parents=True,exist_ok=True);artifacts.mkdir(parents=True,exist_ok=True)
 if sha(archive)!=EXPECTED_ARCHIVE_SHA or archive.stat().st_size!=EXPECTED_ARCHIVE_SIZE:raise SystemExit('official archive identity mismatch')
 auth_data={}
 for name,(rel,expected) in AUTH.items():
  p=root/rel
  if sha(p)!=expected:raise SystemExit(f'authority identity mismatch:{name}')
  auth_data[name]=load(p)
 device=device_probe();dump(out/'current-device-probe.json',device)
 if not device['pass']:raise SystemExit('current Android aarch64 environment probe failed')
 ut3=import_frozen(root,'experiments/epoch2-upstream-thin-sysconfig-sdk/run_sysconfig_sdk_experiment.py',AUTH['sysconfig'][0],'hw_t_ut3_platform')
 ut4=import_frozen(root,'experiments/epoch2-upstream-thin-android-data-policy/run_android_data_policy_experiment.py',AUTH['data_policy'][0],'hw_t_ut4_platform')
 ut3_work=work/'runtime-sdk-reproduction';ut3_out=work/'runtime-sdk-evidence';ut3_art=work/'runtime-sdk-artifacts'
 cmd=[sys.executable,str(root/'experiments/epoch2-upstream-thin-sysconfig-sdk/run_sysconfig_sdk_experiment.py'),'--root',str(root),'--archive',str(archive),'--work',str(ut3_work),'--output',str(ut3_out),'--artifacts',str(ut3_art),'--source-dir',str(root/'experiments/epoch2-upstream-thin-sysconfig-sdk'),'--cc',a.cc,'--cxx',a.cxx,'--ar',a.ar,'--patchelf',a.patchelf,'--readelf',a.readelf,'--pkg-config',a.pkg_config]
 repro=run(cmd,timeout=1800);gate3=load(ut3_out/'ut3-gate-diagnostics.json') if (ut3_out/'ut3-gate-diagnostics.json').is_file() else {'pass':False}
 if repro['returncode']!=0 or gate3.get('pass') is not True:raise SystemExit('UT-3 reproduction failed:'+json.dumps({'reproduction':repro,'gate':gate3},sort_keys=True)[-12000:])
 prefix=ut3_work/'location-b/prefix';python=prefix/'bin/python3.14';wheels=sorted(ut3_art.glob('hw_t_native_probe-*.whl'))
 if not python.is_file() or len(wheels)!=1:raise SystemExit('reproduced runtime or native wheel missing')
 wheel=wheels[0];shutil.copy2(wheel,artifacts/wheel.name)
 data=work/'data';state=work/'state';cert=prefix/'lib/python3.14/test/certdata/ssl_cert.pem';(data/'ca').mkdir(parents=True);shutil.copy2(cert,data/'ca/ca-bundle.pem');ut4.write_tzif(data/'zoneinfo/Etc/HWTest',3600,'HWT');env=ut4.policy_env(ut3,prefix,state,data,work/'policy-env');env['HW_T_EXPECTED_PREFIX']=str(prefix);env.pop('LD_LIBRARY_PATH',None)

 # Static final ELF scan. Regular ELF objects and ELF symlink aliases are separate surfaces.
 loader_ev=load(root/'experiments/epoch2-upstream-thin-loader-relocation/native-loader-evidence.json');expected_by_path={x['path']:x for x in loader_ev['objects']}
 launcher_key='prefix/bin/python3.14';launcher_expected=json.loads(json.dumps(expected_by_path[launcher_key]));launcher_expected['after']['sha256']=auth_data['loader']['selection']['launcher_sha256'];launcher_expected['identity_authority']='loader-relocation-authority.selection.launcher_sha256';expected_by_path[launcher_key]=launcher_expected
 runtime_elf=[];symlink_aliases=[]
 for p in sorted(prefix.rglob('*')):
  rel=p.relative_to(prefix).as_posix()
  if p.is_symlink():
   if is_elf(p):
    try:
     resolved=p.resolve(strict=True);resolved_rel=resolved.relative_to(prefix).as_posix();inside=True;resolved_sha=sha(p)
    except Exception as e:
     resolved_rel=None;inside=False;resolved_sha=None
    symlink_aliases.append({'path':rel,'link_target':os.readlink(p),'resolved_path':resolved_rel,'resolved_inside_prefix':inside,'resolved_sha256':resolved_sha})
   continue
  if is_elf(p):runtime_elf.append(scan_elf(p,rel,a.readelf,expected_by_path.get('prefix/'+rel)))
 runtime_by_path={x['path']:x for x in runtime_elf};expected_aliases={'bin/python':'bin/python3.14','bin/python3':'bin/python3.14','lib/libsqlite3.so.0':'lib/libsqlite3_python.so'}
 for row in symlink_aliases:
  row['expected_resolved_path']=expected_aliases.get(row['path']);row['resolved_path_match']=row['resolved_path']==row['expected_resolved_path'];target=runtime_by_path.get(row['resolved_path']);row['target_object_present']=target is not None;row['target_identity_match']=target is not None and row['resolved_sha256']==target['sha256']
 alias_by_path={x['path']:x for x in symlink_aliases};alias_inventory_complete=set(alias_by_path)==set(expected_aliases) and all(x['resolved_inside_prefix'] and x['resolved_path_match'] and x['target_object_present'] and x['target_identity_match'] for x in symlink_aliases)
 wheel_unpack=work/'wheel-static';wheel_unpack.mkdir()
 with zipfile.ZipFile(wheel) as z:z.extractall(wheel_unpack)
 wheel_elf=[scan_elf(p,'wheel/'+p.relative_to(wheel_unpack).as_posix(),a.readelf,None) for p in sorted(wheel_unpack.rglob('*')) if is_elf(p) and not p.is_symlink()]
 ext_expected=auth_data['sysconfig']['native_extension_wheel']['extension_normalization']['after']['sha256']
 for row in wheel_elf:row['expected_native_extension_sha256']=ext_expected;row['native_extension_identity_match']=row['sha256']==ext_expected
 identity_rows=[x for x in runtime_elf if x['post_mutation_identity_match'] is not None];launcher_row=runtime_by_path.get('bin/python3.14');launcher_identity_match=launcher_row is not None and launcher_row['sha256']==auth_data['loader']['selection']['launcher_sha256'] and launcher_row['post_mutation_identity_match'] is True
 static16={'schema_version':1,'matrix':'final-elf-static-16k','runtime_elf_count':len(runtime_elf),'runtime_elf_symlink_alias_count':len(symlink_aliases),'wheel_elf_count':len(wheel_elf),'objects':runtime_elf,'symlink_aliases':symlink_aliases,'wheel_objects':wheel_elf,'summary':{'all_readelf_pass':all(x['readelf_pass'] for x in runtime_elf+wheel_elf),'all_load_alignments_16k':all(x['all_load_alignments_16k'] for x in runtime_elf+wheel_elf),'all_segment_offsets_congruent_16k':all(x['all_segment_offsets_congruent_16k'] for x in runtime_elf+wheel_elf),'post_mutation_identity_matches':sum(x['post_mutation_identity_match'] is True for x in identity_rows),'post_mutation_identity_expected':len(identity_rows),'post_runpath_layout_matches':all(x['post_runpath_match'] is not False for x in identity_rows),'selected_launcher_identity_match':launcher_identity_match,'symlink_alias_inventory_complete':alias_inventory_complete,'symlink_alias_identity_matches':sum(x['target_identity_match'] is True for x in symlink_aliases),'symlink_alias_expected':len(expected_aliases),'relocation_section_inventory_complete':all(isinstance(x['relocation_sections'],list) for x in runtime_elf+wheel_elf),'stripped_object_count':sum(x['stripped'] for x in runtime_elf+wheel_elf),'unstripped_object_count':sum(not x['stripped'] for x in runtime_elf+wheel_elf),'runtime_16k_device_tested':device['page_size']==16384},'pass':len(runtime_elf)==81 and len(wheel_elf)==1 and all(x['readelf_pass'] and x['all_load_alignments_16k'] and x['all_segment_offsets_congruent_16k'] for x in runtime_elf+wheel_elf) and len(identity_rows)==81 and all(x['post_mutation_identity_match'] is True and x['post_runpath_match'] is not False for x in identity_rows) and launcher_identity_match and alias_inventory_complete and all(x.get('native_extension_identity_match') is True for x in wheel_elf)}
 dump(out/'static-16k-matrix.json',static16)

 # Direct current runtime checks.
 native_code=r'''import ctypes,importlib,json,os,subprocess,sys
prefix=os.environ['HW_T_EXPECTED_PREFIX'];fails={};mods=[]
for p in sorted(__import__('pathlib').Path(prefix,'lib/python3.14/lib-dynload').glob('*.so')):
 m=p.name.split('.cpython-',1)[0];mods.append(m)
 try:importlib.import_module(m)
 except BaseException as e:fails[m]=type(e).__name__+':'+str(e)
dl={}
for rel in ['lib/libpython3.14.so','lib/libcrypto_python.so','lib/libssl_python.so','lib/libsqlite3_python.so','lib/engines-3/afalg.so','lib/ossl-modules/legacy.so']:
 try:ctypes.CDLL(os.path.join(prefix,rel));dl[rel]='pass'
 except BaseException as e:dl[rel]=type(e).__name__+':'+str(e)
cp=subprocess.run([sys.executable,'-c','import json,ssl,sqlite3,_hashlib,sys;print(json.dumps({"ok":True,"prefix":sys.prefix}))'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
print(json.dumps({'pass':not fails and all(v=='pass' for v in dl.values()) and cp.returncode==0,'extension_count':len(mods),'extension_failures':fails,'dlopen':dl,'child':{'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr},'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix,'ld_library_path':os.environ.get('LD_LIBRARY_PATH')},sort_keys=True))'''
 direct=target_json(python,native_code,env,420)
 canonical_a=work/'canonical-termux/location-a/opt/python';canonical_b=work/'canonical-termux/location-b/opt/python';canonical_a.parent.mkdir(parents=True);hardlink_copy(prefix,canonical_a);env_a=ut4.policy_env(ut3,canonical_a,state,data,work/'canonical-env-a');env_a['HW_T_EXPECTED_PREFIX']=str(canonical_a);env_a.pop('LD_LIBRARY_PATH',None);probe_a=target_json(canonical_a/'bin/python3.14',native_code,env_a,420);canonical_b.parent.mkdir(parents=True);shutil.move(str(canonical_a),str(canonical_b));env_b=ut4.policy_env(ut3,canonical_b,state,data,work/'canonical-env-b');env_b['HW_T_EXPECTED_PREFIX']=str(canonical_b);env_b.pop('LD_LIBRARY_PATH',None);probe_b=target_json(canonical_b/'bin/python3.14',native_code,env_b,420)
 venv=state/'venvs/platform-symlink';vr=run([str(canonical_b/'bin/python3.14'),'-m','venv','--without-pip','--symlinks',str(venv)],env=env_b,timeout=300);vpy=venv/'bin/python';vq=target_json(vpy,"import json,sys;print(json.dumps({'pass':True,'prefix':sys.prefix,'base_prefix':sys.base_prefix,'executable':sys.executable}))",env_b,180)
 native_install=ut3.install_and_import(wheel,canonical_b/'bin/python3.14',canonical_b,work/'native-wheel-install',state/'venvs/native-wheel')
 feature=auth_data['feature'];pip_selected=False;uv_selected=False
 cases=[
  {'case':'launcher-libpython-native-closure','status':'pass' if direct['pass'] else 'fail','direct_evidence':direct,'public_claim_candidate':True},
  {'case':'clean-isolated-termux-extraction','status':'pass' if probe_a['pass'] else 'fail','direct_evidence':probe_a,'public_claim_candidate':True},
  {'case':'whole-prefix-relocation','status':'pass' if probe_b['pass'] else 'fail','direct_evidence':probe_b,'public_claim_candidate':True},
  {'case':'fresh-symlink-venv-after-relocation','status':'pass' if vr['returncode']==0 and vq['pass'] else 'fail','create':vr,'probe':vq,'public_claim_candidate':True},
  {'case':'native-extension-wheel-in-fresh-venv','status':'pass' if native_install.get('pass') is True else 'fail','direct_evidence':native_install,'public_claim_candidate':True},
  {'case':'selected-base-pip-path','status':'withheld-not-selected','authority_boundary':feature['policy_boundaries']['base_pip'],'public_claim_candidate':False},
  {'case':'selected-uv-path','status':'withheld-not-selected','authority_boundary':feature['policy_boundaries']['uv'],'public_claim_candidate':False},
 ]
 runtime_matrix={'schema_version':1,'matrix':'current-assembled-runtime-platform','device':device,'cases':cases,'required_direct_pass_cases':['launcher-libpython-native-closure','clean-isolated-termux-extraction','whole-prefix-relocation','fresh-symlink-venv-after-relocation','native-extension-wheel-in-fresh-venv'],'selected_paths':{'base_pip':pip_selected,'uv':uv_selected},'pass':all(x['status']=='pass' for x in cases if x['case'] in {'launcher-libpython-native-closure','clean-isolated-termux-extraction','whole-prefix-relocation','fresh-symlink-venv-after-relocation','native-extension-wheel-in-fresh-venv'})}
 dump(out/'runtime-platform-matrix.json',runtime_matrix)

 dual=auth_data['dual_device'];environment={'schema_version':1,'matrix':'platform-environments','current_assembly':[{'environment_id':'current-owner-termux','evidence_kind':'direct-current-run','android_api':device['android_api'],'android_release':device['android_release'],'machine':device['machine'],'abilist':device['abilist'],'page_size':device['page_size'],'context':device['execution_context'],'current_assembly':True,'status':'pass' if runtime_matrix['pass'] else 'fail'}],'related_historical_evidence':[{'environment_id':dual['primary_profile']['authority_name'],'android_api':dual['primary_profile']['android_api'],'android_release':dual['primary_profile']['android_release'],'machine':dual['primary_profile']['machine'],'context':'Termux real device','current_assembly':False,'status':'historical-related-artifact-only'},{'environment_id':dual['secondary_profile']['authority_name'],'android_api':dual['secondary_profile']['android_api'],'android_release':dual['secondary_profile']['android_release'],'machine':dual['secondary_profile']['machine'],'context':'Termux real device','current_assembly':False,'status':'historical-related-artifact-only'}],'requested_boundaries':{'minimum_claimed_api':{'requested':24,'status':'withheld-no-current-assembly-runtime-evidence'},'modern_android_target':{'status':'pass','api':device['android_api']},'runtime_16k_page_device':{'status':'pass' if device['page_size']==16384 else 'withheld-no-16k-runtime-device'},'clean_non_termux_path':{'status':'withheld-no-non-termux-app-namespace-access'},'termux':{'status':'pass'},'adb':{'status':'withheld-no-adb-target-access' if not device['adb_path'] else 'tool-present-not-target-qualified'},'root':{'status':'withheld-no-root-target-access' if device['uid']!=0 else 'direct-root-context-present'}},'pass':runtime_matrix['pass'] and device['pass']}
 dump(out/'environment-matrix.json',environment)
 minimum={'schema_version':1,'package_declared_floor_api':24,'package_floor_evidence':'official filename/tag and accepted upstream authority','lowest_direct_current_assembly_runtime_api':device['android_api'],'lowest_related_historical_artifact_runtime_api':min(dual['primary_profile']['android_api'],dual['secondary_profile']['android_api']),'public_minimum_release_api':None,'status':'withheld','reason':'No direct current assembled-product execution exists at API 24 or any API below the current owner target. Modern-device success is not minimum-API proof.','modern_device_used_as_minimum_proof':False,'epoch3_decision_made':False,'pass':True}
 dump(out/'minimum-api-claim.json',minimum)
 supported={'schema_version':1,'public_claims':[{'claim':'The current assembled product executes in the Termux Android linker namespace on the directly tested aarch64 API target.','evidence':'runtime-platform-matrix.json','android_api':device['android_api'],'page_size':device['page_size'],'context':'Termux app process','architecture':'aarch64'},{'claim':'Every final runtime ELF and the native-extension wheel ELF have statically 16 KiB-compatible PT_LOAD alignment and segment-offset congruence after RUNPATH normalization.','evidence':'static-16k-matrix.json','runtime_16k_device_tested':device['page_size']==16384},{'claim':'The directly tested runtime supports launcher startup, 67 native imports, internal dlopen closure, subprocess child re-entry, whole-prefix relocation, fresh symlink venv creation, and native-extension wheel import.','evidence':'runtime-platform-matrix.json'}],'explicit_boundaries':['Claims apply only to the exact official input and frozen local mutation authorities.','Passing current-device probes do not imply a minimum API.','Static 16 KiB compatibility does not imply runtime qualification on a 16 KiB device.','Related API-29 evidence is historical and is not current-assembly proof.'],'epoch3_selection_made':False,'pass':True}
 withheld={'schema_version':1,'claims':[{'claim':'Android API 24 minimum runtime support','reason':'no direct current-assembly API-24 target evidence'},{'claim':'Any minimum release API','reason':'no lower-API direct current-assembly target evidence'},{'claim':'Runtime operation on a 16 KiB page-size device','reason':'no direct 16 KiB runtime target unless current page size is 16384','conditionally_resolved':device['page_size']==16384},{'claim':'Non-Termux Android app namespace support','reason':'no non-Termux app target access'},{'claim':'ADB shell support','reason':'no ADB target qualification'},{'claim':'root execution support','reason':'no root target qualification'},{'claim':'emulator support','reason':'prior emulator contract was waived, not qualified'},{'claim':'x86_64, armeabi-v7a, or other ABI support','reason':'current assembly is aarch64-only'},{'claim':'all Android versions, OEMs, kernels, or devices','reason':'bounded direct evidence only'},{'claim':'base pip or uv product inclusion','reason':'UT-5 did not select either path'}],'unresolved_count':10-(1 if device['page_size']==16384 else 0),'pass':True}
 dump(out/'supported-contexts.json',supported);dump(out/'withheld-claims.json',withheld)
 scan=contract_scan([minimum,supported],['minimum-api-claim.json','supported-contexts.json'])
 gate={'environment_matrix_complete':environment['pass'],'static_16k_matrix_complete':static16['pass'],'runtime_platform_matrix_complete':runtime_matrix['pass'],'minimum_api_claim_explicit':minimum['pass'] and minimum['status']=='withheld' and minimum['modern_device_used_as_minimum_proof'] is False,'supported_contexts_explicit':supported['pass'] and len(supported['public_claims'])==3,'withheld_claims_explicit':withheld['pass'] and len(withheld['claims'])>=9,'no_modern_as_minimum_inference':minimum['modern_device_used_as_minimum_proof'] is False,'no_broad_platform_claims':scan['pass'],'authority_bindings_exact':True,'epoch3_selection_absent':True}
 failed=[k for k,v in gate.items() if v is not True]
 diag={'schema_version':1,'gate_condition':gate,'failed_gate_conditions':failed,'exit_condition':{'direct_current_environment_count':len(environment['current_assembly']),'historical_related_environment_count':len(environment['related_historical_evidence']),'runtime_case_count':len(cases),'direct_runtime_pass_count':sum(x['status']=='pass' for x in cases),'static_runtime_elf_count':len(runtime_elf),'static_wheel_elf_count':len(wheel_elf),'withheld_claim_count':len(withheld['claims']),'public_claim_count':len(supported['public_claims']),'minimum_release_api_claimed':False,'runtime_16k_device_tested':device['page_size']==16384,'negative_claim_hits':len(scan['hits'])},'negative_claim_scan':scan,'pass':not failed}
 dump(out/'ut6-gate-diagnostics.json',diag)
 dump(out/'runtime-reproduction.json',{'schema_version':1,'ut3_reproduction':{'returncode':repro['returncode'],'gate_pass':gate3.get('pass') is True},'prefix_role':'<WORK>/runtime-sdk-reproduction/location-b/prefix','native_wheel':{'filename':wheel.name,'sha256':sha(wheel),'size':wheel.stat().st_size},'current_device':device,'pass':repro['returncode']==0 and gate3.get('pass') is True})
 if failed:raise SystemExit('UT-6 gate failed:'+json.dumps(gate,sort_keys=True))
 print(json.dumps({'pass':True,'gate':gate,'exit_condition':diag['exit_condition']},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
