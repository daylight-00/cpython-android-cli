#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--review-dir',type=Path,required=True);a=p.parse_args();d=a.review_dir;idx=json.loads((d/'review-index.json').read_text());b=json.loads((d/'approval-binding.json').read_text());t=json.loads((d/'owner-approval-template.json').read_text());checks={'notice_bound':h(d/'THIRD-PARTY-NOTICES.review.txt')==b['third_party_notices_sha256'],'map_bound':h(d/'component-license-map.json')==b['component_license_map_sha256'],'review_bound':h(d/'technical-obligation-review.json')==b['technical_obligation_review_sha256'],'pip_bound':h(d/'pip-vendored-component-review.json')==b['pip_vendored_component_review_sha256'],'license_bound':h(d/'LICENSE')==b['project_license_sha256'],'template_pending':t.get('approved') is False and t.get('owner_id')=='','approval_not_inferred':idx.get('approval_status')=='pending'};f=sorted(k for k,v in checks.items() if v is not True);o={'schema_version':1,'audit_kind':'epoch3-rb1-owner-approval-review-independent-audit','pass':not f,'checks':checks,'failed_checks':f,'claim_boundary':{'owner_approved':False,'rb1_closed':False,'selectable':False,'publication':False}};print(json.dumps(o,indent=2,sort_keys=True));return 0 if o['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
