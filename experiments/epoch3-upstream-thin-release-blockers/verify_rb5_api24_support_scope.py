#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/epoch3-upstream-thin-release-blockers'
AUTH_REL = 'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-support-scope-authority.json'
EXPECTED_AUTH = '0c24db1a651924a64d7e4b1f907ed0deaca56413609cf9794449d30040ea2723'
EXPECTED_RB6 = '42642fe5f21c8c82e8a4128316e318927c96246ec0251c00bfa3cb34eb305a0b'

def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(root: Path = ROOT) -> dict[str, Any]:
    auth_path = root / AUTH_REL
    if not auth_path.is_file():
        return {'schema_version': 1, 'verifier_kind': 'epoch3-rb5-api24-support-scope', 'pass': False, 'checks': {'required_inputs': False}, 'failed_checks': ['required_inputs'], 'missing_inputs': [AUTH_REL]}
    auth = load(auth_path)
    ids = auth.get('file_identities', {})
    sources = auth.get('source_authorities', {})
    missing = sorted([p for p in ids if not (root / p).is_file()] + [v['path'] for v in sources.values() if not (root / v['path']).is_file()])
    required = [
        'docs/current/STATE.json', 'docs/current/AGENT_TASK.json',
        'experiments/epoch3-upstream-thin-release-blockers/blocker-register.json',
        'experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-disposition-contract.json',
        'docs/roadmap/EPOCH3_RELEASE_BLOCKER_RESOLUTION_PLAN.md',
    ]
    missing += [p for p in required if not (root / p).is_file()]
    if missing:
        return {'schema_version': 1, 'verifier_kind': 'epoch3-rb5-api24-support-scope', 'pass': False, 'checks': {'required_inputs': False}, 'failed_checks': ['required_inputs'], 'missing_inputs': sorted(set(missing))}
    identity_checks = {p: sha(root / p) == h for p, h in ids.items()}
    source_checks = {k: sha(root / v['path']) == v['sha256'] for k, v in sources.items()}
    inspection = load(root / 'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-runtime-r1-return-inspection.json')
    decision = load(root / 'experiments/epoch3-upstream-thin-release-blockers/rb5-api24-support-scope-decision-contract.json')
    rb6 = load(root / 'experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-disposition-contract.json')
    state = load(root / 'docs/current/STATE.json')
    task = load(root / 'docs/current/AGENT_TASK.json')
    register = load(root / 'experiments/epoch3-upstream-thin-release-blockers/blocker-register.json')
    plan = (root / 'docs/roadmap/EPOCH3_RELEASE_BLOCKER_RESOLUTION_PLAN.md').read_text(encoding='utf-8')
    rb5 = next((x for x in register.get('blockers', []) if x.get('id') == 'RB-5'), {})
    rb6r = next((x for x in register.get('blockers', []) if x.get('id') == 'RB-6'), {})
    b = auth.get('claim_boundary', {})
    sb = state.get('claim_boundaries', {})
    checks = {
        'authority_identity': sha(auth_path) == EXPECTED_AUTH,
        'authority_kind': auth.get('authority_kind') == 'epoch3-rb5-api24-runtime-support-scope-disposition',
        'authority_status': auth.get('status') == 'closed-owner-scope-excluded-api24-unsupported-not-qualified',
        'file_identities': bool(identity_checks) and all(identity_checks.values()),
        'source_authorities': bool(source_checks) and all(source_checks.values()),
        'failed_result': inspection.get('status') == 'verified-fail-closed-exact-target-unavailable' and inspection.get('result_archive', {}).get('sha256') == '4c47f137a72612a5ac44ffb81e6cf21f1fc62c4d67d940a8926889ffdcf56c4d' and inspection.get('target_discovery', {}).get('exact_target_available') is False and inspection.get('transaction', {}).get('rollback_rc') == 0,
        'pre_target_evidence': inspection.get('pre_target_checks', {}).get('release_blocker_tests') == '110/110' and inspection.get('pre_target_checks', {}).get('product_tests') == '73/73' and inspection.get('pre_target_checks', {}).get('extension_inventory_67') is True,
        'owner_decision': decision.get('status') == 'owner-decision-ready' and decision.get('owner_observation', {}).get('additional_device_testing_declined') is True and decision.get('owner_observation', {}).get('x86_does_not_substitute_for_aarch64_runtime_qualification') is True,
        'build_support_split': auth.get('support_policy', {}).get('build_abi_floor_android_api') == 24 and auth.get('support_policy', {}).get('build_sysconfig_platform') == 'android-24-arm64_v8a' and auth.get('support_policy', {}).get('build_identity_retained') is True and auth.get('support_policy', {}).get('api24_runtime_supported') is False and auth.get('support_policy', {}).get('minimum_supported_android_api_declared') is False,
        'authority_boundary': b.get('api24_runtime_attempted') is True and b.get('api24_runtime_qualified') is False and b.get('api24_runtime_supported') is False and b.get('api24_runtime_scope_excluded') is True and b.get('rb5_closed') is True and b.get('rb6_closed') is False and b.get('rb7_closed') is False and b.get('selectable') is False and b.get('publication') is False and b.get('artifact_bytes_changed') is False,
        'rb6_contract': sha(root / 'experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-disposition-contract.json') == EXPECTED_RB6 and rb6.get('status') == 'authorized-not-started' and rb6.get('allowed_dispositions', {}).get('owner_scope_exclusion', {}).get('runtime_16k_claim_must_remain_false') is True,
        'state': state.get('state_revision') == 56 and state.get('active_work_package') == 'experiments/epoch3-upstream-thin-release-blockers/rb6-real-16k-runtime-support-disposition-contract.json' and 'RB-5-api24-runtime-qualification' not in state.get('blockers', []) and sb.get('rb5_closed') is True and sb.get('api24_runtime_supported') is False and sb.get('api24_runtime_scope_excluded') is True and sb.get('minimum_supported_android_api_declared') is False and sb.get('selectable') is False,
        'task': task.get('state_revision') == 56 and task.get('deliverable', {}).get('current_bounded_transition') == 'rb6-real-16k-runtime-support-disposition' and task.get('claim_boundary', {}).get('rb5_closed_claim') is True and task.get('claim_boundary', {}).get('api24_runtime_scope_excluded_claim') is True,
        'register_rb5': rb5.get('status') == 'closed-owner-scope-excluded-api24-unsupported-not-qualified' and rb5.get('evidence', {}).get('support_scope_authority_sha256') == EXPECTED_AUTH and rb5.get('evidence', {}).get('api24_runtime_required_for_selectability') is False,
        'register_rb6': rb6r.get('status') == 'open-owner-support-disposition' and rb6r.get('evidence', {}).get('contract_sha256') == EXPECTED_RB6,
        'plan_policy': 'unsupported-not-qualified-owner-scope-excluded' in plan and 'explicit owner support-scope exclusion' in plan,
        'nonclaims': sb.get('actual_16k_runtime_qualified') is False and sb.get('non_termux_android_context_qualified') is False and sb.get('publication_authorized') is False,
    }
    failed = sorted(k for k, v in checks.items() if v is not True)
    return {'schema_version': 1, 'verifier_kind': 'epoch3-rb5-api24-support-scope', 'pass': not failed, 'checks': dict(sorted(checks.items())), 'failed_checks': failed, 'identity_checks': dict(sorted(identity_checks.items())), 'source_authority_checks': dict(sorted(source_checks.items()))}

def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['pass'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
