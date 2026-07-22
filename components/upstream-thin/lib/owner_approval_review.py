from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[3]
RELEASE_ID='cpython-3.14.6+e3-r2-aarch64-linux-android';FAMILY_FP='b71a0123d9d135b3ab378b59d2227ec312c95b49dc15c6ec40fce91a916f348d';RELEASE_SHA='b2d93c0f13b60e7404a948a54abfa4c7adffdb318194b291a6ec6b668b49c1fb';NOTICE_SHA='80cf82a6b6957fd830701e2559755d1eecdf01c61cbcb4f8f8843b9735eaf613';MAP_SHA='4da6f405f18ff827452f33aea0886f993ab9dab362b515350ab8f92c87b0f7b2';REVIEW_SHA='240b953086110134ea442313212ed24468e057415e5bbeb83ec5cd65f8dfb3df';PIP_SHA='2571c7419781231ab39353723dd9163e91d6ab84f0a48b9f8421be441cf6d85d';LICENSE_SHA='09ca1b4089dc99d077db44d5c90d140c2bbceeacd0712ba3be0e8d61839c55ee';STATEMENT='I approve the exact RB-1 final notice set and component-license mapping identified by the hashes in this approval document.'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path)->dict[str,Any]:
 v=json.loads(p.read_text());
 if not isinstance(v,dict):raise ValueError('expected JSON object')
 return v
def writej(p:Path,o:Any):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def authority_manifest(root:Path=ROOT)->dict[str,Any]:return load(root/'experiments/epoch3-upstream-thin-release-blockers/rb1-legal-integration-authority-evidence/integrated-family-file-manifest.json')
def verify_family(directory:Path,root:Path=ROOT)->dict[str,Any]:
 d=directory.resolve();m=authority_manifest(root);checks={};errors=[];expected={x['path']:(x['sha256'],x['size_bytes']) for x in m['files']};actual={}
 for p in d.rglob('*'):
  if p.is_symlink():errors.append(f'symlink:{p.relative_to(d)}')
  elif p.is_file():actual[p.relative_to(d).as_posix()]=(sha(p),p.stat().st_size)
 checks['exact_manifest']=actual==expected;checks['file_count']=len(actual)==128
 try:i=load(d/'release-index.json');checks['release_identity']=i.get('release',{}).get('release_id')==RELEASE_ID and i.get('family_fingerprint_sha256')==FAMILY_FP and i.get('release_sha256')==RELEASE_SHA
 except Exception as e:checks['release_identity']=False;errors.append(str(e))
 checks['notice']=sha(d/'legal/THIRD-PARTY-NOTICES.candidate.txt')==NOTICE_SHA if (d/'legal/THIRD-PARTY-NOTICES.candidate.txt').is_file() else False
 f=sorted(k for k,v in checks.items() if v is not True);return {'schema_version':1,'verifier_kind':'epoch3-rb1-owner-approval-review-input','pass':not f and not errors,'checks':checks,'failed_checks':f,'errors':errors}
def binding()->dict[str,Any]:return {'schema_version':1,'binding_kind':'epoch3-rb1-final-notice-owner-approval-binding','release_id':RELEASE_ID,'release_sha256':RELEASE_SHA,'family_fingerprint_sha256':FAMILY_FP,'third_party_notices_sha256':NOTICE_SHA,'component_license_map_sha256':MAP_SHA,'technical_obligation_review_sha256':REVIEW_SHA,'pip_vendored_component_review_sha256':PIP_SHA,'project_license_sha256':LICENSE_SHA,'required_statement':STATEMENT}
def validate_approval(doc:dict[str,Any],b:dict[str,Any]|None=None)->dict[str,Any]:
 b=b or binding();checks={'schema':doc.get('schema_version')==1 and doc.get('approval_kind')=='epoch3-rb1-final-notice-set-owner-approval','approved':doc.get('approved') is True,'owner_id':isinstance(doc.get('owner_id'),str) and bool(doc.get('owner_id').strip()),'statement':doc.get('statement')==b['required_statement']}
 for k in ('release_id','release_sha256','family_fingerprint_sha256','third_party_notices_sha256','component_license_map_sha256','technical_obligation_review_sha256','pip_vendored_component_review_sha256','project_license_sha256'):checks[k]=doc.get(k)==b[k]
 f=sorted(k for k,v in checks.items() if v is not True);return {'schema_version':1,'verifier_kind':'epoch3-rb1-explicit-owner-approval-document','pass':not f,'checks':dict(sorted(checks.items())),'failed_checks':f}
def prepare_review(family:Path,out:Path,root:Path=ROOT)->dict[str,Any]:
 v=verify_family(family,root); 
 if not v['pass']:raise ValueError(f'invalid integrated family: {v}')
 if out.exists():shutil.rmtree(out)
 out.mkdir(parents=True);copies={'THIRD-PARTY-NOTICES.review.txt':'legal/THIRD-PARTY-NOTICES.candidate.txt','component-license-map.json':'legal/component-license-map.json','technical-obligation-review.json':'legal/technical-obligation-review.json','pip-vendored-component-review.json':'legal/pip-vendored-component-review.json','LICENSE':'LICENSE'}
 for n,s in copies.items():shutil.copy2(family/s,out/n)
 b=binding();writej(out/'approval-binding.json',b);template={'schema_version':1,'approval_kind':'epoch3-rb1-final-notice-set-owner-approval','approved':False,'owner_id':'','statement':b['required_statement'],**{k:b[k] for k in b if k.endswith('sha256') or k=='release_id'}};writej(out/'owner-approval-template.json',template)
 (out/'OWNER-APPROVAL-REVIEW.txt').write_text('RB-1 FINAL NOTICE OWNER APPROVAL REVIEW\n\nReview every included file. Running a runner is not approval. To approve later, copy owner-approval-template.json, set approved=true and owner_id to your repository owner identity, preserve every hash and the exact statement, then provide that file as the explicit approval input.\n')
 rows=[]
 for p in sorted(out.iterdir()):
  if p.is_file() and p.name!='review-index.json':rows.append({'path':p.name,'sha256':sha(p),'size_bytes':p.stat().st_size})
 fp=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest();writej(out/'review-index.json',{'schema_version':1,'index_kind':'epoch3-rb1-owner-approval-review-dossier','file_count':len(rows)+1,'fingerprint_sha256':fp,'files':rows,'approval_status':'pending'})
 return verify_review(out)
def verify_review(out:Path)->dict[str,Any]:
 checks={};errors=[]
 try:i=load(out/'review-index.json');b=load(out/'approval-binding.json');t=load(out/'owner-approval-template.json');checks['binding']=b==binding();checks['template_pending']=t.get('approved') is False and t.get('owner_id')=='' and validate_approval(t,b).get('pass') is False;checks['notice']=sha(out/'THIRD-PARTY-NOTICES.review.txt')==NOTICE_SHA;checks['map']=sha(out/'component-license-map.json')==MAP_SHA;checks['review']=sha(out/'technical-obligation-review.json')==REVIEW_SHA;checks['pip']=sha(out/'pip-vendored-component-review.json')==PIP_SHA;checks['license']=sha(out/'LICENSE')==LICENSE_SHA;rows=[{'path':p.name,'sha256':sha(p),'size_bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file() and p.name!='review-index.json'];checks['index']=i.get('file_count')==len(rows)+1 and i.get('fingerprint_sha256')==hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest() and i.get('approval_status')=='pending'
 except Exception as e:errors.append(f'{type(e).__name__}:{e}')
 f=sorted(k for k,v in checks.items() if v is not True);return {'schema_version':1,'verifier_kind':'epoch3-rb1-owner-approval-review-dossier','pass':not f and not errors,'checks':dict(sorted(checks.items())),'failed_checks':f,'errors':errors,'claim_boundary':{'owner_approved':False,'rb1_closed':False,'selectable':False,'publication':False}}
