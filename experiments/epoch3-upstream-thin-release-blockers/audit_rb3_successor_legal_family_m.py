#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path):return json.loads(p.read_text())
def inv(root:Path):return [(p.relative_to(root).as_posix(),sha(p),p.stat().st_size) for p in sorted(root.rglob('*')) if p.is_file()]
def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--candidate-dir',type=Path,required=True);p.add_argument('--technical-family-dir',type=Path,required=True);p.add_argument('--predecessor-legal-family-dir',type=Path,required=True);a=p.parse_args();c=a.candidate_dir.resolve();t=a.technical_family_dir.resolve();l=a.predecessor_legal_family_dir.resolve();idx=load(c/'release-index.json');r=idx['release'];checks={}
 checks['release_identity']=r.get('release_id')=='cpython-3.14.6+e3-r3-aarch64-linux-android' and r.get('technical_predecessor_release_id')=='cpython-3.14.6+e3-r2-aarch64-linux-android'
 checks['technical_exact']=all(((c/'lineage/r2'/x.name) if x.name in {'release-index.json','SHA256SUMS'} else (c/x.name)).is_file() and sha((c/'lineage/r2'/x.name) if x.name in {'release-index.json','SHA256SUMS'} else (c/x.name))==sha(x) for x in t.iterdir() if x.is_file()) and len([x for x in t.iterdir() if x.is_file()])==23
 checks['legal_exact']=inv(c/'legal')==inv(l/'legal')
 checks['license_exact']=sha(c/'LICENSE')==sha(l/'LICENSE')
 checks['notice_exact']=sha(c/'legal/THIRD-PARTY-NOTICES.candidate.txt')=='80cf82a6b6957fd830701e2559755d1eecdf01c61cbcb4f8f8843b9735eaf613'
 cm=load(c/'legal/component-license-map.json');pip=load(c/'legal/pip-vendored-component-review.json');tr=load(c/'legal/technical-obligation-review.json');g=load(c/'legal/updated-gap-register.json')
 checks['legal_metrics']=cm.get('mapping_complete') is True and cm.get('review_unit_count')==31 and pip.get('vendor_component_count')==18 and tr.get('review_unit_count')==31 and g.get('blocking_gap_count')==1
 cb=r.get('claim_boundary',{});checks['claims_bounded']=cb.get('successor_legal_family_candidate') is True and cb.get('successor_legal_family_accepted') is False and cb.get('rb1_rebound') is False and cb.get('rb2_rebound') is False and cb.get('predecessor_family_superseded') is False and cb.get('rb3_closed') is False and cb.get('selectable') is False and cb.get('publication') is False
 checks['file_count']=idx.get('file_count')==128 and len([p for p in c.rglob('*') if p.is_file()])==128
 actual=''.join(f'{sha(p)}  {p.relative_to(c).as_posix()}\n' for p in sorted(c.rglob('*')) if p.is_file() and p.relative_to(c).as_posix() not in {'SHA256SUMS','release-index.json'})
 checks['checksums']=(c/'SHA256SUMS').read_text()==actual
 failed=sorted(k for k,v in checks.items() if v is not True);out={'schema_version':1,'audit_kind':'epoch3-rb3-successor-legal-family-independent-audit','pass':not failed,'checks':dict(sorted(checks.items())),'failed_checks':failed,'candidate':{'release_id':r.get('release_id'),'file_count':idx.get('file_count'),'family_fingerprint_sha256':idx.get('family_fingerprint_sha256'),'release_sha256':idx.get('release_sha256')},'claim_boundary':cb};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
