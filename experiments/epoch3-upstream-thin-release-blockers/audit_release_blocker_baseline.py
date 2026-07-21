#!/usr/bin/env python3
"""Independent bounded audit of the RB-1 baseline census output."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_CLASSES=["cpython","project-launcher","pip","openssl","sqlite","bzip2","xz-liblzma","zstd","expat","libmpdec","libffi","android-system-providers"]
EXPECTED_FINGERPRINT="87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302"
EXPECTED_FULL_SHA="20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12"


def load(path: Path) -> dict[str,Any]:
    value=json.loads(path.read_text())
    if not isinstance(value,dict): raise ValueError(path)
    return value


def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def audit(output_dir: Path) -> dict[str,Any]:
    census=load(output_dir/'component-census.json')
    gaps=load(output_dir/'license-gap-register.json')
    result=load(output_dir/'baseline-result.json')
    classes=[row.get('component_class') for row in census.get('components',[])]
    checks={
      'result_pass':result.get('pass') is True,
      'family_identity':census.get('family',{}).get('fingerprint_sha256')==EXPECTED_FINGERPRINT,
      'full_identity':census.get('subject',{}).get('sha256')==EXPECTED_FULL_SHA,
      'component_classes_exact':classes==EXPECTED_CLASSES,
      'component_classes_unique':len(classes)==len(set(classes))==12,
      'mapping_explicitly_incomplete':census.get('summary',{}).get('component_to_license_mapping_complete') is False,
      'claim_boundaries_false':all(census.get('claim_boundary',{}).get(k) is False for k in ('component_license_mapping_complete','selectable','publication')),
      'artifact_not_mutated':census.get('claim_boundary',{}).get('artifact_bytes_mutated') is False and result.get('full_artifact_identity_preserved') is True,
      'gaps_nonempty':gaps.get('blocking_gap_count',0)>0 and gaps.get('closure_status')=='incomplete',
      'libffi_gaps_present':{'libffi-version-unresolved','libffi-license-evidence-not-packaged'} <= {r.get('code') for r in gaps.get('gaps',[]) if r.get('component_class')=='libffi'},
      'project_license_gap_present':'project-license-not-in-release-family' in {r.get('code') for r in gaps.get('gaps',[])},
      'no_complete_overclaim':not any(r.get('license_mapping',{}).get('status')=='complete' for r in census.get('components',[])),
    }
    failed=[k for k,v in checks.items() if not v]
    return {
      'schema_version':1,'audit_kind':'epoch3-release-blocker-component-license-baseline-independent-audit',
      'pass':not failed,'checks':checks,'failed_checks':failed,
      'input_sha256':{
        'component-census.json':digest(output_dir/'component-census.json'),
        'license-gap-register.json':digest(output_dir/'license-gap-register.json'),
        'baseline-result.json':digest(output_dir/'baseline-result.json'),
      },
      'claim_boundary':{'rb1_closed':False,'component_license_mapping_complete':False,'selectable':False,'publication':False},
    }


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('--output-dir',required=True,type=Path); p.add_argument('--write',type=Path)
    a=p.parse_args(); out=audit(a.output_dir.resolve())
    if a.write:
        a.write.parent.mkdir(parents=True,exist_ok=True); a.write.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True)); return 0 if out['pass'] else 1


if __name__=='__main__': raise SystemExit(main())
