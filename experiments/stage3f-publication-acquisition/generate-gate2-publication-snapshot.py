#!/usr/bin/env python3
from __future__ import annotations
import sys
sys.dont_write_bytecode=True
import argparse
from pathlib import Path
from publication_snapshot import build_snapshot_document, canonical_bytes

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(canonical_bytes(build_snapshot_document()))
    return 0
if __name__=="__main__": raise SystemExit(main())
