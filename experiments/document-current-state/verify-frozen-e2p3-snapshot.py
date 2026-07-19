#!/usr/bin/env python3
"""Verify frozen E2-P3 preservation without replaying historical nested verifier chains."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from typing import Any
AUTHORITY=Path("experiments/document-current-state/document-current-state-authority.json")
SECONDARY_VERIFY=Path("experiments/epoch2-archive-qualification/verify-secondary-real-device-qualification-freeze.py")
EXPECTED_COMMIT="7248859ff5c24990f6cc06ad696a21b2d2793202"
EXPECTED_TREE="3a85792eec9c8e78e4955aa1a227e737d9c4c509"
EXPECTED_E2P3_AUTHORITY="e380198cda8c49cad704483e3edc33c2d745cc65857155b3a7edb1887410f06c"
EXPECTED_E2P3_AUDIT="90784e8896479e4ae0db5e7d26a035ec91250b0028bc23638a470290f0976979"
def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha(p:Path)->str:return sha_bytes(p.read_bytes())
def run(argv:list[str],root:Path,timeout:int=900)->subprocess.CompletedProcess[str]:
 return subprocess.run(argv,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
def verify(root:Path)->dict[str,Any]:
 checks={};errors={}
 def ck(n:str,v:bool,e:str=""):
  checks[n]=bool(v)
  if not v and e:errors[n]=e
 try:a=json.loads((root/AUTHORITY).read_text(encoding="utf-8"));ck("authority_parse",isinstance(a,dict))
 except Exception as exc:a={};ck("authority_parse",False,f"{type(exc).__name__}: {exc}")
 pred=a.get("predecessor",{});ck("predecessor_identity",pred=={"commit":EXPECTED_COMMIT,"tree":EXPECTED_TREE})
 cat=run(["git","cat-file","-e",f"{EXPECTED_COMMIT}^{{commit}}"],root,120);ck("predecessor_commit_present",cat.returncode==0,cat.stderr)
 tree=run(["git","rev-parse",f"{EXPECTED_COMMIT}^{{tree}}"],root,120);ck("predecessor_tree_exact",tree.returncode==0 and tree.stdout.strip()==EXPECTED_TREE,tree.stderr)
 hp=a.get("historical_preservation",{});paths=hp.get("protected_paths",[])
 expected_paths=['docs/evidence/E2P3_SECONDARY_REAL_DEVICE_QUALIFICATION_AUTHORITY_FREEZE.md', 'docs/handoff/2026-07-19-e2p3-secondary-real-device-qualification-authority-freeze.md', 'docs/roadmap/EPOCH2_ROADMAP.md', 'docs/roadmap/EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md', 'experiments/epoch2-archive-qualification/README.md', 'experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json', 'experiments/epoch2-archive-qualification/secondary-real-device-qualification-external-audit.json', 'experiments/epoch2-archive-qualification/test-secondary-real-device-qualification-freeze.py', 'experiments/epoch2-archive-qualification/verify-qualification-contract.py', 'experiments/epoch2-archive-qualification/verify-secondary-real-device-qualification-freeze.py']
 ck("preservation_contract",hp.get("mode")=="exact-frozen-byte-preservation-plus-current-freeze-verifier" and paths==expected_paths and hp.get("secondary_freeze_authority_sha256")==EXPECTED_E2P3_AUTHORITY and hp.get("secondary_freeze_audit_sha256")==EXPECTED_E2P3_AUDIT)
 exists=all((root/p).is_file() for p in expected_paths);ck("protected_paths_exist",exists)
 preserved=True;changed=[]
 if exists and cat.returncode==0:
  for rel in expected_paths:
   old=run(["git","show",f"{EXPECTED_COMMIT}:{rel}"],root,120)
   if old.returncode!=0 or old.stdout.encode()!= (root/rel).read_bytes(): preserved=False;changed.append(rel)
 else: preserved=False
 ck("protected_bytes_match_predecessor",preserved,json.dumps(changed))
 staged=run(["git","diff","--cached","--name-only",EXPECTED_COMMIT,"--",*expected_paths],root,120)
 ck("protected_paths_not_staged",staged.returncode==0 and staged.stdout.strip()=="",staged.stdout+staged.stderr)
 ck("secondary_authority_identity",sha(root/"experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json")==EXPECTED_E2P3_AUTHORITY)
 ck("secondary_audit_identity",sha(root/"experiments/epoch2-archive-qualification/secondary-real-device-qualification-external-audit.json")==EXPECTED_E2P3_AUDIT)
 proc=run([sys.executable,str(root/SECONDARY_VERIFY),"--root",str(root)],root,900)
 try:data=json.loads(proc.stdout)
 except Exception as exc:data={};errors["secondary_verifier_parse"]=f"{type(exc).__name__}: {exc}"
 ck("secondary_freeze_verifier_exact",proc.returncode==0 and data.get("pass") is True and data.get("check_count")==28 and data.get("pass_count")==28 and data.get("failed_checks")==[],json.dumps({"rc":proc.returncode,"failed":data.get("failed_checks")},sort_keys=True))
 ck("no_device_execution_required",True)
 failed=sorted(n for n,v in checks.items() if not v)
 return {"schema_version":1,"verifier_kind":"document-phase2-frozen-e2p3-preservation-v2","pass":not failed,"check_count":len(checks),"pass_count":len(checks)-len(failed),"failed_checks":failed,"checks":checks,"errors":errors,"secondary_verifier":{"raw_rc":proc.returncode if 'proc' in locals() else 125,"check_count":data.get("check_count") if 'data' in locals() else None,"pass_count":data.get("pass_count") if 'data' in locals() else None,"failed_checks":data.get("failed_checks") if 'data' in locals() else None}}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--root",default=".");x=p.parse_args();r=verify(Path(x.root).resolve());print(json.dumps(r,indent=2,sort_keys=True));return 0 if r["pass"] else 1
if __name__=="__main__":sys.exit(main())
