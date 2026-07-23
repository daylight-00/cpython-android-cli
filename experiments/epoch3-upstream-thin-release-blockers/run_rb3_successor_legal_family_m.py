#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'components/upstream-thin/lib'))
from successor_legal_family import assemble_successor_legal_family

def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--technical-family-dir',type=Path,required=True);p.add_argument('--predecessor-legal-family-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--zstd',default='zstd');a=p.parse_args()
 try:r=assemble_successor_legal_family(a.technical_family_dir,a.predecessor_legal_family_dir,a.output_dir,root=ROOT,zstd=a.zstd)
 except Exception as e:r={'schema_version':1,'verifier_kind':'epoch3-rb3-successor-legally-integrated-release-family-candidate','pass':False,'error':f'{type(e).__name__}: {e}'}
 print(json.dumps(r,indent=2,sort_keys=True));return 0 if r.get('pass') else 1
if __name__=='__main__':raise SystemExit(main())
