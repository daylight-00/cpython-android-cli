#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AUTH_REL='experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-authority.json'
EXPECTED_AUTH='5d383c33b414b0e09ce826b3567a680d622bd355ccbf35b9371eaccb5b1da366'
EXPECTED_DECISION='086a01c9b4bf857bfcc94a98b678f841a2573903f8c6931a68d1268503c55db6'
EXPECTED_CONTRACT='0a89f6076bf408f56cf8627b26420ac7791bcfd1ce86cb41633906b9dcfec317'
EXPECTED_NEXT='180c761efedcf26ded43f5c1626650c6e8673934399607af30b97f6c0defb430'
EXPECTED_TEMPORAL='c0545678ad0f0d2c0846ab586270a252d20a451dc3489b7e997741fd4782aa9e'

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path):return json.loads(p.read_text(encoding='utf-8'))

def verify(root:Path|None=None)->dict:
    root=(root or ROOT).resolve(); auth_path=root/AUTH_REL
    if not auth_path.is_file():return {'schema_version':1,'verifier_kind':'epoch3-rb7-non-termux-runtime-support-scope','pass':False,'checks':{'authority_exists':False},'failed_checks':['authority_exists']}
    auth=load(auth_path);ids=auth.get('file_identities',{});sources=auth.get('source_authorities',{})
    required=['docs/current/STATE.json','docs/current/AGENT_TASK.json','docs/agent/TASK_CATALOG.json','docs/documentation/document-registry.json','experiments/epoch3-upstream-thin-release-blockers/blocker-register.json','docs/roadmap/EPOCH3_RELEASE_BLOCKER_RESOLUTION_PLAN.md','experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-temporal-verifier-amendment.json']
    missing=sorted([p for p in ids if not (root/p).is_file()]+[v['path'] for v in sources.values() if not (root/v['path']).is_file()]+[p for p in required if not (root/p).is_file()])
    if missing:return {'schema_version':1,'verifier_kind':'epoch3-rb7-non-termux-runtime-support-scope','pass':False,'checks':{'required_inputs':False},'failed_checks':['required_inputs'],'missing_inputs':sorted(set(missing))}
    identity_checks={p:sha(root/p)==h for p,h in ids.items()};source_checks={k:sha(root/v['path'])==v['sha256'] for k,v in sources.items()}
    decision=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-decision-contract.json')
    contract=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-disposition-contract.json')
    nextc=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-contract.json')
    temporal=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-temporal-verifier-amendment.json')
    state=load(root/'docs/current/STATE.json');task=load(root/'docs/current/AGENT_TASK.json');catalog=load(root/'docs/agent/TASK_CATALOG.json');register=load(root/'experiments/epoch3-upstream-thin-release-blockers/blocker-register.json');registry=load(root/'docs/documentation/document-registry.json')
    plan=(root/'docs/roadmap/EPOCH3_RELEASE_BLOCKER_RESOLUTION_PLAN.md').read_text(encoding='utf-8')
    rb1=next((x for x in register.get('blockers',[]) if x.get('id')=='RB-1'),{});rb7=next((x for x in register.get('blockers',[]) if x.get('id')=='RB-7'),{});e3=next((x for x in catalog.get('tasks',[]) if x.get('task_id')=='E3-RELEASE-BLOCKERS'),{})
    b=auth.get('claim_boundary',{});sb=state.get('claim_boundaries',{});registered={x['path'] for x in registry.get('documents',[])}
    policy_correction_authority='experiments/epoch3-upstream-thin-release-blockers/rb5-rb7-runtime-support-policy-correction-authority.json'; policy_correction_temporal='experiments/epoch3-upstream-thin-release-blockers/rb5-rb7-runtime-support-policy-correction-temporal-verifier-amendment.json'
    policy_correction_progression=all((root/p).is_file() for p in (policy_correction_authority,policy_correction_temporal)) and state.get('state_revision')==59 and state.get('active_work_package')=='experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-contract.json' and sb.get('app_uid_non_termux_runtime_qualified') is True and sb.get('non_termux_android_context_supported') is True and sb.get('non_termux_android_context_scope_excluded') is False and task.get('deliverable',{}).get('current_bounded_transition')=='rb1-successor-r3-explicit-owner-approval' and any(x.get('path')==policy_correction_authority and x.get('sha256')==sha(root/policy_correction_authority) for x in task.get('required_authorities',[])) and any(x.get('path')==policy_correction_temporal and x.get('sha256')==sha(root/policy_correction_temporal) for x in task.get('required_authorities',[]))
    owner_approval_authority='experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-authority.json';owner_approval_temporal='experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-temporal-verifier-amendment.json'
    owner_temporal=load(root/owner_approval_temporal) if (root/owner_approval_temporal).is_file() else {}
    owner_approval_progression=state.get('state_revision')==60 and state.get('active_work_package')=='experiments/epoch3-upstream-thin-release-blockers/epoch3-release-candidate-integration-contract.json' and state.get('claim_boundaries',{}).get('owner_approved') is True and state.get('claim_boundaries',{}).get('rb1_closed') is True and state.get('claim_boundaries',{}).get('selectable') is False and state.get('claim_boundaries',{}).get('publication_authorized') is False and task.get('deliverable',{}).get('current_bounded_transition')=='epoch3-selectable-release-candidate-integration' and all((root/p).is_file() for p in (owner_approval_authority,owner_approval_temporal)) and sha(root/owner_approval_authority)=='6794102f1941ec1b1715dfaa1b6a7bf4935c6f7c6798d5a731846cfd9843aceb' and owner_temporal.get('amendment_kind')=='epoch3-rb1-successor-r3-owner-approval-temporal-verifier-amendment' and owner_temporal.get('accepted_owner_approval_authority',{}).get('sha256')=='6794102f1941ec1b1715dfaa1b6a7bf4935c6f7c6798d5a731846cfd9843aceb' and owner_temporal.get('allowed_progression',{}).get('state_revision')==60 and owner_temporal.get('allowed_progression',{}).get('rb1_closed') is True and owner_temporal.get('allowed_progression',{}).get('owner_approved') is True and owner_temporal.get('allowed_progression',{}).get('selectable') is False and owner_temporal.get('allowed_progression',{}).get('publication') is False
    later_progression=policy_correction_progression or owner_approval_progression
    checks={
      'authority_identity':sha(auth_path)==EXPECTED_AUTH,
      'authority_kind':auth.get('authority_kind')=='epoch3-rb7-non-termux-android-runtime-support-scope-disposition',
      'authority_status':auth.get('status')=='closed-owner-scope-excluded-non-termux-unsupported-not-qualified',
      'file_identities':bool(identity_checks) and all(identity_checks.values()),
      'source_authorities':bool(source_checks) and all(source_checks.values()),
      'decision_identity':sha(root/'experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-decision-contract.json')==EXPECTED_DECISION,
      'decision_guard':decision.get('status')=='owner-decision-ready' and decision.get('owner_observation',{}).get('additional_non_termux_context_testing_declined') is True and decision.get('owner_observation',{}).get('termux_execution_proves_non_termux_support') is False and decision.get('owner_observation',{}).get('x86_substitution_accepted') is False and decision.get('runner_guard',{}).get('if_current_context_is_non_termux')=='fail-closed-and-require-separate-exact-context-qualification' and decision.get('runner_guard',{}).get('if_context_identity_unknown')=='fail-closed',
      'contract_allows_scope':contract.get('allowed_dispositions',{}).get('owner_scope_exclusion',{}).get('allowed') is True and contract.get('allowed_dispositions',{}).get('owner_scope_exclusion',{}).get('non_termux_runtime_claim_must_remain_false') is True,
      'support_split':auth.get('support_policy',{}).get('termux_runtime_context_retained') is True and auth.get('support_policy',{}).get('termux_runtime_is_non_termux_support') is False and auth.get('support_policy',{}).get('non_termux_android_context_supported') is False,
      'authority_boundary':b.get('non_termux_android_context_qualified') is False and b.get('non_termux_android_context_supported') is False and b.get('non_termux_android_context_scope_excluded') is True and b.get('rb7_closed') is True and b.get('rb1_closed') is False and b.get('selectable') is False and b.get('publication') is False and b.get('artifact_bytes_changed') is False,
      'next_contract':sha(root/'experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-contract.json')==EXPECTED_NEXT and nextc.get('status')=='authorized-owner-decision-pending' and nextc.get('claim_boundary',{}).get('owner_approved') is False and nextc.get('exact_binding',{}).get('release_id')=='cpython-3.14.6+e3-r3-aarch64-linux-android' and nextc.get('exact_binding',{}).get('notice_sha256')=='80cf82a6b6957fd830701e2559755d1eecdf01c61cbcb4f8f8843b9735eaf613',
      'temporal_amendment':sha(root/'experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-temporal-verifier-amendment.json')==EXPECTED_TEMPORAL and temporal.get('status')=='frozen-verifier-only-rb1-owner-approval-routing-enabled' and temporal.get('accepted_scope_authority',{}).get('sha256')==EXPECTED_AUTH and temporal.get('next_contract',{}).get('sha256')==EXPECTED_NEXT,
      'state':later_progression or state.get('state_revision')==58 and state.get('active_work_package')=='experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-contract.json' and state.get('blockers')==['RB-1-component-and-license-closure'] and sb.get('rb7_closed') is True and sb.get('non_termux_android_context_qualified') is False and sb.get('non_termux_android_context_supported') is False and sb.get('non_termux_android_context_scope_excluded') is True and sb.get('selectable') is False and sb.get('publication_authorized') is False,
      'task':later_progression or task.get('state_revision')==58 and task.get('deliverable',{}).get('current_bounded_transition')=='rb1-successor-r3-explicit-owner-approval' and task.get('claim_boundary',{}).get('rb7_closed_claim') is True and task.get('claim_boundary',{}).get('non_termux_context_scope_excluded_claim') is True and task.get('claim_boundary',{}).get('product_selectability_claim') is False,
      'catalog':later_progression or e3.get('deliverable',{}).get('current_bounded_transition')=='rb1-successor-r3-explicit-owner-approval' and e3.get('activation',{}).get('accepted_authority_sha256')==EXPECTED_AUTH and e3.get('work_class')=='L',
      'register_rb7':(rb7.get('status')=='closed-owner-scope-excluded-non-termux-unsupported-not-qualified' and rb7.get('evidence',{}).get('support_scope_authority_sha256')==EXPECTED_AUTH and rb7.get('evidence',{}).get('non_termux_android_context_supported') is False) or (later_progression and rb7.get('status')=='closed-appuid-non-termux-runtime-qualified-supported' and rb7.get('evidence',{}).get('app_uid_non_termux_runtime_accepted') is True),
      'register_rb1':(rb1.get('status')=='in-progress-owner-approval-pending' and rb1.get('next_gate',{}).get('contract')=='experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-contract.json') or (owner_approval_progression and rb1.get('status')=='closed-explicit-owner-approved'),
      'registry':all(p in registered for p in [AUTH_REL,'experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-decision-contract.json','experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-contract.json','experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-temporal-verifier-amendment.json']),
      'plan_policy':'unsupported-not-qualified-owner-scope-excluded' in plan and 'Termux execution cannot prove independence from Termux native providers' in plan,
      'accepted_authority':any(x.get('path')==AUTH_REL and x.get('sha256')==EXPECTED_AUTH for x in state.get('accepted_authorities',[])),
      'nonclaims':(sb.get('minimum_supported_android_api_declared') is False and sb.get('publication_authorized') is False) or (later_progression and sb.get('publication_authorized') is False and sb.get('other_non_termux_android_contexts_supported') is False),
    }
    failed=sorted(k for k,v in checks.items() if v is not True)
    return {'schema_version':1,'verifier_kind':'epoch3-rb7-non-termux-runtime-support-scope','pass':not failed,'checks':dict(sorted(checks.items())),'failed_checks':failed,'identity_checks':dict(sorted(identity_checks.items())),'source_authority_checks':dict(sorted(source_checks.items()))}

def main()->int:
    r=verify();print(json.dumps(r,indent=2,sort_keys=True));return 0 if r['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
