#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'components/upstream-thin/lib'))
from legal_overlay import synthesize
def main():
 p=argparse.ArgumentParser();p.add_argument('--family-dir',type=Path,required=True);p.add_argument('--cpython-source',type=Path,required=True);p.add_argument('--source',action='append',default=[]);p.add_argument('--xz-asset',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args();sources={}
 for item in a.source:
  comp,path,sha,version=item.split('=',3);sources[comp]={'path':path,'sha256':sha,'version':version}
 try:r=synthesize(a.family_dir.resolve(),a.cpython_source.resolve(),sources,a.xz_asset.resolve(),a.output_dir.resolve(),a.root.resolve());print(json.dumps(r,indent=2,sort_keys=True));return 0
 except Exception as e:print(json.dumps({'schema_version':1,'runner_kind':'epoch3-rb1-legal-overlay-and-provider-policy-synthesis','pass':False,'error':f'{type(e).__name__}: {e}'},indent=2,sort_keys=True));return 1
if __name__=='__main__':raise SystemExit(main())
