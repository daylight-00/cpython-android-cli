#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'components/upstream-thin/lib'))
from legal_integration import assemble_legal_integrated_family
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--family-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 try:r=assemble_legal_integrated_family(a.family_dir,a.output_dir,root=a.root.resolve())
 except Exception as e:r={'schema_version':1,'verifier_kind':'epoch3-rb1-legally-integrated-release-family-candidate','pass':False,'error':f'{type(e).__name__}: {e}'}
 print(json.dumps(r,indent=2,sort_keys=True));return 0 if r.get('pass') else 1
if __name__=='__main__':raise SystemExit(main())
