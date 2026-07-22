#!/usr/bin/env python3
"""Minimal consumer metadata adaptation over upstream CPython metadata.

The upstream producer records remain present and truthful. Only the measured
consumer paths and on-device compiler entry points required by RB-3 profile M
are overlaid. Portable wheel ELF cleanup is deliberately out of scope here.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from archive import sha256_file, write_json

PYTHON_MM = "3.14"
TARGET_TRIPLE = "aarch64-linux-android"
CANONICAL_HEADER = "# system configuration generated and used by the sysconfig module"
PRODUCER_ROOTS = ("/Users/runner/", "/home/runner/", "/data/data/com.termux/", "/usr/local")

CFLAGS = "-fno-strict-overflow -Wsign-compare -Wunreachable-code -DNDEBUG -O2 -Wall -D__BIONIC_NO_PAGE_SIZE_MACRO"
LDFLAGS = "-Wl,--build-id=sha1 -Wl,--no-rosegment -Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384"


def _text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _base_dictionary_updates() -> dict[str, str]:
    """Return the bounded values that must survive uv's sysconfig rewrite.

    uv parses and rewrites only the literal ``build_time_vars = {...}`` mapping.
    Therefore static toolchain policy and ``/install`` placeholders must live in
    that mapping. The direct-runtime overlay below only resolves those
    placeholders for an unpacked standalone tree; uv intentionally discards the
    executable overlay and replaces ``/install`` itself at managed install time.
    """
    ldshared = "clang -shared " + LDFLAGS
    ldcxxshared = "clang++ -shared " + LDFLAGS
    return {
        "BINDIR": "/install/bin",
        "BINLIBDEST": "/install/lib/python3.14",
        "LIBDEST": "/install/lib/python3.14",
        "SCRIPTDIR": "/install/lib",
        "INCLUDEDIR": "/install/include",
        "CONFINCLUDEDIR": "/install/include",
        "INCLUDEPY": "/install/include/python3.14",
        "CONFINCLUDEPY": "/install/include/python3.14",
        "LIBDIR": "/install/lib",
        "LIBPL": "/install/lib/python3.14/config-3.14-aarch64-linux-android",
        "DESTSHARED": "/install/lib/python3.14/lib-dynload",
        "CC": "clang",
        "CXX": "clang++",
        "AR": "llvm-ar",
        "ARFLAGS": "rcs",
        "CCSHARED": "-fPIC",
        "CFLAGS": CFLAGS,
        "PY_CFLAGS": CFLAGS,
        "PY_STDMODULE_CFLAGS": CFLAGS + " -fPIC",
        "CPPFLAGS": "",
        "PY_CPPFLAGS": "",
        "LDFLAGS": LDFLAGS,
        "PY_LDFLAGS": LDFLAGS,
        "PY_CORE_LDFLAGS": LDFLAGS,
        "LDSHARED": ldshared,
        "BLDSHARED": ldshared,
        "LINKCC": "clang",
        "LDCXXSHARED": ldcxxshared,
        "BLDLIBRARY": "-L /install/lib -lpython3.14",
        "LIBPYTHON": "",
        "SHELL": "sh -e",
        "HW_T_METADATA_PROFILE": "upstream-preserved-minimal-consumer-overlay",
        "HW_T_CROSS_BUILD_SDK": "unavailable-without-explicit-ndk-authority",
    }


def _minimal_dynamic_overlay() -> str:
    """Resolve ``/install`` placeholders for direct standalone execution.

    This code is deliberately outside the literal mapping. Direct execution
    evaluates it; uv managed installation rewrites the literal mapping and
    omits this code after replacing ``/install`` with the managed prefix.
    """
    return r'''

# BEGIN HW-T DIRECT-RUNTIME PATH RESOLUTION — E3 selected profile M
import os as _hw_os
_hw_prefix = _hw_os.path.dirname(_hw_os.path.dirname(_hw_os.path.dirname(_hw_os.path.abspath(__file__))))
_hw_lib = _hw_os.path.join(_hw_prefix, "lib")
_hw_stdlib = _hw_os.path.join(_hw_lib, "python3.14")
_hw_include = _hw_os.path.join(_hw_prefix, "include", "python3.14")
_hw_config = _hw_os.path.join(_hw_stdlib, "config-3.14-aarch64-linux-android")
build_time_vars.update({
    "BINDIR": _hw_os.path.join(_hw_prefix, "bin"),
    "BINLIBDEST": _hw_stdlib,
    "LIBDEST": _hw_stdlib,
    "SCRIPTDIR": _hw_lib,
    "INCLUDEDIR": _hw_os.path.join(_hw_prefix, "include"),
    "CONFINCLUDEDIR": _hw_os.path.join(_hw_prefix, "include"),
    "INCLUDEPY": _hw_include,
    "CONFINCLUDEPY": _hw_include,
    "LIBDIR": _hw_lib,
    "LIBPL": _hw_config,
    "DESTSHARED": _hw_os.path.join(_hw_stdlib, "lib-dynload"),
    "BLDLIBRARY": "-L" + _hw_lib + " -lpython3.14",
})
del _hw_config, _hw_include, _hw_stdlib, _hw_lib, _hw_prefix, _hw_os
# END HW-T DIRECT-RUNTIME PATH RESOLUTION
'''


def _literal_sysconfigdata(text: str) -> dict[str, Any]:
    import ast

    tree = ast.parse(text)
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == "build_time_vars":
            values = ast.literal_eval(node.value)
            if not isinstance(values, dict):
                break
            if not all(isinstance(key, str) and isinstance(value, (str, int)) for key, value in values.items()):
                raise RuntimeError("sysconfig mapping contains unsupported uv parser value types")
            return dict(values)
    raise RuntimeError("literal build_time_vars mapping missing")


def _render_literal_sysconfigdata(values: dict[str, Any]) -> str:
    rows = [CANONICAL_HEADER, "build_time_vars = {"]
    for key in sorted(values):
        value = values[key]
        if not isinstance(key, str) or not isinstance(value, (str, int)):
            raise RuntimeError(f"unsupported sysconfig value: {key}={type(value).__name__}")
        rows.append(f"    {key!r}: {value!r},")
    rows.append("}")
    return "\n".join(rows) + "\n"


def _execute_sysconfigdata(path: Path) -> dict[str, Any]:
    namespace: dict[str, Any] = {"__file__": str(path)}
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)  # noqa: S102
    values = namespace.get("build_time_vars")
    if not isinstance(values, dict):
        raise RuntimeError(f"build_time_vars missing: {path}")
    return values


def _overlay_sysconfigdata(path: Path) -> dict[str, Any]:
    before_text = path.read_text(encoding="utf-8")
    before_lines = before_text.splitlines()
    if not before_lines or before_lines[0] != CANONICAL_HEADER:
        raise RuntimeError("minimal profile M requires canonical upstream sysconfig header")
    before_vars = _execute_sysconfigdata(path)
    base_vars = _literal_sysconfigdata(before_text)
    updates = _base_dictionary_updates()
    base_vars.update(updates)
    rendered = _render_literal_sysconfigdata(base_vars) + _minimal_dynamic_overlay()
    compile(rendered, str(path), "exec")
    path.write_text(rendered, encoding="utf-8")
    after_vars = _execute_sysconfigdata(path)
    managed_visible = _literal_sysconfigdata(rendered)
    preserved = {
        key: before_vars.get(key) == after_vars.get(key)
        for key in ("CONFIG_ARGS", "BUILD_GNU_TYPE", "HOST_GNU_TYPE", "SOABI", "MULTIARCH", "EXT_SUFFIX", "ANDROID_API_LEVEL")
    }
    if not all(preserved.values()):
        raise RuntimeError(f"profile M changed producer/target identity: {preserved}")
    for key, expected in updates.items():
        if managed_visible.get(key) != expected:
            raise RuntimeError(f"uv-visible profile M value mismatch: {key}")
    return {
        "path": path.name,
        "before_sha256": _text_sha(before_text),
        "after_sha256": sha256_file(path),
        "canonical_header_preserved": True,
        "producer_and_target_identity_preserved": preserved,
        "effective_metadata_profile": after_vars.get("HW_T_METADATA_PROFILE"),
        "uv_managed_rewrite_compatible": True,
        "literal_mapping_mutated_keys": sorted(updates),
        "direct_runtime_path_resolution": True,
    }


def _patch_makefile_minimal(path: Path) -> dict[str, Any]:
    original = path.read_text(encoding="utf-8")
    overrides = {
        "CC": "clang", "CXX": "clang++", "AR": "llvm-ar", "ARFLAGS": "rcs", "SHELL": "sh -e",
        "CFLAGS": CFLAGS, "PY_CFLAGS": "$(CFLAGS)", "CPPFLAGS": "", "PY_CPPFLAGS": "",
        "LDFLAGS": LDFLAGS, "PY_LDFLAGS": "$(LDFLAGS)", "PY_CORE_LDFLAGS": "$(LDFLAGS)",
        "LDSHARED": "clang -shared $(LDFLAGS)", "BLDSHARED": "clang -shared $(LDFLAGS)",
        "BLDLIBRARY": "-L$(LIBDIR) -lpython3.14",
    }
    output: list[str] = []
    seen: set[str] = set()
    for line in original.splitlines():
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not match:
            output.append(line)
            continue
        key = match.group(1)
        if key == "prefix":
            output.append("prefix := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../..)")
            seen.add(key)
        elif key in overrides:
            output.append(f"{key}=\t\t{overrides[key]}")
            seen.add(key)
        else:
            output.append(line)
    for key, value in overrides.items():
        if key not in seen:
            output.append(f"{key}=\t\t{value}")
    path.write_text("\n".join(output) + "\n", encoding="utf-8")
    after = path.read_text(encoding="utf-8")
    return {
        "path": path.name,
        "before_sha256": _text_sha(original),
        "after_sha256": sha256_file(path),
        "dynamic_prefix": True,
        "producer_provenance_rows_preserved": "consumer-normalized-binary-derived" not in after,
        "overridden_keys": sorted(overrides),
    }


def _patch_pkgconfig(pkgdir: Path) -> list[dict[str, Any]]:
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
                lines.append(line)
        after = "\n".join(lines) + "\n"
        path.write_text(after, encoding="utf-8")
        rows.append({
            "path": path.name,
            "before_sha256": _text_sha(before),
            "after_sha256": sha256_file(path),
            "prefix": "${pcfiledir}/../..",
        })
    return rows


def _patch_build_details(path: Path) -> dict[str, Any]:
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
    return {
        "before_sha256": _text_sha(before_text),
        "after_sha256": sha256_file(path),
        "path_semantics": "relative-to-runtime-root",
    }


def _patch_python_config(path: Path) -> dict[str, Any]:
    before = path.read_text(encoding="utf-8")
    lines = before.splitlines()
    if lines and lines[0].startswith("#!"):
        lines = lines[1:]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(path, 0o644)
    return {
        "path": path.name,
        "before_sha256": _text_sha(before),
        "after_sha256": sha256_file(path),
        "shebang": None,
    }


def normalize_runtime_metadata(install: Path) -> dict[str, Any]:
    stdlib = install / "lib/python3.14"
    sysdata_candidates = sorted(stdlib.glob("_sysconfigdata_*.py"))
    sysvars_candidates = sorted(stdlib.glob("_sysconfig_vars_*.json"))
    if len(sysdata_candidates) != 1 or len(sysvars_candidates) != 1:
        raise RuntimeError("expected exactly one sysconfigdata and sysconfig vars file")
    sysdata = sysdata_candidates[0]
    sysvars = sysvars_candidates[0]
    config_dir = stdlib / "config-3.14-aarch64-linux-android"
    makefile = config_dir / "Makefile"
    python_config = config_dir / "python-config.py"
    build_details = stdlib / "build-details.json"
    required = (sysdata, sysvars, makefile, python_config, build_details)
    if not all(path.is_file() for path in required):
        raise RuntimeError("upstream consumer metadata surface is incomplete")

    sysvars_before = sha256_file(sysvars)
    sysdata_row = _overlay_sysconfigdata(sysdata)
    makefile_row = _patch_makefile_minimal(makefile)
    python_config_row = _patch_python_config(python_config)
    pkgconfig_rows = _patch_pkgconfig(install / "lib/pkgconfig")
    build_details_row = _patch_build_details(build_details)

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

    effective = _execute_sysconfigdata(sysdata)
    expected_paths = {
        "BINDIR": install / "bin",
        "LIBDIR": install / "lib",
        "LIBDEST": install / "lib/python3.14",
        "INCLUDEPY": install / "include/python3.14",
        "LIBPL": config_dir,
        "DESTSHARED": install / "lib/python3.14/lib-dynload",
    }
    for key, expected in expected_paths.items():
        if effective.get(key) != str(expected):
            raise RuntimeError(f"effective consumer path mismatch: {key}={effective.get(key)!r} expected={str(expected)!r}")
    if effective.get("CC") != "clang" or effective.get("HW_T_METADATA_PROFILE") != "upstream-preserved-minimal-consumer-overlay":
        raise RuntimeError("minimal consumer overlay did not become effective")
    if any(root in config_entry.read_text(encoding="utf-8") for root in PRODUCER_ROOTS):
        raise RuntimeError("python config entry contains stale operational path")
    for row in pkgconfig_rows:
        path = install / "lib/pkgconfig" / row["path"]
        if any(root in path.read_text(encoding="utf-8") for root in PRODUCER_ROOTS):
            raise RuntimeError(f"pkg-config consumer surface contains stale path: {path}")

    return {
        "schema_version": 2,
        "normalization_kind": "upstream-preserved-minimal-consumer-overlay",
        "selected_profile": "M",
        "producer_provenance_preserved": True,
        "user_built_wheel_postprocessing": "out-of-scope-external-tool-responsibility",
        "sysconfigdata": {"path": sysdata.relative_to(install).as_posix(), **sysdata_row},
        "sysconfig_vars_json": {
            "path": sysvars.relative_to(install).as_posix(),
            "before_sha256": sysvars_before,
            "after_sha256": sha256_file(sysvars),
            "mutation": "preserved-upstream-byte-exact",
        },
        "makefile": makefile_row,
        "python_config": python_config_row,
        "python_config_entry": {
            "path": config_entry.relative_to(install).as_posix(),
            "sha256": sha256_file(config_entry),
            "dynamic_bindir": True,
        },
        "pkgconfig": pkgconfig_rows,
        "build_details": build_details_row,
        "effective_consumer": {
            "path_semantics": "relative-to-install-root",
            "paths": {
                key: "<install>/" + expected.relative_to(install).as_posix()
                for key, expected in expected_paths.items()
            },
            "CC": effective.get("CC"),
            "CXX": effective.get("CXX"),
            "AR": effective.get("AR"),
            "CFLAGS": effective.get("CFLAGS"),
            "LDFLAGS": effective.get("LDFLAGS"),
            "SOABI": effective.get("SOABI"),
            "MULTIARCH": effective.get("MULTIARCH"),
            "EXT_SUFFIX": effective.get("EXT_SUFFIX"),
            "HOST_GNU_TYPE": effective.get("HOST_GNU_TYPE"),
        },
        "preserved_producer": {
            "BUILD_GNU_TYPE": effective.get("BUILD_GNU_TYPE"),
            "CONFIG_ARGS": effective.get("CONFIG_ARGS"),
        },
    }
