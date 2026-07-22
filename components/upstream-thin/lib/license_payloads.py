#!/usr/bin/env python3
"""Deterministic RB-1 license payload acquisition and component expansion audit."""
from __future__ import annotations
import hashlib, io, json, os, re, subprocess, tarfile
from pathlib import Path, PurePosixPath
from typing import Iterable
from archive import safe_link_target
FAMILY_FINGERPRINT="87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302"
FULL_SHA="20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12"
CPYTHON_SOURCE_SHA="74d0d71d0600e477651a077101d6e62d1e2e69b8e992ba18c993dd643b7ba222"
CPYTHON_SOURCE_SIZE=31234628
BASE_COMPONENTS=["cpython","project-launcher","pip","openssl","sqlite","bzip2","xz-liblzma","zstd","expat","libmpdec","libffi","android-system-providers"]
LICENSE_NAMES=("license","copying","notice","copyright","authors","legal","patents")

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def write_json(p:Path,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def safe_name(name:str)->str:
 p=PurePosixPath(name)
 if name.startswith('/') or '..' in p.parts or '\\' in name or not name:return ''
 parts=[x for x in p.parts if x not in ('','.')]
 return '/'.join(parts)
def license_like(path:str,data:bytes|None=None)->bool:
 n=PurePosixPath(path).name.casefold()
 stem=n.split('.')[0]
 if stem.startswith(LICENSE_NAMES) or any(n==x or n.startswith(x+'.') for x in LICENSE_NAMES):return True
 if n in {'readme','readme.md','readme.txt'} and data is not None:
  s=data[:65536].decode('utf-8','ignore').casefold();return 'license' in s or 'public domain' in s or 'permission is hereby granted' in s
 return False

def iter_tar(path:Path):
 if path.name.endswith('.tar.zst'):
  proc=subprocess.Popen(['zstd','-dc','--',str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  assert proc.stdout is not None
  tf=tarfile.open(fileobj=proc.stdout,mode='r|')
  try:
   for m in tf:yield tf,m
  finally:
   tf.close();proc.stdout.close();err=proc.stderr.read() if proc.stderr else b'';rc=proc.wait()
   if proc.stderr: proc.stderr.close()
   if rc:raise RuntimeError(f'zstd failed rc={rc}: {err.decode("utf-8","replace")[-400:]}')
 else:
  with tarfile.open(path,'r:*') as tf:
   for m in tf:yield tf,m

def inventory_source_archive(component:str,path:Path,expected_sha:str,expected_version:str,out:Path):
 actual=sha_file(path)
 if actual!=expected_sha:raise ValueError(f'{component} source sha mismatch: {actual}')
 seen=set();rows=[];selected=0
 for tf,m in iter_tar(path):
  name=safe_name(m.name)
  if not name:raise ValueError(f'unsafe source member: {m.name!r}')
  if name in seen:raise ValueError(f'duplicate source member: {name}')
  seen.add(name)
  if m.isdir():continue
  if m.issym():
   if not safe_link_target(name,m.linkname):raise ValueError(f'unsafe source symlink: {name} -> {m.linkname}')
   continue
  if m.islnk() or m.isdev() or m.isfifo() or not m.isfile():
   raise ValueError(f'unsupported source member type: {name}')
  if m.size>2*1024*1024:continue
  f=tf.extractfile(m);data=f.read() if f else b''
  if len(data)!=m.size:raise ValueError(f'truncated source member: {name}')
  if not license_like(name,data):continue
  rel=PurePosixPath(*PurePosixPath(name).parts[1:]).as_posix() if len(PurePosixPath(name).parts)>1 else PurePosixPath(name).name
  if not rel:rel=PurePosixPath(name).name
  dest=out/component/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);selected+=1
  rows.append({'source_path':name,'evidence_path':f'{component}/{rel}','sha256':sha_bytes(data),'size_bytes':len(data)})
 return {'component':component,'version':expected_version,'archive':{'filename':path.name,'sha256':actual,'size_bytes':path.stat().st_size},'license_evidence':sorted(rows,key=lambda x:x['evidence_path']),'license_evidence_count':selected,'status':'evidence-acquired' if selected else 'no-license-like-file-found'}

def read_cpython_source(source:Path,out:Path):
 if sha_file(source)!=CPYTHON_SOURCE_SHA or source.stat().st_size!=CPYTHON_SOURCE_SIZE:raise ValueError('CPython source identity mismatch')
 selected=[];mpdec_hits=[];hacl_files=[];seen=set()
 for tf,m in iter_tar(source):
  name=safe_name(m.name)
  if not name:raise ValueError(f'unsafe CPython source member: {m.name!r}')
  if name in seen:raise ValueError(f'duplicate CPython source member: {name}')
  seen.add(name)
  if m.isdir():continue
  if m.issym():
   if not safe_link_target(name,m.linkname):raise ValueError(f'unsafe CPython source symlink: {name} -> {m.linkname}')
   continue
  if m.islnk() or m.isdev() or m.isfifo() or not m.isfile():raise ValueError(f'unsupported CPython source member type: {name}')
  if m.size>3*1024*1024:continue
  relevant=(name.endswith('/LICENSE') or name.endswith('/Misc/externals.spdx.json') or '/Modules/' in name)
  if not relevant:continue
  f=tf.extractfile(m);data=f.read() if f else b''
  low=name.casefold()
  keep=license_like(name,data) or low.endswith('/misc/externals.spdx.json')
  if '/modules/_decimal/libmpdec/' in low and (b'2.5.1' in data or re.search(rb'(?i)mpd[_ ]version',data)):
   mpdec_hits.append({'source_path':name,'sha256':sha_bytes(data),'size_bytes':len(data),'contains_2_5_1':b'2.5.1' in data})
   keep=True
  if '/modules/_hacl/' in low:
   hacl_files.append({'source_path':name,'sha256':sha_bytes(data),'size_bytes':len(data),'license_like':license_like(name,data)})
   if license_like(name,data) or PurePosixPath(name).name.casefold().startswith('readme'):keep=True
  if keep:
   parts=PurePosixPath(name).parts;rel='/'.join(parts[1:]) if len(parts)>1 else parts[0];dest=out/'cpython'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);selected.append({'source_path':name,'evidence_path':f'cpython/{rel}','sha256':sha_bytes(data),'size_bytes':len(data)})
 if not any(x['contains_2_5_1'] for x in mpdec_hits):raise ValueError('libmpdec 2.5.1 not found in exact CPython bundled source')
 return {'archive':{'filename':source.name,'sha256':sha_file(source),'size_bytes':source.stat().st_size},'license_evidence':sorted(selected,key=lambda x:x['evidence_path']),'libmpdec_version_evidence':sorted(mpdec_hits,key=lambda x:x['source_path']),'hacl_source_evidence':sorted(hacl_files,key=lambda x:x['source_path'])}

def scan_full(full:Path,expected_sha:str=FULL_SHA):
 before={'sha256':sha_file(full),'size_bytes':full.stat().st_size}
 if before['sha256']!=expected_sha:raise ValueError('full artifact identity mismatch')
 hits={'hacl':[],'libmpdec':[]};members=[]
 for tf,m in iter_tar(full):
  name=safe_name(m.name)
  if not name:raise ValueError(f'unsafe full member: {m.name!r}')
  if not m.isfile() or m.size>20*1024*1024:continue
  low=name.casefold()
  wanted=('/lib-dynload/_hmac.' in low or '/lib-dynload/_sha3.' in low or '/lib-dynload/_decimal.' in low)
  if not wanted:continue
  f=tf.extractfile(m);data=f.read() if f else b'';row={'path':name,'sha256':sha_bytes(data),'size_bytes':len(data)};members.append(row)
  if b'Modules/_hacl/' in data or b'Modules\\_hacl\\' in data or b'HACL*' in data:hits['hacl'].append(row)
  if b'2.5.1' in data and b'libmpdec' in data:hits['libmpdec'].append(row)
 after={'sha256':sha_file(full),'size_bytes':full.stat().st_size}
 if before!=after:raise ValueError('full artifact mutated during audit')
 if not hits['hacl']:raise ValueError('required HACL* distributed-byte evidence absent')
 if not hits['libmpdec']:raise ValueError('required libmpdec 2.5.1 distributed-byte evidence absent')
 return {'identity':before,'examined_members':sorted(members,key=lambda x:x['path']),'hacl_evidence':sorted(hits['hacl'],key=lambda x:x['path']),'libmpdec_evidence':sorted(hits['libmpdec'],key=lambda x:x['path']),'identity_preserved':True}

def find_full(family:Path)->Path:
 files=list(family.glob('*-full.tar.zst'))
 if len(files)!=1:raise ValueError(f'expected one full artifact, got {len(files)}')
 return files[0]

def acquire_license_evidence(family:Path,cpython_source:Path,sources:dict[str,dict],output:Path,root:Path,expected_full_sha:str=FULL_SHA):
 output.mkdir(parents=True,exist_ok=True);payload=output/'payload';payload.mkdir(exist_ok=True)
 full=find_full(family);full_scan=scan_full(full,expected_full_sha)
 cpy=read_cpython_source(cpython_source,payload)
 source_rows=[]
 for component in sorted(sources):
  spec=sources[component];source_rows.append(inventory_source_archive(component,Path(spec['path']),spec['sha256'],spec['version'],payload/'source-deps'))
 repo_license=root/'LICENSE';ldata=repo_license.read_bytes();(payload/'project').mkdir(exist_ok=True);(payload/'project/LICENSE').write_bytes(ldata)
 source_prov=json.loads((root/'experiments/epoch3-upstream-thin-release-blockers/rb1-source-provenance-authority-evidence/source-provenance.json').read_text())
 spdx={x['name']:x for x in source_prov['cpython_source']['spdx_packages']}
 mismatch=[{'component':'xz-liblzma','frozen_product_version':'5.4.6','quarantined_source_version':spdx['xz']['version'],'reason':'version-mismatch'}, {'component':'libmpdec','frozen_product_version':'2.5.1','quarantined_source_version':spdx['mpdecimal']['version'],'reason':'version-mismatch'}]
 expanded=BASE_COMPONENTS+['hacl-star']
 expansion={'schema_version':1,'audit_kind':'epoch3-rb1-component-expansion','family_fingerprint_sha256':FAMILY_FINGERPRINT,'baseline_components':BASE_COMPONENTS,'expanded_components':expanded,'new_components':[{'component_class':'hacl-star','distributed_byte_evidence':full_scan['hacl_evidence'],'source_evidence_count':len(cpy['hacl_source_evidence'])}],'libmpdec':{'frozen_version':'2.5.1','distributed_byte_evidence':full_scan['libmpdec_evidence'],'source_evidence':cpy['libmpdec_version_evidence']},'mismatch_quarantine':mismatch,'pass':True,'claim_boundary':{'component_set_complete':False,'component_license_mapping_complete':False,'rb1_closed':False,'selectable':False,'publication':False}}
 inventory={'schema_version':1,'inventory_kind':'epoch3-rb1-authoritative-license-source-evidence','family_fingerprint_sha256':FAMILY_FINGERPRINT,'full_artifact':full_scan,'cpython_source':cpy,'source_archives':source_rows,'project_license':{'source_path':'LICENSE','evidence_path':'project/LICENSE','sha256':sha_bytes(ldata),'size_bytes':len(ldata)},'claim_boundary':{'payload_is_evidence_not_release_asset':True,'license_payloads_integrated_into_release_family':False,'component_license_mapping_complete':False,'rb1_closed':False,'selectable':False,'publication':False}}
 evidence_by={r['component']:r for r in source_rows}
 rows=[]
 versions={'cpython':'3.14.6','project-launcher':None,'pip':'26.1.2','openssl':'3.5.7','sqlite':'3.50.4','bzip2':'1.0.8','xz-liblzma':'5.4.6','zstd':'1.5.7','expat':'2.8.1','libmpdec':'2.5.1','libffi':'3.4.4','android-system-providers':None,'hacl-star':'bundled-with-cpython-3.14.6'}
 for comp in expanded:
  status='candidate-evidence-present';paths=[]
  if comp in evidence_by:paths=[x['evidence_path'] for x in evidence_by[comp]['license_evidence']];status=evidence_by[comp]['status']
  elif comp=='cpython':paths=[x['evidence_path'] for x in cpy['license_evidence'] if x['source_path'].endswith('/LICENSE')]
  elif comp=='project-launcher':paths=['project/LICENSE']
  elif comp=='pip':status='already-packaged-license-inventory-present'
  elif comp=='expat':paths=[x['evidence_path'] for x in cpy['license_evidence'] if '/Modules/expat/' in x['source_path']]
  elif comp=='libmpdec':paths=[x['evidence_path'] for x in cpy['license_evidence'] if '/Modules/_decimal/libmpdec/' in x['source_path'] and license_like(x['source_path'])]
  elif comp=='hacl-star':paths=[x['evidence_path'] for x in cpy['license_evidence'] if '/Modules/_hacl/' in x['source_path']]
  elif comp=='xz-liblzma':status='exact-5.4.6-license-source-unresolved'
  elif comp=='android-system-providers':status='external-provider-policy-unfrozen'
  rows.append({'component_class':comp,'version':versions[comp],'status':status,'evidence_paths':sorted(paths),'mapping_complete':False,'release_family_integrated':False})
 cmap={'schema_version':1,'map_kind':'epoch3-rb1-component-license-map-candidate','components':rows,'component_count':len(rows),'new_component_count':1,'mapping_complete':False,'claim_boundary':{'candidate_only':True,'rb1_closed':False,'selectable':False,'publication':False}}
 gaps=[
 {'code':'complete-componentization-and-obligation-review-pending'},
 {'code':'authoritative-license-evidence-not-integrated-into-release-family'},
 {'code':'project-license-not-in-release-family'},
 {'code':'xz-5.4.6-exact-license-source-unresolved'},
 {'code':'sqlite-public-domain-notice-policy-not-frozen'},
 {'code':'android-system-provider-notice-boundary-not-frozen'},
 {'code':'hacl-star-new-component-mapping-and-notice-pending'},
 {'code':'final-notice-set-not-owner-approved'}]
 gap={'schema_version':1,'register_kind':'epoch3-rb1-license-payload-and-expansion-gap-register','source_provenance_gap_count':11,'newly_detected_component_count':1,'remaining_gaps':gaps,'blocking_gap_count':len(gaps),'closure_status':'incomplete','claim_boundary':{'component_license_mapping_complete':False,'rb1_closed':False,'selectable':False,'publication':False}}
 notice=['DRAFT NOTICE CANDIDATE — NOT A RELEASE NOTICE','',f'Frozen family: {FAMILY_FINGERPRINT}','This file inventories candidate evidence only. Legal and owner review remain required.','']
 for row in rows:
  notice.append(f"- {row['component_class']} {row['version'] or '(external/project)'}: {row['status']}")
  for x in row['evidence_paths']:notice.append(f'    evidence: {x}')
 notice_text='\n'.join(notice)+'\n'
 write_json(output/'component-expansion-audit.json',expansion);write_json(output/'license-payload-inventory.json',inventory);write_json(output/'component-license-map-candidate.json',cmap);write_json(output/'updated-gap-register.json',gap);(output/'NOTICE.candidate.txt').write_text(notice_text)
 result={'schema_version':1,'runner_kind':'epoch3-rb1-license-payload-acquisition-and-component-expansion','pass':True,'metrics':{'baseline_component_count':12,'expanded_component_count':len(rows),'new_component_count':1,'fixed_hash_source_archive_count':len(source_rows),'source_archives_with_license_evidence':sum(x['license_evidence_count']>0 for x in source_rows),'remaining_gap_count':len(gaps)},'full_artifact_identity_preserved':True,'outputs':['component-expansion-audit.json','license-payload-inventory.json','component-license-map-candidate.json','NOTICE.candidate.txt','updated-gap-register.json','payload/'],'claim_boundary':{'component_license_mapping_complete':False,'license_payloads_integrated_into_release_family':False,'rb1_closed':False,'selectable':False,'publication':False}}
 write_json(output/'payload-result.json',result);return result

def main() -> int:
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--family-dir',required=True,type=Path)
    parser.add_argument('--cpython-source',required=True,type=Path)
    parser.add_argument('--source',action='append',default=[])
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--root',default=Path(__file__).resolve().parents[3],type=Path)
    args=parser.parse_args();sources={}
    for item in args.source:
        component,path,digest,version=item.split('=',3)
        sources[component]={'path':path,'sha256':digest,'version':version}
    try:
        result=acquire_license_evidence(args.family_dir.resolve(),args.cpython_source.resolve(),sources,args.output_dir.resolve(),args.root.resolve())
        print(json.dumps(result,indent=2,sort_keys=True));return 0
    except Exception as exc:
        print(json.dumps({'schema_version':1,'runner_kind':'epoch3-rb1-license-payload-acquisition-and-component-expansion','pass':False,'error':f'{type(exc).__name__}: {exc}'},indent=2,sort_keys=True));return 1

if __name__=='__main__':
    raise SystemExit(main())
