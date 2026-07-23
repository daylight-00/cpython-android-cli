#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

EXPECTED_BOUNDARY = {
    "successor_legal_family_accepted": True,
    "successor_legal_data_rebinding_started": True,
    "successor_legal_data_rebinding_candidate": True,
    "successor_legal_data_rebinding_accepted": False,
    "rb1_technical_legal_evidence_complete": True,
    "rb2_data_runtime_evidence_complete": True,
    "rb1_rebound": False,
    "rb2_rebound": False,
    "owner_approved": False,
    "predecessor_family_superseded": False,
    "rb3_closed": False,
    "selectable": False,
    "publication": False,
}

def load(path: Path):
    value=json.loads(path.read_text())
    if not isinstance(value,dict): raise ValueError(path)
    return value

def sha(path: Path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument('--result-dir',type=Path,required=True); parser.add_argument('--successor-family-dir',type=Path,required=True); parser.add_argument('--rb2-result-dir',type=Path,required=True); args=parser.parse_args()
    out=args.result_dir.resolve(); family=args.successor_family_dir.resolve(); rb2src=args.rb2_result_dir.resolve(); checks={}; errors=[]
    try:
        result=load(out/'result.json'); fv=load(out/'successor-family-verification.json'); rb1=load(out/'rb1-technical-legal-rebinding.json'); rb2=load(out/'rb2-data-runtime-rebinding.json')
        checks['owner_result_pass']=result.get('pass') is True and not result.get('failed_checks') and all(result.get('checks',{}).values())
        checks['family_exact']=fv.get('pass') is True and fv.get('release',{}).get('release_id')=='cpython-3.14.6+e3-r3-aarch64-linux-android' and fv.get('release',{}).get('file_count')==128 and fv.get('release',{}).get('family_fingerprint_sha256')=='c8d76b6dcb934c12098efb2de985c5ab4799e4b5db5ae1c2b7c0f5a68438a82a'
        checks['rb1_pass']=rb1.get('pass') is True and not rb1.get('failed_checks') and all(rb1.get('checks',{}).values()) and rb1.get('owner_approved') is False and rb1.get('metrics',{}).get('top_level_component_count')==13 and rb1.get('metrics',{}).get('review_unit_count')==31 and rb1.get('metrics',{}).get('remaining_gap_count')==1
        checks['rb2_pass']=rb2.get('pass') is True and not rb2.get('failed_checks') and all(rb2.get('checks',{}).values())
        q=rb2.get('runtime_qualification',{}); checks['runtime_identity']=q.get('pass') is True and q.get('details',{}).get('version')=='3.14.6' and q.get('details',{}).get('soabi')=='cpython-314-aarch64-linux-android' and q.get('details',{}).get('platform')=='android-24-arm64_v8a'
        checks['data_lifecycle']=rb2.get('lifecycle',{}).get('pass') is True and rb2.get('lifecycle',{}).get('final_current_link')=='releases/android-data-ca-2026.6.17-tzdata-2026.3-r1'
        checks['read_only_invariance']=rb2.get('install_root_invariance',{}).get('pass') is True and rb2.get('install_root_invariance',{}).get('before_fingerprint_sha256')==rb2.get('install_root_invariance',{}).get('read_only_after_fingerprint_sha256')==rb2.get('install_root_invariance',{}).get('restored_after_fingerprint_sha256')
        checks['family_invariance']=rb2.get('family_invariance',{}).get('pass') is True and rb2.get('family_invariance',{}).get('before_fingerprint_sha256')==rb2.get('family_invariance',{}).get('after_fingerprint_sha256')
        checks['data_product_identities']=rb2.get('data_products')=={
          'rollback':{'filename':'android-data-ca-2026.5.20-tzdata-2026.2-r1.tar.zst','sha256':'144d96b8f301309fc2269cc73c9f888a37b663afc0ae3e485966834b635d750d','size_bytes':229141},
          'current':{'filename':'android-data-ca-2026.6.17-tzdata-2026.3-r1.tar.zst','sha256':'e7dcdfa84f093d8bbdea50c80f25b9f20bddd8619199610405c4ba344790268d','size_bytes':227318}}
        checks['claim_boundary']=result.get('claim_boundary')==EXPECTED_BOUNDARY
        checks['inputs_still_exact']=sha(family/'release-index.json')=='01d44978aee037f759ba2d4d1effec1925df7e61f7d5a6142275062510f78fc5' and sha(rb2src/'target/artifacts/android-data-ca-2026.6.17-tzdata-2026.3-r1.tar.zst')=='e7dcdfa84f093d8bbdea50c80f25b9f20bddd8619199610405c4ba344790268d'
    except Exception as exc: errors.append(f'{type(exc).__name__}: {exc}')
    failed=sorted(k for k,v in checks.items() if v is not True); audit={'schema_version':1,'audit_kind':'epoch3-rb3-successor-legal-data-rebinding-independent-audit','pass':not failed and not errors,'checks':dict(sorted(checks.items())),'failed_checks':failed,'errors':errors,'claim_boundary':EXPECTED_BOUNDARY}; print(json.dumps(audit,indent=2,sort_keys=True)); return 0 if audit['pass'] else 1
if __name__=='__main__': raise SystemExit(main())
