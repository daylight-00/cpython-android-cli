#!/usr/bin/env python3
"""Deterministic RB-1 technical obligation review and legal-family integration candidate."""
from __future__ import annotations
import hashlib,json,re,shutil,tarfile
from pathlib import Path,PurePosixPath
from typing import Any
from archive import canonical_json_bytes,sha256_file,write_json,normalize_member_name,safe_link_target
from release_family import verify_release_family

ROOT=Path(__file__).resolve().parents[3]
FAMILY_FINGERPRINT='87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302'
LEGAL_AUTHORITY_SHA='faccd8de76e9fc175ced66961c07f18696abd3c40d51d4e184a6e9bc277b79d3'
LEGAL_OVERLAY_FINGERPRINT='e4378c59eabcc6fdf5d07cccd718bd536d87deda531e5e2fcc3115fb6944a878'
INSTALL_ONLY_SHA='84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76'
INSTALL_ONLY_SIZE=23841726
NEW_RELEASE_ID='cpython-3.14.6+e3-r2-aarch64-linux-android'
VENDOR_SPECS={
 'CacheControl':('cachecontrol','Apache-2.0',['LICENSE.txt']),
 'certifi':('certifi','MPL-2.0',['LICENSE']),
 'distlib':('distlib','Python-2.0',['LICENSE.txt']),
 'distro':('distro','Apache-2.0',['LICENSE']),
 'idna':('idna','BSD-3-Clause',['LICENSE.md']),
 'msgpack':('msgpack','Apache-2.0',['COPYING']),
 'packaging':('packaging','Apache-2.0 OR BSD-2-Clause',['LICENSE','LICENSE.APACHE','LICENSE.BSD']),
 'platformdirs':('platformdirs','MIT',['LICENSE']),
 'pyproject-hooks':('pyproject_hooks','MIT',['LICENSE']),
 'requests':('requests','Apache-2.0',['LICENSE']),
 'pygments':('pygments','BSD-2-Clause',['LICENSE']),
 'resolvelib':('resolvelib','ISC',['LICENSE']),
 'rich':('rich','MIT',['LICENSE']),
 'setuptools':('pkg_resources','MIT',['LICENSE']),
 'tomli':('tomli','MIT',['LICENSE']),
 'tomli-w':('tomli_w','MIT',['LICENSE']),
 'truststore':('truststore','MIT',['LICENSE']),
 'urllib3':('urllib3','MIT',['LICENSE.txt']),
}
MODIFIED={'CacheControl','packaging','platformdirs','requests','setuptools'}

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def load_json(p:Path)->dict[str,Any]:
 v=json.loads(p.read_text());
 if not isinstance(v,dict):raise ValueError(f'expected object: {p}')
 return v
def file_row(p:Path,base:Path)->dict[str,Any]:return {'path':p.relative_to(base).as_posix(),'sha256':sha256_file(p),'size_bytes':p.stat().st_size}
def tree_rows(base:Path,*,exclude:set[str]|None=None)->list[dict[str,Any]]:
 exclude=exclude or set();return [file_row(p,base) for p in sorted(base.rglob('*')) if p.is_file() and p.relative_to(base).as_posix() not in exclude]
def fingerprint(rows:list[dict[str,Any]])->str:return hashlib.sha256(canonical_json_bytes({'schema_version':1,'files':rows})).hexdigest()
def safe_copy_tree(src:Path,dst:Path)->None:
 for p in sorted(src.rglob('*')):
  rel=p.relative_to(src);q=dst/rel
  if p.is_symlink():raise ValueError(f'symlink forbidden in frozen legal evidence: {rel}')
  if p.is_dir():q.mkdir(parents=True,exist_ok=True)
  elif p.is_file():q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  else:raise ValueError(f'special legal evidence member: {rel}')
def parse_vendor_txt(data:bytes)->list[dict[str,str]]:
 rows=[]
 for line in data.decode('utf-8').splitlines():
  s=line.strip()
  if not s:continue
  m=re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s]+)',s)
  if not m:raise ValueError(f'invalid pip vendor row: {line!r}')
  rows.append({'name':m.group(1),'version':m.group(2)})
 if len(rows)!=18 or {r['name'] for r in rows}!=set(VENDOR_SPECS):raise ValueError('pip vendor set mismatch')
 return rows

def _read_pip_evidence(archive:Path)->dict[str,bytes]:
 if sha256_file(archive)!=INSTALL_ONLY_SHA or archive.stat().st_size!=INSTALL_ONLY_SIZE:raise ValueError('install-only identity mismatch')
 out={};seen=set()
 with tarfile.open(archive,'r:gz') as tf:
  for m in tf:
   name=normalize_member_name(m.name)
   if name in seen:raise ValueError(f'duplicate archive member: {name}')
   seen.add(name)
   if m.issym():
    if not safe_link_target(name,m.linkname):raise ValueError(f'unsafe symlink: {name}')
    continue
   if m.isdir():continue
   if m.islnk() or m.isdev() or m.isfifo() or not m.isfile():raise ValueError(f'unsupported archive member: {name}')
   keep=(name.endswith('/pip/_vendor/vendor.txt') or name.endswith('/pip/_vendor/README.rst') or '/pip-26.1.2.dist-info/licenses/' in name or name.endswith('/pip-26.1.2.dist-info/METADATA'))
   if not keep:continue
   f=tf.extractfile(m);data=f.read() if f else b''
   if len(data)!=m.size:raise ValueError(f'truncated archive member: {name}')
   out[name]=data
 return out

def extract_pip_review(archive:Path,legal:Path)->dict[str,Any]:
 data=_read_pip_evidence(archive)
 vendor_name=next((n for n in data if n.endswith('/pip/_vendor/vendor.txt')),None);readme_name=next((n for n in data if n.endswith('/pip/_vendor/README.rst')),None);meta_name=next((n for n in data if n.endswith('/pip-26.1.2.dist-info/METADATA')),None)
 if not all([vendor_name,readme_name,meta_name]):raise ValueError('missing pip vendoring metadata')
 rows=parse_vendor_txt(data[vendor_name]);piproot=legal/'pip';piproot.mkdir(parents=True,exist_ok=True)
 (piproot/'vendor.txt').write_bytes(data[vendor_name]);(piproot/'VENDORING-README.rst').write_bytes(data[readme_name]);(piproot/'METADATA').write_bytes(data[meta_name])
 license_prefix=meta_name.rsplit('/',1)[0]+'/licenses/'
 own=[];vendors=[]
 for name,blob in sorted(data.items()):
  if not name.startswith(license_prefix):continue
  rel=name[len(license_prefix):]
  if not rel or rel.endswith('/'):continue
  if rel in ('LICENSE.txt','AUTHORS.txt'):
   dest=piproot/'licenses/pip'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob);own.append({'path':dest.relative_to(legal).as_posix(),'sha256':sha_bytes(blob),'size_bytes':len(blob)})
 for item in rows:
  name=item['name'];folder,expr,files=VENDOR_SPECS[name];evidence=[]
  for fn in files:
   rel=f'src/pip/_vendor/{folder}/{fn}';src=license_prefix+rel
   if src not in data:raise ValueError(f'missing pip vendor license: {name}:{fn}')
   blob=data[src];dest=piproot/'licenses/vendors'/folder/fn;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob);evidence.append({'path':dest.relative_to(legal).as_posix(),'source_archive_path':src,'sha256':sha_bytes(blob),'size_bytes':len(blob)})
  vendors.append({'component':name,'version':item['version'],'vendored_module':folder,'license_expression_candidate':expr,'license_evidence':evidence,'pip_local_modifications_recorded':name in MODIFIED,'technical_obligation_record':{'include_exact_license_evidence':True,'preserve_copyright_and_notice_text':True,'source_or_file_level_terms_require_owner_review':expr=='MPL-2.0','final_legal_approval_required':True}})
 if len(own)!=2:raise ValueError('pip own license evidence mismatch')
 review={'schema_version':1,'review_kind':'pip-26.1.2-vendored-component-technical-obligation-review','pip_version':'26.1.2','vendor_component_count':18,'vendor_components':vendors,'pip_license_expression_candidate':'MIT','pip_license_evidence':own,'vendor_metadata':{'vendor_txt':file_row(piproot/'vendor.txt',legal),'vendoring_readme':file_row(piproot/'VENDORING-README.rst',legal),'metadata':file_row(piproot/'METADATA',legal)},'technical_componentization_complete':True,'technical_obligation_records_complete':True,'owner_approved':False}
 write_json(legal/'pip-vendored-component-review.json',review);return review

def _predecessor_snapshot(family:Path)->dict[str,dict[str,Any]]:return {p.name:{'sha256':sha256_file(p),'size_bytes':p.stat().st_size} for p in family.iterdir() if p.is_file()}
def _copy_predecessor(family:Path,out:Path)->dict[str,dict[str,Any]]:
 snap=_predecessor_snapshot(family);line=out/'lineage/r1';line.mkdir(parents=True)
 for name in sorted(snap):
  if name in ('release-index.json','SHA256SUMS'):shutil.copyfile(family/name,line/name)
  else:shutil.copyfile(family/name,out/name)
 return snap

def _top_level_map(legal:Path,pip:dict[str,Any])->dict[str,Any]:
 base=load_json(legal/'component-license-map-candidate-v2.json');rows=[]
 for old in base['components']:
  row=dict(old);row['mapping_complete']=True;row['technical_obligation_review_complete']=True;row['release_family_integrated']=True;row['owner_approved']=False
  if row['component_class']=='pip':row['vendored_review_path']='pip-vendored-component-review.json';row['vendored_review_unit_count']=pip['vendor_component_count']
  rows.append(row)
 return {'schema_version':3,'map_kind':'epoch3-rb1-component-license-map-integrated-candidate','top_level_component_count':13,'pip_vendored_component_count':18,'review_unit_count':31,'components':rows,'componentization_complete':True,'mapping_complete':True,'technical_obligation_review_complete':True,'release_family_integrated':True,'owner_approved':False,'claim_boundary':{'legal_interpretation_approved':False,'final_notice_approved':False,'rb1_closed':False,'selectable':False,'publication':False}}
def _notice(legal:Path,cmap:dict[str,Any],pip:dict[str,Any])->None:
 base=(legal/'THIRD-PARTY-NOTICES.candidate.txt').read_text().rstrip();lines=[base,'','Pip 26.1.2 vendored review units:']
 for r in pip['vendor_components']:lines.append(f"- {r['component']} {r['version']}: {r['license_expression_candidate']}")
 lines += ['','This integrated notice remains a candidate pending explicit owner approval.',''];(legal/'THIRD-PARTY-NOTICES.candidate.txt').write_text('\n'.join(lines))

def assemble_legal_integrated_family(family:Path,output:Path,*,root:Path=ROOT)->dict[str,Any]:
 family=family.resolve();output=output.resolve();v=verify_release_family(family,root=root)
 if not v.get('pass'):raise ValueError(f'predecessor family verification failed: {v.get("failed_checks")}')
 auth=root/'experiments/epoch3-upstream-thin-release-blockers/rb1-legal-overlay-authority.json'
 if sha256_file(auth)!=LEGAL_AUTHORITY_SHA:raise ValueError('legal overlay authority identity mismatch')
 ae=root/'experiments/epoch3-upstream-thin-release-blockers/rb1-legal-overlay-authority-evidence';idx=load_json(ae/'legal-overlay-index.json')
 if idx.get('file_count')!=72 or idx.get('fingerprint_sha256')!=LEGAL_OVERLAY_FINGERPRINT:raise ValueError('legal overlay authority metrics mismatch')
 if output.exists():shutil.rmtree(output)
 output.mkdir(parents=True)
 predecessor=_copy_predecessor(family,output)
 legal=output/'legal';safe_copy_tree(ae/'legal',legal)
 project=root/'LICENSE';top=output/'LICENSE';shutil.copyfile(project,top)
 if sha256_file(top)!=sha256_file(ae/'legal/licenses/project/LICENSE'):raise ValueError('project license identity mismatch')
 install=next(p for p in family.iterdir() if p.name.endswith('-install_only.tar.gz'))
 pip=extract_pip_review(install,legal);cmap=_top_level_map(legal,pip);write_json(legal/'component-license-map.json',cmap);_notice(legal,cmap,pip)
 review={'schema_version':1,'review_kind':'epoch3-rb1-technical-component-obligation-review','top_level_component_count':13,'pip_vendored_component_count':18,'review_unit_count':31,'all_review_units_have_exact_evidence':True,'all_review_units_have_technical_obligation_records':True,'technical_review_complete':True,'legal_interpretation_approved':False,'owner_approved':False};write_json(legal/'technical-obligation-review.json',review)
 gaps={'schema_version':3,'register_kind':'epoch3-rb1-legal-integration-candidate-gap-register','baseline_gap_count':4,'resolved_gap_count':3,'resolved_gaps':[{'code':'complete-componentization-and-obligation-review-pending'},{'code':'authoritative-license-evidence-not-integrated-into-release-family'},{'code':'project-license-not-in-release-family'}],'remaining_gaps':[{'code':'final-notice-set-not-owner-approved'}],'blocking_gap_count':1,'closure_status':'owner-approval-pending','claim_boundary':{'component_license_mapping_complete':True,'technical_obligation_review_complete':True,'release_family_integrated':True,'owner_approved':False,'rb1_closed':False,'selectable':False,'publication':False}};write_json(legal/'updated-gap-register.json',gaps)
 pred_idx=load_json(family/'release-index.json');assets=pred_idx['release']['assets']
 integration={'schema_version':1,'integration_kind':'epoch3-rb1-revised-release-family-legal-integration-candidate','predecessor':{'release_id':pred_idx['release']['release_id'],'release_index_sha256':sha256_file(family/'release-index.json'),'sha256sums_sha256':sha256_file(family/'SHA256SUMS'),'family_fingerprint_sha256':FAMILY_FINGERPRINT},'artifact_and_sidecar_files_reused_byte_identically':21,'legal_overlay_authority':{'path':'experiments/epoch3-upstream-thin-release-blockers/rb1-legal-overlay-authority.json','sha256':LEGAL_AUTHORITY_SHA,'fingerprint_sha256':LEGAL_OVERLAY_FINGERPRINT},'technical_review':{'top_level_components':13,'pip_vendored_components':18,'review_units':31,'complete':True},'project_license':file_row(top,output),'remaining_gap_count':1,'owner_approved':False,'rb1_closed':False};write_json(legal/'legal-integration.json',integration)
 # Checksums over all payload files except envelope files.
 targets=[p for p in sorted(output.rglob('*')) if p.is_file() and p.relative_to(output).as_posix() not in ('SHA256SUMS','release-index.json')]
 (output/'SHA256SUMS').write_text(''.join(f'{sha256_file(p)}  {p.relative_to(output).as_posix()}\n' for p in targets))
 rows=tree_rows(output,exclude={'release-index.json'});fp=fingerprint(rows)
 release={'schema_version':2,'release_id':NEW_RELEASE_ID,'predecessor_release_id':pred_idx['release']['release_id'],'python_version':'3.14.6','target_triple':'aarch64-linux-android','status':'qualified-legal-integrated-owner-approval-pending-unselectable-unpublished','assets':assets,'legal':{'directory':'legal/','legal_overlay_authority_sha256':LEGAL_AUTHORITY_SHA,'technical_obligation_review_sha256':sha256_file(legal/'technical-obligation-review.json'),'component_license_map_sha256':sha256_file(legal/'component-license-map.json'),'third_party_notices_candidate_sha256':sha256_file(legal/'THIRD-PARTY-NOTICES.candidate.txt'),'updated_gap_register_sha256':sha256_file(legal/'updated-gap-register.json'),'project_license_sha256':sha256_file(top),'owner_approved':False},'family_invariants':pred_idx['release']['family_invariants'],'claim_boundary':{'artifact_family_complete':True,'artifact_bytes_unchanged':True,'component_license_mapping_complete':True,'technical_obligation_review_complete':True,'legal_evidence_integrated':True,'project_license_included':True,'owner_approved':False,'rb1_closed':False,'selectable':False,'publication':False,'api24_runtime':False,'actual_16k_runtime':False,'non_termux_context':False}}
 index={'schema_version':2,'index_kind':'epoch3-upstream-thin-legally-integrated-release-family-candidate','release':release,'release_sha256':hashlib.sha256(canonical_json_bytes(release)).hexdigest(),'family_fingerprint_sha256':fp,'file_count':len(rows)+1,'checksums':{'filename':'SHA256SUMS','sha256':sha256_file(output/'SHA256SUMS')}};write_json(output/'release-index.json',index)
 return verify_legal_integrated_family(output,predecessor_family=family,root=root)

def verify_legal_integrated_family(directory:Path,*,predecessor_family:Path,root:Path=ROOT)->dict[str,Any]:
 checks={};errors=[];directory=directory.resolve();predecessor_family=predecessor_family.resolve()
 try:index=load_json(directory/'release-index.json');release=index['release'];checks['index_parse']=True
 except Exception as e:index={};release={};checks['index_parse']=False;errors.append(f'{type(e).__name__}: {e}')
 pred=verify_release_family(predecessor_family,root=root);checks['predecessor_family']=pred.get('pass') is True
 snap=_predecessor_snapshot(predecessor_family);reuse=True
 for name,ident in snap.items():
  p=(directory/'lineage/r1'/name) if name in ('release-index.json','SHA256SUMS') else directory/name
  if not p.is_file() or sha256_file(p)!=ident['sha256'] or p.stat().st_size!=ident['size_bytes']:reuse=False
 checks['predecessor_files_reused']=reuse and len(snap)==23
 checks['release_identity']=release.get('release_id')==NEW_RELEASE_ID and release.get('predecessor_release_id')=='cpython-3.14.6+e3-r1-aarch64-linux-android'
 checks['release_digest']=index.get('release_sha256')==hashlib.sha256(canonical_json_bytes(release)).hexdigest() if release else False
 legal=directory/'legal'
 try:cmap=load_json(legal/'component-license-map.json');review=load_json(legal/'technical-obligation-review.json');pip=load_json(legal/'pip-vendored-component-review.json');gaps=load_json(legal/'updated-gap-register.json');integ=load_json(legal/'legal-integration.json')
 except Exception as e:cmap=review=pip=gaps=integ={};errors.append(f'legal:{type(e).__name__}:{e}')
 checks['review_units']=review.get('review_unit_count')==31 and review.get('technical_review_complete') is True and pip.get('vendor_component_count')==18 and len(pip.get('vendor_components',[]))==18
 checks['mapping_complete']=cmap.get('mapping_complete') is True and cmap.get('technical_obligation_review_complete') is True and cmap.get('review_unit_count')==31
 checks['single_remaining_gap']=gaps.get('blocking_gap_count')==1 and [x.get('code') for x in gaps.get('remaining_gaps',[])]==['final-notice-set-not-owner-approved']
 checks['integration']=integ.get('artifact_and_sidecar_files_reused_byte_identically')==21 and integ.get('remaining_gap_count')==1
 checks['project_license']=(directory/'LICENSE').is_file() and sha256_file(directory/'LICENSE')==sha256_file(root/'LICENSE')
 ae=root/'experiments/epoch3-upstream-thin-release-blockers/rb1-legal-overlay-authority-evidence/legal';overlay=True
 for p in ae.rglob('*'):
  if p.is_file():
   q=legal/p.relative_to(ae)
   # Candidate notice and map are deliberately superseded; all other accepted evidence must remain exact.
   if p.name in ('THIRD-PARTY-NOTICES.candidate.txt','component-license-map-candidate-v2.json'):continue
   if not q.is_file() or sha256_file(q)!=sha256_file(p):overlay=False
 checks['accepted_overlay_evidence_integrated']=overlay
 actual=''.join(f'{sha256_file(p)}  {p.relative_to(directory).as_posix()}\n' for p in sorted(directory.rglob('*')) if p.is_file() and p.relative_to(directory).as_posix() not in ('SHA256SUMS','release-index.json'))
 checks['sha256sums_exact']=(directory/'SHA256SUMS').is_file() and (directory/'SHA256SUMS').read_text()==actual
 rows=tree_rows(directory,exclude={'release-index.json'});checks['family_fingerprint']=index.get('family_fingerprint_sha256')==fingerprint(rows) and index.get('file_count')==len(rows)+1
 cb=release.get('claim_boundary',{});checks['claims_bounded']=cb.get('component_license_mapping_complete') is True and cb.get('legal_evidence_integrated') is True and cb.get('owner_approved') is False and cb.get('rb1_closed') is False and cb.get('selectable') is False and cb.get('publication') is False
 checks['regular_files_only']=all(not p.is_symlink() for p in directory.rglob('*'))
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {'schema_version':1,'verifier_kind':'epoch3-rb1-legally-integrated-release-family-candidate','pass':not failed and not errors,'checks':dict(sorted(checks.items())),'failed_checks':failed,'errors':errors,'release_id':release.get('release_id'),'file_count':index.get('file_count'),'family_fingerprint_sha256':index.get('family_fingerprint_sha256'),'release_sha256':index.get('release_sha256'),'metrics':{'top_level_component_count':cmap.get('top_level_component_count'),'pip_vendored_component_count':pip.get('vendor_component_count'),'review_unit_count':review.get('review_unit_count'),'resolved_gap_count':3,'remaining_gap_count':gaps.get('blocking_gap_count')},'claim_boundary':cb}

def main() -> int:
 import argparse
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 a=sub.add_parser('assemble');a.add_argument('--family-dir',type=Path,required=True);a.add_argument('--output-dir',type=Path,required=True);a.add_argument('--root',type=Path,default=ROOT)
 v=sub.add_parser('verify');v.add_argument('--candidate-dir',type=Path,required=True);v.add_argument('--predecessor-dir',type=Path,required=True);v.add_argument('--root',type=Path,default=ROOT)
 ns=p.parse_args()
 if ns.command=='assemble':out=assemble_legal_integrated_family(ns.family_dir,ns.output_dir,root=ns.root.resolve())
 else:out=verify_legal_integrated_family(ns.candidate_dir,predecessor_family=ns.predecessor_dir,root=ns.root.resolve())
 print(json.dumps(out,indent=2,sort_keys=True));return 0 if out.get('pass') else 1
if __name__=='__main__':raise SystemExit(main())
