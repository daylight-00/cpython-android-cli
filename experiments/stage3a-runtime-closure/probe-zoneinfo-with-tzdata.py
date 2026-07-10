#!/usr/bin/env python3
from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys
import zoneinfo

keys = ["UTC", "Asia/Seoul", "America/New_York"]
results: dict[str, dict[str, str]] = {}

for key in keys:
    try:
        value = zoneinfo.ZoneInfo(key)
    except Exception as exc:  # noqa: BLE001
        results[key] = {
            "result": "FAIL",
            "error": repr(exc),
        }
    else:
        results[key] = {
            "result": "PASS",
            "repr": repr(value),
        }

try:
    tzdata_version = importlib.metadata.version("tzdata")
except importlib.metadata.PackageNotFoundError:
    tzdata_version = None

summary = {
    "python_executable": sys.executable,
    "sys_prefix": sys.prefix,
    "sys_base_prefix": sys.base_prefix,
    "python_tzpath_env": os.environ.get("PYTHONTZPATH"),
    "zoneinfo_tzpath": list(zoneinfo.TZPATH),
    "tzdata_spec_found": importlib.util.find_spec("tzdata") is not None,
    "tzdata_version": tzdata_version,
    "keys": results,
    "all_keys_pass": all(item["result"] == "PASS" for item in results.values()),
}

print(json.dumps(summary, indent=2, sort_keys=True))
raise SystemExit(0 if summary["all_keys_pass"] else 4)
