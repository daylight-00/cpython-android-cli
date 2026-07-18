#!/usr/bin/env python3
from pathlib import Path
import json, shutil, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[2]
VER=ROOT/'experiments/epoch2-recalibration/verify-recalibration.py'
def run(root):
 p=subprocess.run(['python3',str(VER),'--root',str(root)],capture_output=True,text=True); return p.returncode,json.loads(p.stdout)
def mutate(rel,fn):
 with tempfile.TemporaryDirectory() as td:
  dst=Path(td)/'repo'; shutil.copytree(ROOT,dst,ignore=shutil.ignore_patterns('.git','__pycache__'))
  fn(dst/rel); return run(dst)
rc,base=run(ROOT); assert rc==0 and base['pass']
rc,d=mutate('docs/epochs/EPOCH3_CHARTER.md',lambda p:p.write_text(p.read_text().replace('CPython source patch production','project-owned CPython production').replace('BeeWare dependency recipe production','project-owned dependency production'))); assert rc!=0 and 'epoch3-no-source-owner' in d['failed_checks']
rc,d=mutate('docs/CURRENT_CONTEXT.md',lambda p:p.write_text(p.read_text().replace('dual-device claim     not made','dual-device claim     accepted'))); assert rc!=0 and 'no-dual-claim' in d['failed_checks']
rc,d=mutate('docs/references/raw/2026-07-19-epoch2-epoch4-recalibration/epoch2-android-cpython-research.zip',lambda p:p.write_bytes(p.read_bytes()+b'X')); assert rc!=0 and 'raw-sha256:epoch2-android-cpython-research.zip' in d['failed_checks']
rc,d=mutate('docs/epochs/EPOCH4_CHARTER.md',lambda p:p.unlink()); assert rc!=0 and 'required:docs/epochs/EPOCH4_CHARTER.md' in d['failed_checks']
print(json.dumps({'schema_version':1,'success_check_count':base['check_count'],'fixtures':4,'pass':True},indent=2,sort_keys=True))
