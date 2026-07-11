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
from pathlib import Path, PurePosixPath
from typing import Any

ELF_MAGIC = b"\x7fELF"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_type(mode: int) -> str:
    if stat.S_ISREG(mode):
        return "REGULAR"
    if stat.S_ISDIR(mode):
        return "DIRECTORY"
    if stat.S_ISLNK(mode):
        return "SYMLINK"
    if stat.S_ISCHR(mode):
        return "CHAR"
    if stat.S_ISBLK(mode):
        return "BLOCK"
    if stat.S_ISFIFO(mode):
        return "FIFO"
    if stat.S_ISSOCK(mode):
        return "SOCKET"
    return "OTHER"


def walk_entries(root: Path) -> list[Path]:
    entries: list[Path] = []
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        dirs.sort()
        files.sort()
        current_path = Path(current)
        entries.extend(current_path / name for name in dirs)
        entries.extend(current_path / name for name in files)
    return sorted(entries, key=lambda path: path.relative_to(root).as_posix())


def tree_state(root: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    entry_count = 0
    regular_count = 0
    directory_count = 0
    symlink_count = 0
    pycache_paths: list[str] = []
    special_paths: list[str] = []

    for path in walk_entries(root):
        st = path.lstat()
        relative = path.relative_to(root).as_posix()
        kind = file_type(st.st_mode)
        file_hash = ""
        target = ""
        if kind == "REGULAR":
            regular_count += 1
            file_hash = sha256_file(path)
        elif kind == "DIRECTORY":
            directory_count += 1
        elif kind == "SYMLINK":
            symlink_count += 1
            target = os.readlink(path)
        else:
            special_paths.append(relative)

        if (
            relative.endswith(".pyc")
            or relative.endswith("/__pycache__")
            or "/__pycache__/" in f"/{relative}/"
        ):
            pycache_paths.append(relative)

        row = (
            relative,
            kind,
            f"{stat.S_IMODE(st.st_mode):04o}",
            str(st.st_size),
            str(st.st_mtime_ns),
            file_hash,
            target,
        )
        digest.update("\t".join(row).encode("utf-8", "surrogateescape"))
        digest.update(b"\n")
        entry_count += 1

    return {
        "fingerprint": digest.hexdigest(),
        "entry_count": entry_count,
        "regular_file_count": regular_count,
        "directory_count": directory_count,
        "symlink_count": symlink_count,
        "pycache_paths": pycache_paths,
        "special_paths": special_paths,
    }


def spec_snapshot(name: str) -> dict[str, Any]:
    try:
        spec = importlib.util.find_spec(name)
    except BaseException as exc:
        return {
            "found": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    if spec is None:
        return {"found": False, "origin": None, "locations": []}
    locations = []
    if spec.submodule_search_locations is not None:
        locations = [str(item) for item in spec.submodule_search_locations]
    return {
        "found": True,
        "origin": spec.origin,
        "locations": locations,
    }


def import_probe(name: str) -> dict[str, Any]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    result: dict[str, Any] = {
        "name": name,
        "spec": spec_snapshot(name),
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


def under_prefix(path_value: str | None, prefix: Path) -> bool:
    if not path_value:
        return False
    try:
        path = Path(path_value).resolve()
    except OSError:
        return False
    try:
        path.relative_to(prefix)
    except ValueError:
        return False
    return True


def sysconfig_probe(prefix: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "success": False,
        "error_type": None,
        "error": None,
    }
    try:
        import sysconfig

        paths = sysconfig.get_paths()
        config_vars = sysconfig.get_config_vars()
        makefile = Path(sysconfig.get_makefile_filename())
        config_h = Path(sysconfig.get_config_h_filename())
        data_name = None
        data_import = None
        if hasattr(sysconfig, "_get_sysconfigdata_name"):
            data_name = sysconfig._get_sysconfigdata_name()  # type: ignore[attr-defined]
            data_import = import_probe(data_name)

        sysconfig_json = sorted(
            str(path)
            for path in (prefix / "lib" / "python3.14").glob(
                "_sysconfig_vars_*.json"
            )
        )
        build_details_path = prefix / "lib" / "python3.14" / "build-details.json"
        build_details = None
        build_details_error = None
        if build_details_path.is_file():
            try:
                build_details = json.loads(
                    build_details_path.read_text(encoding="utf-8")
                )
            except BaseException as exc:
                build_details_error = {
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }

        result.update(
            {
                "success": True,
                "paths": paths,
                "paths_under_prefix": {
                    key: under_prefix(value, prefix)
                    for key, value in paths.items()
                },
                "config_var_count": len(config_vars),
                "selected_config_vars": {
                    key: sysconfig.get_config_var(key)
                    for key in (
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
                "sysconfig_vars_json": sysconfig_json,
                "sysconfig_vars_json_count": len(sysconfig_json),
                "build_details_path": str(build_details_path),
                "build_details_exists": build_details_path.is_file(),
                "build_details_parse_success": build_details is not None,
                "build_details_error": build_details_error,
                "build_details_top_level_keys": sorted(build_details)
                if isinstance(build_details, dict)
                else [],
            }
        )
    except BaseException as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    return result


def tkinter_capability_probe() -> dict[str, Any]:
    result: dict[str, Any] = {
        "_tkinter": import_probe("_tkinter"),
        "tkinter": import_probe("tkinter"),
        "tcl_interpreter_success": False,
        "tcl_result": None,
        "tcl_version": None,
        "tk_version": None,
        "error_type": None,
        "error": None,
        "display": os.environ.get("DISPLAY"),
    }
    if not result["tkinter"]["success"]:
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

    module_names = (
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
    modules = {name: import_probe(name) for name in module_names}
    sysconfig_result = sysconfig_probe(prefix)
    tkinter_result = tkinter_capability_probe()

    after = tree_state(prefix)

    required_module_names = ("venv", "ensurepip", "test", "test.support")
    required_modules_pass = all(
        modules[name]["success"] for name in required_module_names
    )
    active_paths_pass = bool(sysconfig_result.get("paths_under_prefix")) and all(
        sysconfig_result.get("paths_under_prefix", {}).values()
    )
    sysconfigdata_import = sysconfig_result.get("sysconfigdata_import") or {}

    passed = (
        before["entry_count"] == args.expected_entry_count
        and before["fingerprint"] == after["fingerprint"]
        and before["entry_count"] == after["entry_count"]
        and not before["pycache_paths"]
        and not after["pycache_paths"]
        and not before["special_paths"]
        and not after["special_paths"]
        and required_modules_pass
        and sysconfig_result.get("success") is True
        and sysconfig_result.get("config_var_count", 0) > 0
        and active_paths_pass
        and sysconfigdata_import.get("success") is True
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
        "required_modules_pass": required_modules_pass,
        "module_probes": modules,
        "sysconfig": sysconfig_result,
        "tkinter_capability": tkinter_result,
        "interpretation_inputs": {
            "test_internal_suite": modules["test"]["success"]
            and modules["test.support"]["success"],
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
        + ("PASS" if result["pass"] else "FAIL")
    )
    return 0 if result["pass"] else 7


if __name__ == "__main__":
    raise SystemExit(main())
