#!/usr/bin/env python3
"""Run the first bounded RB-1 component/license evidence census."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))
from license_census import census_release_family  # noqa: E402


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--family-dir",required=True,type=Path)
    parser.add_argument("--output-dir",required=True,type=Path)
    parser.add_argument("--root",default=ROOT,type=Path)
    parser.add_argument("--zstd",default="zstd")
    args=parser.parse_args()
    try:
        result=census_release_family(args.family_dir.resolve(),args.output_dir.resolve(),root=args.root.resolve(),zstd=args.zstd)
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"schema_version":1,"runner_kind":"epoch3-release-blocker-component-license-baseline","pass":False,"error":f"{type(exc).__name__}: {exc}"},indent=2,sort_keys=True))
        return 1


if __name__=="__main__":
    raise SystemExit(main())
