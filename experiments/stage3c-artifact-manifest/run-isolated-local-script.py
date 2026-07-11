#!/usr/bin/env python3
from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "usage: run-isolated-local-script.py SCRIPT [ARG ...]",
            file=sys.stderr,
        )
        return 2

    script = Path(sys.argv[1]).resolve()
    if not script.is_file():
        print(f"ERROR: local script is missing: {script}", file=sys.stderr)
        return 2

    # Python isolated mode intentionally omits the script directory from
    # sys.path on the target runtime. Add only the selected script's directory
    # so sibling project modules can be imported without enabling PYTHONPATH,
    # user site packages, or current-working-directory imports.
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script), *sys.argv[2:]]
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
