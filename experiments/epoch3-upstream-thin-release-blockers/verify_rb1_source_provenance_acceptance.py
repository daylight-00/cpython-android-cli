#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=Path('experiments/epoch3-upstream-thin-release-blockers');EVID=BASE/'rb1-source-provenance-authority-evidence'
EXPECTED={'family':'87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302','full':'20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12','source':'74d0d71d0600e477651a077101d6e62d1e2e69b8e992ba18c993dd643b7ba222','result':'806692ad56bd3d3dcaf087cae6dc61b228ab121e60f0ba9be7a15d6978d652c4'}
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root:Path):
 checks={};errors={}
 def get(name,path):
  try:checks['parse:'+name]=True;return load(root/path)
  except Exception as e:checks['parse:'+name]=False;errors[name]=f'{type(e).__name__}: {e}';return {}
 a=get('accepted',BASE/'accepted-rb1-source-provenance-r1-return.json');r=get('result',EVID/'provenance-result.json');p=get('provenance',EVID/'source-provenance.json');plan=get('plan',EVID/'license-source-plan.json');g=get('gaps',EVID/'resolved-gap-register.json');audit=get('audit',EVID/'independent-audit.json');repro=get('repro',EVID/'reproducibility.json');summary=get('summary',EVID/'result-summary.json');sin=get('source-input',EVID/'source-input.json')
 checks['accepted_action']=a.get('transaction_rc')==0 and a.get('action')=='applied-rb1-source-provenance-resolved-audited-pushed'
 checks['transition']=a.get('repository_transition',{}).get('post_head')=='1b9dea0979ff0082226f368761e5491f4ee43834' and a.get('repository_transition',{}).get('remote_post_head')=='1b9dea0979ff0082226f368761e5491f4ee43834'
 checks['result_archive']=a.get('result_archive',{}).get('sha256')==EXPECTED['result'] and a.get('result_archive',{}).get('size_bytes')==17565
 checks['family']=p.get('family',{}).get('fingerprint_sha256')==EXPECTED['family'] and p.get('family',{}).get('full',{}).get('sha256')==EXPECTED['full']
 checks['source']=p.get('cpython_source',{}).get('identity',{}).get('sha256')==EXPECTED['source'] and sin.get('exact_identity_verified') is True
 pins=p.get('beeware_dependency_releases',{})
 checks['pins']=set(pins)=={'bzip2','libffi','openssl','sqlite','xz','zstd'} and pins.get('libffi',{}).get('release_tag')=='libffi-3.4.4-3'
 checks['gap_transition']=g.get('baseline_gap_count')==12 and g.get('blocking_gap_count')==11 and [x.get('code') for x in g.get('resolved_gaps',[])]==['libffi-version-unresolved']
 checks['outputs']=r.get('pass') is True and len(plan.get('components',[]))==12
 checks['audit']=audit.get('pass') is True and not audit.get('failed_checks')
 checks['reproducibility']=repro.get('pass') is True and all(x.get('identical') for x in repro.get('files',[]))
 checks['summary']=summary.get('transaction_rc')==0 and summary.get('failure_reason')=='none'
 docs=[a.get('claim_boundary',{}),r.get('claim_boundary',{}),p.get('claim_boundary',{}),plan.get('claim_boundary',{}),g.get('claim_boundary',{}),audit.get('claim_boundary',{}),summary.get('claim_boundary',{})]
 checks['claims_bounded']=all(d.get('selectable') is False and d.get('publication') is False and d.get('component_license_mapping_complete') is False for d in docs) and all(d.get('rb1_closed') is False for d in docs if 'rb1_closed' in d)
 expected=a.get('output_sha256',{});checks['evidence_identity']=all((root/EVID/n).is_file() and sha(root/EVID/n)==v for n,v in expected.items())
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {'schema_version':1,'verifier_kind':'epoch3-rb1-source-provenance-acceptance','pass':not failed and not errors,'check_count':len(checks),'checks':dict(sorted(checks.items())),'failed_checks':failed,'errors':errors}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=ROOT);a=ap.parse_args();out=verify(a.root.resolve());print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
