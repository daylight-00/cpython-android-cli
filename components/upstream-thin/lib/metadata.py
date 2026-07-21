#!/usr/bin/env python3
"""Generate a truthful Astral format-8 PYTHON.json from the final install tree."""
from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from elf import elf_surface, is_elf


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (list, tuple)):
        return " ".join(str(item) for item in value)
    return str(value)


def sanitize_tokens(value: str) -> str:
    value = value.replace("/usr/local", "install")
    tokens = re.findall(r"(?:'[^']*'|\"[^\"]*\"|\S+)", value)
    kept = [token for token in tokens if not any(marker in token for marker in ("/Users/runner/", "/data/data/com.termux/", "/home/runner/"))]
    return " ".join(kept)


def normalized_config_vars(install: Path, python_mm: str) -> dict[str, str]:
    raw = load_json(install / f"lib/python{python_mm}/_sysconfig_vars__android_aarch64-linux-android.json")
    if isinstance(raw, dict) and "build_time_vars" in raw:
        raw = raw["build_time_vars"]
    if not isinstance(raw, dict):
        raise ValueError("sysconfig vars are not an object")
    values = {str(key): sanitize_tokens(normalize_string(value)) for key, value in sorted(raw.items())}
    fixed = {
        "prefix": "install", "exec_prefix": "install", "base": "install", "platbase": "install",
        "installed_base": "install", "installed_platbase": "install", "projectbase": "install/bin",
        "BINDIR": "install/bin", "BINLIBDEST": f"install/lib/python{python_mm}",
        "LIBDEST": f"install/lib/python{python_mm}", "INCLUDEPY": f"install/include/python{python_mm}",
        "CONFINCLUDEPY": f"install/include/python{python_mm}", "LIBDIR": "install/lib",
        "LIBPL": f"install/lib/python{python_mm}/config-{python_mm}-aarch64-linux-android",
        "DESTSHARED": f"install/lib/python{python_mm}/lib-dynload", "CC": "clang", "CXX": "clang++",
        "AR": "llvm-ar", "SHELL": "sh -e", "TZPATH": "", "ANDROID_API_LEVEL": "24",
        "HOST_GNU_TYPE": "aarch64-linux-android", "BUILD_GNU_TYPE": "aarch64-linux-android",
        "HW_T_CROSS_BUILD_SDK": "unavailable-without-explicit-ndk-authority",
    }
    values.update(fixed)
    return values


def provider_map(install: Path, readelf: str) -> dict[str, str]:
    providers: dict[str, str] = {}
    for path in sorted(install.rglob("*")):
        if not is_elf(path):
            continue
        surface = elf_surface(path, readelf)
        for soname in surface["soname"]:
            providers[soname] = "install/" + path.relative_to(install).as_posix()
        providers.setdefault(path.name, "install/" + path.relative_to(install).as_posix())
    return providers


def link_rows(needed: list[str], providers: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in sorted(set(needed)):
        if name in providers:
            rows.append({"name": name, "path_dynamic": providers[name], "system": False})
        else:
            rows.append({"name": name, "system": True})
    return rows


def module_name(filename: str) -> str:
    return filename.split(".cpython-")[0].split(".abi3")[0].split(".so")[0]


def build_python_json(install: Path, contract: dict[str, Any], *, readelf: str = "readelf", fixture_mode: bool = False) -> dict[str, Any]:
    lock = contract["resolved_input_lock"]
    version = lock["python"]["version"]
    python_mm = lock["python"]["major_minor"]
    target = lock["target"]
    build_details_path = install / f"lib/python{python_mm}/build-details.json"
    if build_details_path.is_file():
        details = load_json(build_details_path)
        implementation = details.get("implementation", {})
    else:
        implementation = {"name": "cpython", "cache_tag": "cpython-314", "hexversion": 0x30E06F0, "version": {"major": 3, "minor": 14, "micro": 6, "releaselevel": "final", "serial": 0}}
    version_data = implementation.get("version", {})
    providers = {} if fixture_mode else provider_map(install, readelf)
    extensions: dict[str, list[dict[str, Any]]] = {}
    if not fixture_mode:
        dynload = install / f"lib/python{python_mm}/lib-dynload"
        if dynload.is_dir():
            for path in sorted(dynload.glob("*.so")):
                if not is_elf(path):
                    continue
                surface = elf_surface(path, readelf)
                name = module_name(path.name)
                extensions.setdefault(name, []).append({
                    "in_core": False,
                    "init_fn": f"PyInit_{name}",
                    "links": link_rows(surface["needed"], providers),
                    "required": False,
                    "shared_lib": "install/" + path.relative_to(install).as_posix(),
                    "variant": "shared-library",
                })
    libpython = install / f"lib/libpython{python_mm}.so"
    core: dict[str, Any] = {"shared_lib": f"install/lib/libpython{python_mm}.so", "links": []}
    if not fixture_mode and is_elf(libpython):
        core["links"] = link_rows(elf_surface(libpython, readelf)["needed"], providers)
    config_vars = {} if fixture_mode else normalized_config_vars(install, python_mm)
    return {
        "version": 8,
        "target_triple": target["triple"],
        "build_options": "",
        "python_tag": "cp314",
        "python_abi_tag": "cp314",
        "python_platform_tag": target["wheel_platform_tag"],
        "python_implementation_cache_tag": implementation.get("cache_tag", "cpython-314"),
        "python_implementation_hex_version": hex(int(implementation.get("hexversion", 0x30E06F0))),
        "python_implementation_name": implementation.get("name", "cpython"),
        "python_implementation_version": [str(version_data.get(key, default)) for key, default in (("major", 3), ("minor", 14), ("micro", 6), ("releaselevel", "final"), ("serial", 0))],
        "python_version": version,
        "python_major_minor_version": python_mm,
        "python_paths": {
            "data": "install", "include": f"install/include/python{python_mm}", "platinclude": f"install/include/python{python_mm}",
            "platlib": f"install/lib/python{python_mm}/site-packages", "platstdlib": f"install/lib/python{python_mm}",
            "purelib": f"install/lib/python{python_mm}/site-packages", "stdlib": f"install/lib/python{python_mm}",
        },
        "python_paths_abstract": {
            "data": "{base}", "include": "{installed_base}/include/python{py_version_short}{abiflags}",
            "platinclude": "{installed_platbase}/include/python{py_version_short}{abiflags}",
            "platlib": "{platbase}/lib/python{py_version_short}{abi_thread}/site-packages",
            "platstdlib": "{platbase}/lib/python{py_version_short}{abi_thread}",
            "purelib": "{base}/lib/python{py_version_short}{abi_thread}/site-packages",
            "stdlib": "{installed_base}/lib/python{py_version_short}{abi_thread}",
        },
        "python_config_vars": config_vars,
        "python_exe": f"install/bin/python{python_mm}",
        "python_stdlib_platform_config": f"install/lib/python{python_mm}/config-{python_mm}-{target['triple']}",
        "python_stdlib_test_packages": ["test"],
        "python_suffixes": {"bytecode": [".pyc"], "debug_bytecode": [".pyc"], "extension": [f".cpython-314-{target['triple']}.so", ".abi3.so", ".so"], "optimized_bytecode": [".pyc"], "source": [".py"]},
        "libpython_link_mode": "shared",
        "python_extension_module_loading": ["builtin", "shared-library"],
        "build_info": {"core": core, "extensions": dict(sorted(extensions.items()))},
        "licenses": ["PSF-2.0"],
        "license_path": f"install/lib/python{python_mm}/LICENSE.txt",
    }
