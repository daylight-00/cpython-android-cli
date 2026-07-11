#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

VARIANT_EXPECTATIONS = {
    "runtime-base": {"development": False, "tests": False},
    "runtime-development": {"development": True, "tests": False},
    "runtime-test": {"development": False, "tests": True},
    "runtime-supported": {"development": True, "tests": True},
}
MODULES = (
    "venv",
    "ensurepip",
    "test",
    "test.support",
    "__phello__",
    "tkinter",
    "turtle",
    "idlelib",
    "idlelib.pyshell",
    "turtledemo",
)
RUNTIME_METADATA = (
    "lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py",
    "lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json",
    "lib/python3.14/build-details.json",
)
DEVELOPMENT_PATHS = (
    "include/python3.14/Python.h",
    "include/python3.14/pyconfig.h",
    "lib/pkgconfig/python-3.14.pc",
    "lib/pkgconfig/python3.pc",
    "lib/python3.14/config-3.14-aarch64-linux-android/Makefile",
    "lib/python3.14/config-3.14-aarch64-linux-android/python-config.py",
)
GUI_PATHS = (
    "lib/python3.14/tkinter",
    "lib/python3.14/idlelib",
    "lib/python3.14/turtledemo",
    "lib/python3.14/turtle.py",
)


def spec_result(name: str) -> dict[str, Any]:
    try:
        spec = importlib.util.find_spec(name)
    except BaseException as exc:
        return {
            "found": False,
            "origin": None,
            "locations": [],
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    if spec is None:
        return {"found": False, "origin": None, "locations": []}
    locations = []
    if spec.submodule_search_locations is not None:
        locations = [str(item) for item in spec.submodule_search_locations]
    return {"found": True, "origin": spec.origin, "locations": locations}


def import_result(name: str) -> dict[str, Any]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    result: dict[str, Any] = {
        "name": name,
        "success": False,
        "module_file": None,
        "spec": spec_result(name),
        "stdout": "",
        "stderr": "",
        "error_type": None,
        "error": None,
    }
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            module = importlib.import_module(name)
        result["success"] = True
        result["module_file"] = getattr(module, "__file__", None)
    except BaseException as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    result["stdout"] = stdout.getvalue()
    result["stderr"] = stderr.getvalue()
    return result


def within(path_value: str, prefix: Path) -> bool:
    try:
        Path(path_value).resolve().relative_to(prefix)
    except (OSError, ValueError):
        return False
    return True


def expected_presence(values: dict[str, bool], present: bool) -> bool:
    if present:
        return all(values.values())
    return not any(values.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", required=True, choices=sorted(VARIANT_EXPECTATIONS))
    parser.add_argument("--prefix", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    prefix = args.prefix.resolve()
    output = args.output.resolve()
    expected = VARIANT_EXPECTATIONS[args.variant]
    expected_python = (prefix / "bin" / "python3.14").resolve()
    observed_python = Path(sys.executable).resolve()

    core: dict[str, Any] = {"success": False, "error_type": None, "error": None}
    try:
        import bz2
        import ctypes
        import lzma
        import sqlite3
        import ssl
        import sysconfig
        import zlib

        with sqlite3.connect(":memory:") as database:
            sqlite_result = database.execute("select 42").fetchone()[0]
        ctypes.CDLL("libc.so")
        core.update(
            {
                "success": sqlite_result == 42,
                "ssl_openssl_version": ssl.OPENSSL_VERSION,
                "sqlite_version": sqlite3.sqlite_version,
                "bz2_module": bz2.__name__,
                "lzma_module": lzma.__name__,
                "zlib_version": zlib.ZLIB_VERSION,
            }
        )
    except BaseException as exc:
        core["error_type"] = type(exc).__name__
        core["error"] = str(exc)

    modules = {name: import_result(name) for name in MODULES}

    sysconfig_result: dict[str, Any] = {
        "success": False,
        "error_type": None,
        "error": None,
    }
    try:
        import sysconfig

        paths = sysconfig.get_paths()
        makefile = Path(sysconfig.get_makefile_filename())
        config_h = Path(sysconfig.get_config_h_filename())
        config_vars = sysconfig.get_config_vars()
        sysconfig_result.update(
            {
                "success": True,
                "config_var_count": len(config_vars),
                "paths": paths,
                "paths_under_prefix": {
                    key: within(value, prefix) for key, value in paths.items()
                },
                "makefile": str(makefile),
                "makefile_exists": makefile.is_file(),
                "config_h": str(config_h),
                "config_h_exists": config_h.is_file(),
                "soabi": sysconfig.get_config_var("SOABI"),
                "ext_suffix": sysconfig.get_config_var("EXT_SUFFIX"),
            }
        )
    except BaseException as exc:
        sysconfig_result["error_type"] = type(exc).__name__
        sysconfig_result["error"] = str(exc)

    runtime_metadata = {
        path: (prefix / path).is_file() for path in RUNTIME_METADATA
    }
    development_paths = {
        path: (prefix / path).exists() or (prefix / path).is_symlink()
        for path in DEVELOPMENT_PATHS
    }
    gui_paths = {
        path: (prefix / path).exists() or (prefix / path).is_symlink()
        for path in GUI_PATHS
    }

    expected_module_success = {
        "venv": True,
        "ensurepip": True,
        "test": expected["tests"],
        "test.support": expected["tests"],
        "__phello__": expected["tests"],
        "tkinter": False,
        "turtle": False,
        "idlelib": False,
        "idlelib.pyshell": False,
        "turtledemo": False,
    }
    module_expectations = {
        name: modules[name]["success"] is success
        for name, success in expected_module_success.items()
    }

    checks = {
        "sys_executable_matches": observed_python == expected_python,
        "sys_prefix_matches": Path(sys.prefix).resolve() == prefix,
        "sys_base_prefix_matches": Path(sys.base_prefix).resolve() == prefix,
        "core_runtime_success": core["success"] is True,
        "sysconfig_success": sysconfig_result["success"] is True,
        "sysconfig_config_vars_nonempty": sysconfig_result.get(
            "config_var_count", 0
        )
        > 0,
        "sysconfig_paths_under_prefix": bool(
            sysconfig_result.get("paths_under_prefix")
        )
        and all(sysconfig_result.get("paths_under_prefix", {}).values()),
        "runtime_metadata_present": all(runtime_metadata.values()),
        "development_paths_match_variant": expected_presence(
            development_paths,
            expected["development"],
        ),
        "makefile_state_matches_variant": sysconfig_result.get(
            "makefile_exists"
        )
        is expected["development"],
        "config_h_state_matches_variant": sysconfig_result.get(
            "config_h_exists"
        )
        is expected["development"],
        "gui_paths_absent": not any(gui_paths.values()),
        "module_expectations_match": all(module_expectations.values()),
        "soabi_matches": sysconfig_result.get("soabi")
        == "cpython-314-aarch64-linux-android",
        "ext_suffix_present": isinstance(sysconfig_result.get("ext_suffix"), str)
        and bool(sysconfig_result.get("ext_suffix")),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "schema_version": 1,
        "pass": not failed,
        "check_count": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "variant": args.variant,
        "prefix": str(prefix),
        "sys_executable": sys.executable,
        "sys_prefix": sys.prefix,
        "sys_base_prefix": sys.base_prefix,
        "expected": expected,
        "core": core,
        "modules": modules,
        "module_expectations": module_expectations,
        "runtime_metadata": runtime_metadata,
        "development_paths": development_paths,
        "gui_paths": gui_paths,
        "sysconfig": sysconfig_result,
        "environment": {
            "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH"),
            "SSL_CERT_FILE": os.environ.get("SSL_CERT_FILE"),
            "PYTHONDONTWRITEBYTECODE": os.environ.get("PYTHONDONTWRITEBYTECODE"),
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(
        f"STAGE3C_PHASE1_VARIANT_CAPABILITY[{args.variant}]="
        + ("PASS" if result["pass"] else "FAIL")
    )
    return 0 if result["pass"] else 16


if __name__ == "__main__":
    raise SystemExit(main())
