#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; LIB=ROOT/'components/upstream-thin/lib'; sys.path.insert(0,str(LIB))
from archive import sha256_file  # noqa:E402

def load(p):
 v=json.loads(p.read_text());
 if not isinstance(v,dict): raise ValueError(p)
 return v

def audit(out:Path):
 r=load(out/'rb3-consumer-compatibility-result.json'); protected=load(out/'protected-state.json'); catalog=load(out/'artifacts/custom-downloads.json')
 checks={
  'result_pass':r.get('pass') is True and not r.get('failed_checks'),
  'all_checks':all(r.get('checks',{}).values()),
  'exact_catalog_key':list(catalog)==['cpython-3.14.6-linux-aarch64-none'],
  'exact_archive_hash':catalog['cpython-3.14.6-linux-aarch64-none']['sha256']=='84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76',
  'local_file_transport':catalog['cpython-3.14.6-linux-aarch64-none']['url'].startswith('file://'),
  'protected_state':protected.get('family_unchanged') is True and protected.get('real_managed_root_unchanged') is True,
  'claims_bounded':r.get('claim_boundary')=={'automatic_network_download':False,'built_in_uv_android_catalog':False,'publication':False,'rb3_closed':False,'selectable':False,'upstream_uv_android_support':False},
 }
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {'schema_version':1,'audit_kind':'epoch3-rb3-consumer-compatibility-independent-audit','pass':not failed,'checks':checks,'failed_checks':failed,'subjects':{'result_sha256':sha256_file(out/'rb3-consumer-compatibility-result.json'),'catalog_sha256':sha256_file(out/'artifacts/custom-downloads.json')}}
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--result-dir',type=Path,required=True); a=p.parse_args(); r=audit(a.result_dir); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r['pass'] else 1)
