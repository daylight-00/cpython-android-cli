#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/epoch3-upstream-thin-release-blockers'
AUTH_REL='experiments/epoch3-upstream-thin-release-blockers/rb3-successor-predecessor-supersession-m-authority.json'
EXPECTED_PREDECESSOR_AUTH='102ea6c02198885a08328d821511a10b8043510095970dfde17d8c8ef18e276e'
EXPECTED_PREDECESSOR_LOCK='8c1a06cd67e70219807e463a30524bec767661d33d0ef86eea9cec029a918322'
EXPECTED_SUCCESSOR_AUTH='f4570c47d5f5af1dc1802255b116aecf9fe99724c06e69770baf991cee4240e6'
EXPECTED_REBINDING_AUTH='98417df172d350dff256516c759b6b9b671df2c5d98062ca64fdcd5c9dedfb89'
EXPECTED_RESULT='176e9947df1fd40d0650c77aeedd4701cf03958cc842767f63735d700bb80685'

def load(path:Path)->Any:return json.loads(path.read_text(encoding='utf-8'))
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def verify(root:Path=ROOT)->dict[str,Any]:
 auth_path=root/AUTH_REL
 if not auth_path.is_file():
  return {'schema_version':1,'verifier_kind':'epoch3-rb3-profile-M-successor-predecessor-supersession','pass':False,'checks':{'required_inputs':False},'failed_checks':['required_inputs'],'missing_inputs':['authority']}
 authority=load(auth_path)
 ids=authority.get('file_identities',{})
 missing=sorted(p for p in ids if not (root/p).is_file())
 if missing:
  return {'schema_version':1,'verifier_kind':'epoch3-rb3-profile-M-successor-predecessor-supersession','pass':False,'checks':{'required_inputs':False,'file_identities':False},'failed_checks':['file_identities','required_inputs'],'missing_inputs':missing}
 loaded={p:load(root/p) for p in ids}
 id_checks={p:sha(root/p)==h for p,h in ids.items()}
 source_checks={k:(root/v['path']).is_file() and sha(root/v['path'])==v['sha256'] for k,v in authority.get('source_authorities',{}).items()}
 pred_auth=loaded['experiments/epoch3-upstream-thin-artifact-family/artifact-family-authority.json']
 pred_lock=loaded['config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-artifact-family-r1.lock.json']
 succ_lock=loaded['config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-successor-legal-family-r3.lock.json']
 canonical=loaded['config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-canonical-family-r1.lock.json']
 succ_auth=loaded['experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-family-m-authority.json']
 rebinding=loaded['experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-data-rebinding-m-authority.json']
 contract=loaded['experiments/epoch3-upstream-thin-release-blockers/rb3-successor-predecessor-supersession-m-contract.json']
 receipt=loaded['experiments/epoch3-upstream-thin-release-blockers/rb3-successor-predecessor-supersession-m-closure-receipt.json']
 inspection=loaded['experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-data-rebinding-m-acceptance-r2-return-inspection.json']
 state_path=root/'docs/current/STATE.json'; task_path=root/'docs/current/AGENT_TASK.json'; register_path=BASE/'blocker-register.json'
 state=load(state_path) if state_path.is_file() else {}; task=load(task_path) if task_path.is_file() else {}; register=load(register_path) if register_path.is_file() else {}
 rb5_contract='experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-contract.json';rb4_authority='experiments/epoch3-upstream-thin-release-blockers/rb4-release-operations-authority.json';rb4_temporal='experiments/epoch3-upstream-thin-release-blockers/rb4-release-operations-temporal-verifier-amendment.json'
 rb5_scope_authority='experiments/epoch3-upstream-thin-release-blockers/rb5-api24-support-scope-authority.json';rb5_scope_temporal='experiments/epoch3-upstream-thin-release-blockers/rb5-api24-support-scope-temporal-verifier-amendment.json';rb6_contract='experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-disposition-contract.json'
 rb6_scope_authority='experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-authority.json';rb6_scope_temporal='experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-temporal-verifier-amendment.json';rb7_contract='experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-disposition-contract.json'
 rb7_scope_authority='experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-authority.json';rb7_scope_temporal='experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-temporal-verifier-amendment.json';rb1_owner_contract='experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-contract.json'
 task_reads={x.get('path') for x in task.get('required_reads',[])};task_auth={x.get('path'):x.get('sha256') for x in task.get('required_authorities',[])}
 rb5_progression=state.get('state_revision',0)>=54 and state.get('active_work_package')==rb5_contract and state.get('claim_boundaries',{}).get('rb4_closed') is True and state.get('claim_boundaries',{}).get('release_operations_complete') is True and task.get('deliverable',{}).get('current_bounded_transition')=='rb5-api24-runtime-owner-qualification' and {rb5_contract,rb4_authority,rb4_temporal}.issubset(task_reads) and (root/rb4_authority).is_file() and (root/rb4_temporal).is_file() and task_auth.get(rb4_authority)==sha(root/rb4_authority) and task_auth.get(rb4_temporal)==sha(root/rb4_temporal)
 scope_progression=state.get('state_revision')==56 and state.get('active_work_package')==rb6_contract and state.get('claim_boundaries',{}).get('rb5_closed') is True and state.get('claim_boundaries',{}).get('api24_runtime_supported') is False and state.get('claim_boundaries',{}).get('api24_runtime_scope_excluded') is True and task.get('deliverable',{}).get('current_bounded_transition')=='rb6-real-16k-runtime-support-disposition' and {rb6_contract,rb5_scope_authority,rb5_scope_temporal}.issubset(task_reads) and all((root/p).is_file() for p in (rb6_contract,rb5_scope_authority,rb5_scope_temporal)) and task_auth.get(rb5_scope_authority)==sha(root/rb5_scope_authority) and task_auth.get(rb5_scope_temporal)==sha(root/rb5_scope_temporal)
 rb6_scope_progression=state.get('state_revision')==57 and state.get('active_work_package')==rb7_contract and state.get('claim_boundaries',{}).get('rb6_closed') is True and state.get('claim_boundaries',{}).get('actual_16k_runtime_supported') is False and state.get('claim_boundaries',{}).get('actual_16k_runtime_scope_excluded') is True and task.get('deliverable',{}).get('current_bounded_transition')=='rb7-non-termux-runtime-support-disposition' and {rb7_contract,rb6_scope_authority,rb6_scope_temporal}.issubset(task_reads) and all((root/p).is_file() for p in (rb7_contract,rb6_scope_authority,rb6_scope_temporal)) and task_auth.get(rb6_scope_authority)==sha(root/rb6_scope_authority) and task_auth.get(rb6_scope_temporal)==sha(root/rb6_scope_temporal)
 rb7_scope_progression=state.get('state_revision')==58 and state.get('active_work_package')==rb1_owner_contract and state.get('claim_boundaries',{}).get('rb7_closed') is True and state.get('claim_boundaries',{}).get('non_termux_android_context_supported') is False and state.get('claim_boundaries',{}).get('non_termux_android_context_scope_excluded') is True and task.get('deliverable',{}).get('current_bounded_transition')=='rb1-successor-r3-explicit-owner-approval' and {rb7_scope_authority,rb7_scope_temporal,rb1_owner_contract}.issubset(task_reads) and all((root/p).is_file() for p in (rb7_scope_authority,rb7_scope_temporal,rb1_owner_contract)) and task_auth.get(rb7_scope_authority)==sha(root/rb7_scope_authority) and task_auth.get(rb7_scope_temporal)==sha(root/rb7_scope_temporal)
 later_progression=rb5_progression or scope_progression or rb6_scope_progression or rb7_scope_progression
 pred=pred_lock.get('release_family',{}); succ=succ_lock.get('release_family',{}); boundary=authority.get('claim_boundary',{})
 mapping=authority.get('supersession_map',{}).get('artifact_mapping',[])
 flavors={r.get('flavor') for r in mapping}
 rb3=next((r for r in register.get('blockers',[]) if r.get('id')=='RB-3'),{})
 checks={
  'authority_kind':authority.get('authority_kind')=='epoch3-rb3-profile-M-successor-predecessor-family-supersession-and-rb3-closure',
  'file_identities':bool(id_checks) and all(id_checks.values()),
  'source_authorities':bool(source_checks) and all(source_checks.values()),
  'predecessor_frozen':sha(root/'experiments/epoch3-upstream-thin-artifact-family/artifact-family-authority.json')==EXPECTED_PREDECESSOR_AUTH and sha(root/'config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-artifact-family-r1.lock.json')==EXPECTED_PREDECESSOR_LOCK and pred_auth.get('release_family',{}).get('release_id')==pred.get('release_id') and pred_auth.get('release_family',{}).get('release_sha256')==pred.get('release_sha256') and pred_auth.get('release_family',{}).get('fingerprint_sha256')==pred.get('fingerprint_sha256'),
  'successor_frozen':sha(root/'experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-family-m-authority.json')==EXPECTED_SUCCESSOR_AUTH and sha(root/'experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-data-rebinding-m-authority.json')==EXPECTED_REBINDING_AUTH and all(succ_auth.get('accepted_family',{}).get(k)==rebinding.get('accepted_family',{}).get(k)==succ.get(k) for k in ('release_id','file_count','fingerprint_sha256','release_sha256','release_index_sha256','sha256sums_sha256')),
  'acceptance_receipt':inspection.get('result_archive',{}).get('sha256')==EXPECTED_RESULT and inspection.get('result_archive',{}).get('self_index_file_count')==19 and inspection.get('receipt',{}).get('post_head')=='25e5bae1d48a031d443174e6e8cbb81316910276' and inspection.get('verification',{}).get('total_tests')=='174/174',
  'explicit_map':flavors=={'full','install_only','install_only_stripped'} and len(mapping)==3 and all(r.get('artifact_bytes_reused_from_accepted_successor') is True for r in mapping),
  'canonical_lock':canonical.get('status')=='successor-r3-canonical-predecessor-r1-historical-valid' and canonical.get('canonical_family',{}).get('release_sha256')==succ.get('release_sha256') and canonical.get('superseded_family',{}).get('release_sha256')==pred.get('release_sha256') and canonical.get('claim_boundary',{}).get('rb3_closed') is True,
  'closure_receipt':receipt.get('status')=='pass-successor-r3-canonical-predecessor-r1-historical-valid-rb3-closed' and receipt.get('closure',{}).get('rb3_closed') is True and receipt.get('closure',{}).get('rb1_closed') is False and receipt.get('closure',{}).get('selectable') is False and receipt.get('closure',{}).get('publication') is False,
  'contract':contract.get('success_boundary',{}).get('predecessor_family_superseded') is True and contract.get('success_boundary',{}).get('successor_family_canonical') is True and contract.get('success_boundary',{}).get('rb3_closed') is True,
  'authority_boundary':boundary.get('predecessor_family_superseded') is True and boundary.get('predecessor_family_historical_valid') is True and boundary.get('successor_family_canonical') is True and boundary.get('astral_consumer_compatibility_complete') is True and boundary.get('rb3_closed') is True and boundary.get('rb1_closed') is False and boundary.get('selectable') is False and boundary.get('publication') is False,
  'state':(state.get('state_revision')==53 or later_progression) and state.get('claim_boundaries',{}).get('predecessor_family_superseded') is True and state.get('claim_boundaries',{}).get('successor_family_canonical') is True and state.get('claim_boundaries',{}).get('astral_consumer_compatibility_complete') is True and 'RB-3-sysconfig-sdk-and-astral-consumer-boundary' not in state.get('blockers',[]),
  'task':(task.get('state_revision')==53 and task.get('task',{}).get('work_class')=='T' and task.get('deliverable',{}).get('current_bounded_transition')=='rb3-profile-M-successor-predecessor-supersession-and-rb3-closure-owner-transition') or later_progression,
  'blocker_register':rb3.get('status')=='closed-profile-M-successor-r3-canonical-predecessor-r1-historical-valid' and rb3.get('closure',{}).get('rb3_closed') is True,
 }
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {'schema_version':1,'verifier_kind':'epoch3-rb3-profile-M-successor-predecessor-supersession','pass':not failed,'checks':dict(sorted(checks.items())),'failed_checks':failed,'identity_checks':dict(sorted(id_checks.items())),'source_authority_checks':dict(sorted(source_checks.items()))}
def main()->int:
 result=verify();print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
