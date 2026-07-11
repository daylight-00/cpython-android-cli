#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import ssl
import sqlite3
import subprocess
import sys
import sysconfig
import urllib.request
from pathlib import Path
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--https", action="store_true")
    parser.add_argument("--require-anyio", action="store_true")
    args = parser.parse_args()

    import bz2
    import ctypes
    import lzma
    import zlib

    anyio_name = None
    if args.require_anyio:
        import anyio

        anyio_name = anyio.__name__

    https_status = None
    if args.https:
        with urllib.request.urlopen("https://pypi.org/simple/", timeout=15) as response:
            https_status = response.status

    child_code = (
        "import json,sys; "
        "print(json.dumps({'executable':sys.executable,'prefix':sys.prefix,"
        "'base_prefix':sys.base_prefix},sort_keys=True))"
    )
    child = subprocess.run(
        [sys.executable, "-I", "-B", "-S", "-c", child_code],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    child_identity = json.loads(child.stdout.strip())

    result = {
        "schema_version": 1,
        "pass": True,
        "executable": sys.executable,
        "prefix": sys.prefix,
        "base_prefix": sys.base_prefix,
        "exec_prefix": sys.exec_prefix,
        "base_exec_prefix": sys.base_exec_prefix,
        "version_info": list(sys.version_info[:3]),
        "platform": sys.platform,
        "machine": platform.machine(),
        "soabi": sysconfig.get_config_var("SOABI"),
        "multiarch": sysconfig.get_config_var("MULTIARCH"),
        "sysconfig_paths": sysconfig.get_paths(),
        "sys_path": sys.path,
        "environment": {
            "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH"),
            "SSL_CERT_FILE": os.environ.get("SSL_CERT_FILE"),
            "SSL_CERT_DIR": os.environ.get("SSL_CERT_DIR"),
            "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV"),
        },
        "imports": {
            "ssl": ssl.OPENSSL_VERSION,
            "sqlite3": sqlite3.sqlite_version,
            "bz2": bz2.__name__,
            "ctypes": ctypes.__name__,
            "lzma": lzma.__name__,
            "zlib": zlib.ZLIB_VERSION,
            "anyio": anyio_name,
        },
        "https_status": https_status,
        "child_identity": child_identity,
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
