#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=ROOT/'experiments/epoch3-upstream-thin-release-blockers/rb1-legal-integration-authority-evidence'
def load(n):return json.loads((E/n).read_text())
def main():
 v=load('final-candidate-verification.json');a=load('independent-audit.json');m=load('integrated-family-file-manifest.json');g=load('legal/updated-gap-register.json');i=load('legal/legal-integration.json');checks={'candidate_pass':v.get('pass') is True,'producer_audit_pass':a.get('pass') is True,'manifest_exact':m.get('file_count')==128 and len(m.get('files',[]))==128,'single_owner_gap':g.get('blocking_gap_count')==1,'integration_complete':i.get('technical_review',{}).get('review_units')==31 and i.get('remaining_gap_count')==1,'approval_open':v.get('claim_boundary',{}).get('owner_approved') is False,'rb1_open':v.get('claim_boundary',{}).get('rb1_closed') is False,'selection_closed':v.get('claim_boundary',{}).get('selectable') is False and v.get('claim_boundary',{}).get('publication') is False}
 f=sorted(k for k,vv in checks.items() if vv is not True);o={'schema_version':1,'audit_kind':'epoch3-rb1-legal-integration-acceptance-independent-audit','pass':not f,'checks':dict(sorted(checks.items())),'failed_checks':f};print(json.dumps(o,indent=2,sort_keys=True));return 0 if o['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
