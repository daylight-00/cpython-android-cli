#!/usr/bin/env python3
"""Run the bounded RB-3 sysconfig/SDK C/H/U/M target profile experiment."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
sys.path.insert(0, str(LIB))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from archive import safe_extract_tar, sha256_file, write_json  # noqa: E402
from owner_approval_review import verify_family  # noqa: E402
from rb3_sysconfig_profiles import build_profiles  # noqa: E402

FULL = {"filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-full.tar.zst", "sha256": "20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12", "size_bytes": 39408292}
INSTALL = {"filename": "cpython-3.14.6+e3-full-r4-aarch64-linux-android-install_only.tar.gz", "sha256": "84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76", "size_bytes": 23841726}
KEY = "cpython-3.14.6-linux-aarch64-none"
HOST_ASSEMBLY = ROOT / "experiments/epoch3-upstream-thin-release-blockers/rb3-sysconfig-profile-host-assembly.json"


def expected_profile_identities() -> dict[str, dict[str, Any]]:
    data = json.loads(HOST_ASSEMBLY.read_text(encoding="utf-8"))
    rows = data.get("profiles")
    if not isinstance(rows, list):
        raise ValueError("host profile assembly lacks profiles")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("id") not in {"C", "H", "U", "M"}:
            raise ValueError("invalid host profile identity")
        result[row["id"]] = {
            "sha256": row.get("sha256"),
            "size_bytes": row.get("size_bytes"),
            "header": row.get("header"),
        }
    if set(result) != {"C", "H", "U", "M"}:
        raise ValueError("host profile identity set is incomplete")
    return result


def snapshot(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    rows = []
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append({"path": rel, "type": "symlink", "target": os.readlink(path)})
        elif path.is_dir():
            rows.append({"path": rel, "type": "directory"})
        elif path.is_file():
            rows.append({"path": rel, "type": "file", "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    return rows


def run_capture(name: str, command: list[str], cwd: Path, env: dict[str, str], process_dir: Path, timeout: int = 600) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        row = {"name": name, "command": command, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    except subprocess.TimeoutExpired as exc:
        row = {"name": name, "command": command, "returncode": 124, "stdout": exc.stdout or "", "stderr": (exc.stderr or "") + "\nTIMEOUT\n"}
    write_json(process_dir / f"{name}.json", row)
    return row


def clean_env(base: Path, managed: Path | None = None, policy: str = "never", catalog: Path | None = None) -> dict[str, str]:
    home, data, config, cache = (base / n for n in ("home", "data", "config", "cache"))
    for path in (home, data, config, cache):
        path.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("UV_") or key in {
            "AR", "ARFLAGS", "CC", "CFLAGS", "CPP", "CPPFLAGS", "CXX", "CXXFLAGS",
            "LDFLAGS", "LDSHARED", "LD_LIBRARY_PATH", "LD_PRELOAD", "LIBRARY_PATH",
            "PKG_CONFIG_PATH", "PKG_CONFIG_LIBDIR", "PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV",
        }:
            env.pop(key, None)
    env.update({
        "HOME": str(home), "XDG_DATA_HOME": str(data), "XDG_CONFIG_HOME": str(config), "XDG_CACHE_HOME": str(cache),
        "UV_CACHE_DIR": str(cache / "uv"), "UV_OFFLINE": "1", "UV_NO_CONFIG": "1", "UV_PYTHON_DOWNLOADS": policy,
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
    })
    if managed is not None:
        env["UV_PYTHON_INSTALL_DIR"] = str(managed)
    if catalog is not None:
        env["UV_PYTHON_DOWNLOADS_JSON_URL"] = catalog.resolve().as_uri()
    return env


def identity_code() -> str:
    return "import json,os,platform,sys,sysconfig;print(json.dumps({'executable':sys.executable,'real_executable':os.path.realpath(sys.executable),'version':platform.python_version(),'implementation':platform.python_implementation(),'soabi':sysconfig.get_config_var('SOABI'),'multiarch':sysconfig.get_config_var('MULTIARCH'),'platform':sysconfig.get_platform(),'prefix':sys.prefix,'base_prefix':sys.base_prefix,'cc':sysconfig.get_config_var('CC'),'build_gnu_type':sysconfig.get_config_var('BUILD_GNU_TYPE'),'config_args':sysconfig.get_config_var('CONFIG_ARGS')},sort_keys=True))"


def parse_json_stdout(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("returncode") != 0:
        return None
    try:
        value = json.loads(row.get("stdout", "").strip())
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def android_identity(row: dict[str, Any]) -> bool:
    value = parse_json_stdout(row)
    return bool(value and value.get("implementation") == "CPython" and value.get("version") == "3.14.6" and value.get("soabi") == "cpython-314-aarch64-linux-android" and value.get("multiarch") == "aarch64-linux-android" and value.get("platform") == "android-24-arm64_v8a")


def catalog_row(archive: Path, profile: str) -> dict[str, Any]:
    return {"name": "cpython", "arch": {"family": "aarch64", "variant": None}, "os": "linux", "libc": "none", "major": 3, "minor": 14, "patch": 6, "prerelease": "", "url": archive.resolve().as_uri(), "sha256": sha256_file(archive), "variant": None, "build": f"hw-t-rb3-sysconfig-profile-{profile.lower()}"}


def readelf_surface(path: Path, readelf: str, env: dict[str, str]) -> dict[str, Any]:
    dyn = subprocess.run([readelf, "-dW", str(path)], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ph = subprocess.run([readelf, "-lW", str(path)], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    needed = re.findall(r"\(NEEDED\).*?\[(.*?)\]", dyn.stdout)
    runpath = re.findall(r"\(RUNPATH\).*?\[(.*?)\]", dyn.stdout)
    rpath = re.findall(r"\(RPATH\).*?\[(.*?)\]", dyn.stdout)
    alignments = []
    for line in ph.stdout.splitlines():
        if line.lstrip().startswith("LOAD"):
            token = line.split()[-1]
            try:
                alignments.append(int(token, 16) if token.startswith("0x") else int(token))
            except ValueError:
                pass
    return {"returncode": max(dyn.returncode, ph.returncode), "needed": needed, "runpath": runpath, "rpath": rpath, "load_alignments": alignments, "all_load_alignments_16k": bool(alignments) and all(x >= 16384 and x % 16384 == 0 for x in alignments), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def native_project(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "probe.c").write_text(
        "#define PY_SSIZE_T_CLEAN\n#include <Python.h>\nstatic PyObject* value(PyObject* s, PyObject* a){return PyLong_FromLong(3146);}\nstatic PyMethodDef m[]={{\"value\",value,METH_NOARGS,\"\"},{NULL,NULL,0,NULL}};\nstatic struct PyModuleDef d={PyModuleDef_HEAD_INIT,\"hw_t_rb3_probe\",NULL,-1,m};\nPyMODINIT_FUNC PyInit_hw_t_rb3_probe(void){return PyModule_Create(&d);}\n",
        encoding="utf-8",
    )
    (root / "setup.py").write_text("from setuptools import Extension,setup\nsetup(name='hw-t-rb3-probe',version='0.1.0',ext_modules=[Extension('hw_t_rb3_probe',['probe.c'])])\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[build-system]\nrequires=['setuptools']\nbuild-backend='setuptools.build_meta'\n", encoding="utf-8")


def wheel_probe(
    profile: str,
    python: Path,
    product: Path,
    work: Path,
    env: dict[str, str],
    process_dir: Path,
    readelf: str,
    patchelf: str | None,
    *,
    perform_explicit_normalization: bool = True,
) -> dict[str, Any]:
    work.mkdir(parents=True, exist_ok=True)
    venv = work / "wheel-venv"
    create = run_capture(f"{profile}-wheel-venv", [str(python), "-m", "venv", str(venv)], work, env, process_dir)
    if create["returncode"] != 0:
        return {"pass": False, "stage": "venv", "raw_policy_clean": False}
    setuptools = product / "lib/python3.14/test/wheeldata/setuptools-79.0.1-py3-none-any.whl"
    install_setuptools = run_capture(f"{profile}-wheel-setuptools", [str(venv / "bin/python"), "-m", "pip", "install", "--no-index", "--no-deps", str(setuptools)], work, env, process_dir)
    project = work / "native-project"; native_project(project)
    dist = work / "dist"; dist.mkdir()
    build = run_capture(f"{profile}-wheel-build", [str(venv / "bin/python"), "-m", "pip", "wheel", "--no-index", "--no-deps", "--no-build-isolation", "-w", str(dist), str(project)], work, env, process_dir, timeout=900)
    wheels = sorted(dist.glob("*.whl"))
    row: dict[str, Any] = {"venv_returncode": create["returncode"], "setuptools_returncode": install_setuptools["returncode"], "build_returncode": build["returncode"], "wheel_count": len(wheels), "raw_policy_clean": False}
    if build["returncode"] != 0 or len(wheels) != 1:
        row["pass"] = False
        return row
    wheel = wheels[0]
    install_wheel = run_capture(
        f"{profile}-wheel-install",
        [str(venv / "bin/python"), "-m", "pip", "install", "--no-index", "--no-deps", "--force-reinstall", str(wheel)],
        work, env, process_dir,
    )
    import_wheel = run_capture(
        f"{profile}-wheel-import",
        [str(venv / "bin/python"), "-c", "import hw_t_rb3_probe; assert hw_t_rb3_probe.value() == 3146"],
        work, env, process_dir,
    ) if install_wheel["returncode"] == 0 else {"returncode": 125}
    unpack = work / "wheel-unpack"; unpack.mkdir()
    with zipfile.ZipFile(wheel) as zf:
        zf.extractall(unpack)
    extensions = sorted(unpack.rglob("*.so"))
    row.update({
        "wheel": {"filename": wheel.name, "sha256": sha256_file(wheel), "size_bytes": wheel.stat().st_size},
        "wheel_install_returncode": install_wheel["returncode"],
        "wheel_import_returncode": import_wheel.get("returncode"),
        "extension_count": len(extensions),
    })
    if len(extensions) != 1:
        row["pass"] = False
        return row
    ext = extensions[0]
    before = readelf_surface(ext, readelf, env)
    row["raw_extension"] = before
    row["raw_policy_clean"] = before["returncode"] == 0 and not before["runpath"] and not before["rpath"] and before["all_load_alignments_16k"]
    row["postprocessing_boundary"] = "out-of-scope-external-tool-responsibility"
    if perform_explicit_normalization:
        if not patchelf:
            raise RuntimeError("patchelf is required for the historical explicit-normalization probe")
        normalized = work / "normalized-extension.so"; shutil.copy2(ext, normalized)
        norm = run_capture(f"{profile}-wheel-explicit-rpath-normalization", [patchelf, "--page-size", "16384", "--remove-rpath", str(normalized)], work, env, process_dir)
        normalized_import = run_capture(
            f"{profile}-wheel-explicit-normalization-import",
            [str(python), "-c", "import importlib.util,sys; p=sys.argv[1]; s=importlib.util.spec_from_file_location('hw_t_rb3_probe',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); assert m.value() == 3146", str(normalized)],
            work, env, process_dir,
        ) if norm["returncode"] == 0 else {"returncode": 125}
        row["explicit_normalization"] = {
            "returncode": norm["returncode"],
            "import_returncode": normalized_import.get("returncode"),
            "after": readelf_surface(normalized, readelf, env) if norm["returncode"] == 0 else None,
            "required": bool(before["runpath"] or before["rpath"]),
            "historical_experiment_only": True,
        }
    row["pass"] = build["returncode"] == 0 and before["returncode"] == 0
    return row


def profile_probe(profile: str, archive: Path, uv: Path, base: Path, process_dir: Path, readelf: str, patchelf: str, pkg_config: str) -> dict[str, Any]:
    root = base / "extract"; safe_extract_tar(archive, root, "r:gz")
    initial_product = root / "python"
    moved_parent = base / "moved"; moved_parent.mkdir(); product = moved_parent / "python"; initial_product.rename(product)
    python = product / "bin/python3.14"
    env = clean_env(base / "system-session")
    direct = run_capture(f"{profile}-direct-identity", [str(python), "-c", identity_code()], base, env, process_dir)
    uv_find = run_capture(f"{profile}-system-find", [str(uv), "python", "find", str(python), "--resolve-links", "--no-python-downloads", "--offline", "--no-managed-python", "--system", "--no-config", "--color", "never"], base, env, process_dir)
    venv = base / "system-venv"
    uv_venv = run_capture(f"{profile}-system-venv", [str(uv), "venv", str(venv), "--python", str(python), "--no-python-downloads", "--offline", "--no-managed-python", "--no-cache", "--no-config", "--color", "never"], base, env, process_dir)
    venv_identity = run_capture(f"{profile}-system-venv-identity", [str(venv / "bin/python"), "-c", identity_code()], base, env, process_dir) if uv_venv["returncode"] == 0 else {"returncode": 125}
    config_rows = []
    config_entry = product / "bin/python3.14-config"
    for option in ("--prefix", "--includes", "--cflags", "--libs", "--ldflags", "--extension-suffix", "--configdir"):
        config_rows.append(run_capture(f"{profile}-python-config-{option[2:]}", [str(config_entry), option], base, env, process_dir))
    pcenv = dict(env); pcenv["PKG_CONFIG_PATH"] = pcenv["PKG_CONFIG_LIBDIR"] = str(product / "lib/pkgconfig")
    pc = run_capture(f"{profile}-pkg-config", [pkg_config, "--cflags", "--libs", "python-3.14"], base, pcenv, process_dir)
    catalog = base / "catalog.json"; write_json(catalog, {KEY: catalog_row(archive, profile)})
    managed = base / "managed"; menv = clean_env(base / "managed-session", managed, "manual", catalog)
    managed_install = run_capture(f"{profile}-managed-install", [str(uv), "python", "install", KEY, "--install-dir", str(managed), "--no-bin", "--python-downloads-json-url", catalog.resolve().as_uri(), "--offline", "--no-config", "--color", "never"], base, menv, process_dir, timeout=900)
    fenv = clean_env(base / "managed-find-session", managed, "never", catalog)
    managed_find = run_capture(f"{profile}-managed-find", [str(uv), "python", "find", "3.14.6", "--managed-python", "--no-python-downloads", "--offline", "--python-downloads-json-url", catalog.resolve().as_uri(), "--no-config", "--color", "never"], base, fenv, process_dir)
    managed_python = Path(managed_find["stdout"].strip()) if managed_find["returncode"] == 0 else managed / "missing"
    managed_identity = run_capture(f"{profile}-managed-identity", [str(managed_python), "-c", identity_code()], base, fenv, process_dir) if managed_python.is_file() else {"returncode": 125}
    mvenv = base / "managed-venv"
    managed_venv = run_capture(f"{profile}-managed-venv", [str(uv), "venv", str(mvenv), "--python", "3.14.6", "--managed-python", "--no-python-downloads", "--offline", "--no-cache", "--no-config", "--color", "never"], base, fenv, process_dir)
    managed_venv_identity = run_capture(f"{profile}-managed-venv-identity", [str(mvenv / "bin/python"), "-c", identity_code()], base, fenv, process_dir) if managed_venv["returncode"] == 0 else {"returncode": 125}
    before_reinstall = snapshot(managed)
    reinstall = run_capture(f"{profile}-managed-reinstall", [str(uv), "python", "install", KEY, "--install-dir", str(managed), "--no-bin", "--python-downloads-json-url", catalog.resolve().as_uri(), "--offline", "--no-config", "--color", "never"], base, menv, process_dir, timeout=900)
    after_reinstall = snapshot(managed)
    uninstall = run_capture(f"{profile}-managed-uninstall", [str(uv), "python", "uninstall", "3.14.6", "--install-dir", str(managed), "--offline", "--no-config", "--color", "never"], base, fenv, process_dir)
    wheel = wheel_probe(profile, python, product, base / "wheel", env, process_dir, readelf, patchelf)
    return {
        "profile": profile,
        "archive": {"filename": archive.name, "sha256": sha256_file(archive), "size_bytes": archive.stat().st_size},
        "header": (product / "lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py").read_text(encoding="utf-8").splitlines()[0],
        "checks": {
            "direct_android_identity": android_identity(direct),
            "system_find": uv_find["returncode"] == 0,
            "system_venv": uv_venv["returncode"] == 0 and android_identity(venv_identity),
            "python_config": all(row["returncode"] == 0 for row in config_rows),
            "pkg_config": pc["returncode"] == 0,
            "managed_install": managed_install["returncode"] == 0,
            "managed_find": managed_find["returncode"] == 0,
            "managed_identity": android_identity(managed_identity),
            "managed_venv": managed_venv["returncode"] == 0 and android_identity(managed_venv_identity),
            "managed_reinstall_noop": reinstall["returncode"] == 0 and before_reinstall == after_reinstall,
            "managed_uninstall": uninstall["returncode"] == 0,
            "raw_native_wheel_build": wheel.get("pass") is True,
            "raw_native_wheel_import": wheel.get("wheel_import_returncode") == 0,
            "raw_native_wheel_policy_clean": wheel.get("raw_policy_clean") is True,
            "explicit_normalized_extension_import": wheel.get("explicit_normalization", {}).get("import_returncode") == 0,
        },
        "identity": parse_json_stdout(direct),
        "managed": {
            "install_returncode": managed_install.get("returncode"),
            "install_stdout": managed_install.get("stdout", ""),
            "install_stderr": managed_install.get("stderr", ""),
            "find_returncode": managed_find.get("returncode"),
            "find_stdout": managed_find.get("stdout", ""),
            "find_stderr": managed_find.get("stderr", ""),
            "identity_returncode": managed_identity.get("returncode"),
            "venv_returncode": managed_venv.get("returncode"),
            "venv_identity_returncode": managed_venv_identity.get("returncode"),
            "reinstall_returncode": reinstall.get("returncode"),
            "uninstall_returncode": uninstall.get("returncode"),
        },
        "python_config_outputs": [{"option": row["command"][-1], "returncode": row["returncode"], "stdout": row["stdout"].strip(), "stderr": row["stderr"].strip()} for row in config_rows],
        "pkg_config_output": {"returncode": pc["returncode"], "stdout": pc["stdout"].strip(), "stderr": pc["stderr"].strip()},
        "wheel": wheel,
    }


def run(family: Path, output: Path, uv: Path, zstd: str, readelf: str, patchelf: str, pkg_config: str) -> dict[str, Any]:
    family = family.resolve(); output = output.resolve(); uv = uv.resolve()
    family_check = verify_family(family, ROOT)
    if not family_check["pass"]:
        raise ValueError(f"invalid family: {family_check}")
    full, install = family / FULL["filename"], family / INSTALL["filename"]
    for path, expected in ((full, FULL), (install, INSTALL)):
        actual = {"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        if actual != expected:
            raise ValueError(f"exact artifact mismatch: {actual} != {expected}")
    if output.exists():
        shutil.rmtree(output)
    (output / "process").mkdir(parents=True)
    before_family = snapshot(family)
    real_managed = Path(os.environ.get("UV_PYTHON_INSTALL_DIR", str(Path.home() / ".local/share/uv/python"))).resolve()
    before_real = snapshot(real_managed)
    uv_version = subprocess.check_output([str(uv), "--version"], text=True).strip()
    if "aarch64-linux-android" not in uv_version:
        raise ValueError(f"not Android uv: {uv_version}")
    with tempfile.TemporaryDirectory(prefix="rb3-sysconfig-boundary-") as td:
        temp = Path(td)
        first = build_profiles(install, full, temp / "profiles-a", zstd)
        second = build_profiles(install, full, temp / "profiles-b", zstd)
        first_ids = {row["id"]: {"sha256": row["sha256"], "size_bytes": row["size_bytes"], "header": row["header"]} for row in first["profiles"]}
        second_ids = {row["id"]: {"sha256": row["sha256"], "size_bytes": row["size_bytes"], "header": row["header"]} for row in second["profiles"]}
        reproducible = first_ids == second_ids
        expected_ids = expected_profile_identities()
        host_identity_match = first_ids == expected_ids
        shutil.copytree(temp / "profiles-a", output / "profiles")
        profiles = []
        for row in first["profiles"]:
            profiles.append(profile_probe(row["id"], temp / "profiles-a" / row["archive"], uv, temp / f"run-{row['id']}", output / "process", readelf, patchelf, pkg_config))
    after_family = snapshot(family); after_real = snapshot(real_managed)
    control = next(p for p in profiles if p["profile"] == "C")
    header = next(p for p in profiles if p["profile"] == "H")
    experiment_checks = {
        "family_valid": family_check["pass"],
        "profile_assembly_reproducible": reproducible,
        "profile_identities_match_host_assembly": host_identity_match,
        "all_four_profiles_executed": [p["profile"] for p in profiles] == ["C", "H", "U", "M"],
        "current_control_reproduces_managed_failure": control["checks"]["managed_install"] is False and "header comment" in control["managed"]["install_stderr"],
        "header_profile_managed_install_attempted": isinstance(header["managed"]["install_returncode"], int),
        "frozen_family_unchanged": before_family == after_family,
        "real_managed_root_unchanged": before_real == after_real,
    }
    failed = sorted(k for k, v in experiment_checks.items() if v is not True)
    result = {
        "schema_version": 1,
        "result_kind": "epoch3-rb3-sysconfig-and-on-device-sdk-profile-probe",
        "pass": not failed,
        "checks": experiment_checks,
        "failed_checks": failed,
        "uv": {"version": uv_version, "sha256": sha256_file(uv), "size_bytes": uv.stat().st_size},
        "profiles": profiles,
        "selection": {"selected": False, "reason": "profile selection requires owner review of complete comparative evidence"},
        "claim_boundary": {"canonical_artifact_bytes_changed": False, "artifact_family_superseded": False, "rb3_closed": False, "on_device_sdk_final": False, "selectable": False, "publication": False},
    }
    write_json(output / "rb3-sysconfig-boundary-probe-result.json", result)
    write_json(output / "protected-state.json", {"family_unchanged": before_family == after_family, "real_managed_root_unchanged": before_real == after_real})
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--uv", type=Path, default=Path(shutil.which("uv") or "uv"))
    parser.add_argument("--zstd", default="zstd")
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--patchelf", default="patchelf")
    parser.add_argument("--pkg-config", default="pkg-config")
    args = parser.parse_args()
    try:
        result = run(args.family_dir, args.output_dir, args.uv, args.zstd, args.readelf, args.patchelf, args.pkg_config)
    except Exception as exc:
        result = {"schema_version": 1, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
