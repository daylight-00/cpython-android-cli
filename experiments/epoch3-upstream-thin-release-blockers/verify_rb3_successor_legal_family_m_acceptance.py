#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/epoch3-upstream-thin-release-blockers'
EXPECTED_RESULT='c43975ec955f0d4f692567d728ded4200c1ea246574e2d514fbd44dca64ff3f7'
EXPECTED_FINGERPRINT='c8d76b6dcb934c12098efb2de985c5ab4799e4b5db5ae1c2b7c0f5a68438a82a'
EXPECTED_RELEASE='2c31578f95a11291eee1693db80048568a7b533e77877f36a8b1570241ce1e1c'
EXPECTED_HEAD='2d27f5e2a66c1186a0bec49b2c7b1c96d6624edc'
EXPECTED_TREE='d75b704c5e6268287c6de5a640dabefbb4938d1a'
def load(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root:Path=ROOT)->dict[str,Any]:
 b=root/'experiments/epoch3-upstream-thin-release-blockers'; e=b/'rb3-successor-legal-family-m-authority-evidence'
 authority=load(b/'rb3-successor-legal-family-m-authority.json'); accepted=load(b/'accepted-rb3-successor-legal-family-m-r2-return.json'); inspection=load(b/'rb3-successor-legal-family-m-r2-return-inspection.json'); contract=load(b/'rb3-successor-legal-family-m-acceptance-contract.json'); next_contract=load(b/'rb3-successor-legal-data-rebinding-m-contract.json'); lock=load(root/'config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-successor-legal-family-r3.lock.json')
 summary=load(e/'owner-summary.json'); a=load(e/'owner-assembly-a.json'); bb=load(e/'owner-assembly-b.json'); audit=load(e/'owner-independent-audit.json'); external=load(e/'external-acceptance-audit.json'); repro=load(e/'reproducibility.json'); protected=load(e/'protected-state.json'); host=load(e/'host-identity.json'); index=load(e/'result-index.json'); release=load(e/'release-index.json')
 ids=authority.get('file_identities',{}); id_checks={p:(root/p).is_file() and sha(root/p)==h for p,h in ids.items()}
 boundary={'successor_legal_family_candidate':True,'successor_legal_family_accepted':True,'successor_legal_data_rebinding_authorized':True,'successor_legal_data_rebinding_started':False,'rb1_rebound':False,'rb2_rebound':False,'predecessor_family_superseded':False,'rb3_closed':False,'selectable':False,'publication':False}
 checks={
  'authority_kind':authority.get('authority_kind')=='epoch3-rb3-profile-M-successor-legally-integrated-family-r3',
  'file_identities':bool(id_checks) and all(id_checks.values()),
  'result_identity':accepted.get('result_archive',{}).get('sha256')==inspection.get('result_archive',{}).get('sha256')==authority.get('accepted_evidence',{}).get('result_archive_sha256')==EXPECTED_RESULT and accepted.get('result_archive',{}).get('size_bytes')==87216775,
  'self_index':len(index.get('files',[]))==153 and external.get('checks',{}).get('self_index_exact') is True,
  'summary':summary.get('claim_transaction_rc')==0 and summary.get('action')=='applied-rb3-profile-M-successor-legal-family-r2-integrated-reproduced-audited-pushed' and summary.get('post',{}).get('head')==EXPECTED_HEAD and summary.get('post',{}).get('tree')==EXPECTED_TREE and summary.get('post',{}).get('remote_head')==EXPECTED_HEAD,
  'assemblies':a.get('pass') is True and bb.get('pass') is True and not a.get('failed_checks') and not bb.get('failed_checks') and a.get('file_count')==bb.get('file_count')==128,
  'reproducibility':repro.get('pass') is True and repro.get('all_files_byte_identical') is True and len(repro.get('assembly_a',[]))==128 and repro.get('assembly_a_file_count')==repro.get('assembly_b_file_count')==128,
  'audit':audit.get('pass') is True and not audit.get('failed_checks') and all(audit.get('checks',{}).values()),
  'external_audit':external.get('pass') is True and not external.get('failed_checks') and all(external.get('checks',{}).values()),
  'protected':protected.get('pass') is True and all(protected.get('checks',{}).values()),
  'host_identity':host.get('pass') is True and host.get('expected',{}).get('family_fingerprint_sha256')==EXPECTED_FINGERPRINT,
  'release_identity':release.get('family_fingerprint_sha256')==EXPECTED_FINGERPRINT and release.get('release_sha256')==EXPECTED_RELEASE and release.get('file_count')==128 and release.get('release',{}).get('release_id')=='cpython-3.14.6+e3-r3-aarch64-linux-android',
  'lock_identity':lock.get('release_family',{}).get('fingerprint_sha256')==EXPECTED_FINGERPRINT and lock.get('release_family',{}).get('release_sha256')==EXPECTED_RELEASE and len(lock.get('files',[]))==128,
  'legal_rebinding_evidence':a.get('license_rebinding',{}).get('pass') is True and a.get('license_rebinding',{}).get('component_license_mapping_complete') is True and all(v.get('pass') is True and v.get('license_file_count')==42 for v in a.get('license_rebinding',{}).get('flavors',{}).values()),
  'owner_approval_pending':a.get('license_rebinding',{}).get('owner_approved') is False and authority.get('invariants',{}).get('owner_approved') is False,
  'boundary':accepted.get('claim_boundary')==inspection.get('claim_boundary')==contract.get('success_boundary')==authority.get('claim_boundary')==boundary,
  'next_contract':next_contract.get('contract_kind')=='epoch3-rb3-profile-M-successor-legal-and-data-rebinding' and next_contract.get('success_boundary',{}).get('rb1_rebound') is True and next_contract.get('success_boundary',{}).get('rb2_rebound') is True and next_contract.get('success_boundary',{}).get('predecessor_family_superseded') is False,
 }
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {'schema_version':1,'verifier_kind':'epoch3-rb3-profile-M-successor-legal-family-r3-acceptance','pass':not failed,'checks':dict(sorted(checks.items())),'failed_checks':failed,'identity_checks':dict(sorted(id_checks.items()))}
def main()->int:
 r=verify(); print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
