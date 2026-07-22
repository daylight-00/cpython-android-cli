#!/usr/bin/env python3
from __future__ import annotations
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
VER=ROOT/"experiments/epoch3-upstream-thin-release-blockers/verify_rb1_baseline_acceptance.py"
def run(root):return subprocess.run([sys.executable,str(VER),"--root",str(root)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def main():
 checks={}
 p=run(ROOT);checks["success"]=p.returncode==0 and json.loads(p.stdout).get("pass") is True
 with tempfile.TemporaryDirectory(prefix="rb1-accept-") as td:
  r=Path(td)/"repo";shutil.copytree(ROOT,r,symlinks=True,ignore=shutil.ignore_patterns(".git","__pycache__"))
  target=r/"experiments/epoch3-upstream-thin-release-blockers/rb1-baseline-authority-evidence/component-census.json";target.unlink()
  q=run(r);checks["missing_evidence_negative"]=q.returncode!=0 and json.loads(q.stdout).get("pass") is False
 with tempfile.TemporaryDirectory(prefix="rb1-accept-") as td:
  r=Path(td)/"repo";shutil.copytree(ROOT,r,symlinks=True,ignore=shutil.ignore_patterns(".git","__pycache__"))
  target=r/"experiments/epoch3-upstream-thin-release-blockers/accepted-rb1-baseline-r1-return.json";d=json.loads(target.read_text());d["claim_boundary"]["selectable"]=True;target.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
  q=run(r);checks["overclaim_negative"]=q.returncode!=0 and json.loads(q.stdout).get("pass") is False
 failed=sorted(k for k,v in checks.items() if v is not True);out={"pass":not failed,"checks":checks,"failed_checks":failed};print(json.dumps(out,indent=2,sort_keys=True));return 0 if out["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
