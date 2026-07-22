#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'components/upstream-thin/lib'))
from owner_approval_review import prepare_review
def main():
 p=argparse.ArgumentParser();p.add_argument('--family-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
 try:o=prepare_review(a.family_dir,a.output_dir,a.root.resolve())
 except Exception as e:o={'schema_version':1,'pass':False,'error':f'{type(e).__name__}:{e}'}
 print(json.dumps(o,indent=2,sort_keys=True));return 0 if o.get('pass') else 1
if __name__=='__main__':raise SystemExit(main())
