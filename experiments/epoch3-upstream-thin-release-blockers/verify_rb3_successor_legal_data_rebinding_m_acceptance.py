#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/epoch3-upstream-thin-release-blockers'
EXPECTED_RESULT='04bb2ccca290902c9236682295c655dfe56dcd822bcdc41b1e662aafa2ba6def'
EXPECTED_HEAD='9caabc54552ef51fc517c708f65288e7dc24e66e'
EXPECTED_TREE='269dd804666b04737f46daa15e70df01b2dad25a'
EXPECTED_FAMILY='c8d76b6dcb934c12098efb2de985c5ab4799e4b5db5ae1c2b7c0f5a68438a82a'
def load(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root:Path=ROOT)->dict[str,Any]:
 b=root/'experiments/epoch3-upstream-thin-release-blockers'; e=b/'rb3-successor-legal-data-rebinding-m-authority-evidence'
 required={
  'authority':b/'rb3-successor-legal-data-rebinding-m-authority.json',
  'accepted':b/'accepted-rb3-successor-legal-data-rebinding-m-r2-return.json',
  'inspection':b/'rb3-successor-legal-data-rebinding-m-r2-return-inspection.json',
  'contract':b/'rb3-successor-legal-data-rebinding-m-acceptance-contract.json',
  'next_contract':b/'rb3-successor-predecessor-supersession-m-contract.json',
  'summary':e/'owner-summary.json','owner':e/'owner-result.json','external':e/'external-acceptance-audit.json',
  'audit':e/'owner-independent-audit.json','rb1':e/'rb1-technical-legal-rebinding.json','rb2':e/'rb2-data-runtime-rebinding.json',
  'protected':e/'protected-state.json','family':e/'successor-family-verification.json','index':e/'result-index.json',
 }
 missing=sorted(k for k,p in required.items() if not p.is_file())
 if missing:
  return {'schema_version':1,'verifier_kind':'epoch3-rb3-profile-M-successor-legal-data-rebinding-acceptance','pass':False,'checks':{'required_inputs':False},'failed_checks':['file_identities','required_inputs'],'missing_inputs':missing,'identity_checks':{},'source_authority_checks':{}}
 loaded={k:load(p) for k,p in required.items()}
 authority=loaded['authority'];accepted=loaded['accepted'];inspection=loaded['inspection'];contract=loaded['contract'];next_contract=loaded['next_contract'];summary=loaded['summary'];owner=loaded['owner'];external=loaded['external'];audit=loaded['audit'];rb1=loaded['rb1'];rb2=loaded['rb2'];protected=loaded['protected'];family=loaded['family'];index=loaded['index']
 ids=authority.get('file_identities',{}); id_checks={p:(root/p).is_file() and sha(root/p)==h for p,h in ids.items()}
 source_checks={k:(root/v['path']).is_file() and sha(root/v['path'])==v['sha256'] for k,v in authority.get('source_authorities',{}).items()}
 boundary=authority.get('claim_boundary')
 inv=rb2.get('install_root_invariance',{})
 checks={
  'authority_kind':authority.get('authority_kind')=='epoch3-rb3-profile-M-successor-legal-data-rebinding',
  'file_identities':bool(id_checks) and all(id_checks.values()),
  'source_authorities':bool(source_checks) and all(source_checks.values()),
  'result_identity':accepted.get('result_archive',{}).get('sha256')==inspection.get('result_archive',{}).get('sha256')==authority.get('accepted_evidence',{}).get('result_archive_sha256')==EXPECTED_RESULT and accepted.get('result_archive',{}).get('size_bytes')==13505,
  'self_index':len(index.get('files',[]))==25 and external.get('checks',{}).get('self_index_exact') is True,
  'repository':summary.get('post',{}).get('head')==EXPECTED_HEAD and summary.get('post',{}).get('tree')==EXPECTED_TREE and summary.get('post',{}).get('remote_head')==EXPECTED_HEAD,
  'owner_result':owner.get('pass') is True and not owner.get('failed_checks') and all(owner.get('checks',{}).values()),
  'rb1':rb1.get('pass') is True and not rb1.get('failed_checks') and all(rb1.get('checks',{}).values()) and rb1.get('owner_approved') is False,
  'rb2':rb2.get('pass') is True and not rb2.get('failed_checks') and all(rb2.get('checks',{}).values()),
  'runtime':rb2.get('runtime_qualification',{}).get('pass') is True and all(rb2.get('runtime_qualification',{}).get('checks',{}).values()),
  'read_only':inv.get('pass') is True and inv.get('content_identity_unchanged') is True and inv.get('read_only_modes_enforced') is True and inv.get('original_modes_restored') is True and inv.get('before_content_fingerprint_sha256')==inv.get('read_only_content_fingerprint_sha256')==inv.get('restored_content_fingerprint_sha256') and inv.get('before_full_fingerprint_sha256')==inv.get('restored_full_fingerprint_sha256'),
  'audit':audit.get('pass') is True and not audit.get('failed_checks') and all(audit.get('checks',{}).values()),
  'external_audit':external.get('pass') is True and not external.get('failed_checks') and all(external.get('checks',{}).values()),
  'protected':protected.get('pass') is True and all(protected.get('checks',{}).values()),
  'family':family.get('pass') is True and family.get('release',{}).get('family_fingerprint_sha256')==EXPECTED_FAMILY,
  'boundary':accepted.get('claim_boundary')==inspection.get('claim_boundary')==contract.get('success_boundary')==boundary and boundary.get('rb1_rebound') is True and boundary.get('rb2_rebound') is True and boundary.get('predecessor_family_superseded') is False and boundary.get('rb3_closed') is False,
  'next_contract':next_contract.get('contract_kind')=='epoch3-rb3-profile-M-successor-predecessor-family-supersession-and-rb3-closure' and next_contract.get('success_boundary',{}).get('predecessor_family_superseded') is True and next_contract.get('success_boundary',{}).get('rb3_closed') is True and next_contract.get('success_boundary',{}).get('selectable') is False,
 }
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {'schema_version':1,'verifier_kind':'epoch3-rb3-profile-M-successor-legal-data-rebinding-acceptance','pass':not failed,'checks':dict(sorted(checks.items())),'failed_checks':failed,'identity_checks':dict(sorted(id_checks.items())),'source_authority_checks':dict(sorted(source_checks.items()))}
def main()->int:
 r=verify();print(json.dumps(r,indent=2,sort_keys=True));return 0 if r['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
