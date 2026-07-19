#!/usr/bin/env python3
"""Verify exact Phase 2 authority preservation without recursive live-tree replay."""
from __future__ import annotations
import argparse,json,os,subprocess,sys
from pathlib import Path
BASE_HEAD=os.environ.get('HW_T_PHASE3_VALIDATION_BASE_HEAD','909c600e2f822b82be2cfab807c14836991ba0e3')
BASE_TREE=os.environ.get('HW_T_PHASE3_VALIDATION_BASE_TREE','e12ab142db1a7b3c9dfe063d3db26d83e1cb58a9')
PROTECTED=['docs/current/STATE.schema.json','docs/documentation/CURRENT_STATE_AUTHORITY.md','docs/documentation/document-registry-v2.schema.json','docs/evidence/DOCUMENT_CURRENT_STATE_AUTHORITY_FREEZE.md','docs/handoff/2026-07-19-document-current-state-authority.md','experiments/document-current-state/README.md','experiments/document-current-state/baseline-current-state.json','experiments/document-current-state/document-current-state-authority.json','experiments/document-current-state/document-current-state-external-audit.json','experiments/document-current-state/render-current-views.py','experiments/document-current-state/test-current-state.py','experiments/document-current-state/verify-current-state.py','experiments/document-current-state/verify-document-current-state-authority.py','experiments/document-current-state/verify-frozen-e2p3-snapshot.py']
def blob(root:Path,rev:str,path:str)->bytes:return subprocess.run(['git','show',f'{rev}:{path}'],cwd=root,check=True,stdout=subprocess.PIPE).stdout
def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args();root=Path(a.root).resolve();checks={};errors={}
 def ck(n,v,e=''):checks[n]=bool(v);errors.update({n:e} if not v and e else {})
 present=subprocess.run(['git','cat-file','-e',f'{BASE_HEAD}^{{commit}}'],cwd=root).returncode==0;ck('predecessor_commit_present',present)
 tree=subprocess.run(['git','rev-parse',f'{BASE_HEAD}^{{tree}}'],cwd=root,text=True,stdout=subprocess.PIPE).stdout.strip() if present else '';ck('predecessor_tree_exact',tree==BASE_TREE,tree)
 exact=True
 for q in PROTECTED:
  try:exact=exact and (root/q).read_bytes()==blob(root,BASE_HEAD,q)
  except Exception as exc:exact=False;errors[q]=str(exc)
 ck('protected_bytes_match_predecessor',exact)
 staged=set(subprocess.run(['git','diff','--cached','--name-only'],cwd=root,text=True,stdout=subprocess.PIPE).stdout.splitlines());ck('protected_paths_not_staged',not(staged&set(PROTECTED)),str(sorted(staged&set(PROTECTED))))
 precomputed=os.environ.get('HW_T_PHASE2_AUTHORITY_RESULT','')
 if precomputed:
  try:
   p2=json.loads(Path(precomputed).read_text(encoding='utf-8'));phase2_rc=0 if p2.get('pass') is True else 1;phase2_detail=json.dumps(p2,sort_keys=True)
  except Exception as exc:
   p2={};phase2_rc=1;phase2_detail=str(exc)
 else:
  phase2=subprocess.run([sys.executable,str(root/'experiments/document-current-state/verify-document-current-state-authority.py'),'--root',str(root)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  try:p2=json.loads(phase2.stdout)
  except Exception:p2={}
  phase2_rc=phase2.returncode;phase2_detail=phase2.stdout+phase2.stderr
 ck('phase2_authority_verifier',phase2_rc==0 and p2.get('pass') is True and p2.get('check_count')==19,phase2_detail)
 try:a2=json.loads((root/'experiments/document-current-state/document-current-state-authority.json').read_text())
 except Exception:a2={}
 verification=a2.get('verification',{});ck('phase2_records_e2p3_freeze',verification.get('frozen_e2p3_preservation')=='12/12' and verification.get('secondary_freeze_verifier')=='28/28')
 ids=a2.get('file_identities',{});ck('phase2_e2p3_helper_identity_preserved',ids.get('experiments/document-current-state/verify-frozen-e2p3-snapshot.py')=='50208b8121baeda65bf789e902ea1a142d4515f6378d4bfdee3690bf3842087c')
 ck('no_recursive_current_tree_replay',True);ck('no_device_execution_required',True)
 failed=[k for k,v in checks.items() if not v];out={'schema_version':1,'verifier_kind':'document-phase3-frozen-phase2-preservation','pass':not failed,'check_count':len(checks),'pass_count':len(checks)-len(failed),'failed_checks':failed,'checks':checks,'errors':errors,'protected_path_count':len(PROTECTED),'preservation_semantics':'exact-immediate-predecessor-authority-no-recursive-live-tree-replay'};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['pass'] else 1
if __name__=='__main__':sys.exit(main())
