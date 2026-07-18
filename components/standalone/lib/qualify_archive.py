#!/usr/bin/env python3
"""Execute archive-only E2-P3 qualification against the frozen E2-P2 envelope."""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

RESULT_NAME = "qualification-result.json"
ARTIFACT_ID = "cpython-3.14.6-aarch64-linux-android24-install_only_stripped"
ARCHIVE_NAME = f"{ARTIFACT_ID}.tar.zst"
SIDECAR_NAMES = {
    "artifact": f"{ARTIFACT_ID}.artifact.json",
    "manifest": f"{ARTIFACT_ID}.manifest.json",
    "provenance": f"{ARTIFACT_ID}.provenance.json",
    "qualification": f"{ARTIFACT_ID}.qualification.json",
    "licenses": f"{ARTIFACT_ID}.licenses.json",
}
CLAIM_BOUNDARY = {
    "combined_target_qualification": False,
    "installer_conversion": False,
    "metadata_finalization": False,
    "publication": False,
    "selectability": False,
    "transition_behavior": False,
}


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def read_json(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON is not an object: {path}")
    if raw != canonical_json_bytes(value):
        raise ValueError(f"JSON is not canonical: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_ref(path: Path) -> dict[str, Any]:
    return {"filename": path.name, "sha256": sha256_file(path), "size": path.stat().st_size}


def safe_relative(path: str, root_name: str) -> bool:
    if not path or path.startswith("/") or "\\" in path or "\x00" in path:
        return False
    parts = PurePosixPath(path).parts
    return bool(parts) and parts[0] == root_name and all(part not in {"", ".", ".."} for part in parts)


def safe_symlink_target(member_path: str, target: str, root_name: str) -> bool:
    if not target or target.startswith("/") or "\\" in target or "\x00" in target:
        return False
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
    return bool(resolved) and resolved[0] == root_name


def run(argv: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


def acquire_authority(contract: dict[str, Any], authority_root: Path, no_acquire: bool) -> None:
    if no_acquire:
        return
    remote = contract["input_authority"]["private_authority_remote"]
    temp = authority_root.with_name(authority_root.name + ".incoming")
    if temp.exists():
        shutil.rmtree(temp)
    temp.mkdir(parents=True)
    proc = run(["rclone", "copy", remote, str(temp)], authority_root.parent, timeout=1800)
    if proc.returncode != 0:
        raise RuntimeError(f"authority acquisition failed: {proc.stderr.strip()}")
    if authority_root.exists():
        shutil.rmtree(authority_root)
    temp.replace(authority_root)


def verify_authority(root: Path, contract: dict[str, Any], authority_root: Path) -> dict[str, Any]:
    index_path = authority_root / "authority-index.json"
    expected_index = contract["input_authority"]["private_authority_index_sha256"]
    if not index_path.is_file() or sha256_file(index_path) != expected_index:
        raise ValueError("private authority index identity mismatch")
    index = read_json(index_path)
    files = index.get("files", {})
    if not isinstance(files, dict) or len(files) != 18:
        raise ValueError("private authority indexed file set mismatch")
    mismatched: list[str] = []
    for rel, ref in files.items():
        path = authority_root / rel
        if not path.is_file() or sha256_file(path) != ref.get("sha256") or path.stat().st_size != ref.get("size"):
            mismatched.append(rel)
    if mismatched:
        raise ValueError(f"private authority file identities mismatch: {mismatched}")
    execution = read_json(root / contract["input_authority"]["execution_authority"])
    if execution.get("status") != contract["input_authority"]["execution_authority_status"]:
        raise ValueError("execution authority status mismatch")
    if execution.get("private_authority", {}).get("index_sha256") != expected_index:
        raise ValueError("execution authority private index mismatch")
    artifact = contract["artifact"]
    archive = authority_root / "envelope" / ARCHIVE_NAME
    release_index = authority_root / "envelope/release-index.json"
    if sha256_file(archive) != artifact["archive_sha256"] or archive.stat().st_size != 9933746:
        raise ValueError("envelope archive identity mismatch")
    if sha256_file(release_index) != artifact["release_index_sha256"]:
        raise ValueError("release index identity mismatch")
    return {
        "schema_version": 1,
        "pass": True,
        "authority_index": file_ref(index_path),
        "authority_kind": index.get("authority_kind"),
        "file_count": len(files) + 2,
        "archive": file_ref(archive),
        "release_index": file_ref(release_index),
        "execution_authority_status": execution.get("status"),
    }


def manifest_rows(authority_root: Path) -> list[dict[str, Any]]:
    manifest = read_json(authority_root / "envelope" / SIDECAR_NAMES["manifest"])
    rows = manifest.get("entries", [])
    if not isinstance(rows, list) or len(rows) != 1169:
        raise ValueError("manifest entry count mismatch")
    return rows


def inspect_archive(archive_path: Path, expected_rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected_names = [row["path"] for row in expected_rows]
    proc = subprocess.Popen(["zstd", "-q", "-d", "-c", str(archive_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.stdout is None:
        raise RuntimeError("zstd stdout unavailable")
    observed: list[dict[str, Any]] = []
    try:
        with tarfile.open(fileobj=proc.stdout, mode="r|") as archive:
            for member in archive:
                if not safe_relative(member.name, "python"):
                    raise ValueError(f"unsafe archive path: {member.name}")
                if member.islnk() or member.isdev() or member.isfifo():
                    raise ValueError(f"forbidden archive member: {member.name}")
                row: dict[str, Any] = {"path": member.name, "mode": f"{member.mode:04o}"}
                if member.isdir():
                    row["type"] = "directory"
                elif member.isfile():
                    row["type"] = "regular"
                    stream = archive.extractfile(member)
                    if stream is None:
                        raise ValueError(f"missing regular stream: {member.name}")
                    digest = hashlib.sha256()
                    size = 0
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
                        size += len(block)
                    row.update(size=size, sha256=digest.hexdigest())
                elif member.issym():
                    if not safe_symlink_target(member.name, member.linkname, "python"):
                        raise ValueError(f"unsafe symlink: {member.name} -> {member.linkname}")
                    row.update(type="symlink", symlink_target=member.linkname)
                else:
                    raise ValueError(f"unsupported archive member: {member.name}")
                observed.append(row)
    finally:
        proc.stdout.close()
    stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"zstd decompression failed: {stderr.strip()}")
    if [row["path"] for row in observed] != expected_names:
        raise ValueError("archive member order/path set mismatch")
    expected_by_path = {row["path"]: row for row in expected_rows}
    mismatched: list[str] = []
    for row in observed:
        expected = expected_by_path[row["path"]]
        keys = {"path", "type", "mode"}
        if row["type"] == "regular":
            keys |= {"size", "sha256"}
        elif row["type"] == "symlink":
            keys |= {"symlink_target"}
        if any(row.get(key) != expected.get(key) for key in keys):
            mismatched.append(row["path"])
    if mismatched:
        raise ValueError(f"archive/manifest mismatch: {mismatched[:10]}")
    counts = {kind: sum(row["type"] == kind for row in observed) for kind in ("directory", "regular", "symlink")}
    return {"schema_version": 1, "pass": True, "member_count": len(observed), "type_counts": counts, "member_order": "lexicographic", "mismatched": []}


def extract_archive(archive_path: Path, destination: Path) -> None:
    incoming = destination.with_name(destination.name + ".incoming")
    if incoming.exists():
        shutil.rmtree(incoming)
    incoming.mkdir(parents=True)
    proc = subprocess.Popen(["zstd", "-q", "-d", "-c", str(archive_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.stdout is None:
        raise RuntimeError("zstd stdout unavailable")
    try:
        with tarfile.open(fileobj=proc.stdout, mode="r|") as archive:
            for member in archive:
                if not safe_relative(member.name, "python"):
                    raise ValueError(f"unsafe archive path: {member.name}")
                if member.islnk() or member.isdev() or member.isfifo():
                    raise ValueError(f"forbidden archive member: {member.name}")
                target = incoming / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                if member.isdir():
                    target.mkdir(exist_ok=True)
                    os.chmod(target, member.mode, follow_symlinks=False)
                elif member.isfile():
                    stream = archive.extractfile(member)
                    if stream is None:
                        raise ValueError(f"missing regular stream: {member.name}")
                    with target.open("wb") as output:
                        shutil.copyfileobj(stream, output, length=1024 * 1024)
                    os.chmod(target, member.mode, follow_symlinks=False)
                elif member.issym():
                    if not safe_symlink_target(member.name, member.linkname, "python"):
                        raise ValueError(f"unsafe symlink: {member.name} -> {member.linkname}")
                    os.symlink(member.linkname, target)
                else:
                    raise ValueError(f"unsupported archive member: {member.name}")
    finally:
        proc.stdout.close()
    stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"zstd decompression failed: {stderr.strip()}")
    if destination.exists():
        shutil.rmtree(destination)
    incoming.replace(destination)


def snapshot(prefix_parent: Path) -> list[dict[str, Any]]:
    root = prefix_parent / "python"
    paths = [root, *root.rglob("*")]
    rows: list[dict[str, Any]] = []
    for path in sorted(paths, key=lambda p: "python" if p == root else f"python/{p.relative_to(root).as_posix()}"):
        rel = "python" if path == root else f"python/{path.relative_to(root).as_posix()}"
        observed = path.lstat()
        row: dict[str, Any] = {"path": rel, "mode": f"{stat.S_IMODE(observed.st_mode):04o}"}
        if stat.S_ISDIR(observed.st_mode):
            row["type"] = "directory"
        elif stat.S_ISREG(observed.st_mode):
            row.update(type="regular", size=observed.st_size, sha256=sha256_file(path))
        elif stat.S_ISLNK(observed.st_mode):
            row.update(type="symlink", symlink_target=os.readlink(path))
        else:
            row["type"] = "special"
        rows.append(row)
    return rows


def compare_snapshot(rows: list[dict[str, Any]], manifest: list[dict[str, Any]]) -> dict[str, Any]:
    expected = []
    for row in manifest:
        keys = {"path", "type", "mode"}
        if row["type"] == "regular":
            keys |= {"size", "sha256"}
        elif row["type"] == "symlink":
            keys |= {"symlink_target"}
        expected.append({key: row.get(key) for key in keys})
    return {
        "pass": rows == expected,
        "entry_count": len(rows),
        "expected_entry_count": len(expected),
        "pycache_paths": [row["path"] for row in rows if "__pycache__" in PurePosixPath(row["path"]).parts or row["path"].endswith((".pyc", ".pyo"))],
        "special_paths": [row["path"] for row in rows if row["type"] == "special"],
        "fingerprint": hashlib.sha256(canonical_json_bytes(rows)).hexdigest(),
    }


def sanitized_env(home: Path) -> dict[str, str]:
    env = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "LD_PRELOAD", "SSL_CERT_FILE"):
        env.pop(name, None)
    env.update({
        "HOME": str(home),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "UV_CACHE_DIR": str(home / ".cache/uv"),
        "UV_PYTHON_DOWNLOADS": "never",
        "UV_NO_PROGRESS": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
    })
    return env


def run_json_python(python: Path, code: str, cwd: Path, env: dict[str, str], timeout: int = 180) -> dict[str, Any]:
    proc = run([str(python), "-B", "-c", code], cwd, env, timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"target Python probe failed ({proc.returncode}): {proc.stderr.strip()}")
    value = json.loads(proc.stdout)
    if not isinstance(value, dict):
        raise ValueError("target Python probe did not return an object")
    return value


IDENTITY_CODE = r'''
import json, os, platform, subprocess, sys, sysconfig
imports={}
for name in ("ssl","sqlite3","bz2","ctypes","lzma","zlib"):
    try:
        __import__(name); imports[name]=True
    except Exception as exc:
        imports[name]=f"{type(exc).__name__}: {exc}"
tags=[]
child_code="import json,sys;print(json.dumps({'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix},sort_keys=True))"
child=json.loads(subprocess.check_output([sys.executable,"-B","-c",child_code],text=True))
print(json.dumps({
 "executable":sys.executable,"prefix":sys.prefix,"base_prefix":sys.base_prefix,
 "exec_prefix":sys.exec_prefix,"base_exec_prefix":sys.base_exec_prefix,
 "version_info":list(sys.version_info[:3]),"platform":sys.platform,"machine":platform.machine(),
 "soabi":sysconfig.get_config_var("SOABI"),"multiarch":sysconfig.get_config_var("MULTIARCH"),
 "sysconfig_platform":sysconfig.get_platform(),"sysconfig_paths":sysconfig.get_paths(),
 "sys_path":sys.path,"wheel_tags":tags,"imports":imports,"child":child,
},sort_keys=True))
'''


def path_within(value: Any, root: Path) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        Path(value).resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def lexical_same_path(value: Any, expected: Path) -> bool:
    if not isinstance(value, str) or not value:
        return False
    return os.path.abspath(value) == os.path.abspath(os.fspath(expected))


def has_wheel_platform_tag(tags: Any, platform_tag: str) -> bool:
    return (
        isinstance(tags, list)
        and bool(platform_tag)
        and any(isinstance(tag, str) and tag.endswith("-" + platform_tag) for tag in tags)
    )


def resolve_readelf() -> str:
    explicit = os.environ.get("ANDROID_READELF", "")
    if explicit and Path(explicit).is_file():
        return explicit
    home = Path.home()
    roots = [
        Path(os.environ[name]) for name in ("ANDROID_NDK_ROOT", "ANDROID_NDK_HOME") if os.environ.get(name)
    ] + [home / "opt/android-ndk-r27d"]
    for root in roots:
        for tag in ("linux-arm64", "linux-x86_64"):
            candidate = root / f"toolchains/llvm/prebuilt/{tag}/bin/llvm-readelf"
            if candidate.is_file():
                return str(candidate)
    for candidate in ("llvm-readelf", "readelf"):
        found = shutil.which(candidate)
        if found:
            return found
    raise FileNotFoundError("llvm-readelf/readelf not found")


def is_elf(path: Path) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    with path.open("rb") as stream:
        return stream.read(4) == b"\x7fELF"


def closure_probe(prefix: Path, python: Path, cwd: Path, env: dict[str, str], expected_system: list[str]) -> dict[str, Any]:
    readelf = resolve_readelf()
    elf_paths = [path for path in sorted(prefix.rglob("*")) if is_elf(path)]
    sonames: dict[str, str] = {}
    edges: list[dict[str, str]] = []
    errors: list[str] = []
    for path in elf_paths:
        proc = run([readelf, "-d", str(path)], cwd, env)
        if proc.returncode != 0:
            errors.append(f"{path}: {proc.stderr.strip()}")
            continue
        for line in proc.stdout.splitlines():
            match = re.search(r"\(SONAME\).*\[(.*?)\]", line)
            if match:
                sonames[match.group(1)] = path.relative_to(prefix).as_posix()
            match = re.search(r"\(NEEDED\).*\[(.*?)\]", line)
            if match:
                edges.append({"object": path.relative_to(prefix).as_posix(), "soname": match.group(1)})
    internal_names = {edge["soname"] for edge in edges if edge["soname"] in sonames or (prefix / "lib" / edge["soname"]).exists()}
    external_names = sorted({edge["soname"] for edge in edges if edge["soname"] not in internal_names})
    load_code = "import ctypes,json; names=" + repr(expected_system) + "; out={};\nfor n in names:\n\n try: ctypes.CDLL(n); out[n]=True\n except Exception as e: out[n]=f'{type(e).__name__}: {e}'\nprint(json.dumps(out,sort_keys=True))"
    loads = run_json_python(python, load_code, cwd, env)
    return {
        "schema_version": 1,
        "pass": not errors and len(elf_paths) == 81 and len(edges) == 329 and len({e['soname'] for e in edges}) == 9 and external_names == expected_system and all(value is True for value in loads.values()),
        "readelf": readelf,
        "elf_count": len(elf_paths),
        "needed_edge_count": len(edges),
        "needed_sonames": sorted({e["soname"] for e in edges}),
        "internal_sonames": sorted(internal_names),
        "external_sonames": external_names,
        "system_loadability": loads,
        "errors": errors,
    }


def extension_probe(prefix: Path, python: Path, cwd: Path, env: dict[str, str]) -> dict[str, Any]:
    discovery_code = r"""
import importlib.machinery, json, pathlib, sys, sysconfig
raw=[]
for entry in sys.path:
    if entry and pathlib.Path(entry).name == 'lib-dynload': raw.append(('sys.path', pathlib.Path(entry)))
raw.append(('sys.base_prefix-derived', pathlib.Path(sys.base_prefix)/f'lib/python{sys.version_info.major}.{sys.version_info.minor}/lib-dynload'))
platstdlib=sysconfig.get_path('platstdlib')
if platstdlib: raw.append(('sysconfig.platstdlib-derived', pathlib.Path(platstdlib)/'lib-dynload'))
seen=set(); candidates=[]
for method,path in raw:
    key=str(path)
    if key not in seen:
        seen.add(key); candidates.append({'method':method,'path':key,'is_dir':path.is_dir()})
selected=next((row for row in candidates if row['is_dir']), None)
print(json.dumps({'selected':selected,'candidates':candidates,'suffixes':list(importlib.machinery.EXTENSION_SUFFIXES)},sort_keys=True))
"""
    discovery = run_json_python(python, discovery_code, cwd, env)
    selected = discovery.get("selected")
    if not isinstance(selected, dict) or not selected.get("is_dir"):
        raise RuntimeError("active extension directory was not discovered")
    extension_dir = Path(str(selected["path"]))
    try:
        extension_dir.resolve().relative_to(prefix.resolve())
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"extension directory escapes prefix: {extension_dir}") from exc
    suffixes = [value for value in discovery.get("suffixes", []) if isinstance(value, str) and value]
    candidates: list[str] = []
    for path in sorted(extension_dir.iterdir(), key=lambda item: item.name):
        if not path.is_file():
            continue
        module = next((path.name[:-len(suffix)] for suffix in sorted(suffixes, key=len, reverse=True) if path.name.endswith(suffix)), None)
        if module:
            candidates.append(module)
    outcomes: list[dict[str, Any]] = []
    probe_code = "import importlib,sys; module=importlib.import_module(sys.argv[1]); print(getattr(module,'__file__','<built-in>'))"
    for name in candidates:
        child = run([str(python), "-I", "-B", "-S", "-c", probe_code, name], cwd, env, 90)
        outcomes.append({"module": name, "returncode": child.returncode, "stdout": child.stdout.strip(), "stderr": child.stderr.strip()})
    return {
        "schema_version": 1,
        "pass": len(candidates) == 67 and all(row["returncode"] == 0 for row in outcomes),
        "extension_dir": str(extension_dir),
        "extension_dir_discovery_method": selected.get("method"),
        "discovery_candidates": discovery.get("candidates", []),
        "candidate_count": len(candidates),
        "pass_count": sum(row["returncode"] == 0 for row in outcomes),
        "failed": [row for row in outcomes if row["returncode"] != 0],
        "modules": candidates,
    }


def https_probe(python: Path, cwd: Path, env: dict[str, str], url: str) -> dict[str, Any]:
    code = r'''
import json, ssl, time, urllib.request
url=%r
last=""
for attempt in range(1,4):
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            print(json.dumps({"status":response.status,"url":response.geturl(),"attempt":attempt,"default_paths":ssl.get_default_verify_paths()._asdict()},sort_keys=True)); raise SystemExit
    except Exception as exc:
        last=f"{type(exc).__name__}: {exc}"; time.sleep(attempt)
print(json.dumps({"status":None,"url":url,"attempt":3,"error":last,"default_paths":ssl.get_default_verify_paths()._asdict()},sort_keys=True))
''' % url
    result = run_json_python(python, code, cwd, env, 150)
    result.update({"schema_version": 1, "pass": result.get("status") == 200})
    return result


def wheel_record_hash(data: bytes) -> str:
    return "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")


def build_fixture_wheel(path: Path) -> None:
    files: dict[str, bytes] = {
        "e2p3_fixture/__init__.py": b"VALUE = 'e2p3-offline-wheel'\n",
        "e2p3_fixture-1.0.dist-info/METADATA": b"Metadata-Version: 2.1\nName: e2p3-fixture\nVersion: 1.0\n\n",
        "e2p3_fixture-1.0.dist-info/WHEEL": b"Wheel-Version: 1.0\nGenerator: hw-t\nRoot-Is-Purelib: true\nTag: py3-none-any\n\n",
    }
    record_name = "e2p3_fixture-1.0.dist-info/RECORD"
    rows = [f"{name},{wheel_record_hash(data)},{len(data)}" for name, data in sorted(files.items())]
    rows.append(f"{record_name},,")
    files[record_name] = ("\n".join(rows) + "\n").encode()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)


def venv_pip_uv_probe(prefix: Path, python: Path, cwd: Path, env: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    cwd.mkdir(parents=True, exist_ok=True)
    fixture = cwd / "e2p3_fixture-1.0-py3-none-any.whl"
    build_fixture_wheel(fixture)
    venv_dir = cwd / "venv"
    proc = run([str(python), "-B", "-m", "venv", "--clear", str(venv_dir)], cwd, env, 300)
    vpy = venv_dir / "bin/python"
    identity: dict[str, Any] = {}
    wheel_tags: list[str] = []
    if proc.returncode == 0 and vpy.is_file():
        identity = run_json_python(vpy, "import json,sys;print(json.dumps({'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix},sort_keys=True))", cwd, env)
        tag_probe = run_json_python(
            vpy,
            "from pip._vendor.packaging.tags import sys_tags; import json; print(json.dumps({'wheel_tags':[str(tag) for _,tag in zip(range(50),sys_tags())]},sort_keys=True))",
            cwd,
            env,
        )
        wheel_tags = [tag for tag in tag_probe.get("wheel_tags", []) if isinstance(tag, str)]
    venv_result = {
        "schema_version": 1,
        "pass": (
            proc.returncode == 0
            and vpy.is_file()
            and lexical_same_path(identity.get("executable"), vpy)
            and lexical_same_path(identity.get("prefix"), venv_dir)
            and Path(identity.get("base_prefix", "")).resolve() == prefix.resolve()
        ),
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip(),
        "identity": identity,
        "wheel_tags": wheel_tags,
        "wheel_tag_source": "created-venv-pip-vendored-packaging",
    }
    pip_proc = run([str(vpy), "-B", "-m", "pip", "install", "--no-index", "--no-deps", "--force-reinstall", str(fixture)], cwd, env, 300) if vpy.is_file() else subprocess.CompletedProcess([], 99, "", "venv missing")
    pip_import = run([str(vpy), "-B", "-c", "import e2p3_fixture; print(e2p3_fixture.VALUE)"], cwd, env) if vpy.is_file() else subprocess.CompletedProcess([], 99, "", "venv missing")
    pip_result = {
        "schema_version": 1,
        "pass": pip_proc.returncode == 0 and pip_import.returncode == 0 and pip_import.stdout.strip() == "e2p3-offline-wheel",
        "install_returncode": pip_proc.returncode,
        "import_returncode": pip_import.returncode,
        "import_stdout": pip_import.stdout.strip(),
        "install_stderr": pip_proc.stderr.strip(),
        "wheel": file_ref(fixture),
    }
    uv = shutil.which("uv")
    uv_dir = cwd / "uv-venv"
    uv_rows: dict[str, Any] = {"uv": uv}
    if uv:
        version = run([uv, "--version"], cwd, env)
        create = run([uv, "venv", "--python", str(python), "--clear", str(uv_dir)], cwd, env, 600)
        uvpy = uv_dir / "bin/python"
        install = run([uv, "pip", "install", "--python", str(uvpy), "--offline", "--no-deps", str(fixture)], cwd, env, 600) if uvpy.is_file() else subprocess.CompletedProcess([], 99, "", "uv venv missing")
        imported = run([str(uvpy), "-B", "-c", "import e2p3_fixture; print(e2p3_fixture.VALUE)"], cwd, env) if uvpy.is_file() else subprocess.CompletedProcess([], 99, "", "uv venv missing")
        run_probe = run([uv, "run", "--python", str(python), "--no-project", "--offline", "--", "python", "-B", "-c", "import json,sys;print(json.dumps({'executable':sys.executable,'base_prefix':sys.base_prefix},sort_keys=True))"], cwd, env, 600)
        run_identity = {}
        if run_probe.returncode == 0:
            try:
                run_identity = json.loads(run_probe.stdout)
            except json.JSONDecodeError:
                run_identity = {}
        uv_rows.update({
            "version": version.stdout.strip(),
            "venv_returncode": create.returncode,
            "install_returncode": install.returncode,
            "import_returncode": imported.returncode,
            "import_stdout": imported.stdout.strip(),
            "run_returncode": run_probe.returncode,
            "run_identity": run_identity,
            "stderr": "\n".join(x for x in (create.stderr.strip(), install.stderr.strip(), run_probe.stderr.strip()) if x),
        })
        uv_rows["venv_pass"] = create.returncode == 0 and uvpy.is_file()
        uv_rows["install_pass"] = install.returncode == 0 and imported.returncode == 0 and imported.stdout.strip() == "e2p3-offline-wheel"
        uv_rows["run_pass"] = run_probe.returncode == 0 and Path(run_identity.get("base_prefix", "")).resolve() == prefix.resolve()
    else:
        uv_rows.update(venv_pass=False, install_pass=False, run_pass=False, stderr="uv not found")
    uv_rows.update({"schema_version": 1, "pass": bool(uv_rows.get("venv_pass") and uv_rows.get("install_pass") and uv_rows.get("run_pass"))})
    return venv_result, pip_result, uv_rows


def host_probe(profile: str) -> dict[str, Any]:
    if profile == "static":
        return {"schema_version": 1, "host_role": "host-independent", "target_execution": False, "device_kind": "not-applicable"}
    def text(argv: list[str]) -> str:
        proc = run(argv, Path.cwd())
        return proc.stdout.strip() if proc.returncode == 0 else ""
    api_raw = text(["getprop", "ro.build.version.sdk"])
    qemu_values = [text(["getprop", key]).lower() for key in ("ro.kernel.qemu", "ro.boot.qemu", "ro.hardware")]
    emulator = any(value in {"1", "true"} or "ranchu" in value or "goldfish" in value for value in qemu_values)
    prefix = os.environ.get("PREFIX", "")
    return {
        "schema_version": 1,
        "host_role": "termux",
        "project_role": os.environ.get("PROJECT_ROLE", ""),
        "target_execution": True,
        "device_kind": "emulator" if emulator else "real",
        "android_api": int(api_raw) if api_raw.isdigit() else None,
        "machine": text(["uname", "-m"]),
        "prefix": prefix,
        "termux_prefix": prefix.endswith("/com.termux/files/usr"),
        "qemu_observations": qemu_values,
    }


def run_static_verifier(root: Path, authority_root: Path) -> dict[str, Any]:
    verifier = root / "components/standalone/lib/verify_envelope.py"
    release_dir = authority_root / "envelope"
    proc = run([sys.executable, str(verifier), "--root", str(root), "--release-dir", str(release_dir)], root, timeout=600)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {}
    return {"schema_version": 1, "pass": proc.returncode == 0 and data.get("pass") is True and data.get("check_count") == 52, "returncode": proc.returncode, "verifier": data, "stderr": proc.stderr.strip()}


def qualify(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    contract = read_json(args.contract.resolve())
    profile = args.profile
    expected_checks = contract["profile_checks"][profile]
    output_dir = args.output_dir.resolve()
    evidence_dir = output_dir / "evidence"
    work_root = args.work_root.resolve()
    authority_root = args.authority_root.resolve() if args.authority_root else work_root / "authority"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    evidence_dir.mkdir(parents=True)
    work_root.mkdir(parents=True, exist_ok=True)

    acquire_authority(contract, authority_root, args.no_acquire)
    archive = authority_root / "envelope" / ARCHIVE_NAME
    archive_before = sha256_file(archive)
    authority_evidence = verify_authority(root, contract, authority_root)
    write_json(evidence_dir / "authority.json", authority_evidence)
    static_evidence = run_static_verifier(root, authority_root)
    write_json(evidence_dir / "static-envelope.json", static_evidence)
    manifest = manifest_rows(authority_root)
    archive_evidence = inspect_archive(archive, manifest)

    location_a = work_root / "location-a"
    extract_archive(archive, location_a)
    snap_a_before = snapshot(location_a)
    fidelity_a_before = compare_snapshot(snap_a_before, manifest)
    extraction_a = {**archive_evidence, "location": str(location_a / "python"), "manifest_fidelity": fidelity_a_before}
    write_json(evidence_dir / "extraction-a.json", extraction_a)

    checks: dict[str, bool] = {name: False for name in expected_checks}
    checks.update({
        "authority_index_identity": authority_evidence["authority_index"]["sha256"] == contract["input_authority"]["private_authority_index_sha256"],
        "authority_files_exact": authority_evidence.get("pass") is True,
        "execution_authority_identity": authority_evidence.get("execution_authority_status") == contract["input_authority"]["execution_authority_status"],
        "envelope_static_verifier": static_evidence.get("pass") is True,
        "archive_sha256": archive_before == contract["artifact"]["archive_sha256"],
        "release_index_sha256": authority_evidence["release_index"]["sha256"] == contract["artifact"]["release_index_sha256"],
        "archive_safe": archive_evidence.get("pass") is True,
        "manifest_exact_location_a": fidelity_a_before.get("pass") is True,
    })

    observations: dict[str, Any] = {"manifest_entry_count": len(manifest)}
    host = host_probe(profile)
    if profile == "static":
        fidelity = {
            "schema_version": 1,
            "pass": fidelity_a_before.get("pass") is True,
            "location_a_before": fidelity_a_before,
            "location_a_after": fidelity_a_before,
        }
        checks["input_archive_immutable"] = sha256_file(archive) == archive_before
        write_json(evidence_dir / "fidelity.json", fidelity)
    else:
        location_b = work_root / "location-b"
        extract_archive(archive, location_b)
        snap_b_before = snapshot(location_b)
        fidelity_b_before = compare_snapshot(snap_b_before, manifest)
        write_json(evidence_dir / "extraction-b.json", {**archive_evidence, "location": str(location_b / "python"), "manifest_fidelity": fidelity_b_before})
        prefix_a = location_a / "python"
        prefix_b = location_b / "python"
        py_a = prefix_a / "bin/python3.14"
        py_b = prefix_b / "bin/python3.14"
        isolated_home = work_root / "home"
        isolated_home.mkdir(parents=True, exist_ok=True)
        env = sanitized_env(isolated_home)
        identity_a = run_json_python(py_a, IDENTITY_CODE, work_root, env)
        identity_b = run_json_python(py_b, IDENTITY_CODE, work_root, env)
        write_json(evidence_dir / "identity-a.json", {"schema_version": 1, **identity_a})
        write_json(evidence_dir / "identity-b.json", {"schema_version": 1, **identity_b})
        write_json(evidence_dir / "host.json", host)

        required = contract["required_observations"]
        expected_a = py_a.resolve()
        expected_b = py_b.resolve()
        checks.update({
            "manifest_exact_location_b": fidelity_b_before.get("pass") is True,
            "device_android": identity_a.get("platform") == "android" and identity_b.get("platform") == "android",
            "device_api_floor": isinstance(host.get("android_api"), int) and host["android_api"] >= required["android_api_min"],
            "device_profile": host.get("host_role") == "termux" and host.get("project_role") == "termux" and host.get("termux_prefix") is True and host.get("device_kind") == ("real" if profile == "termux-real" else "emulator"),
            "direct_entrypoint_a": py_a.is_file() and Path(identity_a.get("executable", "")).resolve() == expected_a,
            "direct_entrypoint_b": py_b.is_file() and Path(identity_b.get("executable", "")).resolve() == expected_b,
            "runtime_identity_a": identity_a.get("version_info") == [3, 14, 6] and identity_a.get("machine") == required["architecture"] and identity_a.get("soabi") == required["soabi"] and identity_a.get("multiarch") == required["multiarch"] and Path(identity_a.get("prefix", "")).resolve() == prefix_a.resolve() and all(value is True for value in identity_a.get("imports", {}).values()),
            "runtime_identity_b": identity_b.get("version_info") == [3, 14, 6] and identity_b.get("machine") == required["architecture"] and identity_b.get("soabi") == required["soabi"] and identity_b.get("multiarch") == required["multiarch"] and Path(identity_b.get("prefix", "")).resolve() == prefix_b.resolve() and all(value is True for value in identity_b.get("imports", {}).values()),
            "child_identity": Path(identity_b.get("child", {}).get("executable", "")).resolve() == expected_b and Path(identity_b.get("child", {}).get("prefix", "")).resolve() == prefix_b.resolve(),
            "stale_prefix_absent": str(prefix_a) not in json.dumps(identity_b, sort_keys=True),
            "sysconfig_paths_relocated": identity_a.get("sysconfig_platform") == required["sysconfig_platform"] and identity_b.get("sysconfig_platform") == required["sysconfig_platform"] and all(path_within(value, prefix_a) for value in identity_a.get("sysconfig_paths", {}).values()) and all(path_within(value, prefix_b) for value in identity_b.get("sysconfig_paths", {}).values()),
        })

        closure = closure_probe(prefix_b, py_b, work_root, env, required["android_system_sonames"])
        write_json(evidence_dir / "closure.json", closure)
        checks.update({
            "elf_count_81": closure.get("elf_count") == contract["artifact"]["stripped_elf_count"],
            "needed_edges_329": closure.get("needed_edge_count") == required["elf_needed_edge_count"],
            "needed_sonames_9": len(closure.get("needed_sonames", [])) == required["needed_soname_count"],
            "elf_closure": closure.get("pass") is True and closure.get("external_sonames") == required["android_system_sonames"],
            "system_sonames_5_5": all(value is True for value in closure.get("system_loadability", {}).values()) and len(closure.get("system_loadability", {})) == 5,
        })
        extensions = extension_probe(prefix_b, py_b, work_root, env)
        write_json(evidence_dir / "extensions.json", extensions)
        checks["extension_imports_67_67"] = extensions.get("pass") is True and extensions.get("pass_count") == required["extension_import_count"]
        https = https_probe(py_b, work_root, env, args.https_url)
        write_json(evidence_dir / "https.json", https)
        checks["https_status_200"] = https.get("pass") is True
        venv, pip_result, uv = venv_pip_uv_probe(prefix_b, py_b, work_root / "consumer-probes", env)
        write_json(evidence_dir / "venv.json", venv)
        write_json(evidence_dir / "pip.json", pip_result)
        write_json(evidence_dir / "uv.json", uv)
        checks.update({
            "venv_relocation": venv.get("pass") is True,
            "pip_offline_wheel": pip_result.get("pass") is True,
            "uv_explicit_venv": uv.get("venv_pass") is True,
            "uv_explicit_install": uv.get("install_pass") is True,
            "uv_explicit_run": uv.get("run_pass") is True,
            "wheel_tag_android24": has_wheel_platform_tag(venv.get("wheel_tags"), required["wheel_platform_tag"]),
        })
        snap_a_after = snapshot(location_a)
        snap_b_after = snapshot(location_b)
        fidelity_a_after = compare_snapshot(snap_a_after, manifest)
        fidelity_b_after = compare_snapshot(snap_b_after, manifest)
        fidelity = {
            "schema_version": 1,
            "pass": fidelity_a_before.get("pass") is True and fidelity_b_before.get("pass") is True and snap_a_before == snap_a_after and snap_b_before == snap_b_after,
            "location_a_before": fidelity_a_before,
            "location_a_after": fidelity_a_after,
            "location_b_before": fidelity_b_before,
            "location_b_after": fidelity_b_after,
            "locations_byte_identical": snap_a_after == snap_b_after,
        }
        write_json(evidence_dir / "fidelity.json", fidelity)
        checks.update({
            "product_fidelity_locations": fidelity.get("pass") is True and fidelity.get("locations_byte_identical") is True,
            "no_pycache_mutation": not fidelity_a_after.get("pycache_paths") and not fidelity_b_after.get("pycache_paths"),
            "input_archive_immutable": sha256_file(archive) == archive_before,
        })
        observations.update({
            "android_api": host.get("android_api"),
            "device_kind": host.get("device_kind"),
            "elf_count": closure.get("elf_count"),
            "needed_edge_count": closure.get("needed_edge_count"),
            "extension_import_count": extensions.get("pass_count"),
            "https_status": https.get("status"),
            "uv_version": uv.get("version"),
        })

    evidence_refs = {path.name: file_ref(path) for path in sorted(evidence_dir.iterdir()) if path.is_file()}
    ordered_checks = {name: bool(checks.get(name, False)) for name in sorted(expected_checks)}
    failed = sorted(name for name, passed in ordered_checks.items() if not passed)
    passed = not failed
    result = {
        "schema_version": 1,
        "qualification_kind": "hw-t-standalone-archive-qualification-result",
        "contract_version": 1,
        "profile": profile,
        "artifact_id": ARTIFACT_ID,
        "input": {
            "archive_sha256": contract["artifact"]["archive_sha256"],
            "execution_authority": contract["input_authority"]["execution_authority"],
            "private_authority_index_sha256": contract["input_authority"]["private_authority_index_sha256"],
            "release_index_sha256": contract["artifact"]["release_index_sha256"],
        },
        "host": {key: value for key, value in host.items() if key != "schema_version"},
        "checks": ordered_checks,
        "check_count": len(ordered_checks),
        "pass_count": sum(ordered_checks.values()),
        "failed_checks": failed,
        "pass": passed,
        "status": "passed-individual-profile" if passed else "failed",
        "selectable": False,
        "observations": observations,
        "evidence": evidence_refs,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    write_json(output_dir / RESULT_NAME, result)
    verifier = root / "components/standalone/lib/verify_qualification_result.py"
    proc = run([sys.executable, str(verifier), "--root", str(root), "--contract", str(args.contract.resolve()), "--result-dir", str(output_dir)], root, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"independent qualification-result verification failed: {proc.stdout}\n{proc.stderr}")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cpython-android-qualify")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--profile", choices=("static", "termux-real", "termux-emulator"), required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--profile", choices=("static", "termux-real", "termux-emulator"), required=True)
    run_parser.add_argument("--authority-root", type=Path)
    run_parser.add_argument("--work-root", type=Path, required=True)
    run_parser.add_argument("--output-dir", type=Path, required=True)
    run_parser.add_argument("--no-acquire", action="store_true")
    run_parser.add_argument("--https-url", default="https://www.python.org/")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        contract = read_json(args.contract.resolve())
        if args.command == "plan":
            profile = contract["profiles"][args.profile]
            result = {
                "schema_version": 1,
                "operation": "archive-qualification",
                "profile": args.profile,
                "host_role": profile["host_role"],
                "target_execution": profile["target_execution"],
                "stable_command": contract["stable_command"],
                "input_authority": contract["input_authority"],
                "artifact": contract["artifact"],
                "required_checks": contract["profile_checks"][args.profile],
                "required_evidence": contract["profile_evidence"][args.profile],
                "selection_policy": contract["selection_policy"],
            }
        else:
            result = qualify(args)
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("pass", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
