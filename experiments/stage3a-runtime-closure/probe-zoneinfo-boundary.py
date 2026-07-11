#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess


CHILD_ARGS = ["-B", "-P", "-s", "-c"]


def run_probe(python_bin: Path, env_overrides: dict[str, str | None]) -> dict[str, object]:
    env = os.environ.copy()

    # This probe intentionally tests PYTHONTZPATH. Isolated mode cannot be used,
    # because -I implies -E and would ignore the variable under test. Remove
    # ambient Python controls explicitly, then add only the scenario input.
    for key in list(env):
        if key.startswith("PYTHON"):
            env.pop(key, None)
    env["PYTHONNOUSERSITE"] = "1"

    for key, value in env_overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value

    code = r'''
import importlib.util
import json
import os
import sys
import zoneinfo

keys = ["UTC", "Asia/Seoul", "America/New_York"]
results = {}
for key in keys:
    try:
        zoneinfo.ZoneInfo(key)
    except Exception as exc:
        results[key] = {"result": "FAIL", "error": repr(exc)}
    else:
        results[key] = {"result": "PASS"}

print(json.dumps({
    "pythontzpath_env": os.environ.get("PYTHONTZPATH"),
    "zoneinfo_tzpath": list(zoneinfo.TZPATH),
    "tzpath_exists": {path: os.path.isdir(path) for path in zoneinfo.TZPATH},
    "tzdata_spec_found": importlib.util.find_spec("tzdata") is not None,
    "flags": {
        "isolated": sys.flags.isolated,
        "safe_path": sys.flags.safe_path,
        "no_user_site": sys.flags.no_user_site,
        "dont_write_bytecode": sys.dont_write_bytecode,
    },
    "keys": results,
}, sort_keys=True))
'''

    proc = subprocess.run(
        [str(python_bin), *CHILD_ARGS, code],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    parsed: dict[str, object] | None = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = None

    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "parsed": parsed,
    }


def scenario_pass(result: dict[str, object]) -> bool:
    if result["returncode"] != 0:
        return False
    parsed = result.get("parsed")
    if not isinstance(parsed, dict):
        return False
    keys = parsed.get("keys")
    if not isinstance(keys, dict):
        return False
    return all(
        isinstance(item, dict) and item.get("result") == "PASS"
        for item in keys.values()
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-bin", required=True, type=Path)
    parser.add_argument("--termux-prefix", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    python_bin = args.python_bin.resolve()
    termux_prefix = args.termux_prefix.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    termux_zoneinfo = termux_prefix / "share" / "zoneinfo"

    scenarios = {
        "default": run_probe(python_bin, {"PYTHONTZPATH": None}),
        "tzdata_only": run_probe(python_bin, {"PYTHONTZPATH": ""}),
        "termux_zoneinfo": run_probe(
            python_bin,
            {"PYTHONTZPATH": str(termux_zoneinfo)},
        ),
    }

    summary = {
        "child_args": CHILD_ARGS,
        "termux_zoneinfo_path": str(termux_zoneinfo),
        "termux_zoneinfo_exists": termux_zoneinfo.is_dir(),
        "scenarios": {
            name: {
                "pass": scenario_pass(result),
                "returncode": result["returncode"],
                "parsed": result["parsed"],
                "stderr": result["stderr"],
            }
            for name, result in scenarios.items()
        },
    }

    with (output_dir / "zoneinfo-boundary-probe.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
