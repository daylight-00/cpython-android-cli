#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/epoch3-upstream-thin-release-blockers'
EXPECTED_RESULT='c09d071e476a95470ca5e792aa1dc0897bd45e52198d985256a817a32f4cc306'
EXPECTED_FINGERPRINT='1d3714c21c328c10ad356e29971784e550c8b107c570383b36b1ef5cbdef85b5'
EXPECTED_RELEASE='407a67e81ef15fd1154487bcb31832c092e0068a73aae27f80b5edb498b8e2d1'
EXPECTED_OLD_POST='4d65756046b4718d337b5d4d97f605818bb1811c'
EXPECTED_NEW_POST='94e1aaab15f53d8c47ce71054af222bc64f21cca'
EXPECTED_TREE='3db24449b8009c4056cf5ec29c526a8307e1fe99'

def load(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def verify(root:Path=ROOT)->dict[str,Any]:
 b=root/'experiments/epoch3-upstream-thin-release-blockers'; e=b/'rb3-successor-technical-family-m-authority-evidence'
 authority=load(b/'rb3-successor-technical-family-m-authority.json')
 accepted=load(b/'accepted-rb3-successor-technical-family-m-r1-return.json')
 inspection=load(b/'rb3-successor-technical-family-m-r1-return-inspection.json')
 contract=load(b/'rb3-successor-technical-family-m-acceptance-contract.json')
 rewrite=load(b/'rb3-successor-technical-family-m-author-rewrite-map.json')
 legal=load(b/'rb3-successor-legal-family-m-contract.json')
 amendment=load(b/'rb3-successor-stripped-m-temporal-verifier-amendment.json')
 second=load(b/'rb3-successor-legal-family-temporal-verifier-amendment.json')
 latest=load(b/'rb3-successor-legal-data-rebinding-temporal-verifier-amendment.json')
 fourth=load(b/'rb3-successor-predecessor-supersession-temporal-verifier-amendment.json')
 fifth=load(b/'rb4-release-operations-temporal-verifier-amendment.json')
 sixth=load(b/'rb5-api24-support-scope-temporal-verifier-amendment.json')
 seventh=load(b/'rb6-real-16k-runtime-support-scope-temporal-verifier-amendment.json')
 eighth=load(b/'rb7-non-termux-runtime-support-scope-temporal-verifier-amendment.json')
 lock=load(root/'config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-successor-technical-family-r2.lock.json')
 owner=load(e/'owner-result.json'); owner_audit=load(e/'owner-independent-audit.json'); external=load(e/'external-acceptance-audit.json'); verification=load(e/'technical-family-verification.json'); repro=load(e/'reproducibility.json'); protected=load(e/'protected-state.json'); exact=load(e/'exact-input-verification.json'); index=load(e/'result-index.json'); release=load(e/'release-index.json')
 ids=authority.get('file_identities',{});second_replacements=second.get('replacements',{});latest_replacements=latest.get('replacements',{});fourth_replacements=fourth.get('replacements',{});fifth_replacements=fifth.get('replacements',{});sixth_replacements=sixth.get('replacements',{});seventh_replacements=seventh.get('replacements',{});eighth_replacements=eighth.get('replacements',{})
 id_checks={rel:(root/rel).is_file() and sha(root/rel)==eighth_replacements.get(rel,seventh_replacements.get(rel,sixth_replacements.get(rel,fifth_replacements.get(rel,fourth_replacements.get(rel,latest_replacements.get(rel,second_replacements.get(rel,{}))))))).get('replacement_sha256',expected) for rel,expected in ids.items()}
 expected_boundary={'successor_technical_family_candidate':True,'successor_technical_family_accepted':True,'successor_legal_family_integration_authorized':True,'successor_legal_family_integration_started':False,'rb1_rebound':False,'rb2_rebound':False,'predecessor_family_superseded':False,'rb3_closed':False,'selectable':False,'publication':False}
 checks={
  'authority_kind':authority.get('authority_kind')=='epoch3-rb3-profile-M-successor-technical-family-r2',
  'file_identities':bool(id_checks) and all(id_checks.values()),
  'accepted_status':accepted.get('status')=='accepted-pass-successor-technical-family-r2-legal-integration-authorized-pending',
  'inspection_status':inspection.get('status')=='accepted-complete-pass-legal-family-integration-authorized',
  'result_identity':accepted.get('result_archive',{}).get('sha256')==inspection.get('result_archive',{}).get('sha256')==authority.get('accepted_evidence',{}).get('result_archive_sha256')==EXPECTED_RESULT and accepted.get('result_archive',{}).get('size_bytes')==87065667 and accepted.get('result_archive',{}).get('self_index_file_count')==45,
  'self_index_count':len(index.get('files',[]))==45,
  'owner_result':owner.get('pass') is True and not owner.get('failed_checks') and all(owner.get('checks',{}).values()),
  'owner_audit':owner_audit.get('pass') is True and not owner_audit.get('failed_checks') and all(owner_audit.get('checks',{}).values()),
  'external_audit':external.get('pass') is True and not external.get('failed_checks') and all(external.get('checks',{}).values()),
  'technical_verification':verification.get('pass') is True and not verification.get('failed_checks') and all(verification.get('checks',{}).values()) and verification.get('file_count')==23 and verification.get('fingerprint_sha256')==EXPECTED_FINGERPRINT and verification.get('release_sha256')==EXPECTED_RELEASE,
  'reproducibility':repro.get('pass') is True and repro.get('all_files_byte_identical') is True and repro.get('inventory_byte_identical') is True and repro.get('first',{}).get('fingerprint_sha256')==EXPECTED_FINGERPRINT and repro.get('second',{}).get('fingerprint_sha256')==EXPECTED_FINGERPRINT,
  'protected':protected.get('pass') is True and protected.get('predecessor_family_unchanged') is True and protected.get('successor_authorities_unchanged') is True,
  'exact_inputs':exact.get('pass') is True,
  'release_candidate':release.get('release',{}).get('status')=='successor-technical-family-candidate-unaccepted',
  'lock_identity':lock.get('release_family',{}).get('fingerprint_sha256')==EXPECTED_FINGERPRINT and lock.get('release_family',{}).get('release_sha256')==EXPECTED_RELEASE and len(lock.get('files',[]))==23 and lock.get('claim_boundary',{}).get('technical_family_accepted') is True,
  'stripped_temporal_amendment':amendment.get('amendment_kind')=='epoch3-rb3-successor-stripped-temporal-routing-verifier-amendment' and amendment.get('invariants',{}).get('accepted_stripped_bytes_changed') is False,
  'second_temporal_amendment':second.get('amendment_kind')=='epoch3-rb3-successor-legal-family-temporal-routing-verifier-amendment' and second.get('invariants',{}).get('accepted_artifact_bytes_changed') is False,
  'latest_temporal_amendment':latest.get('amendment_kind')=='epoch3-rb3-successor-legal-data-rebinding-temporal-routing-verifier-amendment' and latest.get('invariants',{}).get('accepted_artifact_bytes_changed') is False and latest.get('predecessor_amendment',{}).get('path')=='experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-family-temporal-verifier-amendment.json' and latest.get('predecessor_amendment',{}).get('sha256')=='d11ba8f48fab81fe71cbbb3ae8ceb0a8529443211a5624f7ce9e0836e9cf36a5' and all(fourth_replacements.get(rel,{}).get('original_sha256')==row.get('replacement_sha256') for rel,row in latest_replacements.items()),
  'fourth_temporal_amendment':fourth.get('amendment_kind')=='epoch3-rb3-successor-predecessor-supersession-temporal-routing-verifier-amendment' and fourth.get('invariants',{}).get('accepted_artifact_bytes_changed') is False and fourth.get('predecessor_amendment',{}).get('path')=='experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-data-rebinding-temporal-verifier-amendment.json' and fourth.get('predecessor_amendment',{}).get('sha256')=='5f70109c21101c593da595e444f0db5dd8c64e928627d778d9a26cb44758ee95' and all(fifth_replacements.get(rel,{}).get('original_sha256')==row.get('replacement_sha256') for rel,row in fourth_replacements.items()),
  'fifth_temporal_amendment':fifth.get('amendment_kind')=='epoch3-rb4-release-operations-temporal-routing-verifier-amendment' and fifth.get('invariants',{}).get('accepted_artifact_bytes_changed') is False and fifth.get('predecessor_amendment',{}).get('path')=='experiments/epoch3-upstream-thin-release-blockers/rb3-successor-predecessor-supersession-temporal-verifier-amendment.json' and fifth.get('predecessor_amendment',{}).get('sha256')=='71eb3559290c0be75e9b0f37ec5d2b13aa7e06f0e4f9ba260829d8acc2d559a6' and all(sixth_replacements.get(rel,{}).get('original_sha256')==row.get('replacement_sha256') for rel,row in fifth_replacements.items()),
  'sixth_temporal_amendment':sixth.get('amendment_kind')=='epoch3-rb5-api24-support-scope-temporal-verifier-amendment' and sixth.get('invariants',{}).get('accepted_artifact_bytes_changed') is False and sixth.get('predecessor_amendment',{}).get('path')=='experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-temporal-verifier-amendment.json' and sixth.get('predecessor_amendment',{}).get('sha256')=='bc8aa9da7c81d4d2a48b11759a9aa058118f6db8be9a5f2501ebc220d134d8c0' and all((seventh_replacements.get(rel,{}).get('original_sha256')==row.get('replacement_sha256')) if rel in seventh_replacements else ((root/rel).is_file() and sha(root/rel)==row.get('replacement_sha256')) for rel,row in sixth_replacements.items()),
  'seventh_temporal_amendment':seventh.get('amendment_kind')=='epoch3-rb6-real-16k-runtime-support-scope-temporal-verifier-amendment' and seventh.get('invariants',{}).get('accepted_artifact_bytes_changed') is False and seventh.get('predecessor_amendment',{}).get('path')=='experiments/epoch3-upstream-thin-release-blockers/rb5-api24-support-scope-temporal-verifier-amendment.json' and seventh.get('predecessor_amendment',{}).get('sha256')=='22f54b767cd606453c952ddf8e58fb5ac46446e44f98aa1e02137c6b34fe9c89' and all((eighth_replacements.get(rel,{}).get('original_sha256')==row.get('replacement_sha256')) if rel in eighth_replacements else ((root/rel).is_file() and sha(root/rel)==row.get('replacement_sha256')) for rel,row in seventh_replacements.items()),
  'eighth_temporal_amendment':eighth.get('amendment_kind')=='epoch3-rb7-non-termux-runtime-support-scope-temporal-verifier-amendment' and eighth.get('invariants',{}).get('accepted_artifact_bytes_changed') is False and eighth.get('predecessor_amendment',{}).get('path')=='experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-temporal-verifier-amendment.json' and eighth.get('predecessor_amendment',{}).get('sha256')=='606bb992ede5470a53c95dedf7a3b23f34df2033879d54e784c23de7f51ceb85' and all((root/rel).is_file() and sha(root/rel)==row.get('replacement_sha256') for rel,row in eighth_replacements.items()),
  'author_rewrite':rewrite.get('rewrite_scope',{}).get('mapped_commit_count')==12 and rewrite.get('receipt_binding',{}).get('old_post_head')==EXPECTED_OLD_POST and rewrite.get('receipt_binding',{}).get('new_post_head')==EXPECTED_NEW_POST and rewrite.get('receipt_binding',{}).get('post_tree')==EXPECTED_TREE and rewrite.get('invariants',{}).get('tree_subject_author_date_preserved') is True,
  'acceptance_boundary':accepted.get('claim_boundary')==inspection.get('claim_boundary')==contract.get('success_boundary')==expected_boundary,
  'authority_boundary':authority.get('claim_boundary')=={'successor_technical_family_candidate':True,'successor_technical_family_accepted':True,'successor_legal_family_integration_authorized':True,'successor_legal_family_integration_started':False,'successor_legal_family_candidate':False,'successor_legal_family_accepted':False,'rb1_rebound':False,'rb2_rebound':False,'predecessor_family_superseded':False,'rb3_closed':False,'selectable':False,'publication':False},
  'next_contract':legal.get('contract_kind')=='epoch3-rb3-profile-M-successor-legal-family-integration' and legal.get('accepted_technical_family',{}).get('fingerprint_sha256')==EXPECTED_FINGERPRINT and legal.get('proposed_output',{}).get('release_id')=='cpython-3.14.6+e3-r3-aarch64-linux-android' and legal.get('success_boundary',{}).get('successor_legal_family_candidate') is True and legal.get('success_boundary',{}).get('predecessor_family_superseded') is False,
 }
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {'schema_version':1,'verifier_kind':'epoch3-rb3-profile-M-successor-technical-family-r2-acceptance','pass':not failed,'checks':dict(sorted(checks.items())),'failed_checks':failed,'identity_checks':dict(sorted(id_checks.items()))}

def main()->int:
 r=verify(); print(json.dumps(r,indent=2,sort_keys=True)); return 0 if r['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
