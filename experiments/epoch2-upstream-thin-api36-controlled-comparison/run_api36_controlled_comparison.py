#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, re, shlex, shutil, statistics, subprocess, sys, tarfile, time
from pathlib import Path
from typing import Any

HOST='aarch64-linux-android'; CPYTHON_VERSION='3.14.6'; API_A=24; API_BC=36; BASELINE_NDK_VERSION='27.3.13750724'
OFFICIAL_SHA='38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5'
SOURCE_SHA='143b1dddefaec3bd2e21e3b839b34a2b7fb9842272883c576420d605e9f30c63'
LA2_SHA='94e5d27c9ed421b8cbbeefa2b56a531a9b7f94ea5adc8072911da7bf32b79a17'
DEP_TAGS=[('bzip2','1.0.8','3'),('libffi','3.4.4','3'),('openssl','3.5.7','0'),('sqlite','3.50.4','0'),('xz','5.4.6','1'),('zstd','1.5.7','2')]
DEP_ARCHIVES={
 'bzip2-1.0.8-3':('265397f190467b02c7240871856f0d8850750a08bbb2f51453520188e2fd4f7d',9105),
 'libffi-3.4.4-3':('a62b0629ceebad486149add1c7cb01a25a2b63a8ecc664384947b1b3cd2728d0',7775),
 'openssl-3.5.7-0':('018fcb54cad2078462ca8f95c7e920163181f2895f84229195bdb6bd1f2433fa',15149),
 'sqlite-3.50.4-0':('f77e764265d52feb800901dfe42f9d5647726cbf72aa253eea46ae2526d069f8',9346),
 'xz-5.4.6-1':('791b4ea0dcea392324f33acd83975ab7d192a5d1a568f7958bd908453c8ce2a2',7780),
 'zstd-1.5.7-2':('3731a5223183213353b325e78917a69dfff26164f9cd7b652dec35bf5f7f5105',15150),
}
OFFICIAL_DEP_ASSETS={
 'bzip2-1.0.8-3':('2385f46e173d525f079946957c007000a8ad11d8496ba66bae99129183d74bd9',197400),
 'libffi-3.4.4-3':('9f2c0255ce025c177d44db16174ad5158c7560efe3c7ef0c8c0c64b2196e6a9d',42455),
 'openssl-3.5.7-0':('3d62143ba57f17dfa25816b1ce06256944cb23e5bad1212a419cfd073b1eebab',6321792),
 'sqlite-3.50.4-0':('f446f18d381ed641cb9d58b4768097f9cb7fcce79f7d13be371ee089f2c93e27',1287749),
 'xz-5.4.6-1':('320b76d45dc3499cf855e5310f875cba61c2608e4a98bb280cc4f1b8f189da1a',651211),
 'zstd-1.5.7-2':('c3ae98fbe54b0cef9601d9dc120ed692d79609087e6926c70d8fc30face07fe7',490959),
}
OFFICIAL_DEP_REQUIRED_PATHS={
 'bzip2':['include/bzlib.h','lib/libbz2.a'],
 'libffi':['include/ffi.h','lib/libffi.a'],
 'openssl':['include/openssl/ssl.h','lib/libcrypto_python.so','lib/libssl_python.so'],
 'sqlite':['include/sqlite3.h','lib/libsqlite3_python.so'],
 'xz':['include/lzma.h','lib/liblzma.a'],
 'zstd':['include/zstd.h','lib/libzstd.a'],
}
OFFICIAL_DEP_REPRESENTATIVES={
 'bzip2':'lib/libbz2.a','libffi':'lib/libffi.a','openssl':'lib/libcrypto_python.so',
 'sqlite':'lib/libsqlite3_python.so','xz':'lib/liblzma.a','zstd':'lib/libzstd.a',
}
CORE_DEP_FILES=['libcrypto_python.so','libssl_python.so','libsqlite3_python.so']
HOST_CONTAMINATION_VARIABLES=['CPATH','C_INCLUDE_PATH','CPLUS_INCLUDE_PATH','OBJC_INCLUDE_PATH','LIBRARY_PATH','LD_LIBRARY_PATH','PKG_CONFIG_PATH','PKG_CONFIG_LIBDIR','PKG_CONFIG_SYSROOT_DIR','CC','CXX','CPP','AR','AS','LD','NM','RANLIB','READELF','STRIP','CFLAGS','CXXFLAGS','CPPFLAGS','LDFLAGS','LIBS']
FORBIDDEN_HOST_LIBRARY_PATHS=['/usr/local/lib','/usr/local/lib64','/data/data/com.termux/files/usr/lib','/data/data/com.termux/files/usr/lib64']
FORBIDDEN_HOST_INCLUDE_PATHS=['/usr/local/include','/data/data/com.termux/files/usr/include']

def dump(p:Path,o:Any): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()
def run(cmd:list[str],*,cwd:Path|None=None,env:dict[str,str]|None=None,log:Path|None=None,timeout:int=7200,check:bool=True)->subprocess.CompletedProcess[str]:
 t=time.monotonic(); p=subprocess.run(cmd,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
 if log:
  log.parent.mkdir(parents=True,exist_ok=True); log.write_text('$ '+shlex.join(map(str,cmd))+'\n\nSTDOUT\n'+p.stdout+'\nSTDERR\n'+p.stderr+f'\nRETURN_CODE={p.returncode}\nDURATION_SECONDS={time.monotonic()-t:.3f}\n')
 if check and p.returncode: raise RuntimeError(f'command failed rc={p.returncode}: {shlex.join(map(str,cmd))}\n{p.stderr[-5000:]}')
 return p

def safe_extract(archive:Path,dest:Path)->Path:
 if dest.exists(): shutil.rmtree(dest)
 dest.mkdir(parents=True)
 with tarfile.open(archive,'r:*') as tf:
  seen=set()
  for m in tf.getmembers():
   q=Path(m.name)
   if q.is_absolute() or '..' in q.parts or m.name in seen: raise RuntimeError('unsafe archive member:'+m.name)
   seen.add(m.name)
   if m.issym() or m.islnk():
    l=Path(m.linkname)
    if l.is_absolute() or '..' in l.parts: raise RuntimeError('unsafe archive link:'+m.name)
  tf.extractall(dest,filter='data')
 children=list(dest.iterdir())
 return children[0] if len(children)==1 and children[0].is_dir() else dest

def acquire(url:str,cache:Path,filename:str,expected_sha:str|None=None,expected_size:int|None=None)->dict[str,Any]:
 cache.mkdir(parents=True,exist_ok=True); p=cache/filename; mode='owner-local-cache-reuse'
 valid=p.is_file() and (expected_sha is None or sha(p)==expected_sha) and (expected_size is None or p.stat().st_size==expected_size)
 if not valid:
  tmp=cache/f'.{filename}.tmp.{os.getpid()}'; tmp.unlink(missing_ok=True)
  run(['curl','--fail','--location','--silent','--show-error','--retry','5','--retry-all-errors','--output',str(tmp),url],timeout=3600)
  if expected_sha and sha(tmp)!=expected_sha: tmp.unlink(missing_ok=True); raise RuntimeError('download SHA mismatch:'+filename)
  if expected_size and tmp.stat().st_size!=expected_size: tmp.unlink(missing_ok=True); raise RuntimeError('download size mismatch:'+filename)
  tmp.replace(p); mode='owner-local-bounded-download'
 return {'url':url,'path':str(p),'filename':filename,'sha256':sha(p),'size':p.stat().st_size,'expected_sha256':expected_sha,'expected_size':expected_size,'acquisition_mode':mode,'network_acquisition':mode.endswith('download'),'exact_identity':(expected_sha is None or sha(p)==expected_sha) and (expected_size is None or p.stat().st_size==expected_size)}

def load_module(path:Path,name:str):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod); return mod

def prefix_from_package(root:Path)->Path:
 for p in [root/'prefix',*[x for x in root.rglob('prefix') if x.is_dir()]]:
  if (p/'lib').is_dir() and any((p/'lib').glob('libpython3.14.so*')) and (p/'include/python3.14/Python.h').is_file(): return p
 raise RuntimeError('package prefix not found:'+str(root))

def tree_stats(root:Path)->dict[str,Any]:
 files=[]; total=0
 for p in sorted(root.rglob('*')):
  if p.is_file() and not p.is_symlink():
   s=p.stat().st_size; total+=s; files.append({'path':p.relative_to(root).as_posix(),'size':s,'sha256':sha(p)})
 return {'file_count':len(files),'total_bytes':total,'snapshot_sha256':hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()}

def path_manifest(root:Path)->dict[str,Any]:
 rows=[]
 for p in sorted(root.rglob('*')):
  rel=p.relative_to(root).as_posix()
  if p.is_symlink(): rows.append({'path':rel,'kind':'symlink','target':os.readlink(p)})
  elif p.is_file(): rows.append({'path':rel,'kind':'file','size':p.stat().st_size,'sha256':sha(p)})
 digest=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return {'entry_count':len(rows),'entries':rows,'snapshot_sha256':digest}

def dependency_prefix_from_asset(root:Path,name:str)->Path:
 required=OFFICIAL_DEP_REQUIRED_PATHS[name]
 candidates=[root,*[x for x in root.rglob('*') if x.is_dir()]]
 matches=[]
 for candidate in candidates:
  if all((candidate/rel).is_file() for rel in required):matches.append(candidate)
 matches=sorted(set(matches),key=lambda x:(len(x.parts),x.as_posix()))
 if len(matches)!=1:raise RuntimeError(f'official dependency prefix resolution failed:{name}:matches={len(matches)}')
 return matches[0]

def merge_dependency_prefix(source:Path,destination:Path)->dict[str,Any]:
 copied=0;identical_collisions=0;excluded_bin=0
 for item in sorted(source.rglob('*')):
  rel=item.relative_to(source)
  if rel.parts and rel.parts[0]=='bin':excluded_bin+=1;continue
  target=destination/rel
  if item.is_dir() and not item.is_symlink():target.mkdir(parents=True,exist_ok=True);continue
  target.parent.mkdir(parents=True,exist_ok=True)
  if item.is_symlink():
   expected=os.readlink(item)
   if target.is_symlink():
    if os.readlink(target)!=expected:raise RuntimeError('official dependency symlink collision:'+rel.as_posix())
    identical_collisions+=1
   elif target.exists():raise RuntimeError('official dependency kind collision:'+rel.as_posix())
   else:target.symlink_to(expected);copied+=1
  elif item.is_file():
   if target.is_file() and not target.is_symlink():
    if target.stat().st_size!=item.stat().st_size or sha(target)!=sha(item):raise RuntimeError('official dependency file collision:'+rel.as_posix())
    identical_collisions+=1
   elif target.exists() or target.is_symlink():raise RuntimeError('official dependency kind collision:'+rel.as_posix())
   else:shutil.copy2(item,target);copied+=1
 return {'source_prefix':str(source),'copied_entry_count':copied,'identical_collision_count':identical_collisions,'excluded_bin_entry_count':excluded_bin,'pass':copied>0}

def inspect_official_builder_dependency_pins(source:Path)->dict[str,Any]:
 p=source/'Android/android.py'
 text=p.read_text();start=text.find('def unpack_deps(');end=text.find('\ndef download(',start)
 if start<0 or end<0:raise RuntimeError('official CPython dependency pin scope missing')
 scope=text[start:end];tags=[f'{n}-{v}-{b}' for n,v,b in DEP_TAGS]
 counts={tag:scope.count(f'"{tag}"')+scope.count(f"'{tag}'") for tag in tags}
 deps_url='https://github.com/beeware/cpython-android-source-deps/releases/download'
 result={'path':'Android/android.py','scope':'unpack_deps-function-bounded','cpython_source_sha256':SOURCE_SHA,'expected_tags':tags,'tag_counts':counts,'deps_url':deps_url,'deps_url_present':deps_url in scope,'host_filename_expression_present':'filename = f"{name_ver}-{host}.tar.gz"' in scope,'pass':all(counts[tag]==1 for tag in tags) and deps_url in scope and 'filename = f"{name_ver}-{host}.tar.gz"' in scope}
 if not result['pass']:raise RuntimeError('official CPython dependency pin contract mismatch:'+json.dumps(result,sort_keys=True))
 return result

def inspect_official_package_rebuild_surface(prefix:Path)->dict[str,Any]:
 rows=[]
 for name,required in OFFICIAL_DEP_REQUIRED_PATHS.items():
  present=[rel for rel in required if (prefix/rel).is_file()];missing=[rel for rel in required if not (prefix/rel).is_file()]
  rows.append({'name':name,'required_paths':required,'present_paths':present,'missing_paths':missing,'complete':not missing})
 complete_names=sorted(x['name'] for x in rows if x['complete']);missing_names=sorted(x['name'] for x in rows if not x['complete'])
 result={'mode':'exact-official-final-package-rebuild-surface-inspection','official_archive_sha256':OFFICIAL_SHA,'dependencies':rows,'complete_dependency_names':complete_names,'incomplete_dependency_names':missing_names,'complete_rebuild_surface':not missing_names,'expected_complete_dependency_names':['openssl','sqlite'],'expected_incomplete_dependency_names':['bzip2','libffi','xz','zstd'],'pass':complete_names==['openssl','sqlite'] and missing_names==['bzip2','libffi','xz','zstd']}
 if not result['pass']:raise RuntimeError('official package dependency rebuild surface drift:'+json.dumps(result,sort_keys=True))
 return result

def compare_path_manifest(root:Path,expected:dict[str,Any])->dict[str,Any]:
 rows=[];equal=0
 for item in expected.get('entries',[]):
  p=root/item['path'];actual={'path':item['path'],'kind':None,'equal':False}
  if p.is_symlink():actual.update({'kind':'symlink','target':os.readlink(p)});actual['equal']=item.get('kind')=='symlink' and actual['target']==item.get('target')
  elif p.is_file():actual.update({'kind':'file','size':p.stat().st_size,'sha256':sha(p)});actual['equal']=item.get('kind')=='file' and actual['size']==item.get('size') and actual['sha256']==item.get('sha256')
  if actual['equal']:equal+=1
  rows.append(actual)
 return {'expected_entry_count':len(expected.get('entries',[])),'equal_entry_count':equal,'mismatched_entries':[x for x in rows if not x['equal']],'pass':equal==len(expected.get('entries',[])) and len(expected.get('entries',[]))>0}

def dependency_artifact_closure(prefix:Path,readelf:Path,ar:Path,name:str)->dict[str,Any]:
 dynamic=[]; archives=[]
 libdir=prefix/'lib'
 for item in sorted(libdir.rglob('*')) if libdir.is_dir() else []:
  if not item.is_file() or item.is_symlink():continue
  try:magic=item.open('rb').read(8)
  except OSError:continue
  if magic.startswith(b'\x7fELF'):
   q=run([str(readelf),'-dW',str(item)],check=False,timeout=120)
   needed=re.findall(r'\(NEEDED\).*?\[(.*?)\]',q.stdout);runpath=re.findall(r'\((?:RUNPATH|RPATH)\).*?\[(.*?)\]',q.stdout)
   dynamic.append({'path':item.relative_to(prefix).as_posix(),'needed':needed,'runpath':runpath,'readelf_rc':q.returncode,'pass':q.returncode==0})
  elif magic==b'!<arch>\n' or item.suffix=='.a':
   listing=run([str(ar),'t',str(item)],check=False,timeout=120)
   members=[x.strip() for x in listing.stdout.splitlines() if x.strip()]
   headers=run([str(readelf),'-hW',str(item)],check=False,timeout=120)
   objects=[]
   blocks=re.split(r'(?m)^\s*File:\s+',headers.stdout)
   for block in blocks[1:]:
    first,_,body=block.partition('\n')
    machine=re.search(r'(?m)^\s*Machine:\s*(.*?)\s*$',body)
    etype=re.search(r'(?m)^\s*Type:\s*(\S+)',body)
    objects.append({'member':first.strip(),'machine':machine.group(1).strip() if machine else None,'type':etype.group(1).strip() if etype else None})
   # llvm-readelf emits one File: block per archive member. Keep a bounded
   # fallback for implementations which omit File: but still emit every header.
   if not objects and headers.returncode==0:
    machines=[x.strip() for x in re.findall(r'(?m)^\s*Machine:\s*(.*?)\s*$',headers.stdout)]
    types=[x.strip() for x in re.findall(r'(?m)^\s*Type:\s*(\S+)',headers.stdout)]
    objects=[{'member':members[i] if i<len(members) else f'index-{i}','machine':m,'type':types[i] if i<len(types) else None} for i,m in enumerate(machines)]
   unsafe_members=[x for x in members if x.startswith('/') or '..' in Path(x).parts]
   machine_ok=bool(objects) and all(x.get('machine')=='AArch64' for x in objects)
   type_ok=bool(objects) and all(str(x.get('type') or '').startswith('REL') for x in objects)
   count_ok=bool(members) and len(objects)==len(members)
   archives.append({'path':item.relative_to(prefix).as_posix(),'ar_rc':listing.returncode,'readelf_rc':headers.returncode,'member_count':len(members),'members':members,'object_count':len(objects),'objects':objects,'unsafe_members':unsafe_members,'machine_aarch64':machine_ok,'relocatable_objects':type_ok,'pass':listing.returncode==0 and headers.returncode==0 and count_ok and machine_ok and type_ok and not unsafe_members})
 host_runpaths=[{'path':x['path'],'value':v,'forbidden_segments':[seg for seg in v.split(':') if any(seg==base or seg.startswith(base+'/') for base in FORBIDDEN_HOST_LIBRARY_PATHS) or '/data/data/com.termux' in seg or '/com.termux/' in seg]} for x in dynamic for v in x['runpath'] if any(any(seg==base or seg.startswith(base+'/') for base in FORBIDDEN_HOST_LIBRARY_PATHS) or '/data/data/com.termux' in seg or '/com.termux/' in seg for seg in v.split(':'))]
 forbidden=[{'path':x['path'],'needed':n} for x in dynamic for n in x['needed'] if n=='libz.so.1']
 sqlite_rows=[x for x in dynamic if Path(x['path']).name=='libsqlite3_python.so']
 sqlite_ok=True
 if name=='sqlite':sqlite_ok=len(sqlite_rows)==1 and 'libz.so' in sqlite_rows[0]['needed'] and 'libz.so.1' not in sqlite_rows[0]['needed']
 modes=[]
 if dynamic:modes.append('shared-elf')
 if archives:modes.append('static-archive')
 dynamic_ok=all(x['pass'] for x in dynamic) and not host_runpaths and not forbidden
 static_ok=all(x['pass'] for x in archives)
 bzip2_static_ok=name!='bzip2' or (len(archives)>=1 and any(Path(x['path']).name=='libbz2.a' for x in archives))
 artifact_count=len(dynamic)+len(archives)
 return {'readelf':str(readelf),'ar':str(ar),'artifact_modes':modes,'artifact_count':artifact_count,'elf_count':len(dynamic),'objects':dynamic,'static_archive_count':len(archives),'static_object_count':sum(x['object_count'] for x in archives),'static_archives':archives,'host_runpaths':host_runpaths,'forbidden_needed':forbidden,'sqlite_android_zlib_closure':sqlite_ok,'bzip2_static_archive_contract':bzip2_static_ok,'dynamic_closure_pass':dynamic_ok,'static_archive_pass':static_ok,'pass':artifact_count>0 and dynamic_ok and static_ok and sqlite_ok and bzip2_static_ok}

# Compatibility name for older local fixtures; evidence uses artifact_closure.
dependency_elf_closure=dependency_artifact_closure

def extension_modules(repo:Path)->list[str]:
 d=json.loads((repo/'experiments/epoch2-upstream-thin-control/elf-and-extension-inventory.json').read_text()); out=[]
 for x in d['native_extensions']:
  n=Path(x).name.split('.cpython-')[0]
  if n not in out: out.append(n)
 return out

def compile_launcher(repo:Path,prefix:Path,work:Path,loader)->dict[str,Any]:
 evidence=loader.compile_launchers(repo/'experiments/epoch2-upstream-thin-loader-relocation',prefix,work,'clang','patchelf','readelf')
 la2=work/'la_2'; actual=sha(la2)
 if actual!=LA2_SHA: raise RuntimeError(f'LA-2 identity drift {actual} != {LA2_SHA}')
 target=loader.install_launcher(prefix,la2)
 return {'launcher':str(target),'sha256':actual,'expected_sha256':LA2_SHA,'source_revision':'UT-2 LA-2 frozen source','patch_revision':'LR-3/LA-2','build_evidence':evidence['LA-2']}

def prepare_runtime(repo:Path,src_prefix:Path,dst:Path,loader,mods:list[str])->dict[str,Any]:
 if dst.exists(): shutil.rmtree(dst)
 shutil.copytree(src_prefix,dst,symlinks=True)
 rows=loader.patch_objects(dst,'lr3','patchelf','readelf',set())
 if not rows or not all(x['exact_mutation_check'] and x['alignment_16k_compatible'] for x in rows): raise RuntimeError('LR-3 patch failed')
 launch=compile_launcher(repo,dst,dst.parent/'launcher-build',loader)
 probe=loader.execute_runtime_probe(Path(launch['launcher']),dst,dst.parent/'runtime-probe',mods,timeout=900)
 return {'prefix':str(dst),'loader_rows':rows,'launcher':launch,'runtime_probe':probe,'tree':tree_stats(dst)}

def elf_surface(prefix:Path)->dict[str,Any]:
 rows=[]; names=set()
 for p in sorted(prefix.rglob('*')):
  if not p.is_file() or p.is_symlink(): continue
  try:
   if p.open('rb').read(4)!=b'\x7fELF': continue
  except OSError: continue
  rel=p.relative_to(prefix).as_posix(); dyn=run(['readelf','-dW',str(p)],check=False,timeout=120).stdout; ver=run(['readelf','--version-info',str(p)],check=False,timeout=120).stdout
  needed=re.findall(r'\(NEEDED\).*?\[(.*?)\]',dyn); runpath=re.findall(r'\((?:RUNPATH|RPATH)\).*?\[(.*?)\]',dyn)
  syms=sorted(set(re.findall(r'\b(?:LIBC|LIBDL|LIBM)_(\d+)\b',ver))); names.update(int(x) for x in syms)
  ph=run(['readelf','-lW',str(p)],check=False,timeout=120).stdout; aligns=[int(x,16) for x in re.findall(r'^\s*LOAD\s+.*?\s(0x[0-9a-fA-F]+)\s*$',ph,re.M)]
  rows.append({'path':rel,'sha256':sha(p),'size':p.stat().st_size,'needed':needed,'runpath':runpath,'android_api_symbol_versions':[int(x) for x in syms],'load_alignments':aligns,'alignment_16k_compatible':bool(aligns) and all(x>=16384 and x%16384==0 for x in aligns)})
 return {'elf_count':len(rows),'objects':rows,'observed_android_api_symbol_versions':sorted(names),'max_observed_versioned_android_api':max(names) if names else None,'minimum_runtime_inference_made':False,'all_16k_compatible':all(x['alignment_16k_compatible'] for x in rows)}

def sysconfig_probe(python:Path)->dict[str,Any]:
 code='''import json,sys,sysconfig\nkeys=["SOABI","EXT_SUFFIX","MULTIARCH","HOST_GNU_TYPE","CC","CFLAGS","LDFLAGS","ANDROID_API_LEVEL","Py_GIL_DISABLED"]\nprint(json.dumps({"version":sys.version,"platform":sysconfig.get_platform(),"vars":{k:sysconfig.get_config_var(k) for k in keys}},sort_keys=True))'''
 p=run([str(python),'-c',code],check=False,timeout=180); data=None
 try: data=json.loads(p.stdout.strip().splitlines()[-1])
 except Exception: pass
 return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'data':data,'pass':p.returncode==0 and isinstance(data,dict)}

def behavior_probe(python:Path,work:Path)->dict[str,Any]:
 code=r'''import json,os,pathlib,subprocess,tempfile,time,ssl,sqlite3,hashlib
r={}
r['subprocess']=subprocess.run([os.environ.get('SHELL','/system/bin/sh'),'-c','printf api36'],capture_output=True,text=True).stdout=='api36'
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d)/'x';p.write_bytes(b'x'*4096);r['filesystem']=p.stat().st_size==4096 and p.read_bytes()==b'x'*4096
r['monotonic']=time.monotonic_ns()>0
r['tls']=ssl.OPENSSL_VERSION
r['sqlite']=sqlite3.sqlite_version
r['sha256']=hashlib.sha256(b'api36').hexdigest()
print(json.dumps(r,sort_keys=True))'''
 p=run([str(python),'-c',code],check=False,timeout=180); data=None
 try:data=json.loads(p.stdout.strip().splitlines()[-1])
 except Exception:pass
 return {'returncode':p.returncode,'data':data,'stdout':p.stdout,'stderr':p.stderr,'pass':p.returncode==0 and isinstance(data,dict) and data.get('subprocess') is True and data.get('filesystem') is True and data.get('monotonic') is True}

def benchmark(python:Path)->dict[str,Any]:
 startup=[]
 for _ in range(7):
  t=time.perf_counter(); q=run([str(python),'-S','-c','pass'],check=False,timeout=60); startup.append((time.perf_counter()-t)*1000)
  if q.returncode: break
 code='''import hashlib,json,time\nt=time.perf_counter();x=0\nfor i in range(1000000):x=(x+i)%1000000007\na=(time.perf_counter()-t)*1000\nt=time.perf_counter();h=hashlib.sha256(b"x"*1048576).hexdigest();b=(time.perf_counter()-t)*1000\nprint(json.dumps({"loop_ms":a,"sha256_1m_ms":b,"digest":h,"value":x},sort_keys=True))'''
 q=run([str(python),'-c',code],check=False,timeout=180); data=None
 try:data=json.loads(q.stdout.strip().splitlines()[-1])
 except Exception:pass
 return {'startup_ms':startup,'startup_median_ms':statistics.median(startup) if startup else None,'micro':data,'pass':len(startup)==7 and q.returncode==0 and isinstance(data,dict)}

def native_probe(source:Path,cross:Path,prefix:Path,python:Path,work:Path,api:int)->dict[str,Any]:
 # Measurement compilation is intentionally held constant across A/B/C and uses
 # the already-qualified owner-local Termux clang surface from UT-3.  The class
 # compile API remains a property of the producer build, not of this probe.
 work.mkdir(parents=True,exist_ok=True); src=work/'api36_probe.c'
 ext_q=run([str(python),'-c','import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX") or ".so")'],check=False,timeout=60)
 ext=(ext_q.stdout.strip() if ext_q.returncode==0 else '') or '.cpython-314-aarch64-linux-android.so'
 if '/' in ext or '\x00' in ext: raise RuntimeError('unsafe EXT_SUFFIX:'+repr(ext))
 so=work/f'api36_probe{ext}'
 src.write_text('#include <Python.h>\nstatic PyObject* f(PyObject*s,PyObject*a){return PyLong_FromLong(36);}\nstatic PyMethodDef m[]={{"value",f,METH_NOARGS,""},{NULL,NULL,0,NULL}};static struct PyModuleDef d={PyModuleDef_HEAD_INIT,"api36_probe",NULL,-1,m};PyMODINIT_FUNC PyInit_api36_probe(void){return PyModule_Create(&d);}\n')
 cmd=['clang','-shared','-fPIC','-O2','-D__BIONIC_NO_PAGE_SIZE_MACRO',f'-I{prefix}/include/python3.14',str(src),f'-L{prefix}/lib','-lpython3.14','-Wl,--build-id=sha1','-Wl,--no-rosegment','-Wl,-z,max-page-size=16384','-Wl,-z,common-page-size=16384','-o',str(so)]
 q=run(cmd,log=work/'compile.log',check=False,timeout=600)
 if q.returncode:return {'compile_rc':q.returncode,'pass':False,'command':cmd,'stderr':q.stderr,'compiler_scope':'owner-local-termux-clang','producer_compile_api':api}
 r=run([str(python),'-c',f'import sys;sys.path.insert(0,{str(work)!r});import api36_probe;print(api36_probe.value())'],check=False,timeout=180)
 ph=run(['readelf','-lW',str(so)],check=False,timeout=60).stdout; aligns=[int(x,16) for x in re.findall(r'^\s*LOAD\s+.*?\s(0x[0-9a-fA-F]+)\s*$',ph,re.M)]
 return {'compile_rc':0,'import_rc':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'sha256':sha(so),'size':so.stat().st_size,'load_alignments':aligns,'compiler':'clang','compiler_scope':'owner-local-termux-clang','producer_compile_api':api,'measurement_compile_api_claim':None,'pass':r.returncode==0 and r.stdout.strip()=='36' and bool(aligns) and all(x>=16384 and x%16384==0 for x in aligns)}

def patch_android_host_env_capture(source:Path)->dict[str,Any]:
 p=source/'Android/android.py'; before=sha(p); text=p.read_text(); lines=text.splitlines(keepends=True)
 starts=[i for i,line in enumerate(lines) if line.startswith('def android_env(host):')]
 if len(starts)!=1: raise RuntimeError(f'android.py android_env function anchor count={len(starts)}')
 start=starts[0]
 ends=[i for i,line in enumerate(lines[start+1:],start+1) if line.startswith('def build_python_path():')]
 if len(ends)!=1: raise RuntimeError(f'android.py build_python_path boundary count={len(ends)}')
 end=ends[0]
 anchors=[i for i in range(start+1,end) if lines[i].strip()=='f"export",']
 if len(anchors)!=1: raise RuntimeError(f'android.py host environment capture anchor count={len(anchors)}')
 index=anchors[0]; original=lines[index]; indent=original[:len(original)-len(original.lstrip(' \t'))]
 newline='\r\n' if original.endswith('\r\n') else ('\n' if original.endswith('\n') else '')
 lines[index]=indent+'f"env",'+newline
 p.write_text(''.join(lines))
 return {'path':'Android/android.py','before_sha256':before,'after_sha256':sha(p),'change':'bounded host-build portability normalization: use env output instead of shell export output for KEY=VALUE capture','anchor_scope':'android_env-function-bounded','anchor_match_count':len(anchors),'source_line_number':index+1,'source_indentation_columns':len(indent.expandtabs(8)),'command_before':'export','command_after':'env','affected_scope':'build-host-environment-capture-only','termux_failure_signature':'shell export output contained variable names without assignments','product_source_semantics_changed':False}

def inspect_android_prepopulated_dependency_flow(source:Path)->dict[str,Any]:
 p=source/'Android/android.py'; before=sha(p); lines=p.read_text().splitlines(keepends=True)
 starts=[i for i,line in enumerate(lines) if line.startswith('def configure_host_python(')]
 if len(starts)!=1: raise RuntimeError(f'android.py configure_host_python anchor count={len(starts)}')
 start=starts[0]
 ends=[i for i,line in enumerate(lines[start+1:],start+1) if line.startswith('def make_host_python(')]
 if len(ends)!=1: raise RuntimeError(f'android.py make_host_python boundary count={len(ends)}')
 end=ends[0]
 prefix_anchors=[i for i in range(start+1,end) if lines[i].strip()=='prefix_dir = host_dir / "prefix"']
 guard_anchors=[i for i in range(start+1,end) if lines[i].strip()=='if not prefix_dir.exists():']
 unpack_anchors=[i for i in range(start+1,end) if lines[i].strip()=='unpack_deps(host, prefix_dir, cache_dir)']
 if len(prefix_anchors)!=1: raise RuntimeError(f'android.py prefix_dir anchor count={len(prefix_anchors)}')
 if len(guard_anchors)!=1: raise RuntimeError(f'android.py prefix existence guard count={len(guard_anchors)}')
 if len(unpack_anchors)!=1: raise RuntimeError(f'android.py unpack_deps anchor count={len(unpack_anchors)}')
 prefix_index=prefix_anchors[0]; guard_index=guard_anchors[0]; unpack_index=unpack_anchors[0]
 if not (prefix_index < guard_index < unpack_index < end): raise RuntimeError('android.py dependency prepopulation control-flow order mismatch')
 def indentation(line:str)->int:
  raw=line[:len(line)-len(line.lstrip(' \t'))]
  return len(raw.expandtabs(8))
 guard_indent=indentation(lines[guard_index]); unpack_indent=indentation(lines[unpack_index])
 nested_lines=[line for line in lines[guard_index+1:unpack_index+1] if line.strip()]
 if unpack_indent<=guard_indent or any(indentation(line)<=guard_indent for line in nested_lines):
  raise RuntimeError('android.py unpack_deps is not nested under prefix existence guard')
 after=sha(p)
 return {'path':'Android/android.py','before_sha256':before,'after_sha256':after,'mode':'native-prefix-existence-control-flow','anchor_scope':'configure_host_python-function-bounded','prefix_anchor_count':len(prefix_anchors),'guard_match_count':len(guard_anchors),'unpack_match_count':len(unpack_anchors),'prefix_line_number':prefix_index+1,'guard_line_number':guard_index+1,'unpack_line_number':unpack_index+1,'guard_indentation_columns':guard_indent,'unpack_indentation_columns':unpack_indent,'prepopulated_prefix_bypasses_unpack':True,'source_patch_applied':False,'product_source_semantics_changed':False}

def patch_android_ndk_revision(source:Path,ndk_revision:str)->dict[str,Any]:
 p=source/'Android/android-env.sh'
 if not p.is_file(): raise RuntimeError('CPython Android/android-env.sh missing')
 before=sha(p); text=p.read_text(); matches=list(re.finditer(r'(?m)^ndk_version=([^\n]+)$',text))
 if len(matches)!=1: raise RuntimeError(f'CPython Android NDK revision anchor count={len(matches)}')
 m=matches[0]; original=m.group(1).strip(); changed=original!=ndk_revision
 if changed: p.write_text(text[:m.start(1)]+ndk_revision+text[m.end(1):])
 return {'path':'Android/android-env.sh','before_sha256':before,'after_sha256':sha(p),'original_ndk_revision':original,'effective_ndk_revision':ndk_revision,'changed':changed,'change':'bounded build-toolchain revision selection for truthful API36 link capability','product_source_semantics_changed':False}

def seed_external_build_python(cross:Path,logdir:Path)->dict[str,Any]:
 exe=Path(sys.executable); resolved=exe.resolve(); version='.'.join(map(str,sys.version_info[:3]))
 if version!=CPYTHON_VERSION or sys.version_info[:2]!=(3,14):
  raise RuntimeError(f'exact external build Python required: got {version} expected {CPYTHON_VERSION}')
 build_dir=cross/'build'
 if build_dir.exists(): shutil.rmtree(build_dir)
 build_dir.mkdir(parents=True)
 wrapper=build_dir/'python'
 wrapper.write_text('#!/usr/bin/env sh\nexec '+shlex.quote(str(exe))+' "$@"\n')
 wrapper.chmod(0o755)
 q=run([str(wrapper),'-c','import json,platform,sys;print(json.dumps({"version":".".join(map(str,sys.version_info[:3])),"major_minor":f"{sys.version_info.major}.{sys.version_info.minor}","implementation":platform.python_implementation(),"platform":sys.platform,"machine":platform.machine()},sort_keys=True))'],log=logdir/'build-python-bootstrap.log',timeout=120)
 data=json.loads(q.stdout.strip().splitlines()[-1])
 meta={'schema_version':1,'mode':'owner-local-external-python-exact-version','required_version':CPYTHON_VERSION,'version':data['version'],'major_minor':data['major_minor'],'implementation':data['implementation'],'platform':data['platform'],'machine':data['machine'],'accepted_platforms':['android','linux'],'host_platform_policy':'runnable-owner-local-cpython-3.14.6-on-android-or-linux-aarch64','executable':str(exe),'resolved_executable':str(resolved),'executable_sha256':sha(resolved),'wrapper':str(wrapper),'wrapper_sha256':sha(wrapper),'source_tree_rebuilt_natively':False,'product_source_semantics_changed':False,'pass':data['version']==CPYTHON_VERSION and data['major_minor']=='3.14' and data['implementation']=='CPython' and data['platform'] in {'android','linux'} and data['machine'] in {'aarch64','arm64'}}
 if not meta['pass']: raise RuntimeError('external build Python probe failed:'+json.dumps(meta,sort_keys=True))
 return meta

def build_python(source:Path,cross:Path,cache:Path,api:int,logdir:Path,ndk_revision:str,prepopulate:Path|None=None)->dict[str,Any]:
 env=dict(os.environ); env.update({'ANDROID_API_LEVEL':str(api),'PYTHONDONTWRITEBYTECODE':'1'})
 t=time.monotonic(); cross.mkdir(parents=True,exist_ok=True); cache.mkdir(parents=True,exist_ok=True)
 host_env_capture_patch=patch_android_host_env_capture(source)
 android_ndk_revision_patch=patch_android_ndk_revision(source,ndk_revision)
 bootstrap=seed_external_build_python(cross,logdir)
 prepopulation_contract=None
 if prepopulate is not None:
  prefix=cross/HOST/'prefix'; prefix.parent.mkdir(parents=True,exist_ok=True)
  if prefix.exists():shutil.rmtree(prefix)
  shutil.copytree(prepopulate,prefix,symlinks=True)
  prepopulation_contract=inspect_android_prepopulated_dependency_flow(source)
  prepopulation_contract.update({'prepopulated_prefix_path':str(prefix),'prepopulated_prefix_exists_before_builder':prefix.is_dir(),'prepopulated_prefix_source':str(prepopulate),'prepopulated_prefix_source_tree':tree_stats(prepopulate),'prepopulated_prefix_source_manifest':path_manifest(prepopulate)})
  if not prepopulation_contract['prepopulated_prefix_exists_before_builder']: raise RuntimeError('dependency prefix prepopulation failed')
  cmd=[sys.executable,str(source/'Android/android.py'),'build','--cross-build-dir',str(cross),'--cache-dir',str(cache),HOST]
 else:
  cmd=[sys.executable,str(source/'Android/android.py'),'build','--cross-build-dir',str(cross),'--cache-dir',str(cache),'--clean',HOST]
 run(cmd,cwd=source,env=env,log=logdir/'build-host.log',timeout=21600)
 prefix=cross/HOST/'prefix'
 if not any((prefix/'lib').glob('libpython3.14.so*')): raise RuntimeError('built libpython missing')
 if prepopulate is not None:
  prepopulation_contract['retention_verification']=compare_path_manifest(prefix,prepopulation_contract['prepopulated_prefix_source_manifest'])
  if not prepopulation_contract['retention_verification']['pass']:raise RuntimeError('prepopulated dependency bytes changed during CPython build')
 return {'prefix':str(prefix),'duration_seconds':time.monotonic()-t,'compile_api':api,'tree':tree_stats(prefix),'cross_build_dir':str(cross),'cache_dir':str(cache),'host_environment_capture_patch':host_env_capture_patch,'android_ndk_revision_patch':android_ndk_revision_patch,'dependency_prepopulation_contract':prepopulation_contract,'build_python_bootstrap':bootstrap,'build_python_ready_before_cross':True,'native_build_python_built_first':False,'external_build_python_reused':True}

def official_dependency_assets(cache:Path,work:Path,source:Path)->dict[str,Any]:
 base='https://github.com/beeware/cpython-android-source-deps/releases/download';merged=work/'merged-prefix';shutil.rmtree(work,ignore_errors=True);merged.mkdir(parents=True,exist_ok=True);rows=[]
 pin_contract=inspect_official_builder_dependency_pins(source)
 for name,version,build in DEP_TAGS:
  tag=f'{name}-{version}-{build}';filename=f'{tag}-{HOST}.tar.gz';expected_sha,expected_size=OFFICIAL_DEP_ASSETS[tag]
  acq=acquire(f'{base}/{tag}/{filename}',cache,filename,expected_sha,expected_size)
  extracted=safe_extract(Path(acq['path']),work/f'extract-{tag}');prefix=dependency_prefix_from_asset(extracted,name);merge=merge_dependency_prefix(prefix,merged)
  rows.append({'name':name,'version':version,'build':build,'tag':tag,'provenance_mode':'exact-cpython-builder-pinned-beeware-release-asset','asset':acq,'asset_prefix':str(prefix),'asset_prefix_tree':tree_stats(prefix),'merge':merge,'required_paths':OFFICIAL_DEP_REQUIRED_PATHS[name],'representative_path':OFFICIAL_DEP_REPRESENTATIVES[name],'exact_identity':acq.get('exact_identity') is True})
 manifest=path_manifest(merged);representatives={}
 for name,rel in OFFICIAL_DEP_REPRESENTATIVES.items():
  item=merged/rel
  if not item.is_file():raise RuntimeError('official dependency representative missing:'+name+':'+rel)
  representatives[name]={'path':rel,'sha256':sha(item),'size':item.stat().st_size}
 complete=len(rows)==len(DEP_TAGS) and pin_contract.get('pass') is True and manifest.get('entry_count',0)>0 and all(x.get('exact_identity') is True and x.get('asset',{}).get('expected_sha256')==OFFICIAL_DEP_ASSETS[x['tag']][0] and x.get('asset',{}).get('expected_size')==OFFICIAL_DEP_ASSETS[x['tag']][1] and x.get('merge',{}).get('pass') is True for x in rows) and len(representatives)==len(DEP_TAGS)
 return {'dependency_binding':'exact-cpython-3.14.6-builder-pinned-release-assets','identity_policy':'hard-pinned-url-filename-sha256-size','dependencies':rows,'complete':complete,'release_asset_count':len(rows),'builder_pin_contract':pin_contract,'merged_prefix':str(merged),'merged_prefix_manifest':manifest,'representative_artifacts':representatives,'network_acquisition':any(x.get('asset',{}).get('network_acquisition') is True for x in rows),'owner_local_bounded_network_allowed':True,'official_package_final_bytes_used_as_rebuild_input':False}

def patch_libffi_android_configure_fallback(source:Path)->dict[str,Any]:
 p=source/'libffi/build.sh'
 if not p.is_file():raise RuntimeError('libffi build recipe missing')
 before=sha(p);text=p.read_text();anchor='./configure --host=$HOST --prefix=$prefix --disable-shared --with-pic'
 marker_begin='# HW-T libffi Android configure fallback BEGIN';marker_end='# HW-T libffi Android configure fallback END'
 block=(marker_begin+'\n'
        'ac_cv_func_memfd_create=no\n'
        'ac_cv_func_mkostemp=no\n'
        'ac_cv_func_mkstemp=yes\n'
        'export ac_cv_func_memfd_create ac_cv_func_mkostemp ac_cv_func_mkstemp\n'
        +marker_end+'\n')
 anchor_lines=[i for i,line in enumerate(text.splitlines()) if line.strip()==anchor]
 begin_count=text.count(marker_begin);end_count=text.count(marker_end);block_count=text.count(block)
 if begin_count or end_count:
  if begin_count!=1 or end_count!=1 or block_count!=1:raise RuntimeError(f'libffi configure fallback marker drift begin={begin_count} end={end_count} block={block_count}')
  insertion_mode='existing-exact-before-configure-block'
 else:
  if len(anchor_lines)!=1:raise RuntimeError(f'libffi configure anchor count={len(anchor_lines)}')
  lines=text.splitlines(keepends=True);idx=next(i for i,line in enumerate(lines) if line.strip()==anchor)
  lines.insert(idx,block+'\n');text=''.join(lines);insertion_mode='inserted-immediately-before-configure'
 p.write_text(text)
 syntax=subprocess.run(['bash','-n',str(p)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if syntax.returncode:raise RuntimeError('libffi build recipe syntax failed:'+syntax.stderr[-2000:])
 patched=p.read_text();begin_after=patched.count(marker_begin);end_after=patched.count(marker_end);block_after=patched.count(block);anchor_after=sum(1 for line in patched.splitlines() if line.strip()==anchor)
 block_before_configure=patched.find(block)>=0 and patched.find(block)<patched.find(anchor)
 memfd_cache_count=patched.count('ac_cv_func_memfd_create=no');mkostemp_cache_count=patched.count('ac_cv_func_mkostemp=no');mkstemp_cache_count=patched.count('ac_cv_func_mkstemp=yes')
 patch_pass=(begin_after==1 and end_after==1 and block_after==1 and anchor_after==1 and block_before_configure and memfd_cache_count==1 and mkostemp_cache_count==1 and mkstemp_cache_count==1 and syntax.returncode==0)
 if not patch_pass:raise RuntimeError('libffi configure fallback patch verification failed')
 return {'path':'libffi/build.sh','before_sha256':before,'after_sha256':sha(p),'mode':'bounded-libffi-configure-cache-fallback','insertion_mode':insertion_mode,'insertion_point':'immediately-before-pinned-configure-invocation','configure_anchor':anchor,'configure_anchor_count_after':anchor_after,'marker_begin_count_after':begin_after,'marker_end_count_after':end_after,'exact_block_count_after':block_after,'block_before_configure':block_before_configure,'forced_cache_values':{'ac_cv_func_memfd_create':'no','ac_cv_func_mkostemp':'no','ac_cv_func_mkstemp':'yes'},'memfd_cache_line_count_after':memfd_cache_count,'mkostemp_cache_line_count_after':mkostemp_cache_count,'mkstemp_cache_line_count_after':mkstemp_cache_count,'shell_syntax_pass':syntax.returncode==0,'recipe_build_environment_changed':True,'source_patch_applied':False,'product_source_semantics_changed':False,'pass':patch_pass}

def probe_libffi_android_mkstemp_fallback(compiler:Path,work:Path)->dict[str,Any]:
 work.mkdir(parents=True,exist_ok=True);src=work/'libffi-mkstemp-fallback.c';out=work/'libffi-mkstemp-fallback'
 src.write_text('''#include <stdlib.h>\nint main(void) {\n  char name[] = "/data/local/tmp/libffiXXXXXX";\n  int fd = mkstemp(name);\n  return fd == -2;\n}\n''')
 cmd=[str(compiler),'-Werror=implicit-function-declaration',str(src),'-o',str(out)]
 q=run(cmd,check=False,timeout=120);passed=q.returncode==0 and out.is_file()
 meta={'schema_version':1,'mode':'selected-r30-api36-compile-and-link-mkstemp-fallback-probe','compiler':str(compiler),'command':cmd,'required_declarations':['mkstemp'],'required_symbols':['mkstemp'],'forced_unavailable_functions':['memfd_create','mkostemp'],'returncode':q.returncode,'output_exists':out.is_file(),'output_sha256':sha(out) if out.is_file() else None,'stdout_tail':q.stdout[-2000:],'stderr_tail':q.stderr[-2000:],'source_patch_applied':False,'product_source_semantics_changed':False,'pass':passed}
 if not passed:raise RuntimeError('libffi Android mkstemp fallback probe failed:'+json.dumps(meta,sort_keys=True))
 return meta

def inspect_libffi_config(source:Path,version:str)->dict[str,Any]:
 root=source/'libffi'/'build'/version/HOST;candidates=sorted(root.rglob('fficonfig.h')) if root.is_dir() else []
 rows=[]
 for cfg in candidates:
  data=cfg.read_text(errors='replace');rows.append({'path':str(cfg),'sha256':sha(cfg),'have_memfd_create':bool(re.search(r'(?m)^#define HAVE_MEMFD_CREATE 1\s*$',data)),'have_mkostemp':bool(re.search(r'(?m)^#define HAVE_MKOSTEMP 1\s*$',data)),'have_mkstemp':bool(re.search(r'(?m)^#define HAVE_MKSTEMP 1\s*$',data))})
 selected=next((x for x in rows if x['have_mkstemp']),rows[0] if rows else {})
 mode='mkstemp-compatible-fallback' if selected.get('have_mkstemp') and not selected.get('have_memfd_create') and not selected.get('have_mkostemp') else 'unexpected-configure-selection'
 passed=bool(rows) and selected.get('have_mkstemp') is True and selected.get('have_memfd_create') is False and selected.get('have_mkostemp') is False and mode=='mkstemp-compatible-fallback'
 return {'schema_version':1,'config_header_count':len(rows),'config_headers':rows,'selected_config_header':selected,'selected_exec_temp_backend':mode,'have_memfd_create':selected.get('have_memfd_create'),'have_mkostemp':selected.get('have_mkostemp'),'have_mkstemp':selected.get('have_mkstemp'),'forced_cache_values_observed':selected.get('have_memfd_create') is False and selected.get('have_mkostemp') is False,'pass':passed}

def patch_source_dep_ndk(source:Path,ndk_revision:str)->dict[str,Any]:
 p=source/'android-env.sh'
 if not p.is_file(): raise RuntimeError('source dependency android-env.sh missing')
 before=sha(p); text=p.read_text(); m=re.search(r'(?m)^ndk_version=([^\n]+)$',text)
 if not m: raise RuntimeError('source dependency ndk_version anchor missing')
 original=m.group(1).strip(); revision_changed=original!=ndk_revision
 if revision_changed:text=text[:m.start(1)]+ndk_revision+text[m.end(1):]
 marker_begin='# HW-T API36 library precedence BEGIN'
 marker_end='# HW-T API36 library precedence END'
 block=(marker_begin+'\n'
        'hw_t_api_libdir="$toolchain/sysroot/usr/lib/$HOST/$ANDROID_API_LEVEL"\n'
        'if ! [ -d "$hw_t_api_libdir" ]; then\n'
        '    echo "HW-T API library directory missing: $hw_t_api_libdir" >&2\n'
        '    return 1 2>/dev/null || exit 1\n'
        'fi\n'
        'LDFLAGS="-L$hw_t_api_libdir ${LDFLAGS:-}"\n'
        'export LDFLAGS\n'
        +marker_end+'\n')
 begin_count=text.count(marker_begin); end_count=text.count(marker_end); block_count=text.count(block)
 ldflags_assignments_before=len(re.findall(r'(?m)^(?:export\s+)?LDFLAGS\s*=.*$',text))
 if begin_count or end_count:
  if begin_count!=1 or end_count!=1 or block_count!=1:raise RuntimeError(f'source dependency API library precedence marker drift begin={begin_count} end={end_count} block={block_count}')
  insertion_mode='existing-exact-end-block'
 else:
  if ldflags_assignments_before<1:raise RuntimeError('source dependency LDFLAGS semantic anchor missing')
  text=text.rstrip('\n')+'\n\n'+block
  insertion_mode='appended-after-all-existing-environment-logic'
 p.write_text(text)
 syntax=subprocess.run(['bash','-n',str(p)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if syntax.returncode:raise RuntimeError('source dependency android-env.sh syntax failed:'+syntax.stderr[-2000:])
 patched=p.read_text(); begin_after=patched.count(marker_begin); end_after=patched.count(marker_end); block_after=patched.count(block)
 script_end_block=patched.rstrip('\n').endswith(block.rstrip('\n'))
 precedence_line='LDFLAGS="-L$hw_t_api_libdir ${LDFLAGS:-}"'
 line_count_after=patched.count(precedence_line)
 patch_pass=(begin_after==1 and end_after==1 and block_after==1 and line_count_after==1 and script_end_block and syntax.returncode==0)
 if not patch_pass:raise RuntimeError('source dependency API library precedence end-block verification failed')
 after=sha(p)
 return {'path':'android-env.sh','before_sha256':before,'after_sha256':after,'original_ndk_revision':original,'effective_ndk_revision':ndk_revision,'changed':before!=after,'change':'bounded build-environment revision and end-of-script API-library precedence normalization','api_library_precedence_patch':{'mode':'bounded-end-of-sourced-environment-script','expression':'$toolchain/sysroot/usr/lib/$HOST/$ANDROID_API_LEVEL','insertion_mode':insertion_mode,'insertion_point':'end-of-script-after-all-existing-environment-logic','marker_begin':marker_begin,'marker_end':marker_end,'marker_begin_count_after':begin_after,'marker_end_count_after':end_after,'exact_block_count_after':block_after,'ldflags_assignment_count_before':ldflags_assignments_before,'precedence_line_count_after':line_count_after,'script_end_block':script_end_block,'shell_syntax_pass':syntax.returncode==0,'pass':patch_pass},'product_source_semantics_changed':False}

def verify_ndk(ndk:Path,expected_revision:str)->dict[str,Any]:
 sp=ndk/'source.properties'
 if not sp.is_file(): raise RuntimeError('NDK source.properties missing')
 text=sp.read_text(errors='replace'); m=re.search(r'(?m)^Pkg\.Revision\s*=\s*(.+?)\s*$',text)
 rev=m.group(1) if m else None
 marker=ndk/'HW_T_NDK_COMPAT.json'
 if not marker.is_file(): raise RuntimeError('NDK compatibility marker missing')
 meta=json.loads(marker.read_text())
 toolchain=Path(meta.get('toolchain_root','')); wrapper=Path(meta.get('api36_clang','')); base=Path(meta.get('base_clang','')); sysroot=Path(meta.get('sysroot','')); api_libdir=Path(meta.get('api36_library_dir',''))
 q=run([str(wrapper),'-dM','-E','-x','c','/dev/null'],check=False,timeout=120) if wrapper.is_file() else None
 macro=None
 if q is not None:
  mm=re.search(r'(?m)^#define __ANDROID_MIN_SDK_VERSION__ (\d+)\s*$',q.stdout) or re.search(r'(?m)^#define __ANDROID_API__ (\d+)\s*$',q.stdout); macro=int(mm.group(1)) if mm else None
 driver=meta.get('driver_contract',{}); filter_policy=driver.get('host_path_argument_filter',{}); crt=meta.get('api36_crt_inventory',{})
 ok=(rev==expected_revision=='30.0.15729638-beta2' and meta.get('selected_ndk_revision')==expected_revision and meta.get('selection_policy')=='exact-owner-local-r30-beta2-standard-sdk-plus-executable-and-system-library-link' and meta.get('release_channel')=='pre-release' and meta.get('prerelease') is True and meta.get('revision_suffix')=='beta2' and meta.get('pass') is True and meta.get('compatibility_overlay') is True and meta.get('original_ndk_content_mutated') is False and meta.get('target')=='aarch64-linux-android36' and meta.get('target_macro_api')==36 and macro==36 and meta.get('platform_metadata',{}).get('supports_api36') is True and meta.get('platform_metadata',{}).get('max')==36 and meta.get('api36_directory_present') is True and meta.get('api36_link_probe',{}).get('pass') is True and meta.get('api36_system_library_probe',{}).get('pass') is True and meta.get('api36_system_library_probe',{}).get('needed') and 'libz.so' in meta.get('api36_system_library_probe',{}).get('needed') and 'libz.so.1' not in meta.get('api36_system_library_probe',{}).get('needed') and driver.get('pass') is True and {'CPATH','LIBRARY_PATH','LD_LIBRARY_PATH','PKG_CONFIG_PATH','PKG_CONFIG_LIBDIR','PKG_CONFIG_SYSROOT_DIR'}.issubset(set(driver.get('host_contamination_variables_unset_by_wrapper',[]))) and filter_policy.get('enabled') is True and filter_policy.get('contract_version')==2 and filter_policy.get('implementation')=='bash-array-preserving-filter' and filter_policy.get('raw_absolute_host_paths_filtered') is True and filter_policy.get('colon_separated_rpath_lists_filtered') is True and set(FORBIDDEN_HOST_LIBRARY_PATHS).issubset(set(filter_policy.get('forbidden_library_paths',[]))) and set(FORBIDDEN_HOST_INCLUDE_PATHS).issubset(set(filter_policy.get('forbidden_include_paths',[]))) and filter_policy.get('target_arguments_preserved') is True and filter_policy.get('product_source_semantics_changed') is False and driver.get('selected_strategy') in {'native-target-wrapper','base-clang-target-only','base-clang-target-explicit-sysroot','base-clang-target-explicit-sysroot-api-libdir'} and isinstance(driver.get('driver_args'),list) and crt.get('complete') is True and api_libdir.is_dir() and all((api_libdir/x).is_file() for x in ['crtbegin_dynamic.o','crtend_android.o','libc.so']) and toolchain.is_dir() and wrapper.is_file() and os.access(wrapper,os.X_OK) and base.is_file() and os.access(base,os.X_OK) and sysroot.is_dir() and (toolchain/'bin/llvm-ar').is_file() and (toolchain/'bin/llvm-readelf').is_file())
 if not ok: raise RuntimeError(f'NDK identity/toolchain compatibility mismatch: revision={rev} macro={macro} meta={meta}')
 return {'path':str(ndk),'original_ndk_path':meta.get('original_ndk_path'),'selection_policy':meta.get('selection_policy'),'baseline_ndk_revision':meta.get('baseline_ndk_revision'),'selected_ndk_revision':expected_revision,'release_channel':meta.get('release_channel'),'prerelease':meta.get('prerelease'),'revision_suffix':meta.get('revision_suffix'),'official_version_label':meta.get('official_version_label'),'ndk_revision_delta':meta.get('ndk_revision_delta'),'source_properties_revision':rev,'toolchain_root':str(toolchain),'original_toolchain_root':meta.get('original_toolchain_root'),'api36_clang':str(wrapper),'base_clang':str(base),'compiler_invocation_mode':meta.get('compiler_invocation_mode'),'driver_contract':driver,'target':meta.get('target'),'target_macro_api':macro,'sysroot':str(sysroot),'supported_api_directories':meta.get('supported_api_directories'),'maximum_supported_api_directory':meta.get('maximum_supported_api_directory'),'api36_directory_present':meta.get('api36_directory_present'),'api36_library_dir':str(api_libdir),'api36_crt_inventory':crt,'api36_link_probe':meta.get('api36_link_probe'),'api36_system_library_probe':meta.get('api36_system_library_probe'),'platform_metadata':meta.get('platform_metadata'),'acquisition':meta.get('acquisition'),'compatibility_overlay':True,'original_ndk_content_mutated':False,'pass':True}

def build_source_deps(cache:Path,work:Path,android_home:Path,ndk_revision:str)->dict[str,Any]:
 merged=work/'merged-prefix'; shutil.rmtree(merged,ignore_errors=True);merged.mkdir(parents=True,exist_ok=True);rows=[]
 ndk=android_home/'ndk'/ndk_revision;prebuilt=next((ndk/'toolchains/llvm/prebuilt').glob('*'));readelf=prebuilt/'bin/llvm-readelf';ar=prebuilt/'bin/llvm-ar';sysroot=prebuilt/'sysroot';compat_meta=json.loads((ndk/'HW_T_NDK_COMPAT.json').read_text());argument_filter=compat_meta.get('driver_contract',{}).get('host_path_argument_filter',{});libffi_probe=probe_libffi_android_mkstemp_fallback(prebuilt/'bin/aarch64-linux-android36-clang',work/'libffi-mkstemp-fallback-probe')
 empty_pkg=work/'empty-pkgconfig';empty_pkg.mkdir(parents=True,exist_ok=True)
 base_env=dict(os.environ)
 removed={k:base_env.pop(k) for k in HOST_CONTAMINATION_VARIABLES if k in base_env}
 base_env.update({'ANDROID_HOME':str(android_home),'ANDROID_API_LEVEL':'36','PYTHONDONTWRITEBYTECODE':'1','PKG_CONFIG_PATH':'','PKG_CONFIG_LIBDIR':str(empty_pkg),'PKG_CONFIG_SYSROOT_DIR':str(sysroot),'CONFIG_SITE':'/dev/null'})
 environment_contract={'mode':'sanitized-android-sysroot-only-plus-compiler-argument-filter','removed_variable_names':sorted(removed),'forbidden_variable_names':HOST_CONTAMINATION_VARIABLES,'empty_pkg_config_dir':str(empty_pkg),'pkg_config_path':'','pkg_config_libdir':str(empty_pkg),'pkg_config_sysroot_dir':str(sysroot),'termux_prefix_search_allowed':False,'compiler_argument_filter':argument_filter,'api_library_precedence_expression':'$toolchain/sysroot/usr/lib/$HOST/$ANDROID_API_LEVEL','libffi_android_configure_fallback_probe':libffi_probe,'pass':all(k not in base_env or k in {'PKG_CONFIG_PATH','PKG_CONFIG_LIBDIR','PKG_CONFIG_SYSROOT_DIR'} for k in HOST_CONTAMINATION_VARIABLES) and argument_filter.get('enabled') is True and argument_filter.get('contract_version')==2 and argument_filter.get('raw_absolute_host_paths_filtered') is True and argument_filter.get('colon_separated_rpath_lists_filtered') is True and set(FORBIDDEN_HOST_LIBRARY_PATHS).issubset(set(argument_filter.get('forbidden_library_paths',[]))) and argument_filter.get('target_arguments_preserved') is True and libffi_probe.get('pass') is True}
 if not environment_contract['pass']:raise RuntimeError('source dependency host environment isolation failed')
 for name,version,build in DEP_TAGS:
  tag=f'{name}-{version}-{build}';fn=f'cpython-android-source-deps-{tag}.tar.gz';url=f'https://github.com/beeware/cpython-android-source-deps/archive/refs/tags/{tag}.tar.gz'
  expected_sha,expected_size=DEP_ARCHIVES[tag];acq=acquire(url,cache,fn,expected_sha,expected_size);srcroot=safe_extract(Path(acq['path']),work/f'src-{tag}');ndk_patch=patch_source_dep_ndk(srcroot,ndk_revision)
  if ndk_patch.get('api_library_precedence_patch',{}).get('pass') is not True:raise RuntimeError('source dependency API library precedence patch failed:'+tag)
  libffi_patch={'applicable':False,'pass':True,'source_patch_applied':False,'product_source_semantics_changed':False}
  if name=='libffi':
   libffi_patch=patch_libffi_android_configure_fallback(srcroot);libffi_patch['applicable']=True
   if libffi_patch.get('pass') is not True:raise RuntimeError('libffi Android configure fallback recipe patch failed')
  t=time.monotonic();run(['bash',str(srcroot/'build.sh'),name,version,build,HOST],cwd=srcroot,env=base_env,log=work/f'build-{tag}.log',timeout=21600)
  products=sorted((srcroot/name/'build'/version/HOST).glob(f'{name}-{version}-{build}-{HOST}.tar.gz'))
  if not products:raise RuntimeError('source dependency product missing:'+tag)
  product=products[-1];eroot=work/f'.extract-{tag}';srcprefix=safe_extract(product,eroot)
  closure=dependency_artifact_closure(srcprefix,readelf,ar,name)
  if not closure['pass']:raise RuntimeError('source dependency Android artifact closure failed:'+tag+':'+json.dumps(closure,sort_keys=True))
  libffi_config=inspect_libffi_config(srcroot,version) if name=='libffi' else {'applicable':False,'pass':True}
  if name=='libffi' and libffi_config.get('pass') is not True:raise RuntimeError('libffi generated configuration contract failed:'+json.dumps(libffi_config,sort_keys=True))
  for item in sorted(srcprefix.rglob('*')):
   rel=item.relative_to(srcprefix)
   if rel.parts and rel.parts[0]=='bin':continue
   dst=merged/rel
   if item.is_dir() and not item.is_symlink():dst.mkdir(parents=True,exist_ok=True)
   elif item.is_symlink():dst.parent.mkdir(parents=True,exist_ok=True);dst.unlink(missing_ok=True);dst.symlink_to(os.readlink(item))
   elif item.is_file():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(item,dst)
  shutil.rmtree(eroot)
  rows.append({'name':name,'version':version,'build':build,'tag':tag,'recipe_archive':acq,'recipe_tree':tree_stats(srcroot),'product':{'path':str(product),'sha256':sha(product),'size':product.stat().st_size},'duration_seconds':time.monotonic()-t,'ndk_orchestration_patch':ndk_patch,'host_environment_isolation':environment_contract,'libffi_android_configure_fallback_patch':libffi_patch,'libffi_config_contract':libffi_config,'artifact_closure':closure,'build_utility_binaries_merged':False})
 libffi_row=next((x for x in rows if x.get('name')=='libffi'),{})
 libffi_complete=libffi_probe.get('pass') is True and libffi_row.get('libffi_android_configure_fallback_patch',{}).get('pass') is True and libffi_row.get('libffi_android_configure_fallback_patch',{}).get('applicable') is True and libffi_row.get('libffi_config_contract',{}).get('pass') is True
 complete=len(rows)==len(DEP_TAGS) and libffi_complete and all(x['recipe_archive'].get('exact_identity') is True and x['artifact_closure']['pass'] and x['host_environment_isolation']['pass'] for x in rows)
 return {'prefix':str(merged),'dependencies':rows,'complete':complete,'tree':tree_stats(merged),'api':36,'ndk_version':ndk_revision,'host_environment_isolation':environment_contract,'libffi_android_configure_fallback_probe':libffi_probe,'libffi_android_configure_fallback_complete':libffi_complete,'source_dependency_host_isolation_complete':complete}

def class_measure(repo:Path,label:str,prefix:Path,work:Path,loader,mods:list[str],compile_api:int,build_meta:dict[str,Any],source:Path,cross:Path)->dict[str,Any]:
 runtime=prepare_runtime(repo,prefix,work/'runtime',loader,mods); python=Path(runtime['launcher']['launcher'])
 return {'label':label,'compile_api':compile_api,'cpython_version':CPYTHON_VERSION,'build':build_meta,'source_prefix_tree':tree_stats(prefix),'runtime':runtime,'elf':elf_surface(Path(runtime['prefix'])),'sysconfig':sysconfig_probe(python),'behavior':behavior_probe(python,work/'behavior'),'benchmark':benchmark(python),'native_extension_probe':native_probe(source,cross,Path(runtime['prefix']),python,work/'native-probe',compile_api)}

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--repo',type=Path,required=True); ap.add_argument('--official-archive',type=Path,required=True); ap.add_argument('--source-archive',type=Path,required=True); ap.add_argument('--work',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--android-home',type=Path,required=True); ap.add_argument('--ndk-path',type=Path,required=True); ap.add_argument('--ndk-revision',required=True); a=ap.parse_args()
 repo=a.repo.resolve(); work=a.work.resolve(); out=a.output.resolve(); ndk_revision=a.ndk_revision.strip(); ndk_identity=verify_ndk(a.ndk_path.resolve(),ndk_revision); work.mkdir(parents=True,exist_ok=True); out.mkdir(parents=True,exist_ok=True)
 if sha(a.official_archive)!=OFFICIAL_SHA or sha(a.source_archive)!=SOURCE_SHA: raise RuntimeError('official input identity mismatch')
 loader=load_module(repo/'experiments/epoch2-upstream-thin-loader-relocation/run_loader_relocation_experiment.py','ut2_loader'); mods=extension_modules(repo)
 source_b=safe_extract(a.source_archive,work/'cpython-source-b'); source_c=safe_extract(a.source_archive,work/'cpython-source-c')
 for s in (source_b,source_c):
  if not (s/'Android/android.py').is_file():raise RuntimeError('CPython Android builder missing')
 aroot=safe_extract(a.official_archive,work/'class-a-package'); aprefix=prefix_from_package(aroot)
 official_package_surface=inspect_official_package_rebuild_surface(aprefix)
 ca=class_measure(repo,'A-exact-official-api24',aprefix,work/'class-a',loader,mods,API_A,{'producer':'Python.org/BeeWare official binary','exact_official':True,'official_archive_sha256':OFFICIAL_SHA},source_b,work/'class-b-cross')
 official_assets=official_dependency_assets(work/'official-dependency-cache',work/'official-dependency-assets',source_b)
 b_derivation={'mode':'exact-cpython-builder-pinned-release-assets-merged-prefix','destination_prefix':official_assets['merged_prefix'],'asset_identity_policy':official_assets['identity_policy'],'builder_pin_contract':official_assets['builder_pin_contract'],'manifest':official_assets['merged_prefix_manifest'],'representative_artifacts':official_assets['representative_artifacts'],'release_asset_count':official_assets['release_asset_count'],'complete':official_assets['complete']}
 bmeta=build_python(source_b,work/'class-b-cross',work/'class-b-unused-download-cache',API_BC,work/'class-b-logs',ndk_revision,Path(official_assets['merged_prefix']))
 bprefix=Path(bmeta['prefix']);cb=class_measure(repo,'B-api36-same-cpython-official-deps',bprefix,work/'class-b',loader,mods,API_BC,bmeta,source_b,work/'class-b-cross');cb['official_dependency_assets']=official_assets;cb['official_dependency_prefix_derivation']=b_derivation;cb['official_package_rebuild_surface']=official_package_surface
 dep_cmp={}
 for name,item in official_assets['representative_artifacts'].items():
  pb=bprefix/item['path'];dep_cmp[name]={'path':item['path'],'asset_sha256':item['sha256'],'asset_size':item['size'],'b_sha256':sha(pb) if pb.is_file() else None,'b_size':pb.stat().st_size if pb.is_file() else None,'equal':pb.is_file() and pb.stat().st_size==item['size'] and sha(pb)==item['sha256']}
 cb['official_dependency_binary_comparison']=dep_cmp
 cb['official_dependency_manifest_retention']=compare_path_manifest(bprefix,official_assets['merged_prefix_manifest'])
 deps=build_source_deps(work/'source-deps-cache',work/'source-deps-build',a.android_home,ndk_revision)
 cmeta=build_python(source_c,work/'class-c-cross',work/'class-c-official-cache',API_BC,work/'class-c-logs',ndk_revision,Path(deps['prefix']))
 cprefix=Path(cmeta['prefix']); cc=class_measure(repo,'C-api36-same-source-revisions-source-built-deps',cprefix,work/'class-c',loader,mods,API_BC,cmeta,source_c,work/'class-c-cross'); cc['source_dependencies']=deps
 classes={'A':ca,'B':cb,'C':cc}
 dump(out/'control-class-a.json',ca); dump(out/'control-class-b.json',cb); dump(out/'control-class-c.json',cc)
 runtime={k:{'compile_api':v['compile_api'],'runtime_probe':v['runtime']['runtime_probe'],'behavior':v['behavior'],'elf':v['elf']} for k,v in classes.items()}; dump(out/'runtime-and-elf-measurements.json',runtime)
 bench={k:{'prefix_tree':v['source_prefix_tree'],'runtime_tree':v['runtime']['tree'],'benchmark':v['benchmark']} for k,v in classes.items()}; dump(out/'benchmark-and-size.json',bench)
 wsp={k:{'sysconfig':v['sysconfig'],'native_extension_probe':v['native_extension_probe'],'extension_failures':v['runtime']['runtime_probe']['required_extension_failures'],'observed_android_api_symbol_versions':v['elf']['observed_android_api_symbol_versions']} for k,v in classes.items()}; dump(out/'wheel-sysconfig-and-symbols.json',wsp)
 additional=[
  {'id':'api36-capable-ndk-toolchain','classes':['B','C'],'reason':f'official CPython 3.14.6 pins NDK {BASELINE_NDK_VERSION}; the controlled API36 rebuild selects exact owner-local custom r30 beta2 {ndk_revision} only after standard-symlink, API36 CRT, and executable-link verification and applies it equally to B/C','enumerated':True,'baseline_ndk_revision':BASELINE_NDK_VERSION,'selected_ndk_revision':ndk_revision,'revision_changed':ndk_revision!=BASELINE_NDK_VERSION,'product_source_semantics_changed':False},
  {'id':'ndk-prerelease-channel','classes':['B','C'],'reason':'API 36 compilation requires the owner-local NDK r30 beta2 pre-release in this run; this is an explicitly enumerated build-tool delta and does not establish stable-toolchain or Epoch 3 product adoption','enumerated':True,'selected_ndk_revision':ndk_revision,'release_channel':'pre-release','epoch3_selection':False,'product_source_semantics_changed':False},
  {'id':'producer-context','classes':['B','C'],'reason':'A is official release output; B/C are bounded owner-local rebuilds','enumerated':True},
  {'id':'build-python-bootstrap','classes':['B','C'],'reason':'owner-local exact CPython 3.14.6 is reused as the external build Python because the official Android builder only requires a matching major/minor interpreter for regeneration and freezing; no product source semantics change','enumerated':True,'product_source_semantics_changed':False},
  {'id':'build-timestamp-and-build-id','classes':['B','C'],'reason':'rebuild output includes run-specific timestamps/build IDs','enumerated':True},
  {'id':'class-b-exact-official-release-asset-prepopulation','classes':['B'],'reason':'the exact final A package omits the development headers and static archives for bzip2, libffi, xz, and zstd, so B prepopulates the exact six release assets pinned by CPython 3.14.6 Android/unpack_deps; every asset is hard-bound by URL, filename, SHA-256, and size and the merged dependency manifest is retained byte-for-byte through the API36 CPython build','enumerated':True,'identity_policy':'hard-pinned-url-filename-sha256-size','network_acquisition_allowed':True,'official_package_final_bytes_used_as_rebuild_input':False,'product_source_semantics_changed':False},
  {'id':'dependency-producer','classes':['C'],'reason':'C rebuilds pinned BeeWare dependency tags from source at API 36','enumerated':True},
  {'id':'source-dependency-ndk-orchestration','classes':['C'],'reason':f'pinned source-dependency recipes are build-environment-normalized to the same selected NDK revision {ndk_revision} used by CPython B/C','enumerated':True,'product_source_semantics_changed':False},
  {'id':'source-dependency-host-isolation','classes':['C'],'reason':'compiler and linker wrappers unset Termux variables and filter host -L/-I/RPATH arguments; source-dependency android-env prepends the selected API36 sysroot library directory; SQLite must resolve libz.so rather than Termux libz.so.1','enumerated':True,'termux_host_library_allowed':False,'product_source_semantics_changed':False},
  {'id':'source-dependency-libffi-android-configure-fallback','classes':['C'],'reason':'libffi 3.4.4 AC_CHECK_FUNCS cross-link checks can mark memfd_create and mkostemp available even when the API36 C99 compile surface lacks declarations; the pinned recipe forces those configure cache results to no and verifies the declared mkstemp fallback with the selected r30/API36 compiler','enumerated':True,'forced_cache_values':{'ac_cv_func_memfd_create':'no','ac_cv_func_mkostemp':'no','ac_cv_func_mkstemp':'yes'},'selected_exec_temp_backend':'mkstemp-compatible-fallback','recipe_build_environment_changed':True,'source_patch_applied':False,'product_source_semantics_changed':False},
  {'id':'termux-host-environment-capture-portability','classes':['B','C'],'reason':'bounded Android/android.py host-build patch uses env rather than shell export so Termux emits KEY=VALUE assignments; target product semantics are unchanged','enumerated':True,'product_semantics_changed':False},
  {'id':'dependency-prepopulation-native-control-flow','classes':['B','C'],'reason':'Classes B and C prepopulate exact dependency prefixes before invoking the unmodified CPython configure_host_python flow; the existing prefix-existence guard natively bypasses official dependency unpacking','enumerated':True,'source_patch_applied':False,'product_source_semantics_changed':False},
  {'id':'measurement-normalization','classes':['A','B','C'],'reason':'LA-2 and LR-3 are held constant for runnable measurement copies and are not part of raw producer identity','enumerated':True},
 ]
 delta={'schema_version':1,'intended_variable':'ANDROID_API_LEVEL','intended_change':{'A':24,'B':36,'C':36},'controlled_constants':{'cpython_version':'3.14.6','cpython_source_sha256':SOURCE_SHA,'launcher_source_and_patch':'UT-2 LA-2 exact','loader_normalization':'UT-2 LR-3','host':HOST,'ndk_version':ndk_revision,'baseline_cpython_ndk_version':BASELINE_NDK_VERSION,'class_b_dependency_binding':'exact-cpython-3.14.6-builder-pinned-release-assets','class_b_dependency_release_tags':[f'{n}-{v}-{b}' for n,v,b in DEP_TAGS],'class_b_dependency_asset_sha256':{tag:OFFICIAL_DEP_ASSETS[tag][0] for tag in sorted(OFFICIAL_DEP_ASSETS)},'class_b_dependency_asset_size':{tag:OFFICIAL_DEP_ASSETS[tag][1] for tag in sorted(OFFICIAL_DEP_ASSETS)},'class_c_dependency_release_tags':[f'{n}-{v}-{b}' for n,v,b in DEP_TAGS],'class_c_dependency_recipe_archive_sha256':{tag:DEP_ARCHIVES[tag][0] for tag in sorted(DEP_ARCHIVES)}},'unavoidable_additional_deltas':additional,'all_deltas_enumerated':all(x['enumerated'] for x in additional),'epoch3_selection':False,'product_decision':None}; dump(out/'controlled-delta-inventory.json',delta)
 b_retention_complete=official_package_surface['pass'] and official_assets['complete'] and official_assets['builder_pin_contract']['pass'] and cb['official_dependency_manifest_retention']['pass'] and bmeta.get('dependency_prepopulation_contract',{}).get('retention_verification',{}).get('pass') is True and len(dep_cmp)==len(DEP_TAGS) and all(x['equal'] for x in dep_cmp.values())
 prov={'schema_version':1,'cpython_source':{'path':str(a.source_archive),'sha256':sha(a.source_archive),'version':CPYTHON_VERSION},'official_package':{'path':str(a.official_archive),'sha256':sha(a.official_archive),'compile_api':24},'ndk_version':ndk_revision,'baseline_cpython_ndk_version':BASELINE_NDK_VERSION,'android_home':str(a.android_home),'ndk_identity':ndk_identity,'official_dependency_assets':official_assets,'official_package_rebuild_surface':official_package_surface,'class_b_official_dependency_prefix_derivation':b_derivation,'class_b_build':bmeta,'class_c_build':cmeta,'source_dependencies':deps,'owner_local_network_allowed':True,'single_archive_transport':True,'build_python_bootstrap':bmeta['build_python_bootstrap'],'build_python_bootstrap_equal':bmeta['build_python_bootstrap']['executable_sha256']==cmeta['build_python_bootstrap']['executable_sha256'] and bmeta['build_python_bootstrap']['version']==cmeta['build_python_bootstrap']['version'],'api36_link_capability_verified':ndk_identity.get('api36_directory_present') is True and ndk_identity.get('api36_crt_inventory',{}).get('complete') is True and ndk_identity.get('api36_link_probe',{}).get('pass') is True and ndk_identity.get('api36_system_library_probe',{}).get('pass') is True and ndk_identity.get('driver_contract',{}).get('pass') is True,'cpython_ndk_revision_normalization_complete':all(x.get('effective_ndk_revision')==ndk_revision and x.get('product_source_semantics_changed') is False for x in [bmeta['android_ndk_revision_patch'],cmeta['android_ndk_revision_patch']]),'host_environment_capture_normalization_complete':all(x.get('product_source_semantics_changed') is False and x.get('anchor_scope')=='android_env-function-bounded' and x.get('anchor_match_count')==1 and x.get('source_indentation_columns')==8 and x.get('command_before')=='export' and x.get('command_after')=='env' for x in [bmeta['host_environment_capture_patch'],cmeta['host_environment_capture_patch']]),'class_b_exact_official_dependency_retention_complete':b_retention_complete,'dependency_prepopulation_native_flow_complete':all(m.get('dependency_prepopulation_contract',{}).get('mode')=='native-prefix-existence-control-flow' and m.get('dependency_prepopulation_contract',{}).get('prepopulated_prefix_bypasses_unpack') is True and m.get('dependency_prepopulation_contract',{}).get('prepopulated_prefix_exists_before_builder') is True and m.get('dependency_prepopulation_contract',{}).get('source_patch_applied') is False and m.get('dependency_prepopulation_contract',{}).get('before_sha256')==m.get('dependency_prepopulation_contract',{}).get('after_sha256') and m.get('dependency_prepopulation_contract',{}).get('retention_verification',{}).get('pass') is True for m in [bmeta,cmeta]),'build_burden':{'official_control':'extract and measure','class_b':'acquire or reuse six exact CPython-3.14.6-builder-pinned dependency release assets under hard SHA-256/size binding + merge and prepopulate exact dependency prefix + API36 CPython build','class_c':'six pinned source-dependency builds under Android-sysroot-only environment plus host-path compiler/linker argument filtering + prepopulate merged prefix through CPython native prefix-existence control flow + API36 CPython build'},'source_dependency_ndk_normalization_complete':all(x.get('ndk_orchestration_patch',{}).get('effective_ndk_revision')==ndk_revision and x.get('ndk_orchestration_patch',{}).get('api_library_precedence_patch',{}).get('pass') is True and x.get('ndk_orchestration_patch',{}).get('api_library_precedence_patch',{}).get('mode')=='bounded-end-of-sourced-environment-script' and x.get('ndk_orchestration_patch',{}).get('api_library_precedence_patch',{}).get('script_end_block') is True and x.get('ndk_orchestration_patch',{}).get('api_library_precedence_patch',{}).get('shell_syntax_pass') is True and x.get('ndk_orchestration_patch',{}).get('api_library_precedence_patch',{}).get('exact_block_count_after')==1 and x.get('ndk_orchestration_patch',{}).get('api_library_precedence_patch',{}).get('marker_begin_count_after')==1 and x.get('ndk_orchestration_patch',{}).get('api_library_precedence_patch',{}).get('marker_end_count_after')==1 and x.get('ndk_orchestration_patch',{}).get('api_library_precedence_patch',{}).get('ldflags_assignment_count_before',0)>=1 and x.get('ndk_orchestration_patch',{}).get('product_source_semantics_changed') is False for x in deps['dependencies']),'source_dependency_host_isolation_complete':deps.get('source_dependency_host_isolation_complete') is True and all(x.get('artifact_closure',{}).get('pass') is True and x.get('host_environment_isolation',{}).get('pass') is True for x in deps['dependencies']),'libffi_android_configure_fallback_complete':deps.get('libffi_android_configure_fallback_complete') is True and deps.get('libffi_android_configure_fallback_probe',{}).get('pass') is True,'provenance_complete':True}; dump(out/'provenance-and-build-burden.json',prov)
 gate={
  'class_a_exact_official':ca['build']['exact_official'] and sha(a.official_archive)==OFFICIAL_SHA,
  'class_b_build_complete':bool(bmeta.get('tree',{}).get('snapshot_sha256')),
  'class_c_build_complete':bool(cmeta.get('tree',{}).get('snapshot_sha256')),
  'class_b_official_dependencies_retained':prov['class_b_exact_official_dependency_retention_complete'],
  'class_c_source_tags_complete':deps['complete'] and len(deps['dependencies'])==6 and prov['source_dependency_host_isolation_complete'],
  'controlled_delta_inventory_complete':delta['all_deltas_enumerated'] and delta['intended_variable']=='ANDROID_API_LEVEL',
  'runtime_matrix_complete':all(v['runtime']['runtime_probe']['startup_pass'] and v['runtime']['runtime_probe']['required_extension_failures']==0 and v['behavior']['pass'] for v in classes.values()),
  'elf_16k_matrix_complete':all(v['elf']['all_16k_compatible'] for v in classes.values()),
  'benchmark_and_size_complete':all(v['benchmark']['pass'] and v['source_prefix_tree']['file_count']>0 for v in classes.values()),
  'wheel_sysconfig_symbols_complete':all(v['sysconfig']['pass'] and v['native_extension_probe']['pass'] for v in classes.values()),
  'provenance_and_build_burden_complete':prov['provenance_complete'] and prov['ndk_identity']['pass'] and prov['api36_link_capability_verified'] and prov['cpython_ndk_revision_normalization_complete'] and prov['source_dependency_ndk_normalization_complete'] and prov['build_python_bootstrap']['pass'] and prov['build_python_bootstrap_equal'] and prov['host_environment_capture_normalization_complete'] and prov['dependency_prepopulation_native_flow_complete'] and prov['class_b_exact_official_dependency_retention_complete'] and prov['source_dependency_host_isolation_complete'] and prov['libffi_android_configure_fallback_complete'] and deps['complete'] and official_assets['complete'],
  'no_minimum_runtime_inference':all(v['elf']['minimum_runtime_inference_made'] is False for v in classes.values()),
  'no_epoch3_selection':delta['epoch3_selection'] is False and delta['product_decision'] is None,
 }
 diagnostics={'schema_version':1,'gate_condition':{k:bool(v) for k,v in gate.items()},'failed_gate_conditions':[k for k,v in gate.items() if not bool(v)],'pass':all(bool(v) for v in gate.values()),'exit_condition':{'class_count':3,'official_dependency_asset_count':official_assets['release_asset_count'],'b_official_dependency_asset_identity_count':sum(x.get('exact_identity') is True for x in official_assets['dependencies']),'b_official_dependency_manifest_entry_count':official_assets['merged_prefix_manifest']['entry_count'],'b_official_dependency_manifest_equal_count':cb['official_dependency_manifest_retention']['equal_entry_count'],'b_representative_dependency_count':len(dep_cmp),'b_representative_dependency_equal_count':sum(x['equal'] for x in dep_cmp.values()),'b_official_package_incomplete_rebuild_dependency_count':len(official_package_surface['incomplete_dependency_names']),'c_source_dependency_host_isolation_complete':deps['source_dependency_host_isolation_complete'],'c_libffi_android_configure_fallback_complete':deps['libffi_android_configure_fallback_complete'],'c_source_dependency_count':len(deps['dependencies']),'runtime_pass_count':sum(v['runtime']['runtime_probe']['startup_pass'] for v in classes.values()),'behavior_pass_count':sum(v['behavior']['pass'] for v in classes.values()),'all_16k':all(v['elf']['all_16k_compatible'] for v in classes.values()),'additional_delta_count':len(additional)}}; dump(out/'api36-gate-diagnostics.json',diagnostics)
 if not diagnostics['pass']: raise RuntimeError('API36 gate failed:'+json.dumps(diagnostics['gate_condition'],sort_keys=True))
 return 0
if __name__=='__main__': raise SystemExit(main())
