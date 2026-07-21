#!/usr/bin/env python3
"""Relocation-aware runtime and on-device SDK metadata normalization."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import pprint
import re
from pathlib import Path
from typing import Any

from archive import sha256_file, write_json

PYTHON_MM = "3.14"
TARGET_TRIPLE = "aarch64-linux-android"
PLACEHOLDER = "@HW_T_PREFIX@"
PRODUCER_ROOTS = ("/Users/runner/", "/home/runner/", "/data/data/com.termux/", "/usr/local")


def _text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _parse_build_time_vars(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "build_time_vars" for target in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, dict):
                return value
    raise RuntimeError(f"cannot parse build_time_vars: {path}")


def _sanitize_tokens(value: str, replacement_prefix: str = PLACEHOLDER) -> str:
    value = value.replace("/usr/local", replacement_prefix)
    tokens = re.findall(r"(?:'[^']*'|\"[^\"]*\"|\S+)", value)
    kept = [token for token in tokens if not any(root in token for root in PRODUCER_ROOTS[:3])]
    value = " ".join(kept)
    for root in PRODUCER_ROOTS[:3]:
        value = re.sub(re.escape(root) + r"[^\s'\"]+", "", value)
    return " ".join(value.split())


def _sanitize_vars(values: dict[str, Any]) -> dict[str, Any]:
    return {key: _sanitize_tokens(value) if isinstance(value, str) else value for key, value in values.items()}


def _dynamic_normalizer() -> str:
    return r'''

# BEGIN HW-T CONSUMER NORMALIZATION — E3 upstream-thin
import os as _hw_os
_hw_prefix = _hw_os.path.dirname(_hw_os.path.dirname(_hw_os.path.dirname(_hw_os.path.abspath(__file__))))
_hw_lib = _hw_os.path.join(_hw_prefix, "lib")
_hw_stdlib = _hw_os.path.join(_hw_lib, "python3.14")
_hw_include = _hw_os.path.join(_hw_prefix, "include", "python3.14")
_hw_config = _hw_os.path.join(_hw_stdlib, "config-3.14-aarch64-linux-android")
_hw_placeholder = "@" + "HW_T_PREFIX" + "@"
for _hw_key, _hw_value in list(build_time_vars.items()):
    if isinstance(_hw_value, str):
        build_time_vars[_hw_key] = _hw_value.replace(_hw_placeholder, _hw_prefix)
_hw_ldflags = "-Wl,--build-id=sha1 -Wl,--no-rosegment -Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384"
_hw_cflags = "-fno-strict-overflow -Wsign-compare -Wunreachable-code -DNDEBUG -O2 -Wall -D__BIONIC_NO_PAGE_SIZE_MACRO"
build_time_vars.update({
    "prefix": _hw_prefix, "exec_prefix": _hw_prefix, "base": _hw_prefix, "platbase": _hw_prefix,
    "installed_base": _hw_prefix, "installed_platbase": _hw_prefix,
    "host_prefix": _hw_prefix, "host_exec_prefix": _hw_prefix,
    "projectbase": _hw_os.path.join(_hw_prefix, "bin"), "BINDIR": _hw_os.path.join(_hw_prefix, "bin"),
    "BINLIBDEST": _hw_stdlib, "LIBDEST": _hw_stdlib, "SCRIPTDIR": _hw_lib,
    "INCLUDEDIR": _hw_os.path.join(_hw_prefix, "include"), "CONFINCLUDEDIR": _hw_os.path.join(_hw_prefix, "include"),
    "INCLUDEPY": _hw_include, "CONFINCLUDEPY": _hw_include, "LIBDIR": _hw_lib,
    "LIBPL": _hw_config, "DESTSHARED": _hw_os.path.join(_hw_stdlib, "lib-dynload"),
    "srcdir": _hw_config, "abs_srcdir": _hw_config, "abs_builddir": _hw_config, "builddir": _hw_config,
    "CC": "clang", "CXX": "clang++", "AR": "llvm-ar", "ARFLAGS": "rcs", "CCSHARED": "-fPIC",
    "CFLAGS": _hw_cflags, "PY_CFLAGS": _hw_cflags, "PY_STDMODULE_CFLAGS": _hw_cflags + " -fPIC",
    "CPPFLAGS": "", "PY_CPPFLAGS": "", "LDFLAGS": _hw_ldflags, "PY_LDFLAGS": _hw_ldflags,
    "PY_CORE_LDFLAGS": _hw_ldflags, "LDSHARED": "clang -shared " + _hw_ldflags,
    "BLDSHARED": "clang -shared " + _hw_ldflags, "BLDLIBRARY": "-L" + _hw_lib + " -lpython3.14",
    "LIBPYTHON": "", "LIBS": "-ldl -lm", "SYSLIBS": "-llog", "SHELL": "sh -e",
    "CONFIG_ARGS": "--host=aarch64-linux-android --enable-shared --without-static-libpython --without-ensurepip consumer-normalized-binary-derived",
    "BUILD_GNU_TYPE": "aarch64-linux-android", "HOST_GNU_TYPE": "aarch64-linux-android", "TZPATH": "",
    "ANDROID_API_LEVEL": 24, "SOABI": "cpython-314-aarch64-linux-android", "MULTIARCH": "aarch64-linux-android",
    "EXT_SUFFIX": ".cpython-314-aarch64-linux-android.so", "HW_T_METADATA_PROFILE": "on-device-sdk",
    "HW_T_CROSS_BUILD_SDK": "unavailable-without-explicit-ndk-authority",
})
for _hw_key, _hw_value in build_time_vars.items():
    if isinstance(_hw_value, str) and _hw_placeholder in _hw_value:
        raise RuntimeError("HW-T sysconfig placeholder residue: %s=%r" % (_hw_key, _hw_value))
del _hw_key, _hw_value, _hw_cflags, _hw_ldflags, _hw_config, _hw_include, _hw_stdlib, _hw_lib, _hw_prefix, _hw_placeholder, _hw_os
# END HW-T CONSUMER NORMALIZATION
'''


def _render_sysconfigdata(values: dict[str, Any]) -> str:
    rendered = "# system configuration normalized for relocatable Android consumers\n"
    rendered += "build_time_vars = " + pprint.pformat(values, width=120, sort_dicts=True) + "\n"
    rendered += _dynamic_normalizer()
    if any(root in rendered for root in PRODUCER_ROOTS):
        raise RuntimeError("rendered sysconfigdata contains producer or stale install path")
    compile(rendered, "<normalized-sysconfigdata>", "exec")
    return rendered


def _normalize_makefile(path: Path) -> dict[str, Any]:
    original = path.read_text(encoding="utf-8")
    overrides = {
        "CC": "clang", "CXX": "clang++", "AR": "llvm-ar", "ARFLAGS": "rcs", "SHELL": "sh -e",
        "CFLAGS": "-fno-strict-overflow -Wsign-compare -Wunreachable-code -DNDEBUG -O2 -Wall -D__BIONIC_NO_PAGE_SIZE_MACRO",
        "PY_CFLAGS": "$(CFLAGS)", "CPPFLAGS": "", "PY_CPPFLAGS": "",
        "LDFLAGS": "-Wl,--build-id=sha1 -Wl,--no-rosegment -Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384",
        "PY_LDFLAGS": "$(LDFLAGS)", "PY_CORE_LDFLAGS": "$(LDFLAGS)",
        "LDSHARED": "clang -shared $(LDFLAGS)", "BLDSHARED": "clang -shared $(LDFLAGS)",
        "BLDLIBRARY": "-L$(LIBDIR) -lpython3.14",
        "CONFIG_ARGS": "--host=aarch64-linux-android --enable-shared --without-static-libpython --without-ensurepip consumer-normalized-binary-derived",
        "BUILD_GNU_TYPE": TARGET_TRIPLE, "HOST_GNU_TYPE": TARGET_TRIPLE, "TZPATH": "",
    }
    output: list[str] = []
    seen: set[str] = set()
    for line in original.splitlines():
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not match:
            output.append(_sanitize_tokens(line, "$(prefix)"))
            continue
        key, value = match.group(1), match.group(2)
        if key == "prefix":
            output.append("prefix := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../..)")
            seen.add(key)
        elif key in overrides:
            output.append(f"{key}=\t\t{overrides[key]}")
            seen.add(key)
        else:
            output.append(f"{key}=\t\t{_sanitize_tokens(value, '$(prefix)')}")
            seen.add(key)
    for key, value in overrides.items():
        if key not in seen:
            output.append(f"{key}=\t\t{value}")
    normalized = "\n".join(output) + "\n"
    if any(root in normalized for root in PRODUCER_ROOTS):
        raise RuntimeError("Makefile producer residue remains")
    path.write_text(normalized, encoding="utf-8")
    return {"path": path.name, "before_sha256": _text_sha(original), "after_sha256": sha256_file(path), "dynamic_prefix": True}


def _normalize_pkgconfig(pkgdir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(pkgdir.glob("*.pc")):
        if path.is_symlink():
            continue
        before = path.read_text(encoding="utf-8")
        lines: list[str] = []
        for line in before.splitlines():
            if line.startswith("prefix="):
                lines.append("prefix=${pcfiledir}/../..")
            elif "$(BLDLIBRARY)" in line:
                lines.append(line.replace(" $(BLDLIBRARY)", ""))
            else:
                lines.append(_sanitize_tokens(line, "${prefix}"))
        after = "\n".join(lines) + "\n"
        if any(root in after for root in PRODUCER_ROOTS):
            raise RuntimeError(f"pkg-config producer residue remains: {path}")
        path.write_text(after, encoding="utf-8")
        rows.append({"path": path.name, "before_sha256": _text_sha(before), "after_sha256": sha256_file(path), "prefix": "${pcfiledir}/../.."})
    return rows


def _relativize(value: Any, old_prefix: str) -> Any:
    if isinstance(value, str):
        return value.replace(old_prefix, "${prefix}")
    if isinstance(value, list):
        return [_relativize(item, old_prefix) for item in value]
    if isinstance(value, dict):
        return {key: _relativize(item, old_prefix) for key, item in value.items()}
    return value


def _normalize_build_details(path: Path) -> dict[str, Any]:
    before_text = path.read_text(encoding="utf-8")
    data = json.loads(before_text)
    data["base_interpreter"] = "bin/python3.14"
    data["base_prefix"] = "."
    if isinstance(data.get("c_api"), dict):
        data["c_api"]["headers"] = "include/python3.14"
        data["c_api"]["pkgconfig_path"] = "lib/pkgconfig"
    if isinstance(data.get("suffixes"), dict):
        data["suffixes"]["extensions"] = [".cpython-314-aarch64-linux-android.so", ".abi3.so", ".so"]
    if isinstance(data.get("libpython"), dict):
        data["libpython"]["dynamic"] = "lib/libpython3.14.so"
        data["libpython"]["dynamic_stableabi"] = "lib/libpython3.so"
    data["hw_t_path_semantics"] = "relative-to-runtime-root"
    write_json(path, data)
    return {"before_sha256": _text_sha(before_text), "after_sha256": sha256_file(path), "path_semantics": "relative-to-runtime-root"}


def normalize_runtime_metadata(install: Path) -> dict[str, Any]:
    stdlib = install / "lib/python3.14"
    sysdata = stdlib / "_sysconfigdata__android_aarch64-linux-android.py"
    sysvars = stdlib / "_sysconfig_vars__android_aarch64-linux-android.json"
    configdir = stdlib / "config-3.14-aarch64-linux-android"
    makefile = configdir / "Makefile"
    python_config = configdir / "python-config.py"
    build_details = stdlib / "build-details.json"
    required = (sysdata, sysvars, makefile, python_config, build_details)
    missing = [str(path.relative_to(install)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"required upstream SDK metadata missing: {missing}")

    original_vars = _parse_build_time_vars(sysdata)
    before_sysdata = sha256_file(sysdata)
    sysdata.write_text(_render_sysconfigdata(_sanitize_vars(original_vars)), encoding="utf-8")

    before_config = python_config.read_text(encoding="utf-8")
    config_text = before_config
    if config_text.startswith("#!"):
        config_text = "\n".join(config_text.splitlines()[1:]) + "\n"
    python_config.write_text(config_text, encoding="utf-8")
    os.chmod(python_config, 0o644)

    relative_vars = _relativize(_sanitize_vars(original_vars), PLACEHOLDER)
    relative_vars.update({
        "prefix": "${prefix}", "exec_prefix": "${prefix}", "base": "${prefix}", "platbase": "${prefix}",
        "installed_base": "${prefix}", "installed_platbase": "${prefix}", "projectbase": "${prefix}/bin",
        "BINDIR": "${prefix}/bin", "LIBDIR": "${prefix}/lib", "LIBDEST": "${prefix}/lib/python3.14",
        "BINLIBDEST": "${prefix}/lib/python3.14", "INCLUDEPY": "${prefix}/include/python3.14",
        "CONFINCLUDEPY": "${prefix}/include/python3.14", "LIBPL": "${prefix}/lib/python3.14/config-3.14-aarch64-linux-android",
        "DESTSHARED": "${prefix}/lib/python3.14/lib-dynload", "CC": "clang", "CXX": "clang++", "AR": "llvm-ar",
        "SHELL": "sh -e", "TZPATH": "", "ANDROID_API_LEVEL": 24, "HOST_GNU_TYPE": TARGET_TRIPLE,
        "BUILD_GNU_TYPE": TARGET_TRIPLE, "HW_T_METADATA_PROFILE": "on-device-sdk",
        "HW_T_CROSS_BUILD_SDK": "unavailable-without-explicit-ndk-authority", "_HW_T_PATH_SEMANTICS": "${prefix}-relative",
    })
    write_json(sysvars, relative_vars)

    config_entry = install / "bin/python3.14-config"
    config_entry.parent.mkdir(parents=True, exist_ok=True)
    config_entry.write_text(
        "#!/system/bin/sh\n"
        "case \"$0\" in /*) _hw_script=\"$0\" ;; *) _hw_script=\"$(pwd)/$0\" ;; esac\n"
        "_hw_bindir=${_hw_script%/*}\n"
        "exec \"$_hw_bindir/python3.14\" \"$_hw_bindir/../lib/python3.14/config-3.14-aarch64-linux-android/python-config.py\" \"$@\"\n",
        encoding="utf-8",
    )
    os.chmod(config_entry, 0o755)

    result = {
        "schema_version": 1,
        "normalization_kind": "relocation-aware-runtime-and-on-device-sdk",
        "sysconfigdata": {"path": sysdata.relative_to(install).as_posix(), "before_sha256": before_sysdata, "after_sha256": sha256_file(sysdata), "dynamic_prefix": True},
        "sysconfig_vars_json": {"path": sysvars.relative_to(install).as_posix(), "after_sha256": sha256_file(sysvars), "path_semantics": "${prefix}-relative"},
        "makefile": _normalize_makefile(makefile),
        "python_config": {"path": python_config.relative_to(install).as_posix(), "before_sha256": _text_sha(before_config), "after_sha256": sha256_file(python_config), "shebang": None},
        "python_config_entry": {"path": config_entry.relative_to(install).as_posix(), "sha256": sha256_file(config_entry), "dynamic_bindir": True},
        "pkgconfig": _normalize_pkgconfig(install / "lib/pkgconfig"),
        "build_details": _normalize_build_details(build_details),
    }
    for path in (sysdata, sysvars, makefile, python_config, build_details, config_entry, *(install / "lib/pkgconfig").glob("*.pc")):
        if path.is_file() and any(root.encode() in path.read_bytes() for root in PRODUCER_ROOTS):
            raise RuntimeError(f"producer path remains in active metadata: {path}")
    return result
