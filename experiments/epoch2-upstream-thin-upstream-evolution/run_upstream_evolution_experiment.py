#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, base64, hashlib, json, os, posixpath, re, shutil, subprocess, tarfile
from pathlib import Path
from typing import Any

CURRENT_SHA='38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5'
CURRENT_SIZE=22358404
AUTH={
 'plan':('experiments/epoch2-upstream-thin-plan/plan-authority.json','62b3b07f37a90b497747562bb00a9db5a3d78b3b2cb45df8f66db22818f5eafa'),
 'control':('experiments/epoch2-upstream-thin-control/upstream-control-authority.json','6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c'),
 'artifact':('experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json','387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306'),
 'loader':('experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json','05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2'),
 'sysconfig':('experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json','6cff1984d4601a37e8b57762bb170a57e695cb64d516c1dab0023b7e809dc808'),
 'data':('experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json','be25e52aba1d6c9d0b2e25fec2bd1d8a0a0d9eb870436f00e81f347e90d012b7'),
 'feature':('experiments/epoch2-upstream-thin-feature-qualification/feature-qualification-authority.json','3b56a38898a3a2384cf9419fe3cd124faa8dbf367cdd5532724b3424092a62e5'),
 'platform':('experiments/epoch2-upstream-thin-platform-portability/platform-portability-authority.json','b21eddfee574343772d0875a7b6f26aa7b5dd494ccf0a5f1be9b8c09201276f4'),
}
VERSION_TOKENS=[(re.compile(r'python3\.(?:14|15)'), 'python<PYVER>'),(re.compile(r'libpython3\.(?:14|15)'), 'libpython<PYVER>'),(re.compile(r'cpython-(?:314|315)'), 'cpython-<PYTAG>'),(re.compile(r'cp(?:314|315)'), 'cp<PYTAG>'),(re.compile(r'3\.(?:14|15)'), '<PYVER>')]

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def load(p:Path)->Any:return json.loads(p.read_text())
def dump(p:Path,v:Any)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def run(cmd:list[str],timeout:int=90)->dict[str,Any]:
 try:p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
 except subprocess.TimeoutExpired as e:return {'command':cmd,'returncode':124,'stdout':e.stdout or '','stderr':e.stderr or 'timeout'}
 return {'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def normver(s:str)->str:
 for pat,repl in VERSION_TOKENS:s=pat.sub(repl,s)
 return s
def safe_extract(archive:Path,dest:Path)->dict[str,Any]:
 shutil.rmtree(dest,ignore_errors=True);dest.mkdir(parents=True)
 seen=set();pending=[];count=0
 with tarfile.open(archive,'r:gz') as tf:
  for m in tf:
   n=posixpath.normpath(m.name)
   while n.startswith('./'):n=n[2:]
   if n in ('','.'):continue
   if m.name.startswith('/') or n=='..' or n.startswith('../') or n in seen:raise ValueError('unsafe archive member:'+m.name)
   seen.add(n);count+=1;out=dest/n;out.parent.mkdir(parents=True,exist_ok=True)
   if m.isdir():out.mkdir(parents=True,exist_ok=True);os.chmod(out,m.mode&0o7777)
   elif m.isfile():
    src=tf.extractfile(m)
    if src is None:raise ValueError('missing member body:'+n)
    with out.open('wb') as f:shutil.copyfileobj(src,f)
    os.chmod(out,m.mode&0o7777)
   elif m.issym() or m.islnk():
    target=m.linkname
    if os.path.isabs(target):raise ValueError('absolute link:'+n)
    resolved=(out.parent/target).resolve(strict=False);root=dest.resolve()
    if resolved!=root and root not in resolved.parents:raise ValueError('escaping link:'+n)
    pending.append((out,target,m.islnk()))
   else:raise ValueError('unsupported member:'+n)
 for out,target,hard in pending:
  if hard:os.link((out.parent/target).resolve(),out)
  else:os.symlink(target,out)
 return {'member_count':count,'unique_count':len(seen),'pass':count==len(seen)}
def prefix_facts(p:Path)->dict[str,bool]:
 bindir=p/'bin';libdir=p/'lib'
 launcher=bindir.is_dir() and any(x.name.startswith('python3.') for x in bindir.iterdir())
 stdlib=libdir.is_dir() and any(x.name.startswith('python3.') and x.is_dir() for x in libdir.iterdir())
 sysconfig=stdlib and any(x.name.startswith('_sysconfigdata') and x.suffix=='.py' for x in libdir.rglob('_sysconfigdata*.py'))
 return {'launcher':launcher,'bin':bindir.is_dir(),'lib':libdir.is_dir(),'stdlib':stdlib,'sysconfig':sysconfig,'include':(p/'include').is_dir(),'python_json':(p/'PYTHON.json').is_file()}

def find_prefix(root:Path)->Path:
 c=[]
 if (root/'prefix').is_dir():c.append(root/'prefix')
 for p in root.rglob('bin'):
  if p.is_dir() and any(x.name.startswith('python3.') for x in p.iterdir()):c.append(p.parent)
 for p in root.rglob('lib'):
  if p.is_dir() and any(x.name.startswith('python3.') and x.is_dir() for x in p.iterdir()):c.append(p.parent)
 uniq=[]
 for p in c:
  p=p.resolve()
  if p not in uniq:uniq.append(p)
 def score(p:Path)->tuple[int,int,int]:
  f=prefix_facts(p);return (sum(map(int,f.values())),int(p.name=='prefix'),-len(p.parts))
 if not uniq:raise RuntimeError('prefix not found')
 best=max(uniq,key=score);f=prefix_facts(best)
 # Official Python.org Android packages are embedded distributions. A console
 # launcher and prefix/bin are not required; prefix/lib/python3.X plus the
 # installed sysconfig data are the executable package-analysis anchors.
 if not (f['lib'] and f['stdlib'] and f['sysconfig']):raise RuntimeError('prefix incomplete:'+str(best)+':'+json.dumps(f,sort_keys=True))
 return best

def find_package_file(root:Path,prefix:Path,name:str)->Path|None:
 candidates=[prefix/name,root/name,prefix.parent/name]
 candidates.extend(sorted(root.rglob(name)))
 seen=set()
 for p in candidates:
  try:q=p.resolve()
  except OSError:continue
  if q in seen:continue
  seen.add(q)
  if p.is_file():return p
 return None

def parse_sysconfig(path:Path)->dict[str,Any]:
 try:tree=ast.parse(path.read_text(errors='replace'))
 except Exception:return {'path':str(path),'parse_pass':False,'keys':[],'values':{}}
 value=None
 for n in tree.body:
  if isinstance(n,(ast.Assign,ast.AnnAssign)):
   targets=n.targets if isinstance(n,ast.Assign) else [n.target]
   if any(isinstance(t,ast.Name) and t.id=='build_time_vars' for t in targets):
    try:value=ast.literal_eval(n.value)
    except Exception:value=None
 if not isinstance(value,dict):return {'path':str(path),'parse_pass':False,'keys':[],'values':{}}
 selected={k:value.get(k) for k in ['VERSION','py_version','ABIFLAGS','SOABI','EXT_SUFFIX','MULTIARCH','MACHDEP','ANDROID_API_LEVEL','HOST_GNU_TYPE','BUILD_GNU_TYPE','CC','CFLAGS','LDFLAGS','LIBDIR','LIBPL','BINDIR','INCLUDEPY','DESTSHARED','HAVE_PIDFD_OPEN','HAVE_PIDFD_SEND_SIGNAL'] if k in value}
 return {'path':str(path),'parse_pass':True,'keys':sorted(map(str,value)),'values':selected,'value_fingerprint':hashlib.sha256(json.dumps(value,sort_keys=True,default=str).encode()).hexdigest()}
def readelf_surface(p:Path,readelf:str)->dict[str,Any]:
 d=run([readelf,'-dW',str(p)],30);h=run([readelf,'-hW',str(p)],30);paths=[]
 for line in d['stdout'].splitlines():
  if '(RUNPATH)' in line or '(RPATH)' in line:
   m=re.search(r'\[(.*?)\]',line)
   if m:paths.extend(m.group(1).split(':'))
 return {'returncode':0 if d['returncode']==0 and h['returncode']==0 else 1,'runpath':paths,'class':'ELF64' if 'ELF64' in h['stdout'] else None,'machine':'AArch64' if 'AArch64' in h['stdout'] else None}
def is_elf(p:Path)->bool:
 try:return p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'
 except OSError:return False

def flatten_json(v:Any,prefix='')->dict[str,Any]:
 out={}
 if isinstance(v,dict):
  for k,x in v.items():out.update(flatten_json(x,f'{prefix}.{k}' if prefix else str(k)))
 elif isinstance(v,list):
  for i,x in enumerate(v):out.update(flatten_json(x,f'{prefix}[{i}]'))
 else:out[prefix]=v
 return out

def snapshot(label:str,archive:Path,manifest:dict[str,Any],work:Path,readelf:str)->dict[str,Any]:
 package_root=work/label;ext=safe_extract(archive,package_root);prefix=find_prefix(package_root)
 rows={};normalized={};collisions=[]
 for p in sorted(prefix.rglob('*')):
  rel=p.relative_to(prefix).as_posix();nrel=normver(rel)
  if p.is_symlink():row={'kind':'symlink','target':os.readlink(p)}
  elif p.is_dir():row={'kind':'directory'}
  elif p.is_file():row={'kind':'file','size':p.stat().st_size,'sha256':sha(p)}
  else:continue
  rows[rel]=row
  if nrel in normalized and normalized[nrel]!=row:collisions.append(nrel)
  normalized[nrel]=row
 launchers=[];shared=[];extensions=[];elf=[];runpaths={}
 for rel,row in rows.items():
  p=prefix/rel
  if rel.startswith('bin/python'):launchers.append({'path':rel,**row})
  if re.match(r'lib/(?:lib)?python.*\.so',rel) or re.match(r'lib/lib[^/]+\.so',rel):shared.append(rel)
  if '/lib-dynload/' in rel and rel.endswith('.so'):extensions.append(rel)
  if row['kind']=='file' and is_elf(p):
   surf=readelf_surface(p,readelf);elf.append({'path':rel,'sha256':row['sha256'],**surf})
   if surf['runpath']:runpaths[normver(rel)]=[normver(x) for x in surf['runpath']]
 sc=[]
 for p in sorted(prefix.rglob('_sysconfigdata*.py')):sc.append(parse_sysconfig(p))
 pyjson={};pj=find_package_file(package_root,prefix,'PYTHON.json');pyjson_rel=None
 if pj is not None:
  pyjson_rel=pj.relative_to(package_root).as_posix()
  try:pyjson=json.loads(pj.read_text())
  except Exception:pyjson={'parse_error':True}
 build_details=[]
 for p in sorted(package_root.rglob('build-details.json')):
  rel=p.relative_to(package_root).as_posix()
  try:build_details.append({'path':rel,'data':json.loads(p.read_text())})
  except Exception:build_details.append({'path':rel,'parse_error':True})
 wheels=sorted(p.relative_to(package_root).as_posix() for p in package_root.rglob('*.whl'))
 pyvers=sorted(set(re.findall(r'python(3\.\d+)', '\n'.join(rows))))
 pidfd=[]
 for p in prefix.rglob('*.py'):
  if p.name in {'subprocess.py','selectors.py','posixpath.py'} or 'multiprocessing' in p.parts:
   text=p.read_text(errors='ignore')
   if 'pidfd' in text.lower():pidfd.append({'path':p.relative_to(prefix).as_posix(),'occurrences':text.lower().count('pidfd')})
 syskeys=sorted(set(k for x in sc for k in x.get('keys',[])))
 selected={}
 for x in sc:
  selected.update(x.get('values',{}))
 facts=prefix_facts(prefix)
 return {'schema_version':3,'label':label,'input':manifest,'archive_sha256':sha(archive),'archive_size':archive.stat().st_size,'extraction':ext,'prefix_rel':prefix.relative_to(package_root).as_posix(),'prefix_facts':facts,'distribution_mode':'embedded-android','console_launcher_expected':False,'console_launcher_present':bool(launchers),'python_json_rel':pyjson_rel,'path_count':len(rows),'normalized_path_count':len(normalized),'normalized_path_collisions':sorted(set(collisions)),'rows':rows,'normalized_rows':normalized,'launchers':launchers,'shared_libraries':sorted(shared),'extensions':sorted(extensions),'extension_modules':sorted(normver(Path(x).name.split('.')[0]) for x in extensions),'elf_count':len(elf),'elf':elf,'runpaths':runpaths,'sysconfig_files':sc,'sysconfig_keys':syskeys,'sysconfig_selected':selected,'python_json':pyjson,'python_json_flat':flatten_json(pyjson),'build_details':build_details,'wheels':wheels,'python_versions':pyvers,'pidfd_static_evidence':pidfd,'pass':ext['pass'] and not collisions and facts['lib'] and facts['stdlib'] and facts['sysconfig'] and bool(sc)}

def set_delta(a:list[str],b:list[str])->dict[str,Any]:
 aa=set(a);bb=set(b);return {'added':sorted(bb-aa),'removed':sorted(aa-bb),'unchanged_count':len(aa&bb),'added_count':len(bb-aa),'removed_count':len(aa-bb)}
def map_delta(a:dict[str,Any],b:dict[str,Any])->dict[str,Any]:
 keys=set(a)|set(b);added=[];removed=[];changed=[]
 for k in sorted(keys):
  if k not in a:added.append(k)
  elif k not in b:removed.append(k)
  elif a[k]!=b[k]:changed.append({'key':k,'from':a[k],'to':b[k]})
 return {'added':added,'removed':removed,'changed':changed,'added_count':len(added),'removed_count':len(removed),'changed_count':len(changed)}
def normalized_layout_delta(a:dict[str,Any],b:dict[str,Any])->dict[str,Any]:
 aa={k:v['kind'] for k,v in a['normalized_rows'].items()};bb={k:v['kind'] for k,v in b['normalized_rows'].items()};return map_delta(aa,bb)
def source_assumptions(root:Path)->dict[str,Any]:
 files=[]
 for _,(rel,_) in AUTH.items():
  try:d=load(root/rel)
  except Exception:continue
  for name in d.get('file_identities',{}):
   p=(root/rel).parent/name
   if p.suffix in {'.py','.sh','.c'} and p.is_file():files.append(p)
 files=sorted(set(files));patterns=['python3.14','libpython3.14','3.14','cp314','cpython-314','python3.15','libpython3.15','3.15','cp315']
 hits=[]
 for p in files:
  text=p.read_text(errors='ignore');counts={x:text.count(x) for x in patterns if text.count(x)}
  if counts:hits.append({'path':p.relative_to(root).as_posix(),'counts':counts})
 return {'files_scanned':len(files),'files_with_version_literals':len(hits),'hits':hits,'parameterization_required':bool(hits),'pass':True}
def classify_sysconfig_changes(delta:dict[str,Any])->dict[str,int]:
 out={'version_or_tag':0,'path_or_toolchain':0,'feature_flag':0,'other':0}
 for x in delta['changed']:
  k=x['key'].upper()
  if any(t in k for t in ['VERSION','SOABI','SUFFIX','MULTIARCH','ABI']):out['version_or_tag']+=1
  elif any(t in k for t in ['DIR','PATH','CC','CFLAGS','LDFLAGS','HOST','BUILD','PREFIX']):out['path_or_toolchain']+=1
  elif k.startswith('HAVE_') or k.startswith('WITH_'):out['feature_flag']+=1
  else:out['other']+=1
 return out

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--current-archive',type=Path,required=True);ap.add_argument('--patch-archive',type=Path,required=True);ap.add_argument('--preview-archive',type=Path,required=True);ap.add_argument('--current-manifest',type=Path,required=True);ap.add_argument('--patch-manifest',type=Path,required=True);ap.add_argument('--preview-manifest',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--readelf',default='readelf');a=ap.parse_args()
 root=a.root.resolve();work=a.work.resolve();out=a.output.resolve();shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True);out.mkdir(parents=True,exist_ok=True)
 if sha(a.current_archive)!=CURRENT_SHA or a.current_archive.stat().st_size!=CURRENT_SIZE:raise SystemExit('current archive identity mismatch')
 for name,(rel,h) in AUTH.items():
  if sha(root/rel)!=h:raise SystemExit('authority mismatch:'+name)
 manifests=[load(a.current_manifest),load(a.patch_manifest),load(a.preview_manifest)]
 expected_names=['python-3.14.6-aarch64-linux-android.tar.gz','python-3.14.5-aarch64-linux-android.tar.gz','python-3.15.0b4-aarch64-linux-android.tar.gz']
 for m,n,p in zip(manifests,expected_names,[a.current_archive,a.patch_archive,a.preview_archive]):
  if m.get('filename')!=n or m.get('sha256')!=sha(p) or m.get('size')!=p.stat().st_size or m.get('sigstore_digest_match') is not True:raise SystemExit('input manifest binding mismatch:'+n)
 current=snapshot('current-3.14.6',a.current_archive,manifests[0],work,a.readelf);patch=snapshot('patch-predecessor-3.14.5',a.patch_archive,manifests[1],work,a.readelf);preview=snapshot('preview-3.15.0b4',a.preview_archive,manifests[2],work,a.readelf)
 if not all(x['pass'] for x in [current,patch,preview]):raise SystemExit('snapshot failed')
 owner_exact=all(m.get('acquisition_scope')=='bounded-owner-local' and m.get('exact_identity_verified') is True and m.get('acquisition_mode') in {'owner-local-cache-reuse','owner-local-bounded-download'} for m in manifests);identities={'schema_version':3,'inputs':[{'role':'current-accepted','version':'3.14.6',**manifests[0]},{'role':'official-patch-predecessor','version':'3.14.5',**manifests[1]},{'role':'python315-preview','version':'3.15.0b4',**manifests[2]}],'all_sigstore_digest_bound':all(m.get('sigstore_digest_match') is True for m in manifests),'all_exact_owner_inputs':owner_exact,'owner_network_download_count':sum(1 for m in manifests if m.get('network_acquisition') is True),'preview_release_claim':False,'pass':owner_exact and all(m.get('sigstore_digest_match') is True for m in manifests)};dump(out/'input-identities.json',identities)
 patch_layout=normalized_layout_delta(patch,current);preview_layout=normalized_layout_delta(current,preview)
 patch_ext=set_delta(patch['extension_modules'],current['extension_modules']);preview_ext=set_delta(current['extension_modules'],preview['extension_modules'])
 patch_shared=set_delta([normver(x) for x in patch['shared_libraries']],[normver(x) for x in current['shared_libraries']]);preview_shared=set_delta([normver(x) for x in current['shared_libraries']],[normver(x) for x in preview['shared_libraries']])
 layout={'schema_version':1,'patch_update':{'from':'3.14.5','to':'3.14.6','normalized_layout':patch_layout,'extension_modules':patch_ext,'shared_libraries':patch_shared,'raw_counts':{'from_paths':patch['path_count'],'to_paths':current['path_count'],'from_extensions':len(patch['extensions']),'to_extensions':len(current['extensions'])}},'python315_preview':{'from':'3.14.6','to':'3.15.0b4','normalized_layout':preview_layout,'extension_modules':preview_ext,'shared_libraries':preview_shared,'raw_counts':{'from_paths':current['path_count'],'to_paths':preview['path_count'],'from_extensions':len(current['extensions']),'to_extensions':len(preview['extensions'])}},'complete':True,'pass':True};dump(out/'layout-and-extension-delta.json',layout)
 patch_sys=map_delta(patch['sysconfig_selected'],current['sysconfig_selected']);preview_sys=map_delta(current['sysconfig_selected'],preview['sysconfig_selected']);patch_keys=set_delta(patch['sysconfig_keys'],current['sysconfig_keys']);preview_keys=set_delta(current['sysconfig_keys'],preview['sysconfig_keys']);patch_run=map_delta(patch['runpaths'],current['runpaths']);preview_run=map_delta(current['runpaths'],preview['runpaths'])
 runsc={'schema_version':1,'patch_update':{'sysconfig_keys':patch_keys,'sysconfig_selected':patch_sys,'sysconfig_change_classes':classify_sysconfig_changes(patch_sys),'runpaths':patch_run},'python315_preview':{'sysconfig_keys':preview_keys,'sysconfig_selected':preview_sys,'sysconfig_change_classes':classify_sysconfig_changes(preview_sys),'runpaths':preview_run},'selected_launcher_authority_sha256':AUTH['loader'][1],'sysconfig_authority_sha256':AUTH['sysconfig'][1],'complete':True,'pass':True};dump(out/'runpath-and-sysconfig-delta.json',runsc)
 patch_wheels=set_delta([normver(x) for x in patch['wheels']],[normver(x) for x in current['wheels']]);preview_wheels=set_delta([normver(x) for x in current['wheels']],[normver(x) for x in preview['wheels']]);wheelpip={'schema_version':1,'patch_update':{'wheels':patch_wheels,'python_json':map_delta(patch['python_json_flat'],current['python_json_flat']),'pip_strategy':'bundled-wheel inventory comparison; no base-pip product selection','compatibility_qualification_required':True},'python315_preview':{'wheels':preview_wheels,'python_json':map_delta(current['python_json_flat'],preview['python_json_flat']),'pip_strategy':'preview bundled wheels are inventory evidence only; separate compatibility qualification required','expected_abi_tag_family':'cp315','release_or_product_selection':False},'ut5_base_pip_selected':False,'ut5_uv_selected':False,'complete':True,'pass':True};dump(out/'wheel-and-pip-delta.json',wheelpip)
 assumptions=source_assumptions(root);config={'schema_version':1,'patch_update':{'configuration_only_candidate':not any([patch_layout['added_count'],patch_layout['removed_count'],patch_ext['added_count'],patch_ext['removed_count'],patch_shared['added_count'],patch_shared['removed_count'],patch_keys['added_count'],patch_keys['removed_count']]),'non_configuration_delta_count':sum([patch_layout['added_count'],patch_layout['removed_count'],patch_ext['added_count'],patch_ext['removed_count'],patch_shared['added_count'],patch_shared['removed_count'],patch_keys['added_count'],patch_keys['removed_count']]),'configuration_changes':['version','URL','checksum','upstream metadata','expected package identity'],'qualification_replay_required':True},'version_specific_assumptions':assumptions,'automation_boundary':{'parameterize_package_identity':True,'parameterize_python_minor':True,'re-run_full_authority_chain':True,'configuration_only_may_not_bypass_runtime_qualification':True},'complete':True,'pass':True};dump(out/'configuration-only-delta.json',config)
 patch_changed=map_delta({k:v.get('sha256') or json.dumps(v,sort_keys=True) for k,v in patch['normalized_rows'].items()},{k:v.get('sha256') or json.dumps(v,sort_keys=True) for k,v in current['normalized_rows'].items()})
 rehearsal={'schema_version':1,'from_version':'3.14.5','to_version':'3.14.6','official_inputs':identities['inputs'][:2],'expected_identity_changes':['version','URL','checksum','upstream metadata','expected package identity'],'all_other_normalized_file_changes':patch_changed,'layout_extension_delta_file':'layout-and-extension-delta.json','runpath_sysconfig_delta_file':'runpath-and-sysconfig-delta.json','wheel_pip_delta_file':'wheel-and-pip-delta.json','qualification_replay_required':['loader and native closure','relocation','sysconfig and native SDK','Android data and state policy','feature qualification','platform portability'],'configuration_only_candidate':config['patch_update']['configuration_only_candidate'],'every_non_identity_delta_recorded':True,'pass':True};dump(out/'patch-update-rehearsal.json',rehearsal)
 preview_changed=map_delta({k:v.get('kind') for k,v in current['normalized_rows'].items()},{k:v.get('kind') for k,v in preview['normalized_rows'].items()});preview_delta={'schema_version':1,'preview_version':'3.15.0b4','preview_only':True,'release_claim':False,'runtime_support_claim':False,'product_selection':False,'package_and_prefix_layout':preview_layout,'launcher_and_getpath':{'upstream_distribution_mode':preview['distribution_mode'],'console_launcher_expected':preview['console_launcher_expected'],'launcher_paths':preview['launchers'],'local_product_launcher_authority_remains_separate':True,'version_parameterization_required':True},'sysconfig':{'keys':preview_keys,'selected_values':preview_sys},'extension_surface':preview_ext,'wheel_and_abi_tags':preview_wheels,'pidfd_related_subprocess_behavior':{'static_evidence':preview['pidfd_static_evidence'],'direct_runtime_qualified':False,'qualification_required':True},'pip_strategy':wheelpip['python315_preview']['pip_strategy'],'version_specific_transformations':assumptions,'all_normalized_layout_changes':preview_changed,'evidence_not_release_claim':True,'pass':True};dump(out/'python315-preview-delta.json',preview_delta)
 security={'schema_version':1,'ownership':[{'surface':'CPython source security fixes and CVE response','owner':'CPython upstream','local_obligation':'consume signed official patch releases and review release notes'},{'surface':'Android package production and upstream Android patches','owner':'Python.org/BeeWare release pipeline','local_obligation':'verify official identity and enumerate packaging deltas'},{'surface':'launcher, RUNPATH, relocation, sysconfig and metadata transformations','owner':'local cpython-android-cli maintainers','local_obligation':'replay full authority chain for each accepted update'},{'surface':'bundled dependency versions, wheel and pip policy','owner':'shared upstream plus local policy','local_obligation':'inventory changes and requalify selected surfaces'},{'surface':'preview interpretation','owner':'local research maintainers','local_obligation':'never convert preview evidence into a release or support claim'}],'maintenance_model':{'minimum_roles':['implementation maintainer','independent reviewer'],'patch_update_steps':['acquire and bind official artifacts','run structural delta','review non-identity changes','replay qualification','freeze successor authority'],'release_cadence_decision_enabled':True,'staffing_decision_enabled':True,'automatic_release_on_green':False},'pass':True};dump(out/'security-ownership.json',security)
 gate={'official_inputs_sigstore_bound':bool(identities['all_sigstore_digest_bound'] and identities['all_exact_owner_inputs']),'patch_update_rehearsal_complete':bool(rehearsal['pass'] and rehearsal['every_non_identity_delta_recorded']),'configuration_only_boundary_explicit':bool(config['pass'] and config['automation_boundary']['configuration_only_may_not_bypass_runtime_qualification']),'layout_and_extension_delta_complete':bool(layout['pass']),'runpath_and_sysconfig_delta_complete':bool(runsc['pass']),'wheel_and_pip_delta_complete':bool(wheelpip['pass']),'python315_preview_delta_complete':bool(preview_delta['pass']),'preview_release_claim_absent':bool(preview_delta['release_claim'] is False and preview_delta['runtime_support_claim'] is False),'version_specific_assumptions_explicit':bool(assumptions['pass'] and assumptions['parameterization_required']),'security_ownership_explicit':bool(security['pass'] and len(security['ownership'])>=5),'update_burden_explicit':bool(rehearsal['qualification_replay_required'] and security['maintenance_model']['patch_update_steps']),'authority_bindings_exact':True,'epoch3_selection_absent':bool(preview_delta['product_selection'] is False)}
 failed=[k for k,v in gate.items() if v is not True];diag={'schema_version':1,'gate_condition':gate,'failed_gate_conditions':failed,'exit_condition':{'patch_normalized_changed_count':patch_changed['changed_count'],'patch_layout_added':patch_layout['added_count'],'patch_layout_removed':patch_layout['removed_count'],'patch_sysconfig_key_added':patch_keys['added_count'],'patch_sysconfig_key_removed':patch_keys['removed_count'],'preview_layout_added':preview_layout['added_count'],'preview_layout_removed':preview_layout['removed_count'],'preview_extension_added':preview_ext['added_count'],'preview_extension_removed':preview_ext['removed_count'],'version_literal_file_count':assumptions['files_with_version_literals'],'preview_release_claim':False,'epoch3_selection':False},'pass':not failed};dump(out/'ut7-gate-diagnostics.json',diag)
 if failed:raise SystemExit('UT-7 gate failed:'+json.dumps(gate,sort_keys=True))
 print(json.dumps({'pass':True,'gate':gate,'exit_condition':diag['exit_condition']},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
