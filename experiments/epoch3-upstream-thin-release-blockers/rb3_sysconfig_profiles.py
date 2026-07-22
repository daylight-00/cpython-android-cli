#!/usr/bin/env python3
"""Build bounded RB-3 sysconfig/SDK comparison profiles without selecting one."""
from __future__ import annotations

import ast
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "components/upstream-thin/lib"
import sys
sys.path.insert(0, str(LIB))
from archive import copy_entry, safe_extract_tar, sha256_file, write_json, write_tar_gz  # noqa: E402

CANONICAL_HEADER = "# system configuration generated and used by the sysconfig module"
PYTHON_MM = "3.14"
SYSDATA_REL = Path("lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py")
SYSVARS_REL = Path("lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json")
BUILD_DETAILS_REL = Path("lib/python3.14/build-details.json")
CONFIG_DIR_REL = Path("lib/python3.14/config-3.14-aarch64-linux-android")
MAKEFILE_REL = CONFIG_DIR_REL / "Makefile"
PYCONFIG_REL = CONFIG_DIR_REL / "python-config.py"
PC_RELS = (Path("lib/pkgconfig/python-3.14.pc"), Path("lib/pkgconfig/python-3.14-embed.pc"))
RESTORE_RELS = (SYSDATA_REL, SYSVARS_REL, BUILD_DETAILS_REL, MAKEFILE_REL, PYCONFIG_REL, *PC_RELS)


def parse_build_time_vars(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "build_time_vars" for t in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, dict):
                return value
    raise ValueError(f"build_time_vars not found: {path}")


def replace_header(path: Path) -> dict[str, str]:
    before = sha256_file(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError("empty _sysconfigdata_")
    lines[0] = CANONICAL_HEADER
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"before_sha256": before, "after_sha256": sha256_file(path)}


def copy_exact(source: Path, target: Path) -> dict[str, str]:
    before = sha256_file(target) if target.is_file() else None
    if target.exists() or target.is_symlink():
        target.unlink()
    copy_entry(source, target)
    return {"before_sha256": before, "after_sha256": sha256_file(target)}


def restore_upstream_metadata(official_prefix: Path, product_python: Path) -> list[dict[str, Any]]:
    rows = []
    for rel in RESTORE_RELS:
        source = official_prefix / rel
        target = product_python / rel
        if not source.is_file() or not target.is_file():
            raise ValueError(f"profile metadata missing: {rel}")
        row = {"path": rel.as_posix(), **copy_exact(source, target)}
        rows.append(row)
    return rows


def minimal_dynamic_block() -> str:
    # Core prefix values are still set by CPython sysconfig from sys.prefix. The
    # block below changes only measured consumer paths and on-device toolchain
    # policy. It deliberately preserves producer CONFIG_ARGS/BUILD_GNU_TYPE and
    # upstream target identity values.
    return r'''

# BEGIN HW-T MINIMAL CONSUMER OVERLAY — RB-3 boundary probe only
import os as _hw_os
_hw_prefix = _hw_os.path.dirname(_hw_os.path.dirname(_hw_os.path.dirname(_hw_os.path.abspath(__file__))))
_hw_lib = _hw_os.path.join(_hw_prefix, "lib")
_hw_stdlib = _hw_os.path.join(_hw_lib, "python3.14")
_hw_include = _hw_os.path.join(_hw_prefix, "include", "python3.14")
_hw_config = _hw_os.path.join(_hw_stdlib, "config-3.14-aarch64-linux-android")
_hw_ldflags = "-Wl,--build-id=sha1 -Wl,--no-rosegment -Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384"
_hw_cflags = "-fno-strict-overflow -Wsign-compare -Wunreachable-code -DNDEBUG -O2 -Wall -D__BIONIC_NO_PAGE_SIZE_MACRO"
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
    "CC": "clang", "CXX": "clang++", "AR": "llvm-ar", "ARFLAGS": "rcs", "CCSHARED": "-fPIC",
    "CFLAGS": _hw_cflags, "PY_CFLAGS": _hw_cflags, "PY_STDMODULE_CFLAGS": _hw_cflags + " -fPIC",
    "CPPFLAGS": "", "PY_CPPFLAGS": "", "LDFLAGS": _hw_ldflags, "PY_LDFLAGS": _hw_ldflags,
    "PY_CORE_LDFLAGS": _hw_ldflags, "LDSHARED": "clang -shared " + _hw_ldflags,
    "BLDSHARED": "clang -shared " + _hw_ldflags,
    "BLDLIBRARY": "-L" + _hw_lib + " -lpython3.14",
    "LIBPYTHON": "", "SHELL": "sh -e",
    "HW_T_METADATA_PROFILE": "rb3-minimal-consumer-overlay-probe",
    "HW_T_CROSS_BUILD_SDK": "unavailable-without-explicit-ndk-authority",
})
del _hw_config, _hw_include, _hw_stdlib, _hw_lib, _hw_prefix, _hw_cflags, _hw_ldflags, _hw_os
# END HW-T MINIMAL CONSUMER OVERLAY
'''


def apply_minimal_sysconfig_overlay(path: Path) -> dict[str, str]:
    before = sha256_file(path)
    source = path.read_text(encoding="utf-8")
    if source.splitlines()[0] != CANONICAL_HEADER:
        raise ValueError("minimal overlay requires canonical upstream header")
    source = source.rstrip() + "\n" + minimal_dynamic_block()
    compile(source, str(path), "exec")
    path.write_text(source, encoding="utf-8")
    return {"before_sha256": before, "after_sha256": sha256_file(path)}


def patch_makefile_minimal(path: Path) -> dict[str, str]:
    before = sha256_file(path)
    overrides = {
        "CC": "clang", "CXX": "clang++", "AR": "llvm-ar", "ARFLAGS": "rcs", "SHELL": "sh -e",
        "CFLAGS": "-fno-strict-overflow -Wsign-compare -Wunreachable-code -DNDEBUG -O2 -Wall -D__BIONIC_NO_PAGE_SIZE_MACRO",
        "PY_CFLAGS": "$(CFLAGS)", "CPPFLAGS": "", "PY_CPPFLAGS": "",
        "LDFLAGS": "-Wl,--build-id=sha1 -Wl,--no-rosegment -Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384",
        "PY_LDFLAGS": "$(LDFLAGS)", "PY_CORE_LDFLAGS": "$(LDFLAGS)",
        "LDSHARED": "clang -shared $(LDFLAGS)", "BLDSHARED": "clang -shared $(LDFLAGS)",
        "BLDLIBRARY": "-L$(LIBDIR) -lpython3.14",
    }
    out = []
    seen = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not m:
            out.append(line)
            continue
        key = m.group(1)
        if key == "prefix":
            out.append("prefix := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../..)")
            seen.add(key)
        elif key in overrides:
            out.append(f"{key}=\t\t{overrides[key]}")
            seen.add(key)
        else:
            out.append(line)
    for key, value in overrides.items():
        if key not in seen:
            out.append(f"{key}=\t\t{value}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return {"before_sha256": before, "after_sha256": sha256_file(path)}


def patch_python_pc(path: Path) -> dict[str, str]:
    before = sha256_file(path)
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("prefix="):
            out.append("prefix=${pcfiledir}/../..")
        elif "$(BLDLIBRARY)" in line:
            out.append(line.replace(" $(BLDLIBRARY)", ""))
        else:
            out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return {"before_sha256": before, "after_sha256": sha256_file(path)}


def patch_build_details(path: Path) -> dict[str, str]:
    before = sha256_file(path)
    data = json.loads(path.read_text(encoding="utf-8"))
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
    return {"before_sha256": before, "after_sha256": sha256_file(path)}


def patch_python_config(path: Path) -> dict[str, str]:
    before = sha256_file(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].startswith("#!"):
        lines = lines[1:]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(path, 0o644)
    return {"before_sha256": before, "after_sha256": sha256_file(path)}


def apply_profile(profile: str, official_prefix: Path, product_python: Path) -> dict[str, Any]:
    if profile == "C":
        return {"profile": profile, "mutations": []}
    if profile == "H":
        return {"profile": profile, "mutations": [{"path": SYSDATA_REL.as_posix(), **replace_header(product_python / SYSDATA_REL)}]}
    rows = restore_upstream_metadata(official_prefix, product_python)
    if profile == "U":
        return {"profile": profile, "mutations": rows}
    if profile != "M":
        raise ValueError(f"unknown profile: {profile}")
    extra = [
        {"path": SYSDATA_REL.as_posix(), **apply_minimal_sysconfig_overlay(product_python / SYSDATA_REL)},
        {"path": MAKEFILE_REL.as_posix(), **patch_makefile_minimal(product_python / MAKEFILE_REL)},
        {"path": PYCONFIG_REL.as_posix(), **patch_python_config(product_python / PYCONFIG_REL)},
        {"path": BUILD_DETAILS_REL.as_posix(), **patch_build_details(product_python / BUILD_DETAILS_REL)},
    ]
    for rel in PC_RELS:
        extra.append({"path": rel.as_posix(), **patch_python_pc(product_python / rel)})
    return {"profile": profile, "mutations": rows + extra}


def extract_official_from_full(full_archive: Path, work: Path, zstd: str = "zstd") -> Path:
    import subprocess
    work.mkdir(parents=True, exist_ok=True)
    tar_path = work / "full.tar"
    with tar_path.open("wb") as out:
        p = subprocess.run([zstd, "-q", "-d", "-c", str(full_archive)], stdout=out, stderr=subprocess.PIPE)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors="replace"))
    full_root = work / "full"
    safe_extract_tar(tar_path, full_root, "r:")
    candidates = sorted((full_root / "python/build/upstream/package").glob("python-3.14.6-aarch64-linux-android.tar.gz"))
    if len(candidates) != 1:
        raise ValueError("embedded official archive not found")
    official_root = work / "official"
    safe_extract_tar(candidates[0], official_root, "r:gz")
    prefix = official_root / "prefix"
    if not prefix.is_dir():
        raise ValueError("official prefix missing")
    return prefix


def build_profiles(install_archive: Path, full_archive: Path, output: Path, zstd: str = "zstd") -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rb3-profile-build-") as td:
        temp = Path(td)
        official_prefix = extract_official_from_full(full_archive, temp / "official-source", zstd)
        profiles = []
        for profile in ("C", "H", "U", "M"):
            root = temp / f"profile-{profile}"
            safe_extract_tar(install_archive, root, "r:gz")
            product = root / "python"
            if not product.is_dir():
                raise ValueError("install-only archive lacks python root")
            change = apply_profile(profile, official_prefix, product)
            archive = output / f"rb3-sysconfig-profile-{profile}.tar.gz"
            rows = write_tar_gz(product, archive)
            profiles.append({
                "id": profile,
                "archive": archive.name,
                "sha256": sha256_file(archive),
                "size_bytes": archive.stat().st_size,
                "member_count": len(rows),
                "header": (product / SYSDATA_REL).read_text(encoding="utf-8").splitlines()[0],
                "mutations": change["mutations"],
            })
    result = {"schema_version": 1, "profiles": profiles, "profile_selected": False}
    write_json(output / "profile-manifest.json", result)
    return result
