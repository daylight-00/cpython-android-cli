#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
P=Path('experiments/agent-bootstrap/frozen-phase5-snapshot.json')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');x=ap.parse_args();r=Path(x.root).resolve();checks={};errors={}
 def ck(n,v,e=''):checks[n]=bool(v);errors.update({n:e} if not v and e else {})
 try:o=json.loads((r/P).read_text());ck('parse',True)
 except Exception as e:o={};ck('parse',False,str(e))
 ck('identity',o.get('snapshot_kind')=='frozen-document-lifecycle-phase5-predecessor' and o.get('schema_version')==1)
 ck('predecessor',o.get('predecessor')=={'commit':'34695ed741411067302bd7372e3b7024b5fab541','tree':'8537ad0495915491fce158abe1f25851f5149708'})
 a=o.get('phase5_authority',{});ck('authority',a.get('path')=='experiments/document-legacy-authority-decoupling/legacy-authority-decoupling-authority.json' and (r/a.get('path','')).is_file() and sha(r/a['path'])==a.get('sha256'))
 ids=o.get('file_identities',{});ck('count',o.get('file_count')==len(ids) and len(ids)>=19)
 ok=True
 for p,d in ids.items():
  if not (r/p).is_file() or sha(r/p)!=d:ok=False;break
 ck('file_identities',ok)
 cb=o.get('claim_boundary',{});ck('claim_boundary',cb.get('documentation_lifecycle_migration_complete') is True and cb.get('legacy_authority_decoupled') is True and cb.get('bootstrap_transition_changes_phase5_claim') is False)
 ck('phase5_status',json.loads((r/a['path']).read_text()).get('status')=='frozen-pass-legacy-authority-decoupled-document-migration-complete' if a.get('path') else False)
 ck('no_recursive_replay','recursive_verifier' not in o)
 failed=[k for k,v in checks.items() if not v];out={'schema_version':1,'verifier_kind':'frozen-phase5-predecessor-snapshot','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':errors};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())
