#!/usr/bin/env python3
"""Run bounded Android target qualification against a canonical full archive."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from archive import safe_extract_tar, sha256_file


def _run(command: list[str], *, env: dict[str, str], cwd: Path | None = None, timeout: int = 300) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"command": command, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "timed_out": True}
    except OSError as exc:
        # Android app shells are intentionally minimal and may not expose
        # optional POSIX utilities such as getconf. Missing diagnostic tools
        # are evidence, not a reason for the qualification harness to crash.
        return {
            "command": command,
            "returncode": 127,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "timed_out": False,
            "tool_unavailable": True,
        }


def _json_probe(python: Path, code: str, env: dict[str, str], timeout: int = 300) -> dict[str, Any]:
    row = _run([str(python), "-c", code], env=env, timeout=timeout)
    try:
        row["data"] = json.loads(row["stdout"].strip().splitlines()[-1]) if row["stdout"].strip() else None
    except Exception as exc:  # noqa: BLE001
        row["parse_error"] = f"{type(exc).__name__}: {exc}"
        row["data"] = None
    row["pass"] = row["returncode"] == 0 and isinstance(row.get("data"), dict) and row["data"].get("pass") is True
    return row


def _clean_env(prefix: Path, state: Path) -> dict[str, str]:
    env = os.environ.copy()
    for key in ("LD_LIBRARY_PATH", "PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP", "VIRTUAL_ENV"):
        env.pop(key, None)
    for name in ("home", "tmp", "cache", "pycache", "userbase"):
        (state / name).mkdir(parents=True, exist_ok=True)
    env.update({
        "HOME": str(state / "home"),
        "TMPDIR": str(state / "tmp"),
        "XDG_CACHE_HOME": str(state / "cache"),
        "PYTHONPYCACHEPREFIX": str(state / "pycache"),
        "PYTHONUSERBASE": str(state / "userbase"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "HW_T_EXPECTED_PREFIX": str(prefix),
    })
    return env


def _runtime_code(modules: list[str]) -> str:
    return f'''
import ctypes, importlib, json, os, subprocess, sys, sysconfig
mods={modules!r}
fail={{}}
for name in mods:
    try:
        importlib.import_module(name)
    except BaseException as exc:
        fail[name]=type(exc).__name__+":"+str(exc)
prefix=os.environ["HW_T_EXPECTED_PREFIX"]
dl={{}}
for rel in ("lib/libcrypto_python.so","lib/libssl_python.so","lib/libsqlite3_python.so","lib/engines-3/afalg.so","lib/ossl-modules/legacy.so"):
    path=os.path.join(prefix,rel)
    if not os.path.exists(path):
        dl[rel]="absent"
        continue
    try:
        ctypes.CDLL(path); dl[rel]="pass"
    except BaseException as exc:
        dl[rel]=type(exc).__name__+":"+str(exc)
child_code='import json,os,ssl,sqlite3,_hashlib,sys;print(json.dumps({{"pass":True,"executable":sys.executable,"prefix":sys.prefix,"base_prefix":sys.base_prefix,"ld":os.environ.get("LD_LIBRARY_PATH")}}))'
env=dict(os.environ);env.pop("LD_LIBRARY_PATH",None)
child=subprocess.run([sys.executable,"-c",child_code],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
    child_data=json.loads(child.stdout.strip())
except BaseException:
    child_data=None
paths=sysconfig.get_paths()
vars={{k:sysconfig.get_config_var(k) for k in ("prefix","exec_prefix","BINDIR","LIBDIR","LIBDEST","INCLUDEPY","DESTSHARED","LIBPL","CC","LDSHARED","ANDROID_API_LEVEL","HOST_GNU_TYPE","BUILD_GNU_TYPE","HW_T_CROSS_BUILD_SDK")}}
within=lambda value: isinstance(value,str) and (value==prefix or value.startswith(prefix+os.sep))
path_ok=all(within(value) for value in paths.values())
var_path_keys=("prefix","exec_prefix","BINDIR","LIBDIR","LIBDEST","INCLUDEPY","DESTSHARED","LIBPL")
var_ok=all(within(vars[key]) for key in var_path_keys)
print(json.dumps({{
 "pass":not fail and child.returncode==0 and isinstance(child_data,dict) and child_data.get("pass") is True and child_data.get("ld") is None and path_ok and var_ok and os.environ.get("LD_LIBRARY_PATH") is None,
 "executable":sys.executable,"base_executable":getattr(sys,"_base_executable",None),"prefix":sys.prefix,"base_prefix":sys.base_prefix,
 "extension_count":len(mods),"extension_failures":fail,"dlopen":dl,"child":{{"returncode":child.returncode,"data":child_data,"stderr":child.stderr}},
 "sysconfig":{{"paths":paths,"vars":vars,"paths_within_prefix":path_ok,"path_vars_within_prefix":var_ok}},
 "ld_library_path":os.environ.get("LD_LIBRARY_PATH"),
}},sort_keys=True))
'''


def _chmod_read_only(root: Path) -> None:
    for path in sorted([*root.rglob("*"), root], key=lambda item: len(item.parts), reverse=True):
        if path.is_symlink():
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        path.chmod(mode & ~0o222)


def _restore_owner_write(root: Path) -> None:
    for path in sorted([root, *root.rglob("*")], key=lambda item: len(item.parts)):
        if path.is_symlink():
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        path.chmod(mode | stat.S_IWUSR)


def qualify(archive: Path, *, output: Path | None = None, zstd: str = "zstd", pkg_config: str = "pkg-config") -> dict[str, Any]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    evidence: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="qualify-full-") as tmp:
        root = Path(tmp)
        tar_path = root / "full.tar"
        decomp = subprocess.run([zstd, "-q", "-d", "-f", str(archive), "-o", str(tar_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        checks["decompress"] = decomp.returncode == 0
        if decomp.returncode:
            errors.append(decomp.stderr)
        else:
            extracted = root / "extracted"
            safe_extract_tar(tar_path, extracted, "r:")
            py = json.loads((extracted / "python/PYTHON.json").read_text(encoding="utf-8"))
            modules = sorted(py.get("build_info", {}).get("extensions", {}))
            runtime_a = root / "runtime-a/prefix"
            runtime_a.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(extracted / "python/install"), runtime_a)
            python_a = runtime_a / "bin/python3.14"
            env_a = _clean_env(runtime_a, root / "state-a")
            probe_a = _json_probe(python_a, _runtime_code(modules), env_a, 420)
            evidence["runtime_location_a"] = probe_a
            checks["runtime_location_a"] = probe_a["pass"]

            runtime_b = root / "relocated/deep/path/prefix"
            runtime_b.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(runtime_a), runtime_b)
            python_b = runtime_b / "bin/python3.14"
            env_b = _clean_env(runtime_b, root / "state-b")
            probe_b = _json_probe(python_b, _runtime_code(modules), env_b, 420)
            evidence["runtime_location_b"] = probe_b
            checks["whole_prefix_relocation"] = probe_b["pass"]

            command_rows: dict[str, Any] = {}
            for name in ("python", "python3", "python3.14"):
                row = _run([str(runtime_b / "bin" / name), "-c", "import json,sys;print(json.dumps({'pass':True,'executable':sys.executable,'version':sys.version_info[:3]}))"], env=env_b)
                command_rows[name] = row
            checks["python_alias_commands"] = all(row["returncode"] == 0 for row in command_rows.values())
            evidence["python_alias_commands"] = command_rows

            pip_rows: dict[str, Any] = {}
            for name in ("module", "pip", "pip3", "pip3.14"):
                command = [str(python_b), "-m", "pip", "--version"] if name == "module" else [str(runtime_b / "bin" / name), "--version"]
                pip_rows[name] = _run(command, env=env_b)
            checks["pip_surface"] = all(row["returncode"] == 0 and "pip " in row["stdout"] for row in pip_rows.values())
            evidence["pip_surface"] = pip_rows

            config_rows: dict[str, Any] = {}
            for option in ("--prefix", "--exec-prefix", "--includes", "--cflags", "--libs", "--ldflags", "--extension-suffix", "--configdir"):
                config_rows[option] = _run([str(runtime_b / "bin/python3.14-config"), option], env=env_b)
            checks["python_config_surface"] = all(row["returncode"] == 0 and "/data/data/com.termux/files/usr" not in (row["stdout"] + row["stderr"]) for row in config_rows.values())
            evidence["python_config_surface"] = config_rows

            pc_env = dict(env_b)
            pc_env["PKG_CONFIG_PATH"] = str(runtime_b / "lib/pkgconfig")
            pc_env["PKG_CONFIG_LIBDIR"] = str(runtime_b / "lib/pkgconfig")
            pkg_rows: dict[str, Any] = {}
            for package in ("python-3.14", "python-3.14-embed"):
                pkg_rows[package] = _run([pkg_config, "--cflags", "--libs", package], env=pc_env)
            checks["pkg_config_surface"] = all(row["returncode"] == 0 and str(runtime_b) in row["stdout"] and "/data/data/com.termux/files/usr" not in row["stdout"] for row in pkg_rows.values())
            evidence["pkg_config_surface"] = pkg_rows

            venv = root / "state-b/venvs/fresh"
            venv_create = _run([str(python_b), "-m", "venv", "--without-pip", "--symlinks", str(venv)], env=env_b, timeout=300)
            venv_probe = _json_probe(venv / "bin/python", "import json,sys;print(json.dumps({'pass':sys.prefix!=sys.base_prefix,'prefix':sys.prefix,'base_prefix':sys.base_prefix,'executable':sys.executable}))", env_b)
            checks["fresh_venv"] = venv_create["returncode"] == 0 and venv_probe["pass"]
            evidence["fresh_venv"] = {"create": venv_create, "probe": venv_probe}

            _chmod_read_only(runtime_b)
            env_ro = _clean_env(runtime_b, root / "state-read-only")
            read_only_probe = _json_probe(python_b, _runtime_code(modules), env_ro, 420)
            checks["read_only_install"] = read_only_probe["pass"]
            evidence["read_only_install"] = read_only_probe
            _restore_owner_write(runtime_b)

            checks["all_67_extensions"] = len(modules) == 67 and probe_a.get("data", {}).get("extension_count") == 67 and probe_b.get("data", {}).get("extension_count") == 67
            page_size = _run(
                [str(python_b), "-c", "import os; print(os.sysconf('SC_PAGE_SIZE'))"],
                env=env_b,
            )
            evidence["device"] = {
                "uname": _run(["uname", "-a"], env=env_b),
                "getprop_sdk": _run(["getprop", "ro.build.version.sdk"], env=env_b),
                "getprop_release": _run(["getprop", "ro.build.version.release"], env=env_b),
                "python_sysconf_pagesize": page_size,
                "optional_getconf_pagesize": _run(["getconf", "PAGESIZE"], env=env_b),
                "id": _run(["id"], env=env_b),
                "execution_context": "Termux app process used only as an Android/Bionic qualification context",
            }

    failed = sorted(key for key, value in checks.items() if not value)
    result = {
        "schema_version": 1,
        "qualification_kind": "epoch3-canonical-full-android-target",
        "pass": not failed,
        "checks": dict(sorted(checks.items())),
        "failed_checks": failed,
        "errors": errors,
        "evidence": evidence,
        "archive": {"path": str(archive), "sha256": sha256_file(archive), "size_bytes": archive.stat().st_size},
        "claim_boundary": {
            "qualified_context": "current owner Termux app process on Android/Bionic",
            "termux_native_dependency_claim": False,
            "api24_runtime_claim": False,
            "actual_16k_runtime_claim": False,
            "non_termux_context_claim": False,
            "selectable": False,
            "publication": False,
        },
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    parser.add_argument("--output")
    parser.add_argument("--zstd", default="zstd")
    parser.add_argument("--pkg-config", default="pkg-config")
    args = parser.parse_args()
    result = qualify(Path(args.archive).resolve(), output=Path(args.output).resolve() if args.output else None, zstd=args.zstd, pkg_config=args.pkg_config)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
