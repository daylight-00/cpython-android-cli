#!/usr/bin/env python3
from __future__ import annotations
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];B=ROOT/'experiments/epoch3-upstream-thin-release-blockers';E=B/'rb1-source-provenance-authority-evidence'
def load(n):return json.loads((E/n).read_text())
def main():
 p=load('source-provenance.json');g=load('resolved-gap-register.json');checks={
 'full_immutable':p['family']['full']['sha256']=='20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12',
 'source_exact':p['cpython_source']['identity']=={'filename':'Python-3.14.6.tgz','sha256':'74d0d71d0600e477651a077101d6e62d1e2e69b8e992ba18c993dd643b7ba222','size_bytes':31234628,'url':'https://www.python.org/ftp/python/3.14.6/Python-3.14.6.tgz'},
 'android_py_double_bound':p['android_py']['byte_identical'] is True and p['android_py']['embedded_metadata_sha256']==p['android_py']['nested_package_sha256'],
 'libffi_exact':p['resolved']['libffi']=={'build_revision':3,'release_tag':'libffi-3.4.4-3','version':'3.4.4'},
 'gap_open':g['blocking_gap_count']==11 and g['closure_status']=='incomplete',
 'claims_bounded':p['claim_boundary']['rb1_closed'] is False and p['claim_boundary']['selectable'] is False and p['claim_boundary']['publication'] is False}
 failed=[k for k,v in checks.items() if v is not True];out={'schema_version':1,'audit_kind':'epoch3-rb1-source-provenance-acceptance-audit','pass':not failed,'checks':checks,'failed_checks':failed};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
