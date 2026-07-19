#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
F=Path('experiments/agent-task-completion/frozen-agent-bootstrap-snapshot.json')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');x=ap.parse_args();r=Path(x.root).resolve();checks={};errors={}
 def ck(n,v,e=''):checks[n]=bool(v);errors.update({n:e} if not v and e else {})
 try:o=json.loads((r/F).read_text());a=json.loads((r/o['authority']['path']).read_text());ck('parse',True)
 except Exception as e:o={};a={};ck('parse',False,str(e))
 ck('identity',o.get('snapshot_kind')=='frozen-agent-bootstrap-authority-predecessor' and o.get('schema_version')==1)
 ck('predecessor',o.get('predecessor')=={'commit':'2b5b0b9ef742c36d5a29d4643fb53bf471000415','tree':'e16010a5712c6c098b29887958e1352469436cba'})
 apath=o.get('authority',{}).get('path','');ck('authority_digest',bool(apath) and (r/apath).is_file() and sha(r/apath)==o.get('authority',{}).get('sha256'))
 ck('authority_identity',a.get('authority_kind')=='immutable-agent-bootstrap-and-bundle-session-protocol' and a.get('status')=='frozen-pass-agent-bootstrap-established-handoff-loop-retired')
 ids=o.get('file_identities',{});ck('identity_set',ids==a.get('file_identities'))
 repl=o.get('replacement_snapshots',{});ck('replacement_count',o.get('replacement_count')==4 and len(repl)==4)
 ok=True
 for p,d in ids.items():
  q=r/repl.get(p,p)
  if not q.is_file() or sha(q)!=d:ok=False;break
 ck('resolved_file_identities',ok)
 ck('bootstrap_unchanged',sha(r/'AGENT_BOOTSTRAP.md')=='64c4ab8331e6696788fd6d34e1113177e99963373d81abae0130502b89fc0e11')
 ck('current_files_decoupled',all((r/p).is_file() and sha(r/p)!=ids[p] for p in repl))
 failed=[k for k,v in checks.items() if not v];out={'schema_version':1,'verifier_kind':'frozen-agent-bootstrap-predecessor','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':errors};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())
