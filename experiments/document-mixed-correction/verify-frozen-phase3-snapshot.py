#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,sys
from pathlib import Path
P=Path('experiments/document-mixed-correction/frozen-phase3-snapshot.json')
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default='.');x=a.parse_args();r=Path(x.root).resolve();checks={};err={}
 def ck(n,v,e=''):checks[n]=bool(v);err.update({n:e} if not v and e else {})
 try:s=json.loads((r/P).read_text());ck('parse',True)
 except Exception as e:s={};ck('parse',False,str(e))
 ck('identity',s.get('snapshot_kind')=='frozen-phase3-document-navigation' and s.get('schema_version')==1)
 ck('predecessor',s.get('predecessor')=={'commit':'38889c8ec1daf26ac029a230bb2281296ef92680','tree':'64a5d860c92235a5a857cc97f473b436fb2db468'})
 ids=s.get('file_identities',{});ok=bool(ids)
 for p,d in ids.items():
  if not (r/p).is_file() or sha(r/p)!=d:ok=False;break
 ck('file_identities',ok)
 ck('authority_digest',ids.get('experiments/document-navigation/document-navigation-authority.json')==s.get('phase3_authority_sha256')=='28faa2ba26dbded39ecd581a849288d87f030a25b81a1639796f863db86b1f23')
 try:a=json.loads((r/'experiments/document-navigation/document-navigation-authority.json').read_text());ck('authority_shape',a.get('status')=='frozen-pass-complete-generated-navigation-established' and a.get('scope',{}).get('tracked_markdown_json_count')==447 and a.get('scope',{}).get('navigation_target_count')==13)
 except Exception as e:ck('authority_shape',False,str(e))
 rec=s.get('recorded_results',{});ck('recorded_results',rec=={'render':'17/17','navigation':'39/39','negative_fixtures':'12/12','phase3_authority':'19/19','phase2_snapshot':'9/9','phase2_authority':'19/19','phase1_authority':'18/18'})
 ck('no_recursive_replay',s.get('recursive_current_tree_replay') is False)
 ck('phase3_claim_boundary',a.get('claim_boundary',{}).get('mixed_document_normalization') is False and a.get('claim_boundary',{}).get('product_or_experiment_claim_change') is False)
 ck('phase3_next_boundary',a.get('next_action_class')=='execute-document-lifecycle-phase4-mixed-document-correction')
 failed=[k for k,v in checks.items() if not v];o={'schema_version':1,'verifier_kind':'frozen-phase3-document-navigation-snapshot','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':err};print(json.dumps(o,indent=2,sort_keys=True));return 0 if o['pass'] else 1
if __name__=='__main__':sys.exit(main())
