#!/usr/bin/env python3
"""Generate truthful Astral-style artifacts from the accepted official Android package."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import posixpath
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

VERSION = "3.14.6"
PYTHON_MM = "3.14"
TARGET = "aarch64-linux-android"
ANDROID_ABI = "arm64-v8a"
ANDROID_API = 24
WHEEL_PLATFORM = "android_24_arm64_v8a"
SYSCONFIG_PLATFORM = "android-24-arm64_v8a"
PACKAGE_NAME = "python-3.14.6-aarch64-linux-android.tar.gz"
PACKAGE_SHA256 = "38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5"
PACKAGE_SIZE = 22358404
UPSTREAM_AUTHORITY_SHA256 = "6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c"
ARTIFACT_STEM = "cpython-3.14.6+aarch64-linux-android24-upstream"


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_archive_member_name(path: str) -> str:
    if not path or path.startswith("/") or "\\" in path or "\x00" in path:
        raise ValueError(f"unsafe path: {path!r}")
    normalized = posixpath.normpath(path)
    if normalized == ".":
        return normalized
    if normalized == ".." or normalized.startswith("../"):
        raise ValueError(f"unsafe path component: {path!r}")
    parts = PurePosixPath(normalized).parts
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"unsafe path component: {path!r}")
    return normalized


def ensure_safe_relative(path: str) -> None:
    normalized = normalize_archive_member_name(path)
    if normalized == ".":
        raise ValueError(f"archive root marker is not a material path: {path!r}")


def safe_link_target(member_path: str, target: str) -> bool:
    if not target or target.startswith("/") or "\\" in target or "\x00" in target:
        return False
    member_parts = PurePosixPath(member_path).parts
    if not member_parts:
        return False
    root_component = member_parts[0]
    resolved = list(PurePosixPath(member_path).parent.parts)
    for part in PurePosixPath(target).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not resolved:
                return False
            resolved.pop()
        else:
            resolved.append(part)
    return bool(resolved) and resolved[0] == root_component


def safe_extract(archive_path: Path, destination: Path) -> list[dict[str, Any]]:
    destination.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    with tarfile.open(archive_path, "r:gz") as tf:
        members: list[tuple[tarfile.TarInfo, str]] = []
        names: set[str] = set()
        for m in tf.getmembers():
            name = normalize_archive_member_name(m.name)
            if name == ".":
                if not m.isdir():
                    raise ValueError("archive root member is not a directory")
                continue
            if name in names:
                raise ValueError(f"duplicate archive member: {name}")
            names.add(name)
            if m.islnk() or m.isdev() or m.isfifo():
                raise ValueError(f"unsupported archive member type: {name}")
            if not (m.isdir() or m.isfile() or m.issym()):
                raise ValueError(f"unsupported archive member type: {name}")
            if m.issym() and not safe_link_target(name, m.linkname):
                raise ValueError(f"unsafe symlink: {name} -> {m.linkname}")
            members.append((m, name))
        for m, name in members:
            dst = destination / name
            mode = stat.S_IMODE(m.mode)
            if m.isdir():
                dst.mkdir(parents=True, exist_ok=True)
                os.chmod(dst, mode, follow_symlinks=False)
                kind = "directory"
                digest = None
            elif m.isfile():
                dst.parent.mkdir(parents=True, exist_ok=True)
                source = tf.extractfile(m)
                if source is None:
                    raise ValueError(f"cannot read archive member: {m.name}")
                with dst.open("wb") as out:
                    shutil.copyfileobj(source, out)
                os.chmod(dst, mode, follow_symlinks=False)
                kind = "file"
                digest = sha256_file(dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(m.linkname, dst)
                kind = "symlink"
                digest = None
            rows.append(
                {
                    "path": name,
                    "type": kind,
                    "mode": f"0o{mode:o}",
                    "size": m.size,
                    "sha256": digest,
                    "linkname": m.linkname if m.issym() else None,
                }
            )
    return rows


def verify_against_ut0(extracted_rows: list[dict[str, Any]], expected_path: Path) -> dict[str, Any]:
    expected = load_json(expected_path)
    expected_rows = expected["members"]
    by_path = {r["path"]: r for r in extracted_rows}
    expected_by_path = {r["path"]: r for r in expected_rows}
    errors: list[str] = []
    if len(extracted_rows) != len(expected_rows):
        errors.append("archive-member-count-mismatch")
    if set(by_path) != set(expected_by_path):
        errors.append("archive-member-path-set-mismatch")
    for path in sorted(set(by_path) & set(expected_by_path)):
        got, want = by_path[path], expected_by_path[path]
        for key in ("type", "size", "sha256", "linkname"):
            if got.get(key) != want.get(key):
                errors.append(f"member-{key}-mismatch:{path}")
    return {
        "pass": not errors,
        "errors": errors,
        "member_count": len(extracted_rows),
        "expected_member_count": expected["archive_member_count"],
        "expected_manifest_sha256": expected["archive_member_manifest_sha256"],
        "expected_prefix_snapshot_sha256": expected["prefix_snapshot_sha256"],
    }


def copy_entry(src: Path, dst: Path) -> None:
    st = src.lstat()
    mode = stat.S_IMODE(st.st_mode)
    if stat.S_ISDIR(st.st_mode):
        dst.mkdir(parents=True, exist_ok=True)
        for child in sorted(src.iterdir(), key=lambda p: p.name):
            copy_entry(child, dst / child.name)
        os.chmod(dst, mode, follow_symlinks=False)
    elif stat.S_ISREG(st.st_mode):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst, follow_symlinks=False)
        os.chmod(dst, mode, follow_symlinks=False)
    elif stat.S_ISLNK(st.st_mode):
        target = os.readlink(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(target, dst)
    else:
        raise ValueError(f"unsupported filesystem entry: {src}")


def copy_tree_contents(src: Path, dst: Path) -> None:
    src_mode = stat.S_IMODE(src.lstat().st_mode)
    dst.mkdir(parents=True, exist_ok=True)
    for child in sorted(src.iterdir(), key=lambda p: p.name):
        copy_entry(child, dst / child.name)
    os.chmod(dst, src_mode, follow_symlinks=False)


def is_elf(path: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    with path.open("rb") as f:
        return f.read(4) == b"\x7fELF"


def strip_tree(root: Path, strip_tool: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in sorted(root.rglob("*"), key=lambda q: q.as_posix()):
        if not is_elf(p):
            continue
        rel = p.relative_to(root).as_posix()
        mode = stat.S_IMODE(p.stat().st_mode)
        before_size = p.stat().st_size
        before = sha256_file(p)
        proc = subprocess.run(
            [strip_tool, "--strip-unneeded", str(p)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"strip failed for {rel}: {proc.stderr.strip()}")
        os.chmod(p, mode)
        after = sha256_file(p)
        rows.append(
            {
                "path": f"python/{rel}",
                "before_sha256": before,
                "after_sha256": after,
                "before_size": before_size,
                "after_size": p.stat().st_size,
                "changed": before != after,
            }
        )
    if not rows:
        raise RuntimeError("no ELF files found for stripped flavor")
    return rows


def normalize_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (list, tuple)):
        return " ".join(str(x) for x in value)
    return str(value)


def link_rows(needed: list[str], providers: dict[str, Any], install_prefix: str = "install") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for soname in sorted(set(needed)):
        provider = providers.get(soname)
        if not isinstance(provider, dict):
            rows.append({"name": soname, "system": True})
            continue
        kind = provider.get("kind")
        if kind == "android-system":
            rows.append({"name": soname, "system": True})
        elif kind == "archive-member":
            paths = provider.get("paths") or []
            candidates = [p for p in paths if isinstance(p, str) and p.startswith("prefix/")]
            row: dict[str, Any] = {"name": soname, "system": False}
            if candidates:
                chosen = sorted(candidates, key=lambda p: (0 if p.endswith(soname) else 1, len(p), p))[0]
                row["path_dynamic"] = f"{install_prefix}/{chosen.removeprefix('prefix/')}"
            rows.append(row)
        else:
            rows.append({"name": soname, "system": True})
    return rows


def build_python_json(root: Path, install_tree: Path) -> dict[str, Any]:
    control = root / "experiments/epoch2-upstream-thin-control"
    sysc = load_json(control / "sysconfig-census.json")
    elf = load_json(control / "elf-and-extension-inventory.json")
    deps = load_json(control / "dependency-provider-map.json")
    prov = load_json(control / "provenance-map.json")
    build_details = sysc["build_details"][0]["data"]
    sysvars_path = install_tree / f"lib/python{PYTHON_MM}/_sysconfig_vars__android_aarch64-linux-android.json"
    sysvars_raw = load_json(sysvars_path)
    if isinstance(sysvars_raw, dict) and "build_time_vars" in sysvars_raw:
        sysvars_raw = sysvars_raw["build_time_vars"]
    if not isinstance(sysvars_raw, dict):
        raise ValueError("sysconfig vars JSON does not contain an object")
    config_vars = {str(k): normalize_string(v) for k, v in sorted(sysvars_raw.items())}

    ext_rows = {row["path"]: row for row in elf["elf_objects"]}
    providers = deps["providers"]
    extensions: dict[str, list[dict[str, Any]]] = {}
    for path in elf["native_extensions"]:
        rel = path.removeprefix("prefix/")
        filename = PurePosixPath(path).name
        module = filename.split(".cpython-")[0].split(".abi3")[0].split(".so")[0]
        row = ext_rows[path]
        candidate: dict[str, Any] = {
            "in_core": False,
            "init_fn": f"PyInit_{module}",
            "links": link_rows(row.get("needed", []), providers),
            "required": False,
            "shared_lib": f"install/{rel}",
            "variant": "shared-library",
        }
        extensions.setdefault(module, []).append(candidate)

    libpython = next((r for r in elf["elf_objects"] if r["path"] == f"prefix/lib/libpython{PYTHON_MM}.so"), None)
    if libpython is None:
        raise ValueError("official package does not contain expected shared libpython")

    impl = build_details["implementation"]
    iv = impl["version"]
    result: dict[str, Any] = {
        "version": 8,
        "target_triple": TARGET,
        "build_options": "",
        "python_tag": "cp314",
        "python_abi_tag": "cp314",
        "python_platform_tag": WHEEL_PLATFORM,
        "python_implementation_cache_tag": impl["cache_tag"],
        "python_implementation_hex_version": hex(int(impl["hexversion"])),
        "python_implementation_name": impl["name"],
        "python_implementation_version": [str(iv[k]) for k in ("major", "minor", "micro", "releaselevel", "serial")],
        "python_version": VERSION,
        "python_major_minor_version": PYTHON_MM,
        "python_paths": {
            "data": "install",
            "include": f"install/include/python{PYTHON_MM}",
            "platinclude": f"install/include/python{PYTHON_MM}",
            "platlib": f"install/lib/python{PYTHON_MM}/site-packages",
            "platstdlib": f"install/lib/python{PYTHON_MM}",
            "purelib": f"install/lib/python{PYTHON_MM}/site-packages",
            "stdlib": f"install/lib/python{PYTHON_MM}",
        },
        "python_paths_abstract": {
            "data": "{base}",
            "include": "{installed_base}/include/python{py_version_short}{abiflags}",
            "platinclude": "{installed_platbase}/include/python{py_version_short}{abiflags}",
            "platlib": "{platbase}/lib/python{py_version_short}{abi_thread}/site-packages",
            "platstdlib": "{platbase}/lib/python{py_version_short}{abi_thread}",
            "purelib": "{base}/lib/python{py_version_short}{abi_thread}/site-packages",
            "stdlib": "{installed_base}/lib/python{py_version_short}{abi_thread}",
        },
        "python_config_vars": config_vars,
        "python_exe": None,
        "python_stdlib_platform_config": f"install/lib/python{PYTHON_MM}/config-{PYTHON_MM}-{TARGET}",
        "python_stdlib_test_packages": ["test"],
        "python_suffixes": {
            "bytecode": [".pyc"],
            "debug_bytecode": [".pyc"],
            "extension": [sysc["selected_extension_suffix"], ".abi3.so", ".so"],
            "optimized_bytecode": [".pyc"],
            "source": [".py"],
        },
        "libpython_link_mode": "shared",
        "python_extension_module_loading": ["builtin", "shared-library"],
        "build_info": {
            "core": {
                "links": link_rows(libpython.get("needed", []), providers),
                "shared_lib": f"install/lib/libpython{PYTHON_MM}.so",
            },
            "extensions": dict(sorted(extensions.items())),
        },
        "licenses": ["PSF-2.0"],
        "license_path": f"install/lib/python{PYTHON_MM}/LICENSE.txt",
        "hw_t": {
            "schema_version": 1,
            "artifact_origin": "binary-derived-official-python-org",
            "official_package": {
                "filename": PACKAGE_NAME,
                "sha256": PACKAGE_SHA256,
                "size": PACKAGE_SIZE,
                "version": VERSION,
            },
            "target": {
                "android_abi": ANDROID_ABI,
                "android_api_min": ANDROID_API,
                "libc": "bionic",
                "sysconfig_platform": SYSCONFIG_PLATFORM,
                "wheel_platform_tag": WHEEL_PLATFORM,
            },
            "availability": {
                "python_exe": "unavailable-official-package",
                "core_object_files": "unavailable-official-package",
                "static_libpython": "unavailable-official-package",
                "extension_object_files": "unavailable-official-package",
                "static_dependency_archives": "unavailable-official-package",
                "relinkable_inittab": "unavailable-official-package",
                "optimization_profile": "not-evidenced",
                "bytecode_magic_number": "not-observed-without-target-runtime",
            },
            "claim_boundary": {
                "artifact_structure": True,
                "official_install_bytes": True,
                "android_runtime": False,
                "launcher": False,
                "relocation": False,
                "selectable": False,
                "publication": False,
            },
            "provenance": {
                "upstream_control_authority_sha256": UPSTREAM_AUTHORITY_SHA256,
                "source_tag": prov["cpython_source"]["tag"],
                "source_archive_sha256": prov["cpython_source"]["source_archive_sha256"],
            },
        },
    }
    return result


def mode_string(path: Path) -> str:
    return f"{stat.S_IMODE(path.lstat().st_mode):04o}"


def canonical_mode(value: Any) -> str:
    text = str(value)
    if text.startswith("0o"):
        parsed = int(text[2:], 8)
    else:
        parsed = int(text, 8)
    return f"{stat.S_IMODE(parsed):04o}"


def official_mode_overrides(extracted_rows: list[dict[str, Any]], artifact_prefix: str) -> dict[str, str]:
    ensure_safe_relative(artifact_prefix)
    overrides: dict[str, str] = {}
    for row in extracted_rows:
        source = row.get("path")
        if source == "prefix":
            destination = artifact_prefix
        elif isinstance(source, str) and source.startswith("prefix/"):
            destination = f"{artifact_prefix}/{source.removeprefix('prefix/')}"
        else:
            continue
        if destination in overrides:
            raise ValueError(f"duplicate official mode destination: {destination}")
        overrides[destination] = canonical_mode(row["mode"])
    if artifact_prefix not in overrides:
        raise ValueError("official prefix root mode is missing")
    return overrides


def tree_manifest(tree: Path, mode_overrides: dict[str, str] | None = None) -> list[dict[str, Any]]:
    if not tree.is_dir():
        raise ValueError(f"tree is not a directory: {tree}")
    overrides = mode_overrides or {}
    items = [tree, *tree.rglob("*")]
    rows: list[dict[str, Any]] = []
    observed_paths: set[str] = set()
    for p in sorted(items, key=lambda q: "python" if q == tree else f"python/{q.relative_to(tree).as_posix()}"):
        member = "python" if p == tree else f"python/{p.relative_to(tree).as_posix()}"
        ensure_safe_relative(member)
        observed_paths.add(member)
        st = p.lstat()
        row: dict[str, Any] = {"path": member, "mode": overrides.get(member, mode_string(p))}
        if stat.S_ISDIR(st.st_mode):
            row["type"] = "directory"
        elif stat.S_ISREG(st.st_mode):
            row.update(type="file", size=st.st_size, sha256=sha256_file(p))
        elif stat.S_ISLNK(st.st_mode):
            target = os.readlink(p)
            if not safe_link_target(member, target):
                raise ValueError(f"unsafe staged symlink: {member} -> {target}")
            row.update(type="symlink", linkname=target)
        else:
            raise ValueError(f"unsupported staged type: {p}")
        rows.append(row)
    missing_overrides = sorted(set(overrides) - observed_paths)
    if missing_overrides:
        raise ValueError(f"official mode override paths are missing from staged tree: {missing_overrides[:20]}")
    return rows


def tar_info(row: dict[str, Any]) -> tarfile.TarInfo:
    info = tarfile.TarInfo(row["path"])
    info.mode = int(row["mode"], 8)
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    info.pax_headers = {}
    if row["type"] == "directory":
        info.type = tarfile.DIRTYPE
        info.size = 0
    elif row["type"] == "file":
        info.type = tarfile.REGTYPE
        info.size = row["size"]
    elif row["type"] == "symlink":
        info.type = tarfile.SYMTYPE
        info.size = 0
        info.linkname = row["linkname"]
    else:
        raise ValueError(row["type"])
    return info


def write_tar(tree: Path, manifest: list[dict[str, Any]], tar_path: Path) -> None:
    with tar_path.open("wb") as raw, tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for row in manifest:
            info = tar_info(row)
            if row["type"] == "file":
                src = tree if row["path"] == "python" else tree / row["path"].removeprefix("python/")
                with src.open("rb") as f:
                    tf.addfile(info, f)
            else:
                tf.addfile(info)


def compress_zstd(tar_path: Path, destination: Path, zstd: str) -> dict[str, Any]:
    proc = subprocess.run([zstd, "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    version = proc.stdout.strip().splitlines()[0]
    subprocess.run([zstd, "-q", "-f", "-19", "-T1", "--check", "-o", str(destination), str(tar_path)], check=True)
    return {"format": "pax-tar+zstd", "tool": version, "level": 19, "threads": 1, "frame_checksum": True}


def compress_gzip(tar_path: Path, destination: Path) -> dict[str, Any]:
    with tar_path.open("rb") as src, destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as gz:
            shutil.copyfileobj(src, gz)
    return {"format": "pax-tar+gzip", "tool": f"python-gzip-{sys.version_info.major}.{sys.version_info.minor}", "level": 9, "mtime": 0, "filename_header": ""}


def file_ref(path: Path) -> dict[str, Any]:
    return {"filename": path.name, "sha256": sha256_file(path), "size": path.stat().st_size}


def write_full_build_metadata(full_root: Path, root: Path, archive: Path, sigstore: Path, python_json: dict[str, Any]) -> None:
    project = full_root / "build/project"
    upstream_package = full_root / "build/upstream/package"
    project.mkdir(parents=True, exist_ok=True)
    upstream_package.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(archive, upstream_package / archive.name)
    shutil.copyfile(sigstore, upstream_package / sigstore.name)
    os.chmod(upstream_package / archive.name, 0o644)
    os.chmod(upstream_package / sigstore.name, 0o644)

    control = root / "experiments/epoch2-upstream-thin-control"
    authority = load_json(control / "upstream-control-authority.json")
    prov = load_json(control / "provenance-map.json")
    dump_json(project / "provenance.json", {
        "schema_version": 1,
        "artifact_origin": "binary-derived-official-python-org",
        "official_package": file_ref(archive),
        "sigstore_bundle": file_ref(sigstore),
        "upstream_control_authority": {
            "sha256": UPSTREAM_AUTHORITY_SHA256,
            "official_input": authority["official_input"],
        },
        "cpython_source": prov["cpython_source"],
        "dependency_products": prov["dependencies"]["products"],
    })
    dump_json(project / "overlays.json", {
        "schema_version": 1,
        "overlays": [],
        "statement": "No project files are overlaid into python/install for UT-1.",
    })
    dump_json(project / "mutations.json", {
        "schema_version": 1,
        "binary_mutations": [],
        "path_transformations": [
            {"source": "prefix/", "destination": "python/install/", "kind": "archive-layout-only"}
        ],
        "statement": "The full and install_only flavors preserve official regular-file bytes; only archive paths and normalized tar headers change.",
    })
    dump_json(project / "qualification.json", {
        "schema_version": 1,
        "status": "not-run",
        "selectable": False,
        "checks": {"static_artifact": "prototype-only", "android_runtime": "not-run", "relocation": "not-run"},
        "next_gate": "E2-R1/UT-2",
    })
    dump_json(project / "licenses.json", {
        "schema_version": 1,
        "complete_for_payload": False,
        "known": [{"component": "CPython", "spdx": "PSF-2.0", "path": f"python/install/lib/python{PYTHON_MM}/LICENSE.txt"}],
        "limitation": "Dependency license identities require a later complete release inventory; no license is fabricated from filename heuristics.",
    })
    dump_json(project / "unavailable-fields.json", python_json["hw_t"]["availability"])


def artifact_contract() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "contract_kind": "e2-r1-ut1-astral-artifact-prototype",
        "canonical_full_root": {"root": "python/", "metadata": "python/PYTHON.json", "build": "python/build/", "install": "python/install/"},
        "flavors": {
            "full": {"required": True, "compression": "zstd", "self_describing": True, "install_bytes": "official-byte-exact"},
            "install_only": {"required": True, "compression": "gzip", "derivation": "rewrite python/install/* to python/*", "install_bytes": "official-byte-exact"},
            "install_only_stripped": {"required": True, "compression": "gzip", "derivation": "install_only plus recorded --strip-unneeded mutation", "install_bytes": "recorded-mutation"},
        },
        "selectable": False,
        "reason_unselectable": "The official package contains no interpreter executable; launcher, getpath, native loader, and relocation remain UT-2 work.",
        "forbidden_fabrications": ["core object files", "static libpython", "extension object lists", "static dependency archives", "relinkable inittab material", "interpreter executable"],
    }


def schema_mapping(python_json: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "mapping_kind": "astral-python-json-v8-to-official-android-package",
        "astral_format_version": 8,
        "field_sources": {
            "target_triple": "UT-0 selected_target",
            "python_tag": "CPython version deterministic derivation",
            "python_abi_tag": "CPython version and non-free-threaded ABI deterministic derivation",
            "python_platform_tag": "official build-details platform normalized to Android wheel platform syntax",
            "python_implementation_*": "official build-details.json",
            "python_paths": "observed prefix topology rewritten from python/install",
            "python_config_vars": "official _sysconfig_vars__android_aarch64-linux-android.json normalized to strings",
            "python_suffixes": "official sysconfig EXT_SUFFIX plus stable/generic suffixes",
            "libpython_link_mode": "observed packaged shared libpython",
            "build_info.core.shared_lib": "observed packaged shared libpython",
            "build_info.extensions.*.shared_lib": "UT-0 native extension inventory",
            "build_info.*.links": "UT-0 dependency-provider map",
            "licenses": "official CPython license file",
        },
        "project_extension_key": "hw_t",
        "python_exe": {"value": None, "availability": "unavailable-official-package", "must_not_be_fabricated": True},
        "prototype_python_json_sha256": sha256_bytes(canonical_json_bytes(python_json)),
    }


def unavailable_policy() -> dict[str, Any]:
    fields = {
        "python_exe": "null-with-hw_t-availability",
        "build_info.core.objs": "omit",
        "build_info.core.static_lib": "omit",
        "build_info.core.inittab_object": "omit",
        "build_info.core.inittab_source": "omit",
        "build_info.core.inittab_cflags": "omit",
        "build_info.extensions.*.objs": "omit",
        "build_info.extensions.*.static_lib": "omit",
        "python_bytecode_magic_number": "omit-not-observed",
        "crt_features": "omit-no-standard-Astral-Android-value",
        "run_tests": "omit-no-evidenced-compatible-script",
        "build_options": "empty-string-and-hw_t-not-evidenced",
    }
    return {
        "schema_version": 1,
        "policy_kind": "explicit-unavailable-field-policy",
        "fields": fields,
        "rules": [
            "Never synthesize a path to a file absent from the accepted package.",
            "Never translate a shared library into a static or object-file surface.",
            "Unknown and unavailable are distinct from false or empty producer output.",
            "A downstream consumer must inspect hw_t.availability before assuming Astral producer completeness.",
        ],
    }


def derivation_rules() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "rules_kind": "deterministic-artifact-derivation",
        "input": {"filename": PACKAGE_NAME, "sha256": PACKAGE_SHA256, "size": PACKAGE_SIZE},
        "normalization": {"member_order": "lexicographic", "mtime": 0, "uid": 0, "gid": 0, "uname": "", "gname": "", "hardlinks": "forbidden", "special_files": "forbidden"},
        "full": ["copy prefix/* to python/install/* byte-for-byte", "retain original archive and sigstore under python/build/upstream/package", "retain non-prefix extracted metadata under python/build/upstream/extracted-metadata", "generate only evidence-backed project metadata under python/build/project", "write python/PYTHON.json"],
        "install_only": ["copy prefix/* to python/* byte-for-byte", "exclude PYTHON.json and build area exactly as Astral install-only derivation"],
        "install_only_stripped": ["derive from install_only", "run one recorded strip --strip-unneeded operation per observed ELF regular file", "preserve non-ELF bytes and symlink topology"],
    }


def path_contract() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "full": {"archive_root": "python/", "metadata": "python/PYTHON.json", "install_root": "python/install/", "build_root": "python/build/"},
        "install_only": {"archive_root": "python/", "install_root": "python/", "contains_python_json": False, "contains_build_root": False},
        "install_only_stripped": {"archive_root": "python/", "install_root": "python/", "contains_python_json": False, "contains_build_root": False},
        "path_safety": {"absolute_paths": "forbidden", "dotdot_components": "forbidden", "hardlinks": "forbidden", "special_files": "forbidden", "symlinks": "relative-and-non-escaping"},
    }


def flavor_inputs(strip_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "decision_kind": "artifact-flavor-inputs-not-selection",
        "required": ["full", "install_only", "install_only_stripped"],
        "observations": {
            "official_package_has_python_executable": False,
            "official_package_has_shared_libpython": True,
            "official_package_has_static_libpython": False,
            "official_package_has_core_objects": False,
            "official_package_has_headers": True,
            "official_package_has_pkgconfig": True,
            "stripped_elf_count": len(strip_rows),
            "stripped_changed_count": sum(1 for r in strip_rows if r["changed"]),
        },
        "optional_proposals": {
            "symbols": {"status": "proposal-only", "reason": "No detached symbol producer is available from official package."},
            "debug": {"status": "proposal-only", "reason": "No debug producer artifact is available from official package."},
            "sdk": {"status": "proposal-only", "reason": "UT-3 must decide normalized on-device and cross-build SDK surfaces."},
        },
        "epoch3_selection": False,
    }


def consumer_contract() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "consumer_kind": "astral-style-prototype-extraction",
        "verification_order": ["verify archive SHA-256 and size", "verify exact member manifest", "reject unsafe member types and paths", "extract into staging", "for full read python/PYTHON.json and hw_t.availability before use", "treat all UT-1 flavors as unselectable"],
        "full": {"install_subdirectory": "python/install", "metadata_path": "python/PYTHON.json", "direct_runtime_entry": None},
        "install_only": {"install_subdirectory": "python", "metadata_external": True, "direct_runtime_entry": None},
        "install_only_stripped": {"install_subdirectory": "python", "metadata_external": True, "direct_runtime_entry": None},
        "must_reject": ["unknown manifest schema", "hash mismatch", "unsafe paths", "escaping symlink", "missing python root", "selectable=true", "invented python executable"],
        "claim_boundary": {"archive_extraction": True, "Android_execution": False, "relocation": False, "launcher": False, "product_selection": False},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--sigstore", type=Path, required=True)
    ap.add_argument("--work-dir", type=Path, required=True)
    ap.add_argument("--artifact-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--strip-tool", required=True)
    ap.add_argument("--zstd", default="zstd")
    args = ap.parse_args()

    root = args.root.resolve()
    archive = args.archive.resolve()
    sigstore = args.sigstore.resolve()
    work = args.work_dir.resolve()
    artifacts = args.artifact_dir.resolve()
    output = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    work.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)

    if sha256_file(archive) != PACKAGE_SHA256 or archive.stat().st_size != PACKAGE_SIZE:
        raise SystemExit("official archive identity mismatch")
    if not sigstore.is_file() or sigstore.stat().st_size == 0:
        raise SystemExit("sigstore bundle missing")

    extracted = work / "official-extracted"
    if extracted.exists():
        shutil.rmtree(extracted)
    rows = safe_extract(archive, extracted)
    verify = verify_against_ut0(rows, root / "experiments/epoch2-upstream-thin-control/package-and-file-hashes.json")
    dump_json(output / "official-extraction-verification.json", verify)
    if not verify["pass"]:
        raise SystemExit("official extraction does not match UT-0 authority")
    prefix = extracted / "prefix"
    if not prefix.is_dir():
        raise SystemExit("official package prefix is missing")
    if (prefix / "bin").exists():
        raise SystemExit("unexpected interpreter bin directory appeared; re-audit required")

    full_tree = work / "full/python"
    install_tree = work / "install-only/python"
    stripped_tree = work / "install-only-stripped/python"
    for p in (full_tree.parent, install_tree.parent, stripped_tree.parent):
        if p.exists():
            shutil.rmtree(p)
    full_tree.mkdir(parents=True)
    install_tree.mkdir(parents=True)
    stripped_tree.mkdir(parents=True)

    copy_tree_contents(prefix, full_tree / "install")
    copy_tree_contents(prefix, install_tree)
    copy_tree_contents(prefix, stripped_tree)

    python_json = build_python_json(root, full_tree / "install")
    dump_json(full_tree / "PYTHON.json", python_json)
    write_full_build_metadata(full_tree, root, archive, sigstore, python_json)
    metadata_root = full_tree / "build/upstream/extracted-metadata"
    metadata_root.mkdir(parents=True, exist_ok=True)
    for child in sorted(extracted.iterdir(), key=lambda p: p.name):
        if child.name == "prefix":
            continue
        copy_entry(child, metadata_root / child.name)

    strip_rows = strip_tree(stripped_tree, args.strip_tool)
    dump_json(output / "strip-mutations.json", {
        "schema_version": 1,
        "tool": args.strip_tool,
        "operation": "--strip-unneeded",
        "elf_count": len(strip_rows),
        "changed_count": sum(1 for r in strip_rows if r["changed"]),
        "rows": strip_rows,
        "claim_boundary": "Recorded binary mutation only; no runtime or relocation qualification.",
    })

    full_mode_overrides = official_mode_overrides(rows, "python/install")
    install_mode_overrides = official_mode_overrides(rows, "python")
    definitions = [
        ("full", full_tree, artifacts / f"{ARTIFACT_STEM}-full.tar.zst", "zstd", full_mode_overrides),
        ("install_only", install_tree, artifacts / f"{ARTIFACT_STEM}-install_only.tar.gz", "gzip", install_mode_overrides),
        ("install_only_stripped", stripped_tree, artifacts / f"{ARTIFACT_STEM}-install_only_stripped.tar.gz", "gzip", install_mode_overrides),
    ]
    artifact_rows: list[dict[str, Any]] = []
    for flavor, tree, archive_out, compression, mode_overrides in definitions:
        manifest = tree_manifest(tree, mode_overrides)
        dump_json(output / f"{flavor}.manifest.json", {"schema_version": 1, "flavor": flavor, "member_count": len(manifest), "members": manifest})
        tar_path = work / f"{flavor}.tar"
        write_tar(tree, manifest, tar_path)
        serialization = compress_zstd(tar_path, archive_out, args.zstd) if compression == "zstd" else compress_gzip(tar_path, archive_out)
        tar_path.unlink()
        artifact_rows.append({
            "flavor": flavor,
            "archive": file_ref(archive_out),
            "manifest": file_ref(output / f"{flavor}.manifest.json"),
            "serialization": serialization,
            "selectable": False,
        })

    dump_json(output / "PYTHON.json", python_json)
    dump_json(output / "artifact-contract.json", artifact_contract())
    dump_json(output / "python-json-schema-mapping.json", schema_mapping(python_json))
    dump_json(output / "unavailable-field-policy.json", unavailable_policy())
    dump_json(output / "deterministic-derivation-rules.json", derivation_rules())
    dump_json(output / "archive-root-and-path-contract.json", path_contract())
    dump_json(output / "artifact-flavor-decision-inputs.json", flavor_inputs(strip_rows))
    dump_json(output / "consumer-extraction-contract.json", consumer_contract())
    artifact_set = {
        "schema_version": 1,
        "artifact_set_kind": "e2-r1-ut1-local-prototype",
        "official_input": {"filename": PACKAGE_NAME, "sha256": PACKAGE_SHA256, "size": PACKAGE_SIZE},
        "artifacts": artifact_rows,
        "python_json": file_ref(output / "PYTHON.json"),
        "selectable": False,
        "publication": False,
    }
    dump_json(output / "artifact-set.json", artifact_set)
    sums = []
    for row in artifact_rows:
        sums.append((row["archive"]["filename"], row["archive"]["sha256"]))
    (artifacts / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(sums)), encoding="utf-8")
    dump_json(artifacts / "artifact-set.json", artifact_set)
    for name in (
        "PYTHON.json",
        "artifact-contract.json",
        "python-json-schema-mapping.json",
        "unavailable-field-policy.json",
        "deterministic-derivation-rules.json",
        "archive-root-and-path-contract.json",
        "artifact-flavor-decision-inputs.json",
        "consumer-extraction-contract.json",
        "artifact-set.json",
        "full.manifest.json",
        "install_only.manifest.json",
        "install_only_stripped.manifest.json",
        "strip-mutations.json",
    ):
        shutil.copyfile(output / name, artifacts / name)

    print(json.dumps({"pass": True, "artifacts": artifact_rows, "output_dir": str(output), "artifact_dir": str(artifacts)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
