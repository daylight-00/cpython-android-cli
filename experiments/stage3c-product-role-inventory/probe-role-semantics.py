#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib
import importlib.util
import io
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

MODULE_NAMES = (
    "venv",
    "ensurepip",
    "test",
    "test.support",
    "__phello__",
    "turtle",
    "idlelib",
    "idlelib.pyshell",
    "turtledemo",
)
REQUIRED_MODULE_NAMES = ("venv", "test", "test.support")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def kind(mode: int) -> str:
    if stat.S_ISREG(mode):
        return "REGULAR"
    if stat.S_ISDIR(mode):
        return "DIRECTORY"
    if stat.S_ISLNK(mode):
        return "SYMLINK"
    return "SPECIAL"


def paths(root: Path) -> list[Path]:
    output: list[Path] = []
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        dirs.sort()
        files.sort()
        base = Path(current)
        output.extend(base / name for name in dirs)
        output.extend(base / name for name in files)
    return sorted(output, key=lambda item: item.relative_to(root).as_posix())


def tree_state(root: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    counts = {"REGULAR": 0, "DIRECTORY": 0, "SYMLINK": 0}
    pycache: list[str] = []
    special: list[str] = []

    for path in paths(root):
        relative = path.relative_to(root).as_posix()
        st = path.lstat()
        entry_kind = kind(st.st_mode)
        file_hash = ""
        target = ""
        if entry_kind == "REGULAR":
            file_hash = sha256_file(path)
            counts[entry_kind] += 1
        elif entry_kind == "DIRECTORY":
            counts[entry_kind] += 1
        elif entry_kind == "SYMLINK":
            target = os.readlink(path)
            counts[entry_kind] += 1
        else:
            special.append(relative)

        if (
            relative.endswith(".pyc")
            or relative.endswith("/__pycache__")
            or "/__pycache__/" in f"/{relative}/"
        ):
            pycache.append(relative)

        row = (
            relative,
            entry_kind,
            f"{stat.S_IMODE(st.st_mode):04o}",
            str(st.st_size),
            str(st.st_mtime_ns),
            file_hash,
            target,
        )
        digest.update("\t".join(row).encode("utf-8", "surrogateescape"))
        digest.update(b"\n")

    return {
        "fingerprint": digest.hexdigest(),
        "entry_count": sum(counts.values()) + len(special),
        "regular_file_count": counts["REGULAR"],
        "directory_count": counts["DIRECTORY"],
        "symlink_count": counts["SYMLINK"],
        "pycache_paths": pycache,
        "special_paths": special,
    }


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
        "spec": spec_result(name),
        "success": False,
        "module_file": None,
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


def is_under(path_value: str | None, prefix: Path) -> bool:
    if not path_value:
        return False
    try:
        Path(path_value).resolve().relative_to(prefix)
    except (OSError, ValueError):
        return False
    return True


def probe_sysconfig(prefix: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"success": False, "error_type": None, "error": None}
    try:
        import sysconfig

        config_vars = sysconfig.get_config_vars()
        config_paths = sysconfig.get_paths()
        makefile = Path(sysconfig.get_makefile_filename())
        config_h = Path(sysconfig.get_config_h_filename())
        data_name = (
            sysconfig._get_sysconfigdata_name()  # type: ignore[attr-defined]
            if hasattr(sysconfig, "_get_sysconfigdata_name")
            else None
        )
        data_import = import_result(data_name) if data_name else None
        json_paths = sorted(
            str(path)
            for path in (prefix / "lib" / "python3.14").glob(
                "_sysconfig_vars_*.json"
            )
        )
        details_path = prefix / "lib" / "python3.14" / "build-details.json"
        details = None
        details_error = None
        if details_path.is_file():
            try:
                details = json.loads(details_path.read_text(encoding="utf-8"))
            except BaseException as exc:
                details_error = {
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }

        result.update(
            {
                "success": True,
                "paths": config_paths,
                "paths_under_prefix": {
                    name: is_under(value, prefix)
                    for name, value in config_paths.items()
                },
                "config_var_count": len(config_vars),
                "selected_config_vars": {
                    name: sysconfig.get_config_var(name)
                    for name in (
                        "SOABI",
                        "EXT_SUFFIX",
                        "LIBDIR",
                        "LIBPL",
                        "INCLUDEPY",
                        "MULTIARCH",
                        "HOST_GNU_TYPE",
                        "ANDROID_API_LEVEL",
                    )
                },
                "makefile": str(makefile),
                "makefile_exists": makefile.is_file(),
                "config_h": str(config_h),
                "config_h_exists": config_h.is_file(),
                "sysconfigdata_name": data_name,
                "sysconfigdata_import": data_import,
                "sysconfig_vars_json": json_paths,
                "sysconfig_vars_json_count": len(json_paths),
                "build_details_path": str(details_path),
                "build_details_exists": details_path.is_file(),
                "build_details_parse_success": isinstance(details, dict),
                "build_details_error": details_error,
                "build_details_top_level_keys": sorted(details)
                if isinstance(details, dict)
                else [],
            }
        )
    except BaseException as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    return result


def probe_tkinter() -> dict[str, Any]:
    binary = import_result("_tkinter")
    package = import_result("tkinter")
    result: dict[str, Any] = {
        "_tkinter": binary,
        "tkinter": package,
        "tcl_interpreter_success": False,
        "tcl_result": None,
        "tcl_version": None,
        "tk_version": None,
        "error_type": None,
        "error": None,
        "display": os.environ.get("DISPLAY"),
    }
    if not package["success"]:
        return result
    try:
        import tkinter

        interp = tkinter.Tcl()
        result["tcl_result"] = interp.eval("expr {6 * 7}")
        result["tcl_version"] = getattr(tkinter, "TclVersion", None)
        result["tk_version"] = getattr(tkinter, "TkVersion", None)
        result["tcl_interpreter_success"] = result["tcl_result"] == "42"
    except BaseException as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-entry-count", type=int, default=3155)
    args = parser.parse_args()

    prefix = args.runtime_prefix.resolve()
    output = args.output.resolve()
    if not prefix.is_dir():
        parser.error(f"runtime prefix is not a directory: {prefix}")
    if Path(sys.executable).resolve() != (prefix / "bin" / "python3.14").resolve():
        parser.error(
            "probe must run under the promoted interpreter: "
            f"sys.executable={sys.executable} prefix={prefix}"
        )

    before = tree_state(prefix)
    modules = {name: import_result(name) for name in MODULE_NAMES}
    sysconfig_result = probe_sysconfig(prefix)
    tkinter_result = probe_tkinter()
    after = tree_state(prefix)

    required_modules_pass = all(
        modules[name]["success"] for name in REQUIRED_MODULE_NAMES
    )
    path_states = sysconfig_result.get("paths_under_prefix", {})
    active_paths_pass = bool(path_states) and all(path_states.values())
    data_import = sysconfig_result.get("sysconfigdata_import") or {}

    passed = (
        before["entry_count"] == args.expected_entry_count
        and before["entry_count"] == after["entry_count"]
        and before["fingerprint"] == after["fingerprint"]
        and not before["pycache_paths"]
        and not after["pycache_paths"]
        and not before["special_paths"]
        and not after["special_paths"]
        and required_modules_pass
        and sysconfig_result.get("success") is True
        and sysconfig_result.get("config_var_count", 0) > 0
        and active_paths_pass
        and data_import.get("success") is True
        and sysconfig_result.get("build_details_parse_success") is True
    )

    result = {
        "schema_version": 1,
        "pass": passed,
        "runtime_prefix": str(prefix),
        "sys_executable": sys.executable,
        "expected_entry_count": args.expected_entry_count,
        "before_tree": before,
        "after_tree": after,
        "mutation_pass": before["fingerprint"] == after["fingerprint"],
        "required_module_names": list(REQUIRED_MODULE_NAMES),
        "required_modules_pass": required_modules_pass,
        "module_probes": modules,
        "sysconfig": sysconfig_result,
        "tkinter_capability": tkinter_result,
        "interpretation_inputs": {
            "test_internal_suite": modules["test"]["success"]
            and modules["test.support"]["success"],
            "ensurepip_importable": modules["ensurepip"]["success"],
            "tkinter_python_package_importable": tkinter_result["tkinter"][
                "success"
            ],
            "_tkinter_binary_importable": tkinter_result["_tkinter"][
                "success"
            ],
            "tcl_interpreter_usable": tkinter_result[
                "tcl_interpreter_success"
            ],
            "turtle_importable": modules["turtle"]["success"],
            "idlelib_pyshell_importable": modules["idlelib.pyshell"][
                "success"
            ],
            "turtledemo_importable": modules["turtledemo"]["success"],
            "sysconfig_runtime_service_usable": sysconfig_result.get(
                "success"
            )
            is True
            and active_paths_pass,
        },
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Semantic probes: {output}")
    print(
        "STAGE3C_PHASE1_ROLE_SEMANTIC_PROBE="
        + ("PASS" if passed else "FAIL")
    )
    return 0 if passed else 7


if __name__ == "__main__":
    raise SystemExit(main())
