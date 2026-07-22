#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'components/upstream-thin/lib'))
from license_provenance import resolve_source_provenance  # noqa:E402
def main():
 p=argparse.ArgumentParser();p.add_argument('--family-dir',required=True,type=Path);p.add_argument('--cpython-source',required=True,type=Path);p.add_argument('--output-dir',required=True,type=Path);p.add_argument('--root',default=ROOT,type=Path);p.add_argument('--zstd',default='zstd');a=p.parse_args()
 try:r=resolve_source_provenance(a.family_dir.resolve(),a.cpython_source.resolve(),a.output_dir.resolve(),root=a.root.resolve(),zstd=a.zstd);print(json.dumps(r,indent=2,sort_keys=True));return 0
 except Exception as e:print(json.dumps({'schema_version':1,'runner_kind':'epoch3-rb1-source-provenance-resolution','pass':False,'error':f'{type(e).__name__}: {e}'},indent=2,sort_keys=True));return 1
if __name__=='__main__':raise SystemExit(main())
