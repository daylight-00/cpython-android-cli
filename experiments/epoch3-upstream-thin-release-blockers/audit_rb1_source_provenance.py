#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args();o=a.output_dir.resolve();errors={};docs={}
 for n in ['provenance-result.json','source-provenance.json','license-source-plan.json','resolved-gap-register.json']:
  try:docs[n]=json.loads((o/n).read_text())
  except Exception as e:errors[n]=f'{type(e).__name__}: {e}'
 r=docs.get('provenance-result.json',{});prov=docs.get('source-provenance.json',{});plan=docs.get('license-source-plan.json',{});gaps=docs.get('resolved-gap-register.json',{})
 pins=prov.get('beeware_dependency_releases',{})
 evidence=prov.get('cpython_source',{}).get('license_evidence',[])
 checks={
  'result_pass':r.get('pass') is True,
  'family_identity':prov.get('family',{}).get('fingerprint_sha256')=='87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302',
  'full_identity':prov.get('family',{}).get('full',{}).get('sha256')=='20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12',
  'android_package_identity':prov.get('official_android_package',{}).get('sha256')=='38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5',
  'android_py_double_binding':prov.get('android_py',{}).get('byte_identical') is True and prov.get('android_py',{}).get('embedded_metadata_sha256')==prov.get('android_py',{}).get('nested_package_sha256'),
  'dependency_pin_set':set(pins)=={'bzip2','libffi','openssl','sqlite','xz','zstd'},
  'libffi_resolved':pins.get('libffi',{}).get('version')=='3.4.4' and pins.get('libffi',{}).get('build_revision')==3 and pins.get('libffi',{}).get('release_tag')=='libffi-3.4.4-3',
  'cpython_source_identity':prov.get('cpython_source',{}).get('identity',{}).get('sha256')=='74d0d71d0600e477651a077101d6e62d1e2e69b8e992ba18c993dd643b7ba222',
  'source_evidence_present':bool(evidence) and all((o/'source-evidence'/x.get('evidence_path','')).is_file() and sha(o/'source-evidence'/x['evidence_path'])==x.get('sha256') for x in evidence),
  'plan_component_count':len(plan.get('components',[]))==12,
  'gap_reduction_exact':gaps.get('baseline_gap_count')==12 and gaps.get('blocking_gap_count')==11 and [x.get('code') for x in gaps.get('resolved_gaps',[])]==['libffi-version-unresolved'],
  'claims_bounded':all(d.get('selectable') is False and d.get('publication') is False and d.get('rb1_closed') is False and d.get('component_license_mapping_complete') is False for d in [r.get('claim_boundary',{}),prov.get('claim_boundary',{}),plan.get('claim_boundary',{}),gaps.get('claim_boundary',{})]),
 }
 failed=sorted(k for k,v in checks.items() if v is not True)
 out={'schema_version':1,'audit_kind':'epoch3-rb1-source-provenance-independent-audit','pass':not failed and not errors,'checks':dict(sorted(checks.items())),'failed_checks':failed,'errors':errors,'input_sha256':{n:sha(o/n) for n in docs},'claim_boundary':{'source_provenance_resolved':not failed and not errors,'component_license_mapping_complete':False,'rb1_closed':False,'selectable':False,'publication':False}}
 print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
