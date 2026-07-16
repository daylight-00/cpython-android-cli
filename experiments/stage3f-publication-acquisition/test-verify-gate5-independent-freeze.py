#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
SCRIPT=Path(__file__).resolve().with_name("verify-gate5-independent-freeze.py")
SOURCE=Path(__file__).resolve().parents[2]
def load():
 spec=importlib.util.spec_from_file_location("g5",SCRIPT);assert spec and spec.loader
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main()->int:
 m=load()
 with tempfile.TemporaryDirectory() as td:
  root=Path(td)/"repo";root.mkdir()
  for rel in m.REQUIRED:
   src=SOURCE/rel;dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  subprocess.run(["git","init","-q","-b",m.BRANCH],cwd=root,check=True)
  subprocess.run(["git","config","user.name","fixture"],cwd=root,check=True);subprocess.run(["git","config","user.email","fixture@example.invalid"],cwd=root,check=True)
  subprocess.run(["git","add","-A"],cwd=root,check=True);subprocess.run(["git","commit","-qm","fixture"],cwd=root,check=True)
  success=m.verify(root)
  if not success["pass"]:raise SystemExit(success)
  p=root/"experiments/stage3f-publication-acquisition/gate5-independent-publication-acquisition-freeze.json"
  v=json.loads(p.read_text());v["status"]="broken";p.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n")
  negative=m.verify(root)
  if negative["pass"] or negative["failed_checks"]!=["gate5_status"]:raise SystemExit(negative)
  v["status"]="independent-freeze-complete";p.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n")
  missing=root/"experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json";missing.unlink()
  incomplete=m.verify(root)
  rel=str(missing.relative_to(root))
  if incomplete["pass"] or rel not in incomplete["missing_files"]:raise SystemExit(incomplete)
  print(json.dumps({"schema_version":1,"verification_kind":"stage3f-gate5-freeze-fixtures","pass":True,"fixtures":{"success":success["check_count"],"expected_negative":negative["failed_checks"],"incomplete":incomplete["missing_files"]}},indent=2,sort_keys=True))
 return 0
if __name__=="__main__":raise SystemExit(main())
