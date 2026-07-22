#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=Path('experiments/epoch3-upstream-thin-release-blockers');E=REL/'rb1-legal-integration-authority-evidence'
EXPECTED={'post':'2a6ab3d100960d9a07be4bb0a5a23845601d0f88','result':'5018f4e337f4ee0086e5017db0010c5ef2ae41634f97edd4117b0bccdb8a6375','family':'b71a0123d9d135b3ab378b59d2227ec312c95b49dc15c6ec40fce91a916f348d','release':'b2d93c0f13b60e7404a948a54abfa4c7adffdb318194b291a6ec6b668b49c1fb','notice':'80cf82a6b6957fd830701e2559755d1eecdf01c61cbcb4f8f8843b9735eaf613'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def load(p):
 v=json.loads(p.read_text());assert isinstance(v,dict);return v
def verify(root:Path):
 errors=[];checks={}
 def get(r):
  try:return load(root/r)
  except Exception as e:errors.append(f'{r}:{type(e).__name__}:{e}');return {}
 a=get(REL/'accepted-rb1-legal-integration-r1-return.json');auth=get(REL/'rb1-legal-integration-authority.json');s=get(E/'result-summary.json');v=get(E/'final-candidate-verification.json');au=get(E/'independent-audit.json');rp=get(E/'reproducibility.json');m=get(E/'integrated-family-file-manifest.json');idx=get(E/'release-index.json');g=get(E/'legal/updated-gap-register.json')
 checks['accepted_action']=a.get('transaction_rc')==0 and a.get('action')=='applied-rb1-technical-obligation-review-legal-family-integrated-audited-pushed'
 checks['transition']=a.get('repository_transition',{}).get('post_head')==EXPECTED['post'] and a.get('repository_transition',{}).get('remote_post_head')==EXPECTED['post']
 checks['result_archive']=a.get('result_archive',{}).get('sha256')==EXPECTED['result'] and a.get('result_archive',{}).get('size_bytes')==87683594
 checks['family_identity']=a.get('family',{}).get('file_count')==128 and a.get('family',{}).get('family_fingerprint_sha256')==EXPECTED['family'] and a.get('family',{}).get('release_sha256')==EXPECTED['release']
 checks['manifest']=m.get('file_count')==128 and len(m.get('files',[]))==128 and m.get('family_fingerprint_sha256')==EXPECTED['family']
 checks['candidate_verification']=v.get('pass') is True and not v.get('failed_checks') and v.get('file_count')==128 and v.get('family_fingerprint_sha256')==EXPECTED['family']
 checks['audit']=au.get('pass') is True and not au.get('failed_checks') and au.get('candidate',{}).get('release_sha256')==EXPECTED['release']
 checks['reproducibility']=rp.get('pass') is True and rp.get('file_count')==128 and all(x.get('identical') is True for x in rp.get('files',[]))
 checks['single_gap']=g.get('blocking_gap_count')==1 and [x.get('code') for x in g.get('remaining_gaps',[])]==['final-notice-set-not-owner-approved']
 checks['critical_hashes']=sha(root/E/'release-index.json')=='887c7142a83082143df0073bcffacf70ec7fe81f23d146309bbf6970e987c115' and sha(root/E/'legal/THIRD-PARTY-NOTICES.candidate.txt')==EXPECTED['notice']
 checks['claims_bounded']=all(x.get('owner_approved') is False and x.get('rb1_closed') is False and x.get('selectable') is False and x.get('publication') is False for x in [a.get('claim_boundary',{}),s.get('claim_boundary',{}),v.get('claim_boundary',{}),au.get('claim_boundary',{})])
 ids=auth.get('file_identities',{});checks['authority_identities']=bool(ids) and all((root/p).is_file() and sha(root/p)==h for p,h in ids.items())
 checks['authority_boundary']=auth.get('frozen_family',{}).get('remaining_gap_count')==1 and auth.get('successor_gate',{}).get('implicit_approval_forbidden') is True
 failed=sorted(k for k,vv in checks.items() if vv is not True);return {'schema_version':1,'verifier_kind':'epoch3-rb1-legal-integration-acceptance','pass':not failed and not errors,'check_count':len(checks),'checks':dict(sorted(checks.items())),'failed_checks':failed,'errors':errors}
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args();o=verify(a.root.resolve());print(json.dumps(o,indent=2,sort_keys=True));return 0 if o['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
