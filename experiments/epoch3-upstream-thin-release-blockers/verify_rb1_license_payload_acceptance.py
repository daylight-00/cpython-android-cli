#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];B=Path('experiments/epoch3-upstream-thin-release-blockers');E=B/'rb1-license-payload-authority-evidence'
EXPECTED={'family':'87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302','full':'20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12','result':'3a02139b93f238b2dbf9ea418fd48112aaea62f2b49655f1d739fbced2820a55'}
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root:Path):
 checks={};errors={}
 def get(name,path):
  try:checks['parse:'+name]=True;return load(root/path)
  except Exception as exc:checks['parse:'+name]=False;errors[name]=f'{type(exc).__name__}: {exc}';return {}
 a=get('accepted',B/'accepted-rb1-license-payload-expansion-r3-return.json');r=get('result',E/'payload-result.json');x=get('expansion',E/'component-expansion-audit.json');i=get('inventory',E/'license-payload-inventory.json');m=get('map',E/'component-license-map-candidate.json');g=get('gaps',E/'updated-gap-register.json');audit=get('audit',E/'independent-audit.json');repro=get('repro',E/'reproducibility.json');summary=get('summary',E/'result-summary.json')
 checks['accepted_action']=a.get('transaction_rc')==0 and a.get('action')=='applied-rb1-license-payloads-acquired-component-expansion-audited-pushed'
 checks['transition']=a.get('repository_transition',{}).get('post_head')=='bdd25ce7560ecbac15e9745bd927ad14efb867d3' and a.get('repository_transition',{}).get('remote_post_head')=='bdd25ce7560ecbac15e9745bd927ad14efb867d3'
 checks['result_archive']=a.get('result_archive',{}).get('sha256')==EXPECTED['result'] and a.get('result_archive',{}).get('size_bytes')==107608
 checks['family']=i.get('family_fingerprint_sha256')==EXPECTED['family'] and i.get('full_artifact',{}).get('identity',{}).get('sha256')==EXPECTED['full'] and i.get('full_artifact',{}).get('identity_preserved') is True
 checks['metrics']=r.get('metrics')=={'baseline_component_count':12,'expanded_component_count':13,'new_component_count':1,'fixed_hash_source_archive_count':5,'source_archives_with_license_evidence':4,'remaining_gap_count':8}
 checks['component_expansion']=x.get('pass') is True and x.get('expanded_components',[])[-1:] == ['hacl-star'] and len(x.get('expanded_components',[]))==13
 checks['source_archives']=len(i.get('source_archives',[]))==5 and sum(int(row.get('license_evidence_count',0)>0) for row in i.get('source_archives',[]))==4
 checks['map']=m.get('component_count')==13 and m.get('mapping_complete') is False
 checks['gap_boundary']=g.get('blocking_gap_count')==8 and {z.get('code') for z in g.get('remaining_gaps',[])}=={'complete-componentization-and-obligation-review-pending','authoritative-license-evidence-not-integrated-into-release-family','project-license-not-in-release-family','xz-5.4.6-exact-license-source-unresolved','sqlite-public-domain-notice-policy-not-frozen','android-system-provider-notice-boundary-not-frozen','hacl-star-new-component-mapping-and-notice-pending','final-notice-set-not-owner-approved'}
 checks['audit']=audit.get('pass') is True and not audit.get('failed_checks')
 checks['reproducibility']=repro.get('pass') is True and all(z.get('identical') for z in repro.get('files',[]))
 checks['summary']=summary.get('transaction_rc')==0 and summary.get('post',{}).get('head')=='bdd25ce7560ecbac15e9745bd927ad14efb867d3'
 docs=[a.get('claim_boundary',{}),r.get('claim_boundary',{}),x.get('claim_boundary',{}),i.get('claim_boundary',{}),m.get('claim_boundary',{}),g.get('claim_boundary',{}),audit.get('claim_boundary',{}),summary.get('claim_boundary',{})]
 checks['claims_bounded']=all(d.get('selectable') is False and d.get('publication') is False and d.get('rb1_closed') is False for d in docs)
 expected=a.get('output_sha256',{});checks['evidence_identity']=all((root/E/n).is_file() and sha(root/E/n)==v for n,v in expected.items())
 failed=sorted(k for k,v in checks.items() if v is not True)
 return {'schema_version':1,'verifier_kind':'epoch3-rb1-license-payload-acceptance','pass':not failed and not errors,'check_count':len(checks),'checks':dict(sorted(checks.items())),'failed_checks':failed,'errors':errors}
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args();out=verify(a.root.resolve());print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
