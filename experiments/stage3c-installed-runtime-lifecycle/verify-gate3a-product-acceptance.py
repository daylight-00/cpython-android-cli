#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from gate3a_acceptance_verify_repairs import repair_checks
from gate3a_acceptance_verify_runtime import runtime_checks
from gate3a_acceptance_verify_support import cjson, load_context


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase4-results", required=True, type=Path)
    parser.add_argument("--phase4i-results", required=True, type=Path)
    parser.add_argument("--scenario-results", required=True, type=Path)
    parser.add_argument("--runtime-results", required=True, type=Path)
    parser.add_argument("--gate1-verification", required=True, type=Path)
    parser.add_argument("--input-before", required=True, type=Path)
    parser.add_argument("--input-after", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    ctx = load_context(args)
    checks = {**repair_checks(ctx), **runtime_checks(ctx)}
    if len(checks) != 69:
        raise RuntimeError(f"unexpected acceptance check count: {len(checks)}")
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "missing_files": ctx.missing_files,
        "observed": {
            "isolated_repair_count": len(ctx.repair_rows),
            "sequential_repair_count": len(ctx.sequential_rows),
            "gate1_regression_check_count": ctx.gate1.get("check_count"),
            "https_status": ctx.base.get("https_status"),
            "elf_object_count": ctx.inventory.get("elf_object_count"),
            "needed_edge_count": ctx.inventory.get("needed_edge_count"),
            "extension_import_pass_count": ctx.extension_probe.get("import_pass_count"),
        },
        "claim_boundary": {
            "proved": "The accepted corrected engine passed exact reinstall, all six registered repair classes, and the complete Gate 1 installed-runtime behavior contract after sequential repairs.",
            "not_proved": "Corrected-engine relocation, preservation boundaries, addon lifecycle, uninstall, upgrade, and downgrade remain separate gates.",
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(cjson(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 92


if __name__ == "__main__":
    raise SystemExit(main())
