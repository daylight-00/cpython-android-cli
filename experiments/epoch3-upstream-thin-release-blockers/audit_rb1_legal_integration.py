#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate-dir',type=Path,required=True);p.add_argument('--predecessor-dir',type=Path,required=True);a=p.parse_args();c=a.candidate_dir.resolve();old=a.predecessor_dir.resolve();idx=load(c/'release-index.json');r=idx['release'];g=load(c/'legal/updated-gap-register.json');m=load(c/'legal/component-license-map.json');v=load(c/'legal/pip-vendored-component-review.json');checks={
 'artifact_archives_exact':all((c/x.name).is_file() and sha(c/x.name)==sha(x) for x in old.iterdir() if x.is_file() and (x.name.endswith('.tar.gz') or x.name.endswith('.tar.zst'))),
 'sidecars_exact':all((c/x.name).is_file() and sha(c/x.name)==sha(x) for x in old.iterdir() if x.is_file() and x.name.endswith('.json') and x.name!='release-index.json'),
 'predecessor_envelope_preserved':sha(c/'lineage/r1/release-index.json')==sha(old/'release-index.json') and sha(c/'lineage/r1/SHA256SUMS')==sha(old/'SHA256SUMS'),
 'review_units':m.get('review_unit_count')==31 and v.get('vendor_component_count')==18,
 'single_gap':g.get('blocking_gap_count')==1,
 'project_license':(c/'LICENSE').is_file(),
 'owner_pending':r.get('claim_boundary',{}).get('owner_approved') is False,
 'rb1_open':r.get('claim_boundary',{}).get('rb1_closed') is False,
 'selection_closed':r.get('claim_boundary',{}).get('selectable') is False and r.get('claim_boundary',{}).get('publication') is False}
 failed=sorted(k for k,v in checks.items() if v is not True);out={'schema_version':1,'audit_kind':'epoch3-rb1-legal-integration-independent-audit','pass':not failed,'checks':dict(sorted(checks.items())),'failed_checks':failed,'candidate':{'release_id':r.get('release_id'),'family_fingerprint_sha256':idx.get('family_fingerprint_sha256'),'release_sha256':idx.get('release_sha256')},'claim_boundary':r.get('claim_boundary',{})};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
