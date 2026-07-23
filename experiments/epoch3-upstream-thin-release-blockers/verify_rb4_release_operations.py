#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/epoch3-upstream-thin-release-blockers'
AUTH_REL='experiments/epoch3-upstream-thin-release-blockers/rb4-release-operations-authority.json'
EXPECTED_AUTH='abd185b4ffc4b37c41334a459af6735a85203a4d44ba569bf055b5fb369c8ab8'

def load(path:Path)->Any:return json.loads(path.read_text(encoding='utf-8'))
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def verify(root:Path=ROOT)->dict[str,Any]:
 auth_path=root/AUTH_REL
 if not auth_path.is_file():return {'schema_version':1,'verifier_kind':'epoch3-rb4-release-operations','pass':False,'checks':{'required_inputs':False},'failed_checks':['required_inputs'],'missing_inputs':['authority']}
 authority=load(auth_path);ids=authority.get('file_identities',{});sources=authority.get('source_authorities',{})
 missing=sorted([p for p in ids if not (root/p).is_file()]+[v['path'] for v in sources.values() if not (root/v['path']).is_file()])
 if missing:return {'schema_version':1,'verifier_kind':'epoch3-rb4-release-operations','pass':False,'checks':{'required_inputs':False},'failed_checks':['required_inputs'],'missing_inputs':missing}
 id_checks={p:sha(root/p)==h for p,h in ids.items()};source_checks={k:sha(root/v['path'])==v['sha256'] for k,v in sources.items()}
 e=BASE.relative_to(ROOT)/'rb4-release-operations-authority-evidence'
 patch=load(root/e/'patch-update-binding.json');catalog=load(root/e/'catalog-transition-receipt.json');rollback=load(root/e/'rollback-receipt.json');rev=load(root/e/'revocation-readback.json');security=load(root/e/'security-ownership.json');result=load(root/e/'result.json');audit=load(root/e/'independent-audit.json')
 contract=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb4-release-operations-contract.json');next_contract=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-contract.json')
 state_path=root/'docs/current/STATE.json';task_path=root/'docs/current/AGENT_TASK.json';register_path=root/'experiments/epoch3-upstream-thin-release-blockers/blocker-register.json'
 state=load(state_path) if state_path.is_file() else {};task=load(task_path) if task_path.is_file() else {};register=load(register_path) if register_path.is_file() else {}
 rb4=next((x for x in register.get('blockers',[]) if x.get('id')=='RB-4'),{});boundary=authority.get('claim_boundary',{})
 checks={
  'authority_identity':sha(auth_path)==EXPECTED_AUTH,
  'authority_kind':authority.get('authority_kind')=='epoch3-rb4-release-security-update-rollback-and-revocation-operations',
  'file_identities':bool(id_checks) and all(id_checks.values()),
  'source_authorities':bool(source_checks) and all(source_checks.values()),
  'contract':contract.get('status')=='authorized-local-deterministic-operations-qualification' and contract.get('claim_boundary',{}).get('publication') is False,
  'patch_update':patch.get('pass') is True and patch.get('from',{}).get('version')=='3.14.5' and patch.get('to',{}).get('version')=='3.14.6' and patch.get('checks',{}).get('epoch3_canonical_closure_complete') is True,
  'catalog':catalog.get('pass') is True and catalog.get('catalog_sha256')==authority.get('production_baseline',{}).get('catalog_sha256') and catalog.get('checks',{}).get('ambiguous_replacement_denied') is True,
  'rollback':rollback.get('pass') is True and rollback.get('checks',{}).get('drill_restored_to_baseline') is True and rollback.get('checks',{}).get('production_baseline_unchanged') is True,
  'revocation':rev.get('pass') is True and rev.get('drill_only') is True and rev.get('production_revocation_applied') is False and rev.get('checks',{}).get('revoked_selection_denied') is True and rev.get('checks',{}).get('revocation_rewrite_denied') is True,
  'security':security.get('pass') is True and security.get('checks',{}).get('automatic_release_forbidden') is True and security.get('checks',{}).get('minimum_two_roles') is True,
  'result_and_audit':result.get('pass') is True and audit.get('pass') is True and not audit.get('failed_checks'),
  'authority_boundary':boundary.get('rb4_closed') is True and boundary.get('rb1_closed') is False and boundary.get('rb5_closed') is False and boundary.get('selectable') is False and boundary.get('publication') is False and boundary.get('production_revocation_applied') is False,
  'next_contract':next_contract.get('contract_kind')=='epoch3-rb5-exact-canonical-family-api24-runtime-qualification' and next_contract.get('status')=='authorized-not-started' and next_contract.get('basis',{}).get('rb4_release_operations_authority',{}).get('sha256')==EXPECTED_AUTH,
  'state':state.get('state_revision')==54 and state.get('claim_boundaries',{}).get('rb4_closed') is True and state.get('active_work_package')=='experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-contract.json' and 'RB-4-release-security-update-and-revocation-operations' not in state.get('blockers',[]),
  'task':task.get('state_revision')==54 and task.get('task',{}).get('work_class')=='T' and task.get('deliverable',{}).get('current_bounded_transition')=='rb5-api24-runtime-owner-qualification',
  'blocker_register':rb4.get('status')=='closed-deterministic-release-operations-qualified' and rb4.get('evidence',{}).get('authority_sha256')==EXPECTED_AUTH,
 }
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {'schema_version':1,'verifier_kind':'epoch3-rb4-release-operations','pass':not failed,'checks':dict(sorted(checks.items())),'failed_checks':failed,'identity_checks':dict(sorted(id_checks.items())),'source_authority_checks':dict(sorted(source_checks.items()))}
def main()->int:
 r=verify();print(json.dumps(r,indent=2,sort_keys=True));return 0 if r['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
