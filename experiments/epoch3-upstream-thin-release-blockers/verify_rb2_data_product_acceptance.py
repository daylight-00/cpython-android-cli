#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'experiments/epoch3-upstream-thin-release-blockers/rb2-data-product-authority-evidence'
A=ROOT/'experiments/epoch3-upstream-thin-release-blockers/accepted-rb2-data-products-r3-return.json'

def load(p):
    v=json.loads(p.read_text());
    if not isinstance(v,dict): raise ValueError(p)
    return v

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def verify():
    checks={}; errors=[]
    try:
        accepted=load(A); result=load(E/'result.json'); audit=load(E/'independent-audit.json')
        repro=load(E/'reproducibility.json'); life=load(E/'lifecycle.json'); runtime=load(E/'runtime-qualification.json'); frozen=load(E/'frozen-family-invariance.json'); idx=load(E/'result-index.json')
        checks['external_archive_identity']=accepted['external_archive']=={
          'drive_file_id':'1dU6otT2OJufhVBKUuEZVrA23pCnRs4Jp','filename':'cpython-android-cli-e3-rb2-data-products-r3-results.tar.zst','sha256':'6419154d3888ac1e3e5331b11b9692262ca2d90709389e20dfeb848f28507d1c','size_bytes':459042}
        checks['repository_identity']=accepted['repository']['head']=='7a5d003b303206e326f54df42a38cfd72b66a52d' and accepted['repository']['tree']=='f8503f8112d23c22e21bf183a7e0b6e6ccb09e99' and accepted['repository']['remote_head']==accepted['repository']['head']
        checks['owner_result_pass']=result.get('pass') is True and not result.get('failed_checks') and all(result.get('checks',{}).values())
        checks['independent_audit_pass']=audit.get('pass') is True and not audit.get('failed_checks') and all(audit.get('checks',{}).values())
        checks['two_artifacts_exact']=result.get('current',{}).get('artifact')=={'filename':'android-data-ca-2026.6.17-tzdata-2026.3-r1.tar.zst','sha256':'e7dcdfa84f093d8bbdea50c80f25b9f20bddd8619199610405c4ba344790268d','size_bytes':227318} and result.get('rollback',{}).get('artifact')=={'filename':'android-data-ca-2026.5.20-tzdata-2026.2-r1.tar.zst','sha256':'144d96b8f301309fc2269cc73c9f888a37b663afc0ae3e485966834b635d750d','size_bytes':229141}
        checks['reproducibility']=repro.get('pass') is True and repro['current']['two_run_byte_identity'] is True and repro['rollback']['two_run_byte_identity'] is True
        checks['lifecycle']=life.get('pass') is True and life.get('python_install_root_written') is False and life.get('final_current_link')=='releases/android-data-ca-2026.6.17-tzdata-2026.3-r1'
        checks['runtime']=runtime.get('pass') is True and runtime.get('returncode')==0 and runtime.get('details',{}).get('ca_count',0)>0 and set(runtime.get('details',{}).get('zones',{}))=={'UTC','Asia/Seoul','America/New_York'}
        checks['frozen_family']=frozen.get('pass') is True and frozen.get('file_count')==128 and frozen.get('before_fingerprint_sha256')==frozen.get('after_fingerprint_sha256')
        checks['self_index']=sha(E/'result-index.json')==accepted['self_index']['sha256'] and len(idx.get('files',[]))==accepted['self_index']['indexed_file_count']==34
        checks['claims_bounded']=accepted['claim_boundary']=={'owner_approved':False,'publication':False,'rb1_closed':False,'rb2_closed_by_this_return':False,'rb2_evidence_complete':True,'selectable':False}
    except Exception as exc:
        errors.append(f'{type(exc).__name__}: {exc}')
    failed=sorted(k for k,v in checks.items() if v is not True)
    return {'schema_version':1,'verifier_kind':'epoch3-rb2-data-product-acceptance','pass':not failed and not errors,'checks':dict(sorted(checks.items())),'failed_checks':failed,'errors':errors}
if __name__=='__main__':
    r=verify(); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r['pass'] else 1)
