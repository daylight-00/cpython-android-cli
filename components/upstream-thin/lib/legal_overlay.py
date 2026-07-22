#!/usr/bin/env python3
"""Deterministic RB-1 legal-evidence overlay and provider-policy candidate."""
from __future__ import annotations
import hashlib,json,re,shutil,tarfile,tempfile
from pathlib import Path,PurePosixPath
from archive import safe_link_target
from license_payloads import acquire_license_evidence,iter_tar,safe_name,sha_file,sha_bytes,write_json,CPYTHON_SOURCE_SHA,CPYTHON_SOURCE_SIZE,FAMILY_FINGERPRINT,FULL_SHA
from release_family import verify_release_family
XZ_SHA='320b76d45dc3499cf855e5310f875cba61c2608e4a98bb280cc4f1b8f189da1a';XZ_SIZE=651211
XZ_FILES={'COPYING':('29a1e305b2e34eefe5d4602d00cde1d528b71c5d9f2eec5106972cf6ddb6f73f',3347),'COPYING.GPLv2':('8177f97513213526df2cf6184d8ff986c675afb514d4e68a404010521b880643',18092),'AUTHORS':('07def6a20ec5430b6ad04cf1286da3f53fbb86cf6d2026119945ccd55d3a2258',1402)}
SYSTEM_LIBS=['libc.so','libdl.so','liblog.so','libm.so','libz.so']

def _regular_members(path:Path):
 seen=set()
 for tf,m in iter_tar(path):
  name=safe_name(m.name)
  if not name:raise ValueError(f'unsafe member: {m.name!r}')
  if name in seen:raise ValueError(f'duplicate member: {name}')
  seen.add(name)
  if m.isdir():continue
  if m.issym():
   if not safe_link_target(name,m.linkname):raise ValueError(f'unsafe symlink: {name} -> {m.linkname}')
   continue
  if m.islnk() or m.isdev() or m.isfifo() or not m.isfile():raise ValueError(f'unsupported member type: {name}')
  f=tf.extractfile(m);data=f.read() if f else b''
  if len(data)!=m.size:raise ValueError(f'truncated member: {name}')
  yield name,data

def _family_snapshot(family:Path):
 return [{'path':p.name,'sha256':sha_file(p),'size_bytes':p.stat().st_size} for p in sorted(family.iterdir()) if p.is_file()]

def extract_xz_product_evidence(path:Path,out:Path):
 if sha_file(path)!=XZ_SHA or path.stat().st_size!=XZ_SIZE:raise ValueError('XZ product asset identity mismatch')
 found={}
 for name,data in _regular_members(path):
  base=PurePosixPath(name).name
  if '/share/doc/xz/' not in '/'+name or base not in XZ_FILES:continue
  exp_sha,exp_size=XZ_FILES[base]
  if sha_bytes(data)!=exp_sha or len(data)!=exp_size:raise ValueError(f'XZ evidence mismatch: {base}')
  dest=out/base;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  found[base]={'source_path':name,'evidence_path':f'legal/licenses/xz/{base}','sha256':exp_sha,'size_bytes':exp_size}
 if set(found)!=set(XZ_FILES):raise ValueError(f'missing XZ evidence: {sorted(set(XZ_FILES)-set(found))}')
 return {'schema_version':1,'evidence_kind':'xz-5.4.6-product-matching-license-evidence','asset':{'filename':path.name,'sha256':XZ_SHA,'size_bytes':XZ_SIZE,'release_tag':'xz-5.4.6-1'},'files':[found[k] for k in sorted(found)],'product_version':'5.4.6','mismatched_cpython_spdx_version':'5.2.5','mismatched_spdx_quarantined':True,'pass':True}

def scan_sqlite_public_domain(path:Path,expected_sha:str,out:Path):
 if sha_file(path)!=expected_sha:raise ValueError('SQLite source identity mismatch')
 hits=[]
 phrases=(b'public domain',b'dedicat')
 for name,data in _regular_members(path):
  low=data[:262144].lower()
  if not any(x in low for x in phrases):continue
  if 'sqlite' not in name.casefold() and PurePosixPath(name).name.casefold() not in {'readme','readme.md'}:continue
  text=data[:262144].decode('utf-8','replace');lines=text.splitlines();selected=[line.strip() for line in lines if 'public domain' in line.casefold() or 'dedicat' in line.casefold()][:12]
  if selected:hits.append({'source_path':name,'sha256':sha_bytes(data),'size_bytes':len(data),'matched_lines':selected})
 if not hits:raise ValueError('SQLite public-domain statement not found in exact source')
 doc={'schema_version':1,'evidence_kind':'sqlite-3.50.4-public-domain-policy','source':{'filename':path.name,'sha256':expected_sha,'size_bytes':path.stat().st_size},'product_version':'3.50.4','evidence':sorted(hits,key=lambda x:x['source_path']),'classification':'public-domain-non-spdx','notice_policy':'record-public-domain-status-and-exact-source-evidence-without-inventing-license-text','pass':True}
 write_json(out,doc);return doc

def scan_hacl(source:Path,outdir:Path,outdoc:Path):
 if sha_file(source)!=CPYTHON_SOURCE_SHA or source.stat().st_size!=CPYTHON_SOURCE_SIZE:raise ValueError('CPython source identity mismatch')
 rows=[];upstream_hashes=[];license_ids=set();marker_files=0
 patterns=[re.compile(rb'SPDX-License-Identifier:\s*([^\s*]+)',re.I),re.compile(rb'Permission is hereby granted',re.I),re.compile(rb'Licensed under the Apache License',re.I),re.compile(rb'MIT License',re.I)]
 for name,data in _regular_members(source):
  if '/Modules/_hacl/' not in '/'+name:continue
  base=PurePosixPath(name).name
  if base=='refresh.sh':upstream_hashes += sorted(set(x.decode() for x in re.findall(rb'\b[0-9a-f]{40}\b',data)))
  matched=[]
  for pat in patterns:
   for m in pat.finditer(data[:131072]):matched.append(m.group(0).decode('utf-8','replace'))
  for m in patterns[0].finditer(data[:131072]):license_ids.add(m.group(1).decode('ascii','replace'))
  if matched:
   marker_files+=1;dest=outdir/base
   if dest.exists():dest=outdir/(sha_bytes(data)[:12]+'-'+base)
   dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  if matched or base in {'README.md','refresh.sh'}:rows.append({'source_path':name,'sha256':sha_bytes(data),'size_bytes':len(data),'license_markers':sorted(set(matched))})
 if not rows:raise ValueError('HACL source evidence absent')
 if marker_files==0:raise ValueError('HACL license markers absent in exact bundled source')
 classification=' AND '.join(sorted(license_ids)) if license_ids else ('MIT' if any('Permission is hereby granted' in m for r in rows for m in r['license_markers']) else 'license-header-present-expression-review-pending')
 doc={'schema_version':1,'evidence_kind':'hacl-star-bundled-source-license-evidence','cpython_source':{'filename':source.name,'sha256':CPYTHON_SOURCE_SHA,'size_bytes':CPYTHON_SOURCE_SIZE},'upstream_commit_candidates':sorted(set(upstream_hashes)),'evidence':sorted(rows,key=lambda x:x['source_path']),'license_marker_file_count':marker_files,'license_expression_candidate':classification,'mapping_status':'candidate-evidence-frozen-owner-review-pending','pass':True}
 write_json(outdoc,doc);return doc

def scan_libmpdec(payload:Path,out:Path):
 rows=[]
 for p in sorted((payload/'cpython/Modules/_decimal/libmpdec').glob('mpdecimal.*')):
  data=p.read_bytes();text=data[:12000].decode('utf-8','replace');lines=[x.strip() for x in text.splitlines() if 'Copyright' in x or 'Redistribution and use' in x or 'THIS SOFTWARE IS PROVIDED' in x]
  rows.append({'evidence_path':p.relative_to(payload).as_posix(),'sha256':sha_bytes(data),'size_bytes':len(data),'matched_lines':lines[:20]})
 if not rows or not any(any('Redistribution and use' in x for x in r['matched_lines']) for r in rows):raise ValueError('libmpdec redistribution header missing')
 doc={'schema_version':1,'evidence_kind':'libmpdec-2.5.1-license-header','version':'2.5.1','evidence':rows,'license_expression_candidate':'BSD-2-Clause-like','mapping_status':'candidate-evidence-frozen-owner-review-pending','pass':True};write_json(out,doc);return doc

def provider_policy(root:Path,out:Path):
 src=root/'experiments/epoch3-upstream-thin-full/authority-evidence/full-static-verification.json';doc=json.loads(src.read_text());libs=doc.get('metrics',{}).get('system_libraries')
 if libs!=SYSTEM_LIBS or doc.get('archive',{}).get('sha256')!=FULL_SHA or doc.get('pass') is not True:raise ValueError('full static provider authority mismatch')
 policy={'schema_version':1,'policy_kind':'android-system-provider-notice-boundary','source_authority':{'path':'experiments/epoch3-upstream-thin-full/authority-evidence/full-static-verification.json','sha256':sha_file(src)},'full_artifact_sha256':FULL_SHA,'providers':[{'soname':x,'distributed_in_product':False,'classification':'android-platform-runtime-provider','product_notice_payload_required':False,'runtime_support_claim_separate':True} for x in libs],'boundary':'record provider names and non-distribution; do not package or attribute Android platform library bytes as product components','pass':True};write_json(out,policy);return policy

def synthesize(family:Path,cpython_source:Path,sources:dict[str,dict],xz_asset:Path,output:Path,root:Path):
 output.mkdir(parents=True,exist_ok=True);legal=output/'legal';licenses=legal/'licenses';licenses.mkdir(parents=True,exist_ok=True)
 verify=verify_release_family(family,root=root)
 if not verify.get('pass'):raise ValueError(f'family verification failed: {verify.get("failed_checks")}')
 before=_family_snapshot(family)
 with tempfile.TemporaryDirectory(prefix='legal-overlay-base-') as td:
  base=Path(td);acquire_license_evidence(family,cpython_source,sources,base,root)
  shutil.copytree(base/'payload',licenses,dirs_exist_ok=True)
  base_map=json.loads((base/'component-license-map-candidate.json').read_text())
 xz=extract_xz_product_evidence(xz_asset,licenses/'xz');write_json(legal/'xz-product-license-evidence.json',xz)
 sqlite=scan_sqlite_public_domain(Path(sources['sqlite']['path']),sources['sqlite']['sha256'],legal/'sqlite-public-domain-evidence.json')
 hacl=scan_hacl(cpython_source,legal/'licenses/hacl-star',legal/'hacl-star-license-evidence.json')
 mpdec=scan_libmpdec(licenses,legal/'libmpdec-license-evidence.json')
 policy=provider_policy(root,legal/'android-system-provider-policy.json')
 updates={
  'xz-liblzma':('product-matching-xz-5.4.6-1-evidence-frozen',['xz-product-license-evidence.json','licenses/xz/COPYING','licenses/xz/COPYING.GPLv2','licenses/xz/AUTHORS'],'multi-license-product-asset-evidence-present'),
  'sqlite':('public-domain-policy-evidence-frozen',['sqlite-public-domain-evidence.json'],'public-domain-non-spdx'),
  'hacl-star':('bundled-source-license-header-evidence-frozen',['hacl-star-license-evidence.json'],'license-expression-candidate:'+hacl['license_expression_candidate']),
  'libmpdec':('bundled-2.5.1-license-header-evidence-frozen',['libmpdec-license-evidence.json'],'BSD-2-Clause-like'),
  'android-system-providers':('external-provider-boundary-frozen',['android-system-provider-policy.json'],'external-platform-provider-not-distributed')}
 rows=[]
 for row in base_map['components']:
  row=dict(row);comp=row['component_class'];row['obligation_review_complete']=False
  if comp in updates:
   row['status'],row['evidence_paths'],row['license_classification_candidate']=updates[comp]
  elif comp=='cpython':row['license_classification_candidate']='Python-2.0'
  elif comp=='project-launcher':row['license_classification_candidate']='MIT'
  elif comp=='pip':row['license_classification_candidate']='MIT-plus-vendored-inventory-review-pending'
  elif comp=='openssl':row['license_classification_candidate']='Apache-2.0'
  elif comp=='bzip2':row['license_classification_candidate']='bzip2-1.0.6'
  elif comp=='zstd':row['license_classification_candidate']='BSD-3-Clause OR GPL-2.0-only'
  elif comp=='expat':row['license_classification_candidate']='MIT'
  elif comp=='libffi':row['license_classification_candidate']='MIT'
  row['mapping_complete']=False;row['release_family_integrated']=False;rows.append(row)
 cmap={'schema_version':2,'map_kind':'epoch3-rb1-component-license-map-candidate-v2','component_count':13,'components':rows,'resolved_evidence_gaps':['xz-5.4.6-exact-license-source-unresolved','sqlite-public-domain-notice-policy-not-frozen','android-system-provider-notice-boundary-not-frozen','hacl-star-new-component-mapping-and-notice-pending'],'mapping_complete':False,'claim_boundary':{'candidate_only':True,'complete_obligation_review':False,'release_family_integrated':False,'owner_approved':False,'rb1_closed':False,'selectable':False,'publication':False}}
 write_json(legal/'component-license-map-candidate-v2.json',cmap)
 notice=['DRAFT THIRD-PARTY NOTICES CANDIDATE — OWNER AND OBLIGATION REVIEW REQUIRED','',f'Frozen artifact family: {FAMILY_FINGERPRINT}','No frozen artifact byte is modified by this legal overlay.','']
 for row in rows:
  notice.append(f"- {row['component_class']} {row.get('version') or '(project/external)'}: {row.get('license_classification_candidate','classification-pending')}")
  for ep in row.get('evidence_paths',[]):notice.append(f'    evidence: {ep}')
 notice += ['','Open gates: complete obligation review; release-family legal integration; project-license integration; final owner approval.']
 (legal/'THIRD-PARTY-NOTICES.candidate.txt').write_text('\n'.join(notice)+'\n')
 readme='This directory is a deterministic legal-evidence overlay candidate. It is not an approved release notice, does not modify frozen artifacts, and does not authorize selectability or publication.\n';(legal/'LEGAL-OVERLAY-README.txt').write_text(readme)
 remaining=[{'code':'complete-componentization-and-obligation-review-pending'},{'code':'authoritative-license-evidence-not-integrated-into-release-family'},{'code':'project-license-not-in-release-family'},{'code':'final-notice-set-not-owner-approved'}]
 gaps={'schema_version':2,'register_kind':'epoch3-rb1-legal-overlay-candidate-gap-register','baseline_gap_count':8,'resolved_gap_count':4,'resolved_gaps':[{'code':x} for x in cmap['resolved_evidence_gaps']],'remaining_gaps':remaining,'blocking_gap_count':4,'closure_status':'incomplete','claim_boundary':{'component_license_mapping_complete':False,'legal_overlay_authoritative':False,'rb1_closed':False,'selectable':False,'publication':False}};write_json(output/'updated-gap-register.json',gaps)
 legal_files=[]
 for p in sorted(legal.rglob('*')):
  if p.is_file():legal_files.append({'path':p.relative_to(output).as_posix(),'sha256':sha_file(p),'size_bytes':p.stat().st_size})
 fingerprint=hashlib.sha256(json.dumps(legal_files,separators=(',',':'),sort_keys=True).encode()).hexdigest();index={'schema_version':1,'index_kind':'epoch3-rb1-legal-overlay-file-index','files':legal_files,'file_count':len(legal_files),'fingerprint_sha256':fingerprint};write_json(output/'legal-overlay-index.json',index)
 after=_family_snapshot(family)
 if before!=after:raise ValueError('frozen family mutated')
 result={'schema_version':1,'runner_kind':'epoch3-rb1-legal-overlay-and-provider-policy-synthesis','pass':True,'family_identity_preserved':True,'metrics':{'component_count':13,'exact_input_archive_count':7,'resolved_gap_count':4,'remaining_gap_count':4,'legal_overlay_file_count':len(legal_files)},'legal_overlay_fingerprint_sha256':fingerprint,'outputs':['legal/','legal-overlay-index.json','updated-gap-register.json'],'claim_boundary':{'component_license_mapping_complete':False,'complete_obligation_review':False,'legal_overlay_authoritative':False,'release_family_integrated':False,'owner_approved':False,'rb1_closed':False,'selectable':False,'publication':False}};write_json(output/'legal-overlay-result.json',result);return result
