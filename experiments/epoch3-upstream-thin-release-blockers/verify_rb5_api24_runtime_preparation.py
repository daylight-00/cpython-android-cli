#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/epoch3-upstream-thin-release-blockers'
EXPECTED={
 'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-contract.json':'a2d8f426f4c19ee6460fadb06d9386dc250886fbcb7ce8d74026696a2bdb54ca',
 'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-execution-contract.json':'cf3e70a1c39c4ed95d7c093dc89f787dbe182e856bd84d30cb4af5a674430042',
 'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-host-preflight.json':'2f523028cb817d47f9b08d2419638c2de2b4b0f5cb70db1378d052ea0f2d1080',
 'experiments/epoch3-upstream-thin-release-blockers/run_rb5_api24_runtime.py':'8b0cd09028dcac8ba8c0648e7ea1373de60bce64645c96d3e9009a0ddbafdc6f',
 'experiments/epoch3-upstream-thin-release-blockers/audit_rb5_api24_runtime.py':'b8dc1d2f4e7c2ae3387c6ee948d244f1562db13da636fa355f1ec62422e1e0b9',
 'experiments/epoch3-upstream-thin-release-blockers/test_rb5_api24_runtime.py':'bfcdfa8b741be146b7de36db8264921b89aedb9dabe0cb682f4b251223df291f',
 'experiments/epoch3-upstream-thin-release-blockers/rb4-release-operations-authority.json':'abd185b4ffc4b37c41334a459af6735a85203a4d44ba569bf055b5fb369c8ab8',
 'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-temporal-verifier-amendment.json':'bc8aa9da7c81d4d2a48b11759a9aa058118f6db8be9a5f2501ebc220d134d8c0',
 'experiments/epoch3-upstream-thin-release-blockers/verify_rb4_release_operations.py':'2bbf5e9b9211b874d72cf37ada80afce64ddfa39e2b07a82bc7f6d74fdcec91f',
 'config/products/cpython-3.14.6-aarch64-linux-android-upstream-thin-canonical-family-r1.lock.json':'861d4536b13b58f1181c5249f98e498270f2860d8f51622e0176ed91bf075c0b',
 'experiments/epoch3-upstream-thin-release-blockers/rb3-successor-legal-family-m-authority.json':'f4570c47d5f5af1dc1802255b116aecf9fe99724c06e69770baf991cee4240e6',
 'experiments/epoch3-upstream-thin-release-blockers/rb2-data-product-authority.json':'48ae38370afcd3cf095566307e6859ee2bf88a6ee0c45ad7f07dea7401e77098',
}
def load(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root:Path=ROOT)->dict[str,Any]:
 missing=[p for p in EXPECTED if not (root/p).is_file()]
 if missing:return {'schema_version':1,'verifier_kind':'epoch3-rb5-api24-runtime-preparation','pass':False,'checks':{'required_inputs':False},'failed_checks':['required_inputs'],'missing_inputs':missing}
 ids={p:sha(root/p)==h for p,h in EXPECTED.items()}
 base=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-contract.json')
 execution=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-execution-contract.json')
 preflight=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-host-preflight.json')
 state=load(root/'docs/current/STATE.json');task=load(root/'docs/current/AGENT_TASK.json');register=load(root/'experiments/epoch3-upstream-thin-release-blockers/blocker-register.json')
 rb5=next((x for x in register.get('blockers',[]) if x.get('id')=='RB-5'),{})
 task_reads={x.get('path') for x in task.get('required_reads',[])}
 prepared_state=(state.get('state_revision')==55 and state.get('active_work_package')=='experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-contract.json' and state.get('claim_boundaries',{}).get('api24_runtime_started') is True and state.get('claim_boundaries',{}).get('api24_runtime_candidate') is False and state.get('claim_boundaries',{}).get('api24_runtime_accepted') is False and state.get('claim_boundaries',{}).get('rb4_closed') is True)
 disposed_state=(state.get('state_revision')==56 and state.get('active_work_package')=='experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-disposition-contract.json' and state.get('claim_boundaries',{}).get('api24_runtime_attempted') is True and state.get('claim_boundaries',{}).get('api24_runtime_started') is False and state.get('claim_boundaries',{}).get('api24_runtime_candidate') is False and state.get('claim_boundaries',{}).get('api24_runtime_accepted') is False and state.get('claim_boundaries',{}).get('api24_runtime_qualified') is False and state.get('claim_boundaries',{}).get('api24_runtime_supported') is False and state.get('claim_boundaries',{}).get('api24_runtime_scope_excluded') is True and state.get('claim_boundaries',{}).get('rb5_closed') is True)
 prepared_task=(task.get('state_revision')==55 and task.get('task',{}).get('work_class')=='T' and task.get('deliverable',{}).get('current_bounded_transition')=='rb5-api24-runtime-owner-qualification' and {'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-contract.json','experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-execution-contract.json','experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-host-preflight.json'}.issubset(task_reads))
 disposed_task=(task.get('state_revision')==56 and task.get('task',{}).get('work_class')=='T' and task.get('deliverable',{}).get('current_bounded_transition')=='rb6-real-16k-runtime-support-disposition' and {'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-support-scope-authority.json','experiments/epoch3-upstream-thin-release-blockers/rb5-api24-support-scope-temporal-verifier-amendment.json','experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-disposition-contract.json'}.issubset(task_reads))
 prepared_register=(rb5.get('status')=='in-progress-owner-qualification-prepared' and rb5.get('evidence',{}).get('execution_contract_sha256')==EXPECTED['experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-execution-contract.json'] and rb5.get('evidence',{}).get('temporal_amendment_sha256')==EXPECTED['experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-temporal-verifier-amendment.json'])
 disposed_register=(rb5.get('status')=='closed-owner-scope-excluded-api24-unsupported-not-qualified' and rb5.get('evidence',{}).get('support_scope_authority_sha256')=='0c24db1a651924a64d7e4b1f907ed0deaca56413609cf9794449d30040ea2723' and rb5.get('evidence',{}).get('api24_runtime_qualified') is False and rb5.get('evidence',{}).get('api24_runtime_supported') is False and rb5.get('evidence',{}).get('api24_runtime_required_for_selectability') is False)
 scope_amendment=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-support-scope-temporal-verifier-amendment.json')
 checks={
  'file_identities':all(ids.values()),
  'base_contract':base.get('contract_kind')=='epoch3-rb5-exact-canonical-family-api24-runtime-qualification' and base.get('target',{}).get('android_api')==24 and base.get('target',{}).get('exact_api_required') is True,
  'execution_contract':execution.get('contract_kind')=='epoch3-rb5-api24-runtime-owner-execution' and execution.get('status')=='prepared-owner-qualification' and execution.get('base_contract',{}).get('sha256')==EXPECTED['experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-contract.json'],
  'exact_inputs':execution.get('exact_inputs',{}).get('canonical_legal_family_result',{}).get('sha256')=='c43975ec955f0d4f692567d728ded4200c1ea246574e2d514fbd44dca64ff3f7' and execution.get('exact_inputs',{}).get('accepted_data_product_result',{}).get('sha256')=='6419154d3888ac1e3e5331b11b9692262ca2d90709389e20dfeb848f28507d1c',
  'target_boundary':execution.get('target_selection',{}).get('android_api')==24 and execution.get('target_selection',{}).get('exact_api_required') is True and execution.get('target_selection',{}).get('higher_api_substitution_forbidden') is True,
  'host_preflight':preflight.get('pass') is True and preflight.get('target_execution_performed') is False and preflight.get('target_check',{}).get('exact_target_available') is False and all(v is True for v in preflight.get('input_checks',{}).values()),
  'candidate_only':execution.get('claim_boundary',{}).get('api24_runtime_started') is True and execution.get('claim_boundary',{}).get('api24_runtime_candidate_on_success') is True and execution.get('claim_boundary',{}).get('api24_runtime_accepted') is False and execution.get('claim_boundary',{}).get('rb5_closed') is False,
  'state':prepared_state or disposed_state,
  'task':prepared_task or disposed_task,
  'temporal_amendment':load(root/'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-temporal-verifier-amendment.json').get('predecessor_amendment',{}).get('sha256')=='575688ae02ce564a803acb1b5ba69e2d97e2bf885fc57041e1dedcf70e3cf232' and (prepared_state or (scope_amendment.get('predecessor_amendment',{}).get('sha256')==EXPECTED['experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-temporal-verifier-amendment.json'] and scope_amendment.get('allowed_progression',{}).get('state_revision')==56 and scope_amendment.get('allowed_progression',{}).get('api24_runtime_scope_excluded') is True)),
  'register':prepared_register or disposed_register,
  'claims_withheld':state.get('claim_boundaries',{}).get('actual_16k_runtime_qualified') is False and state.get('claim_boundaries',{}).get('non_termux_android_context_qualified') is False and state.get('claim_boundaries',{}).get('selectable') is False and state.get('claim_boundaries',{}).get('publication_authorized') is False,
 }
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {'schema_version':1,'verifier_kind':'epoch3-rb5-api24-runtime-preparation','pass':not failed,'checks':dict(sorted(checks.items())),'failed_checks':failed,'identity_checks':dict(sorted(ids.items()))}
def main()->int:
 r=verify();print(json.dumps(r,indent=2,sort_keys=True));return 0 if r['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
