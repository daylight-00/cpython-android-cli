#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,sys
from pathlib import Path
P=Path('experiments/document-legacy-authority-decoupling/frozen-phase4-snapshot.json')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default='.');x=a.parse_args();r=Path(x.root).resolve();checks={};err={}
 def ck(n,v,e=''):checks[n]=bool(v);err.update({n:e} if not v and e else {})
 try:s=json.loads((r/P).read_text());ck('parse',True)
 except Exception as e:s={};ck('parse',False,str(e))
 ck('identity',s.get('snapshot_kind')=='frozen-phase4-mixed-document-correction' and s.get('schema_version')==1)
 ck('predecessor',s.get('predecessor')=={'commit':'d201957a11861147bdbe11b6a91bf68fb6714a4d','tree':'1c0c692d7763487ad2ba0d91a7f2bf04b6e0b423'})
 ids=s.get('file_identities',{});ok=bool(ids)
 for p,d in ids.items():
  if not (r/p).is_file() or sha(r/p)!=d:ok=False;break
 ck('file_identities',ok)
 ck('authority_digest',ids.get('experiments/document-mixed-correction/document-mixed-correction-authority.json')==s.get('phase4_authority_sha256')=='45df6e86f0164df8c1d81746af9ca5c44f7921e5a14fc17967213d65a4a43aaf')
 try:o=json.loads((r/'experiments/document-mixed-correction/document-mixed-correction-authority.json').read_text());ck('authority_shape',o.get('status')=='frozen-pass-mixed-document-layers-separated' and o.get('scope',{}).get('tracked_markdown_json_count')==463)
 except Exception as e:ck('authority_shape',False,str(e))
 ck('recorded_results',s.get('recorded_results')=={'render':'18/18','mixed_document_verifier':'27/27','negative_fixtures':'12/12','phase3_snapshot':'10/10','phase4_authority':'22/22'})
 ck('no_recursive_replay',s.get('recursive_current_tree_replay') is False)
 ck('phase4_boundary',o.get('claim_boundary',{}).get('legacy_authority_decoupling') is False and o.get('next_action_class')=='execute-document-lifecycle-phase5-legacy-authority-decoupling')
 failed=[k for k,v in checks.items() if not v];out={'schema_version':1,'verifier_kind':'frozen-phase4-mixed-document-snapshot','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':err};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())
