#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[2]
AUTH_REL = 'experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-authority.json'
EXPECTED_AUTH = '0a38c44e2efcdfa9bda402c4b2aa5db5a51116f7310feb82cca126c8998c8414'
EXPECTED_DECISION = 'b64b66cec9f8bed407f10644e51ea59dde17c1bdc2d4c3b51b005f1b199d40bf'
EXPECTED_RB7 = '0a89f6076bf408f56cf8627b26420ac7791bcfd1ce86cb41633906b9dcfec317'
EXPECTED_TEMPORAL = '606bb992ede5470a53c95dedf7a3b23f34df2033879d54e784c23de7f51ceb85'

def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(root: Path = ROOT) -> dict[str, Any]:
    auth_path = root / AUTH_REL
    if not auth_path.is_file():
        return {'schema_version':1,'verifier_kind':'epoch3-rb6-real-16k-runtime-support-scope','pass':False,'checks':{'required_inputs':False},'failed_checks':['required_inputs'],'missing_inputs':[AUTH_REL]}
    auth=load(auth_path); ids=auth.get('file_identities',{}); sources=auth.get('source_authorities',{})
    required=['docs/current/STATE.json','docs/current/AGENT_TASK.json','docs/agent/TASK_CATALOG.json','docs/documentation/document-registry.json','experiments/epoch3-upstream-thin-release-blockers/blocker-register.json','docs/roadmap/EPOCH3_RELEASE_BLOCKER_RESOLUTION_PLAN.md','experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-temporal-verifier-amendment.json']
    missing=sorted([p for p in ids if not (root/p).is_file()]+[v['path'] for v in sources.values() if not (root/v['path']).is_file()]+[p for p in required if not (root/p).is_file()])
    if missing:
        return {'schema_version':1,'verifier_kind':'epoch3-rb6-real-16k-runtime-support-scope','pass':False,'checks':{'required_inputs':False},'failed_checks':['required_inputs'],'missing_inputs':sorted(set(missing))}
    identity_checks={p:sha(root/p)==h for p,h in ids.items()}
    source_checks={k:sha(root/v['path'])==v['sha256'] for k,v in sources.items()}
    decision=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-decision-contract.json')
    rb6c=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-disposition-contract.json')
    rb7c=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-disposition-contract.json')
    rb7a=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-authority.json')
    rb7t=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-scope-temporal-verifier-amendment.json')
    temporal=load(root/'experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-temporal-verifier-amendment.json')
    platform=load(root/'experiments/epoch2-upstream-thin-platform-portability/platform-portability-authority.json')
    state=load(root/'docs/current/STATE.json'); task=load(root/'docs/current/AGENT_TASK.json'); catalog=load(root/'docs/agent/TASK_CATALOG.json'); register=load(root/'experiments/epoch3-upstream-thin-release-blockers/blocker-register.json'); registry=load(root/'docs/documentation/document-registry.json')
    plan=(root/'docs/roadmap/EPOCH3_RELEASE_BLOCKER_RESOLUTION_PLAN.md').read_text(encoding='utf-8')
    rb6=next((x for x in register.get('blockers',[]) if x.get('id')=='RB-6'),{}); rb7=next((x for x in register.get('blockers',[]) if x.get('id')=='RB-7'),{})
    e3=next((x for x in catalog.get('tasks',[]) if x.get('task_id')=='E3-RELEASE-BLOCKERS'),{})
    b=auth.get('claim_boundary',{}); sb=state.get('claim_boundaries',{}); registered={x['path'] for x in registry.get('documents',[])}
    rb7_progression=state.get('state_revision')==58 and state.get('active_work_package')=='experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-contract.json' and sb.get('rb7_closed') is True and sb.get('non_termux_android_context_supported') is False and sb.get('non_termux_android_context_scope_excluded') is True and task.get('deliverable',{}).get('current_bounded_transition')=='rb1-successor-r3-explicit-owner-approval' and rb7a.get('status')=='closed-owner-scope-excluded-non-termux-unsupported-not-qualified' and rb7t.get('status')=='frozen-verifier-only-rb1-owner-approval-routing-enabled'
    policy_correction_authority='experiments/epoch3-upstream-thin-release-blockers/rb5-rb7-runtime-support-policy-correction-authority.json'; policy_correction_temporal='experiments/epoch3-upstream-thin-release-blockers/rb5-rb7-runtime-support-policy-correction-temporal-verifier-amendment.json'
    policy_correction_progression=state.get('state_revision')==59 and state.get('active_work_package')=='experiments/epoch3-upstream-thin-release-blockers/rb1-successor-r3-owner-approval-contract.json' and sb.get('actual_16k_runtime_supported') is False and sb.get('actual_16k_runtime_scope_excluded') is True and sb.get('api24_runtime_supported') is True and sb.get('app_uid_non_termux_runtime_qualified') is True and task.get('deliverable',{}).get('current_bounded_transition')=='rb1-successor-r3-explicit-owner-approval' and any(x.get('path')==policy_correction_authority and x.get('sha256')==sha(root/policy_correction_authority) for x in task.get('required_authorities',[])) and any(x.get('path')==policy_correction_temporal and x.get('sha256')==sha(root/policy_correction_temporal) for x in task.get('required_authorities',[]))
    checks={
      'authority_identity':sha(auth_path)==EXPECTED_AUTH,
      'authority_kind':auth.get('authority_kind')=='epoch3-rb6-real-16k-runtime-support-scope-disposition',
      'authority_status':auth.get('status')=='closed-owner-scope-excluded-16k-unsupported-not-qualified',
      'file_identities':bool(identity_checks) and all(identity_checks.values()),
      'source_authorities':bool(source_checks) and all(source_checks.values()),
      'decision_identity':sha(root/'experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-decision-contract.json')==EXPECTED_DECISION,
      'decision_guard':decision.get('status')=='owner-decision-ready' and decision.get('owner_observation',{}).get('additional_device_testing_declined') is True and decision.get('owner_observation',{}).get('x86_substitution_accepted') is False and decision.get('runner_guard',{}).get('if_page_size_16384')=='fail-closed-and-require-separate-exact-runtime-qualification' and decision.get('runner_guard',{}).get('if_page_size_unknown')=='fail-closed',
      'contract_allows_scope':rb6c.get('allowed_dispositions',{}).get('owner_scope_exclusion',{}).get('allowed') is True and rb6c.get('allowed_dispositions',{}).get('owner_scope_exclusion',{}).get('runtime_16k_claim_must_remain_false') is True,
      'static_runtime_split':platform.get('claim_boundary',{}).get('static_16k_compatibility') is True and platform.get('claim_boundary',{}).get('runtime_16k_device_qualification') is False and auth.get('support_policy',{}).get('static_16k_compatibility_retained') is True and auth.get('support_policy',{}).get('static_16k_compatibility_is_runtime_support') is False,
      'authority_boundary':b.get('actual_16k_runtime_qualified') is False and b.get('actual_16k_runtime_supported') is False and b.get('actual_16k_runtime_scope_excluded') is True and b.get('rb6_closed') is True and b.get('rb7_closed') is False and b.get('non_termux_android_context_qualified') is False and b.get('selectable') is False and b.get('publication') is False and b.get('artifact_bytes_changed') is False,
      'rb7_contract':sha(root/'experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-disposition-contract.json')==EXPECTED_RB7 and rb7c.get('status')=='authorized-not-started' and rb7c.get('allowed_dispositions',{}).get('owner_scope_exclusion',{}).get('non_termux_runtime_claim_must_remain_false') is True,
      'temporal_amendment':sha(root/'experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-temporal-verifier-amendment.json')==EXPECTED_TEMPORAL and temporal.get('status')=='frozen-verifier-only-rb7-routing-enabled' and temporal.get('accepted_scope_authority',{}).get('sha256')==EXPECTED_AUTH and temporal.get('next_contract',{}).get('sha256')==EXPECTED_RB7,
      'state':(state.get('state_revision')==57 and state.get('active_work_package')=='experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-disposition-contract.json' and 'RB-6-real-16k-runtime-qualification' not in state.get('blockers',[]) and sb.get('rb6_closed') is True and sb.get('actual_16k_runtime_qualified') is False and sb.get('actual_16k_runtime_supported') is False and sb.get('actual_16k_runtime_scope_excluded') is True and sb.get('rb7_closed') is False and sb.get('selectable') is False) or rb7_progression or policy_correction_progression,
      'task':(task.get('state_revision')==57 and task.get('deliverable',{}).get('current_bounded_transition')=='rb7-non-termux-runtime-support-disposition' and task.get('claim_boundary',{}).get('rb6_closed_claim') is True and task.get('claim_boundary',{}).get('actual_16k_runtime_scope_excluded_claim') is True and task.get('claim_boundary',{}).get('non_termux_context_claim') is False and any(x.get('path')=='experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-temporal-verifier-amendment.json' and x.get('sha256')==EXPECTED_TEMPORAL for x in task.get('required_authorities',[]))) or rb7_progression or policy_correction_progression,
      'catalog':(e3.get('deliverable',{}).get('current_bounded_transition')=='rb7-non-termux-runtime-support-disposition' and e3.get('activation',{}).get('accepted_authority_sha256')==EXPECTED_AUTH) or rb7_progression or policy_correction_progression,
      'register_rb6':rb6.get('status')=='closed-owner-scope-excluded-16k-unsupported-not-qualified' and rb6.get('evidence',{}).get('support_scope_authority_sha256')==EXPECTED_AUTH and rb6.get('evidence',{}).get('actual_16k_runtime_supported') is False,
      'register_rb7':(rb7.get('status')=='open-owner-support-disposition' and rb7.get('evidence',{}).get('contract_sha256')==EXPECTED_RB7) or (rb7_progression and rb7.get('status')=='closed-owner-scope-excluded-non-termux-unsupported-not-qualified' and rb7.get('evidence',{}).get('non_termux_android_context_supported') is False) or (policy_correction_progression and rb7.get('status')=='closed-appuid-non-termux-runtime-qualified-supported' and rb7.get('evidence',{}).get('app_uid_non_termux_runtime_accepted') is True),
      'registry':all(p in registered for p in [AUTH_REL,'experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-scope-decision-contract.json','experiments/epoch3-upstream-thin-release-blockers/rb7-non-termux-runtime-support-disposition-contract.json']),
      'plan_policy':'unsupported-not-qualified-owner-scope-excluded' in plan and 'A measured value of 16,384 bytes forbids automatic scope exclusion' in plan,
      'nonclaims':(sb.get('non_termux_android_context_qualified') is False and sb.get('publication_authorized') is False) or (policy_correction_progression and sb.get('actual_16k_runtime_supported') is False and sb.get('publication_authorized') is False),
    }
    failed=sorted(k for k,v in checks.items() if v is not True)
    return {'schema_version':1,'verifier_kind':'epoch3-rb6-real-16k-runtime-support-scope','pass':not failed,'checks':dict(sorted(checks.items())),'failed_checks':failed,'identity_checks':dict(sorted(identity_checks.items())),'source_authority_checks':dict(sorted(source_checks.items()))}

def main()->int:
    result=verify(); print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result['pass'] else 1
if __name__=='__main__': raise SystemExit(main())
