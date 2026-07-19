#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,sys
from pathlib import Path
BASE=Path('docs/documentation/legacy-live-binding-baseline.json');MAP=Path('docs/documentation/legacy-authority-decoupling-map.json')
FORBIDDEN={'README.md','docs/CURRENT_CONTEXT.md','docs/INDEX.md','docs/SESSION_ONBOARDING.md','docs/current/STATE.json','docs/documentation/document-registry.json','docs/roadmap/EPOCH2_ROADMAP.md','docs/handoff/README.md'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def all_bindings(root):
 out=[]
 for p in sorted(root.rglob('*.json')):
  if '.git' in p.parts:continue
  try:o=load(p)
  except Exception:continue
  fi=o.get('file_identities') if isinstance(o,dict) else None
  if isinstance(fi,dict):
   for t,d in fi.items():out.append((p.relative_to(root).as_posix(),t,d))
 return out
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default='.');x=a.parse_args();r=Path(x.root).resolve();checks={};err={}
 def ck(n,v,e=''):checks[n]=bool(v);err.update({n:e} if not v and e else {})
 try:b=load(r/BASE);m=load(r/MAP);ck('parse',True)
 except Exception as e:b={};m={};ck('parse',False,str(e))
 ck('baseline_identity',b.get('baseline_kind')=='legacy-live-document-file-identity-bindings' and b.get('expected_binding_count')==24)
 ck('map_identity',m.get('map_kind')=='legacy-live-binding-decoupling-map' and m.get('binding_count')==m.get('unique_snapshot_count')==24)
 bk={(z.get('authority_path'),z.get('target_path'),z.get('recorded_sha256')) for z in b.get('bindings',[]) if isinstance(z,dict)}
 me=m.get('bindings',[]);mk={(z.get('authority_path'),z.get('target_path'),z.get('recorded_sha256')) for z in me if isinstance(z,dict)}
 ck('binding_key_coverage',len(bk)==24 and mk==bk,f'missing={sorted(bk-mk)} extra={sorted(mk-bk)}')
 snaps=[z.get('snapshot_path') for z in me];ck('snapshot_paths_unique',len(snaps)==len(set(snaps))==24)
 ck('snapshot_paths_bounded',all(isinstance(p,str) and p.startswith('docs/history/legacy-authority-bindings/') and p not in FORBIDDEN for p in snaps))
 snapok=True
 for z in me:
  p=r/z.get('snapshot_path','');d=z.get('recorded_sha256');
  if not p.is_file() or d!=z.get('snapshot_sha256') or sha(p)!=d or p.stat().st_size!=z.get('snapshot_size'):snapok=False;break
 ck('snapshot_bytes',snapok)
 authok=True
 for z in me:
  p=r/z.get('authority_path','')
  try:o=load(p);fi=o.get(z.get('location'),{})
  except Exception:authok=False;break
  if not isinstance(fi,dict) or fi.get(z.get('target_path'))!=z.get('recorded_sha256') or sha(p)!=z.get('authority_file_sha256'):authok=False;break
 ck('original_authority_bindings',authok)
 observed={(a,t,d) for a,t,d in all_bindings(r) if t in FORBIDDEN}
 expected={(z.get('authority_path'),z.get('target_path'),z.get('recorded_sha256')) for z in b.get('bindings',[])}
 ck('no_new_live_bindings',observed==expected,f'missing={sorted(expected-observed)} extra={sorted(observed-expected)}')
 ck('source_metadata',all(len(str(z.get(k,'')))>0 for z in me for k in ('source_commit','source_tree','source_blob_sha1','source_commit_subject')))
 ck('historical_authorities_unmodified',all(z.get('resolution_status')=='resolved-byte-exact' for z in me))
 sem=m.get('resolution_semantics',{});ck('semantic_decoupling',sem.get('live_path_semantics')=='live paths are not constrained to historical recorded digests' and sem.get('historical_authority_bytes_rewritten') is False)
 failed=[k for k,v in checks.items() if not v];o={'schema_version':1,'verifier_kind':'legacy-binding-resolution-phase5','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':err,'metrics':{'binding_count':len(bk),'snapshot_count':len(snaps),'observed_forbidden_binding_count':len(observed)}};print(json.dumps(o,indent=2,sort_keys=True));return 0 if o['pass'] else 1
if __name__=='__main__':sys.exit(main())
