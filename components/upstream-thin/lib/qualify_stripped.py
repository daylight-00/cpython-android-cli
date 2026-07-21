#!/usr/bin/env python3
"""Run canonical install-only runtime qualification against stripped."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from qualify_install_only import qualify


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    parser.add_argument("--output")
    parser.add_argument("--pkg-config", default="pkg-config")
    args = parser.parse_args()
    result = qualify(Path(args.archive).resolve(), pkg_config=args.pkg_config)
    result["qualification_kind"] = "epoch3-canonical-install-only-stripped-android-target"
    result["claim_boundary"]["install_only_authority_frozen"] = True
    result["claim_boundary"]["stripped_started"] = True
    result["claim_boundary"]["stripped_authority_frozen"] = False
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
