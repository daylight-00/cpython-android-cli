#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
from typing import Any

EXPECTED_BRANCH = "agent/epoch2-p2-standalone-build-facade"
EXPECTED_HEAD = "5e8cd1bd1889817d8cdcd0dc4c96574515b6618a"
EXPECTED_TREE = "f72cebdd29e6c35c3944df7cef29c8bf3ce8dd22"
EXPECTED_MAIN = "b5a2ca39d1250122312355dd3dbc6165b9409786"
CORRECTION_COMMIT_SUBJECT = "fix: classify legacy setpwent cache adaptation"
CORRECTION_PATHS = {
    "docs/contracts/E2P2_TERMUX_NATIVE_CPYTHON3146_PRODUCER_AUTHORITY.md",
    "docs/evidence/E2P2_TERMUX_NATIVE_CPYTHON3146_AUTHORITY_OPENING.md",
    "docs/handoff/2026-07-17-e2p2-termux-native-cpython3146-authority-opening.md",
    "experiments/epoch2-termux-native-cpython3146-producer/README.md",
    "experiments/epoch2-termux-native-cpython3146-producer/authority-opening.json",
    "experiments/epoch2-termux-native-cpython3146-producer/preflight.py",
}
SOURCE_HEAD = "c63aec69bd59c55314c06c23f4c22c03de76fe45"
TARGET = "aarch64-linux-android"
API = 24
NDK_REVISION = "27.3.13750724"
ANDROID_PY_SHA = "1dfe8fe9f6187819f83319916f77e27eaf8df43a73a0696e31c3d9c0950fcd09"
ANDROID_ENV_SHA = "fbe3d49cfdf074d1aff493974b07f5781ce7eb8c9d6df6c7824674b16f94fe4e"
DEPENDENCY_LOCK_SHA = "8d414416de820271f06027e26bca612ca0dcb5a3dbfd144b7454663fa3985d21"
ADAPTER_SHA = "0566bc1a4fb44306c3130705c32a139693f6d2c953903909fd68b795682a59da"
TARGET_DRIVER_SHA = "551ef4280536d51df74cde88e5d29878e2e3e478e0bdba8ea12cbaf598f76eb2"
RESOLVED_CLANG_SHA = "d8e576c0fed9e2a0c13c01d92f8bc066a7d57a93fc5d46f6de2496460d4341ab"
ORIGINAL_LLD_SHA = "cf9f6f56dfcb286d52425a73f5ba7c7a17966cc2c71bea0ccb0f16c21d07b15b"
PATCHED_LLD_SHA = "eee71a33b1c9924eeb576673d033008b1e520f84a112a7102cc9482142bf5a09"
TLS_FIELD_OFFSET = 392
EXPECTED_RELEASE_TAGS = [
    "bzip2-1.0.8-3",
    "libffi-3.4.4-3",
    "openssl-3.5.7-0",
    "sqlite-3.50.4-0",
    "xz-5.4.6-1",
    "zstd-1.5.7-2",
]
LEGACY_INITIAL_OVERRIDES = {
    "fexecve", "getloadavg", "getlogin_r", "getpwent",
    "pthread_getname_np", "sem_clockwait", "setpwent",
}
LEGACY_MAPPED_OVERRIDES = LEGACY_INITIAL_OVERRIDES - {"setpwent"}
LEGACY_INERT_CACHE_OVERRIDES = {"setpwent"}
CPYTHON3145_A3_RESULT_SHA256 = "bfd241f959cb081a91f4866cb07cf2773d1028919de0ea0959ed0d95c8984202"
HOST_VISIBILITY_PROBES = {
    "sem_clockwait": "#define _GNU_SOURCE 1\n#include <semaphore.h>\n#include <time.h>\nint main(void){sem_t s; struct timespec ts={0}; return sem_clockwait(&s,CLOCK_MONOTONIC,&ts);}\n",
    "pthread_getname_np": "#define _GNU_SOURCE 1\n#include <pthread.h>\n#include <stddef.h>\nint main(void){char name[32]; return pthread_getname_np(pthread_self(),name,sizeof(name));}\n",
    "fexecve": "#define _GNU_SOURCE 1\n#include <unistd.h>\nint main(void){char *const a[]={0}; char *const e[]={0}; return fexecve(-1,a,e);}\n",
    "getloadavg": "#define _GNU_SOURCE 1\n#include <stdlib.h>\nint main(void){double v[3]; return getloadavg(v,3);}\n",
    "getlogin_r": "#define _GNU_SOURCE 1\n#include <unistd.h>\nint main(void){char b[64]; return getlogin_r(b,sizeof(b));}\n",
    "getpwent": "#define _GNU_SOURCE 1\n#include <pwd.h>\nint main(void){return getpwent()==0;}\n",
    "setpwent": "#define _GNU_SOURCE 1\n#include <pwd.h>\nint main(void){setpwent(); return 0;}\n",
}


def canonical(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_meta(path: pathlib.Path) -> dict[str, Any]:
    try:
        st = path.lstat()
    except FileNotFoundError:
        return {"path": str(path), "exists": False}
    out: dict[str, Any] = {
        "path": str(path),
        "exists": True,
        "mode": f"{stat.S_IMODE(st.st_mode):04o}",
        "size": st.st_size,
    }
    if path.is_symlink():
        out.update(type="symlink", target=os.readlink(path), resolved=str(path.resolve()))
    elif path.is_file():
        out.update(type="regular", sha256=sha256(path))
    elif path.is_dir():
        out["type"] = "directory"
    else:
        out["type"] = "other"
    return out


def git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def read_properties(path: pathlib.Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(errors="replace").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def parse_dependency_tags(android_py: pathlib.Path) -> list[str]:
    text = android_py.read_text(errors="replace")
    match = re.search(
        r"for\s+name_ver\s+in\s*\[(.*?)\]\s*:\s*\n",
        text,
        flags=re.S,
    )
    if not match:
        return []
    return re.findall(r"[\"']([^\"']+)[\"']", match.group(1))


def parse_elf_tls(path: pathlib.Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 64 or data[:4] != b"\x7fELF" or data[4] != 2:
        return {"elf": False, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    endian = "<" if data[5] == 1 else ">"
    phoff = struct.unpack_from(endian + "Q", data, 32)[0]
    phentsize, phnum = struct.unpack_from(endian + "HH", data, 54)
    tls = []
    for index in range(phnum):
        off = phoff + index * phentsize
        if off + 56 > len(data):
            break
        p_type = struct.unpack_from(endian + "I", data, off)[0]
        if p_type == 7:
            tls.append({
                "index": index,
                "header_offset": off,
                "p_align_offset": off + 48,
                "p_align": struct.unpack_from(endian + "Q", data, off + 48)[0],
            })
    return {"elf": True, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data), "tls": tls}


def choose_existing(candidates: list[pathlib.Path]) -> pathlib.Path | None:
    seen: set[str] = set()
    for candidate in candidates:
        text = str(candidate)
        if text in seen:
            continue
        seen.add(text)
        if candidate.is_dir():
            return candidate.resolve()
    return None


def command_probe(argv: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        return {"argv": argv, "returncode": proc.returncode, "output": proc.stdout}
    except Exception as exc:
        return {"argv": argv, "returncode": 98, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--authority-root", default=str(pathlib.Path.home() / ".cache/hw-t-authorities/cpython-android-cli/stage3b-producer-reacquired-v1"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    repo = pathlib.Path(args.root).resolve()
    authority_root = pathlib.Path(args.authority_root).resolve()
    output = pathlib.Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}
    errors: dict[str, str] = {}

    def safe(name: str, fn, default=None):
        try:
            return fn()
        except Exception as exc:
            errors[name] = f"{type(exc).__name__}: {exc}"
            return default

    repo_state = safe("repository", lambda: {
        "branch": git(repo, "branch", "--show-current"),
        "head": git(repo, "rev-parse", "HEAD"),
        "tree": git(repo, "rev-parse", "HEAD^{tree}"),
        "parent": git(repo, "rev-parse", "HEAD^"),
        "subject": git(repo, "log", "-1", "--format=%s"),
        "changed_paths": sorted(filter(None, git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines())),
        "status": git(repo, "status", "--porcelain=v1", "--untracked-files=all"),
        "remote_active": git(repo, "ls-remote", "origin", EXPECTED_BRANCH).split()[0],
        "remote_main": git(repo, "ls-remote", "origin", "refs/heads/main").split()[0],
    }, {})
    details["repository"] = repo_state
    # During the correction transaction, the replacement files are intentionally
    # present but uncommitted. Afterward, the direct correction commit is also an
    # accepted coordinate so the next clean-replay transaction can rerun preflight.
    base_coordinate = (
        repo_state.get("head") == EXPECTED_HEAD
        and repo_state.get("tree") == EXPECTED_TREE
        and repo_state.get("remote_active") == EXPECTED_HEAD
    )
    corrected_coordinate = (
        repo_state.get("parent") == EXPECTED_HEAD
        and repo_state.get("subject") == CORRECTION_COMMIT_SUBJECT
        and set(repo_state.get("changed_paths", [])) == CORRECTION_PATHS
        and repo_state.get("remote_active") == repo_state.get("head")
        and repo_state.get("status") == ""
    )
    checks["repository_coordinate_exact"] = (
        repo_state.get("branch") == EXPECTED_BRANCH
        and repo_state.get("remote_main") == EXPECTED_MAIN
        and (base_coordinate or corrected_coordinate)
    )

    source = authority_root / "source/cpython"
    source_state = safe("source", lambda: {
        "head": git(source, "rev-parse", "HEAD"),
        "status": git(source, "status", "--porcelain=v1", "--untracked-files=all"),
        "android_py": file_meta(source / "Android/android.py"),
        "android_env": file_meta(source / "Android/android-env.sh"),
    }, {})
    details["source"] = source_state
    checks["exact_source_reacquired"] = source_state.get("head") == SOURCE_HEAD and source_state.get("status") == ""
    checks["source_producer_files_exact"] = (
        source_state.get("android_py", {}).get("sha256") == ANDROID_PY_SHA
        and source_state.get("android_env", {}).get("sha256") == ANDROID_ENV_SHA
    )

    snapshot_root = repo / "experiments/bootstrap-android-build/android-python-work"
    snapshot = {
        "android_py": file_meta(snapshot_root / "android.py"),
        "android_env": file_meta(snapshot_root / "android-env.sh"),
    }
    details["tracked_source_snapshot"] = snapshot
    checks["tracked_snapshot_exact"] = (
        snapshot["android_py"].get("sha256") == ANDROID_PY_SHA
        and snapshot["android_env"].get("sha256") == ANDROID_ENV_SHA
    )
    checks["source_snapshot_match"] = safe(
        "source_snapshot_match",
        lambda: (source / "Android/android.py").read_bytes() == (snapshot_root / "android.py").read_bytes()
        and (source / "Android/android-env.sh").read_bytes() == (snapshot_root / "android-env.sh").read_bytes(),
        False,
    )

    dependency_lock_path = repo / "config/dependencies/android-source-deps-aarch64-linux-android.lock.json"
    dependency_lock = safe("dependency_lock", lambda: json.loads(dependency_lock_path.read_text()), {})
    details["dependency_lock"] = {"file": file_meta(dependency_lock_path), "content": dependency_lock}
    checks["dependency_lock_exact"] = (
        details["dependency_lock"]["file"].get("sha256") == DEPENDENCY_LOCK_SHA
        and dependency_lock.get("source_head") == SOURCE_HEAD
        and dependency_lock.get("target_host") == TARGET
    )
    source_tags = safe("source_dependency_tags", lambda: parse_dependency_tags(source / "Android/android.py"), [])
    lock_tags = [item.get("release_tag") for item in dependency_lock.get("products", [])]
    details["dependency_release_tags"] = {"source": source_tags, "lock": lock_tags, "expected": EXPECTED_RELEASE_TAGS}
    checks["dependency_model_exact"] = source_tags == EXPECTED_RELEASE_TAGS and lock_tags == EXPECTED_RELEASE_TAGS
    checks["dependency_identities_complete"] = all(
        item.get("source_url") and item.get("filename") and item.get("size_bytes", 0) > 0
        and re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", "")))
        for item in dependency_lock.get("products", [])
    ) and len(dependency_lock.get("products", [])) == 6

    frozen_lock_path = authority_root / "frozen/extracted/input/contract/input/phase3/input/manifest-schema/input/product-lock.json"
    frozen_lock = safe("frozen_product_lock", lambda: json.loads(frozen_lock_path.read_text()), {})
    details["frozen_product_lock"] = {"file": file_meta(frozen_lock_path), "content": frozen_lock}
    checks["frozen_product_lock_exact"] = (
        frozen_lock.get("python_version") == "3.14.6"
        and frozen_lock.get("source_head") == SOURCE_HEAD
        and frozen_lock.get("target_host") == TARGET
        and frozen_lock.get("android_api") == API
        and frozen_lock.get("ndk_version") == NDK_REVISION
        and frozen_lock.get("archive", {}).get("sha256") == "a16e0433b6f7e69c4634b52ce582d4d387447fbcfed797425f669ac224631f4f"
    )

    adapter = repo / "experiments/epoch2-termux-native-cpython3146-producer/android-shell-adapter.py"
    adapter_meta = file_meta(adapter)
    details["shell_adapter"] = adapter_meta
    checks["shell_adapter_exact"] = adapter_meta.get("sha256") == ADAPTER_SHA and os.access(adapter, os.X_OK)
    adapter_probe: dict[str, Any] = {}
    if checks["shell_adapter_exact"]:
        with tempfile.TemporaryDirectory(prefix="e2p2-adapter-") as td:
            probe_script = pathlib.Path(td) / "probe.py"
            probe_script.write_text(
                "import subprocess\n"
                "p=subprocess.run('export E2P2_ADAPTER=ok; export',shell=True,capture_output=True,text=True,check=True)\n"
                "print(p.stdout)\n"
            )
            env = os.environ.copy()
            env["A3_ANDROID_SHELL"] = shutil.which("bash") or "/data/data/com.termux/files/usr/bin/bash"
            proc = subprocess.run([sys.executable, str(adapter), str(probe_script)], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            adapter_probe = {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "shell": env["A3_ANDROID_SHELL"]}
    details["shell_adapter_probe"] = adapter_probe
    checks["shell_adapter_functional"] = adapter_probe.get("returncode") == 0 and "E2P2_ADAPTER" in adapter_probe.get("stdout", "")

    home = pathlib.Path.home()
    ndk_candidates = [
        pathlib.Path(os.environ.get("NDK", "")) if os.environ.get("NDK") else pathlib.Path("/__missing__"),
        pathlib.Path(os.environ.get("ANDROID_NDK_ROOT", "")) if os.environ.get("ANDROID_NDK_ROOT") else pathlib.Path("/__missing__"),
        home / "opt/android-ndk-r27d",
        home / "opt/android-sdk/ndk/27.3.13750724",
        home / "Android/Sdk/ndk/27.3.13750724",
    ]
    ndk = choose_existing(ndk_candidates)
    sdk_candidates = [
        pathlib.Path(os.environ.get("ANDROID_HOME", "")) if os.environ.get("ANDROID_HOME") else pathlib.Path("/__missing__"),
        pathlib.Path(os.environ.get("ANDROID_SDK_ROOT", "")) if os.environ.get("ANDROID_SDK_ROOT") else pathlib.Path("/__missing__"),
        home / "opt/android-sdk",
        home / "Android/Sdk",
    ]
    sdk = choose_existing(sdk_candidates)
    details["paths"] = {"authority_root": str(authority_root), "source": str(source), "ndk": str(ndk) if ndk else None, "sdk": str(sdk) if sdk else None}
    checks["authority_root_present"] = authority_root.is_dir()
    checks["android_sdk_present"] = sdk is not None
    checks["custom_ndk_present"] = ndk is not None

    ndk_details: dict[str, Any] = {}
    if ndk:
        props = read_properties(ndk / "source.properties")
        prebuilt = ndk / "toolchains/llvm/prebuilt/linux-arm64/bin"
        driver = prebuilt / f"{TARGET}{API}-clang"
        clang = prebuilt / "clang"
        resolved_clang = clang.resolve() if clang.exists() else clang
        lld = prebuilt / "lld"
        ndk_details = {
            "root": str(ndk), "properties": props,
            "driver": file_meta(driver), "driver_version": command_probe([str(driver), "--version"]) if driver.exists() else {},
            "clang": file_meta(clang), "resolved_clang": file_meta(resolved_clang),
            "lld": file_meta(lld), "lld_tls": parse_elf_tls(lld) if lld.is_file() else {},
        }
        checks["ndk_revision_exact"] = props.get("Pkg.Revision") == NDK_REVISION
        checks["target_driver_exact_and_executable"] = ndk_details["driver"].get("sha256") == TARGET_DRIVER_SHA and ndk_details["driver_version"].get("returncode") == 0
        checks["resolved_clang_exact"] = ndk_details["resolved_clang"].get("sha256") == RESOLVED_CLANG_SHA
        checks["original_lld_exact"] = ndk_details["lld"].get("sha256") == ORIGINAL_LLD_SHA
        with tempfile.TemporaryDirectory(prefix="e2p2-lld-") as td:
            patched = pathlib.Path(td) / "lld"
            if lld.is_file():
                data = bytearray(lld.read_bytes())
                before = data[TLS_FIELD_OFFSET] if len(data) > TLS_FIELD_OFFSET else None
                if before == 8:
                    data[TLS_FIELD_OFFSET] = 64
                    patched.write_bytes(data)
                    patch = {"offset": TLS_FIELD_OFFSET, "before": before, "after": 64, "sha256": sha256(patched), "tls": parse_elf_tls(patched)}
                else:
                    patch = {"offset": TLS_FIELD_OFFSET, "before": before, "after": None}
            else:
                patch = {"error": "lld-missing"}
        ndk_details["ephemeral_patch"] = patch
        checks["ephemeral_lld_patch_exact"] = patch.get("sha256") == PATCHED_LLD_SHA and patch.get("before") == 8 and patch.get("after") == 64
    else:
        for name in ("ndk_revision_exact", "target_driver_exact_and_executable", "resolved_clang_exact", "original_lld_exact", "ephemeral_lld_patch_exact"):
            checks[name] = False
    details["ndk"] = ndk_details

    tools = ["bash", "git", "curl", "make", "clang", "pkg-config", "tar", "zstd", "file", "sha256sum"]
    tool_paths = {name: shutil.which(name) for name in tools}
    details["host"] = {
        "platform": platform.platform(), "system": platform.system(), "machine": platform.machine(),
        "python": sys.version, "executable": sys.executable, "tools": tool_paths,
    }
    checks["termux_android_aarch64_host"] = platform.machine() == "aarch64" and bool(os.environ.get("TERMUX_VERSION") or "/data/data/com.termux/" in str(pathlib.Path.home()))
    checks["host_tools_present"] = all(tool_paths.values())
    free_bytes = shutil.disk_usage(home).free
    details["storage"] = {"path": str(home), "free_bytes": free_bytes}
    checks["minimum_storage_available"] = free_bytes >= 8 * 1024**3

    compiler = shutil.which("gcc") or shutil.which("clang")
    probe_rows: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []
    if compiler and source.is_dir():
        configure_text = (source / "configure").read_text(errors="replace")
        pyconfig_text = (source / "pyconfig.h.in").read_text(errors="replace")
        with tempfile.TemporaryDirectory(prefix="e2p2-host-probes-") as td:
            tdir = pathlib.Path(td)
            for name, code in HOST_VISIBILITY_PROBES.items():
                src = tdir / f"{name}.c"; obj = tdir / f"{name}.o"
                src.write_text(code)
                proc = subprocess.run([compiler, "-std=c11", "-Werror=implicit-function-declaration", "-c", str(src), "-o", str(obj)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                probe_rows.append({"function": name, "returncode": proc.returncode, "stderr": proc.stderr})
                macro = "HAVE_" + name.upper()
                mapping_rows.append({
                    "function": name,
                    "cache_variable": f"ac_cv_func_{name}",
                    "macro": macro,
                    "configure_mapping": f"ac_cv_func_{name}" in configure_text,
                    "pyconfig_mapping": macro in pyconfig_text,
                })
    mapping_by_name = {row["function"]: row for row in mapping_rows}
    probe_by_name = {row["function"]: row for row in probe_rows}
    mapped_rows = [mapping_by_name.get(name, {}) for name in sorted(LEGACY_MAPPED_OVERRIDES)]
    inert_rows = [mapping_by_name.get(name, {}) for name in sorted(LEGACY_INERT_CACHE_OVERRIDES)]
    inert_probe_rows = [probe_by_name.get(name, {}) for name in sorted(LEGACY_INERT_CACHE_OVERRIDES)]
    legacy_model = {
        "initial_overrides": sorted(LEGACY_INITIAL_OVERRIDES),
        "mapped_overrides": sorted(LEGACY_MAPPED_OVERRIDES),
        "inert_cache_overrides": sorted(LEGACY_INERT_CACHE_OVERRIDES),
        "mapped_rows": mapped_rows,
        "inert_rows": inert_rows,
        "inert_probe_rows": inert_probe_rows,
        "inert_cache_evidence": {
            "cpython3145_a3_result_sha256": CPYTHON3145_A3_RESULT_SHA256,
            "configure_argument": "ac_cv_func_setpwent=no",
            "observed_configure_result": "no",
            "generated_have_macro_absent": True,
            "build_python_and_target_replay_passed": True,
            "scope": "build-Python configure cache only",
        },
        "policy": (
            "Mapped overrides require exact configure and pyconfig mappings. "
            "setpwent is the sole allowed inert cache entry because the retained "
            "CPython 3.14.5 A3 replay proved that the cache value is recorded as no, "
            "no HAVE_SETPWENT macro is generated, and the complete replay succeeds."
        ),
    }
    details["host_visibility_probes"] = {
        "compiler": compiler,
        "probes": probe_rows,
        "mappings": mapping_rows,
        "legacy_override_model": legacy_model,
    }
    checks["host_probe_compiler_present"] = bool(compiler)
    checks["legacy_override_model_supported"] = (
        set(mapping_by_name) == LEGACY_INITIAL_OVERRIDES
        and all(row.get("configure_mapping") and row.get("pyconfig_mapping") for row in mapped_rows)
        and all(not row.get("configure_mapping") and not row.get("pyconfig_mapping") for row in inert_rows)
        and all(
            row.get("returncode") == 1
            and "setpwent" in row.get("stderr", "")
            and ("undeclared" in row.get("stderr", "") or "implicit" in row.get("stderr", ""))
            for row in inert_probe_rows
        )
    )
    checks["bounded_host_probe_completed"] = len(probe_rows) == len(LEGACY_INITIAL_OVERRIDES) and all(row["returncode"] in (0, 1) for row in probe_rows)

    required = [
        "repository_coordinate_exact", "authority_root_present", "exact_source_reacquired",
        "source_producer_files_exact", "tracked_snapshot_exact", "source_snapshot_match",
        "dependency_lock_exact", "dependency_model_exact", "dependency_identities_complete",
        "frozen_product_lock_exact", "shell_adapter_exact", "shell_adapter_functional",
        "termux_android_aarch64_host", "host_tools_present", "minimum_storage_available",
        "android_sdk_present", "custom_ndk_present", "ndk_revision_exact",
        "target_driver_exact_and_executable", "resolved_clang_exact", "original_lld_exact",
        "ephemeral_lld_patch_exact", "host_probe_compiler_present",
        "legacy_override_model_supported", "bounded_host_probe_completed",
    ]
    blockers = [name for name in required if not checks.get(name, False)]
    result = {
        "schema_version": 1,
        "verification_kind": "e2p2-termux-native-cpython3146-producer-opening-preflight",
        "claim_boundary": "Read-only opening preflight. No CPython build, artifact materialization, runtime qualification, façade producer rebinding, selection, or publication is claimed.",
        "expected": {"branch": EXPECTED_BRANCH, "head": EXPECTED_HEAD, "tree": EXPECTED_TREE, "source_head": SOURCE_HEAD, "target": TARGET, "api": API, "ndk_revision": NDK_REVISION},
        "checks": checks,
        "required_checks": required,
        "check_count": len(required),
        "pass_count": sum(bool(checks.get(name)) for name in required),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "ready_for_clean_replay": not blockers,
        "ready_for_gate2": False,
        "next_action_class": "run-termux-native-cpython3146-clean-replay" if not blockers else "close-opening-preflight-blockers",
        "details": details,
        "errors": errors,
        "pass": not errors,
    }
    output.write_text(canonical(result))
    print(f"E2P2_TERMUX_NATIVE_CPYTHON3146_OPENING_PREFLIGHT={result['pass_count']}/{result['check_count']} {'READY' if result['ready_for_clean_replay'] else 'BLOCKED'}")
    if blockers:
        print("BLOCKERS=" + ",".join(blockers))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
