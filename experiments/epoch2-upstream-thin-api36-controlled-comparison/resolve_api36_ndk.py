#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

BASELINE_REVISION = "27.3.13750724"
REQUIRED_REVISION = "30.0.15729638-beta2"
TARGET = "aarch64-linux-android36"
HOST = "aarch64-linux-android"
API = 36
HOST_CONTAMINATION_VARIABLES = [
    "CPATH", "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH", "OBJC_INCLUDE_PATH",
    "LIBRARY_PATH", "LD_LIBRARY_PATH", "PKG_CONFIG_PATH", "PKG_CONFIG_LIBDIR",
    "PKG_CONFIG_SYSROOT_DIR",
]
FORBIDDEN_HOST_LIBRARY_PATHS = [
    "/usr/local/lib", "/usr/local/lib64",
    "/data/data/com.termux/files/usr/lib", "/data/data/com.termux/files/usr/lib64",
]
FORBIDDEN_HOST_INCLUDE_PATHS = [
    "/usr/local/include",
    "/data/data/com.termux/files/usr/include",
]
FILTERED_ARGUMENT_FAMILIES = [
    "-L", "-I", "-isystem", "-iquote", "-R", "-rpath", "-rpath-link",
    "-Wl,-rpath", "-Wl,--rpath", "-Wl,-R", "-Wl,-rpath-link", "-Xlinker-rpath",
    "absolute-host-path", "colon-separated-rpath-list",
]



def dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(cmd: list[str], *, input_text: str | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def revision_of(ndk: Path) -> str | None:
    p = ndk / "source.properties"
    if not p.is_file():
        return None
    m = re.search(r"(?m)^Pkg\.Revision\s*=\s*([^\r\n]+)", p.read_text(errors="replace"))
    return m.group(1).strip() if m else None


def platform_metadata(ndk: Path) -> dict[str, Any]:
    path = ndk / "meta/platforms.json"
    record: dict[str, Any] = {"path": str(path), "exists": path.is_file(), "pass": False}
    if not path.is_file():
        record["failure"] = "meta-platforms-json-missing"
        return record
    try:
        data = json.loads(path.read_text(errors="strict"))
    except Exception as exc:
        record["failure"] = f"meta-platforms-json-invalid:{type(exc).__name__}:{exc}"
        return record
    minimum = data.get("min")
    maximum = data.get("max")
    record.update({
        "sha256": sha256(path),
        "min": minimum,
        "max": maximum,
        "aliases": data.get("aliases", {}),
        "supports_api36": isinstance(maximum, int) and maximum >= API,
    })
    record["pass"] = record["supports_api36"]
    if not record["pass"]:
        record["failure"] = f"maximum-api-below-{API}:{maximum!r}"
    return record


def find_prebuilt(ndk: Path) -> Path | None:
    for root in sorted((ndk / "toolchains/llvm/prebuilt").glob("*")):
        required = ["clang", "clang++", "llvm-ar", "llvm-readelf", "llvm-ranlib", "llvm-strip"]
        if root.is_dir() and all((root / "bin" / n).is_file() for n in required):
            if all(os.access(root / "bin" / n, os.X_OK) for n in required):
                return root.resolve()
    return None


def numeric_api_dirs(sysroot: Path) -> list[int]:
    root = sysroot / "usr/lib" / HOST
    if not root.is_dir():
        return []
    return sorted({int(p.name) for p in root.iterdir() if p.is_dir() and p.name.isdigit()})


def wrapper_text(executable: Path, driver_args: list[str]) -> str:
    fixed = " ".join(shlex.quote(x) for x in driver_args)
    spacer = " " if fixed else ""
    unset_line = "unset " + " ".join(HOST_CONTAMINATION_VARIABLES) + " 2>/dev/null || true"
    library_cases = "|".join(
        [p for base in FORBIDDEN_HOST_LIBRARY_PATHS for p in (base, base + "/*")]
    )
    include_cases = "|".join(
        [p for base in FORBIDDEN_HOST_INCLUDE_PATHS for p in (base, base + "/*")]
    )
    any_cases = library_cases + "|" + include_cases
    return f"""#!/usr/bin/env bash
set -euo pipefail
{unset_line}
forbidden_library_path() {{
  case "$1" in
    {library_cases}) return 0 ;;
  esac
  return 1
}}
forbidden_include_path() {{
  case "$1" in
    {include_cases}) return 0 ;;
  esac
  return 1
}}
forbidden_host_path() {{
  case "$1" in
    {any_cases}) return 0 ;;
  esac
  return 1
}}
forbidden_library_path_list() {{
  local value="$1" part
  local IFS=':'
  read -r -a parts <<< "$value"
  for part in "${{parts[@]}}"; do
    forbidden_library_path "$part" && return 0
  done
  return 1
}}
args=()
while (($#)); do
  arg="$1"; shift
  case "$arg" in
    -L|-I|-isystem|-iquote)
      if (($#)); then
        path="$1"
        if [[ "$arg" == -L ]] && forbidden_library_path "$path"; then shift; continue; fi
        if [[ "$arg" != -L ]] && forbidden_include_path "$path"; then shift; continue; fi
        args+=("$arg" "$path"); shift
      else
        args+=("$arg")
      fi
      ;;
    -L*) path="${{arg#-L}}"; forbidden_library_path "$path" || args+=("$arg") ;;
    -I*) path="${{arg#-I}}"; forbidden_include_path "$path" || args+=("$arg") ;;
    -isystem*) path="${{arg#-isystem}}"; forbidden_include_path "$path" || args+=("$arg") ;;
    -iquote*) path="${{arg#-iquote}}"; forbidden_include_path "$path" || args+=("$arg") ;;
    -R)
      if (($#)) && forbidden_library_path_list "$1"; then shift; continue; fi
      args+=("$arg")
      if (($#)); then args+=("$1"); shift; fi
      ;;
    -R*) path="${{arg#-R}}"; forbidden_library_path_list "$path" || args+=("$arg") ;;
    -rpath|-rpath-link|--rpath)
      if (($#)) && forbidden_library_path_list "$1"; then shift; continue; fi
      args+=("$arg")
      if (($#)); then args+=("$1"); shift; fi
      ;;
    -Wl,-rpath|-Wl,--rpath|-Wl,-R|-Wl,-rpath-link)
      if (($#)); then
        path="${{1#-Wl,}}"
        if forbidden_library_path_list "$path"; then shift; continue; fi
        args+=("$arg" "$1"); shift
      else
        args+=("$arg")
      fi
      ;;
    -Wl,-rpath,*|-Wl,--rpath,*|-Wl,-R,*|-Wl,-rpath-link,*)
      path="${{arg#*,}}"; path="${{path#*,}}"
      forbidden_library_path_list "$path" || args+=("$arg")
      ;;
    -Wl,-rpath=*|-Wl,--rpath=*|-Wl,-rpath-link=*)
      path="${{arg#*=}}"
      forbidden_library_path_list "$path" || args+=("$arg")
      ;;
    -Xlinker)
      if (($# >= 3)) && [[ "$1" == -rpath || "$1" == --rpath || "$1" == -rpath-link ]] && [[ "$2" == -Xlinker ]] && forbidden_library_path_list "$3"; then
        shift 3; continue
      fi
      if (($#)) && [[ "$1" == -rpath=* || "$1" == --rpath=* || "$1" == -rpath-link=* || "$1" == -R* ]]; then
        path="${{1#*=}}"; [[ "$1" == -R* ]] && path="${{1#-R}}"
        if forbidden_library_path_list "$path"; then shift; continue; fi
      fi
      args+=("$arg")
      ;;
    *)
      forbidden_host_path "$arg" || args+=("$arg")
      ;;
  esac
done
exec {shlex.quote(str(executable))}{spacer}{fixed} "${{args[@]}}"
"""


def make_wrapper(path: Path, executable: Path, driver_args: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(wrapper_text(executable, driver_args))
    path.chmod(0o755)
    return path


def macro_value(wrapper: Path) -> tuple[int | None, subprocess.CompletedProcess[str]]:
    result = run([str(wrapper), "-dM", "-E", "-x", "c", "/dev/null"])
    matches = re.findall(
        r"^#define (?:__ANDROID_MIN_SDK_VERSION__|__ANDROID_API__) ([0-9]+)$",
        result.stdout,
        re.MULTILINE,
    )
    return (int(matches[0]) if matches else None), result


def link_probe(wrapper: Path, out: Path, log: Path) -> dict[str, Any]:
    source = "int main(void) { return __ANDROID_API__ == 36 ? 0 : 1; }\n"
    cmd = [
        str(wrapper), "-x", "c",
        "-D__BIONIC_NO_PAGE_SIZE_MACRO",
        "-Wno-unused-command-line-argument",
        "-fPIE", "-pie", "-fuse-ld=lld",
        "-Wl,--build-id=sha1", "-Wl,--no-rosegment",
        "-Wl,-z,max-page-size=16384", "-Wl,--no-undefined",
        "-o", str(out), "-",
    ]
    result = run(cmd, input_text=source)
    log.write_text("$ " + shlex.join(cmd) + "\n\n[stdout]\n" + result.stdout + "\n[stderr]\n" + result.stderr)
    return {
        "command": cmd,
        "log": str(log),
        "returncode": result.returncode,
        "output": str(out),
        "output_exists": out.is_file(),
        "output_sha256": sha256(out) if out.is_file() else None,
        "stderr_tail": result.stderr[-5000:],
        "pass": result.returncode == 0 and out.is_file(),
    }


def system_library_probe(wrapper: Path, readelf: Path, out: Path, log: Path) -> dict[str, Any]:
    source = "#include <zlib.h>\nint main(void) { return zlibVersion() == 0; }\n"
    cmd = [
        str(wrapper), "-x", "c",
        "-D__BIONIC_NO_PAGE_SIZE_MACRO",
        "-Wno-unused-command-line-argument",
        "-fPIE", "-pie", "-fuse-ld=lld",
        "-Wl,--build-id=sha1", "-Wl,--no-rosegment",
        "-Wl,-z,max-page-size=16384", "-Wl,--no-undefined",
        "-o", str(out), "-", "-lz",
    ]
    result = run(cmd, input_text=source)
    dynamic = run([str(readelf), "-dW", str(out)]) if result.returncode == 0 and out.is_file() else None
    dynamic_stdout = dynamic.stdout if dynamic is not None else ""
    needed = re.findall(r"\(NEEDED\).*?\[(.*?)\]", dynamic_stdout)
    runpaths = re.findall(r"\((?:RUNPATH|RPATH)\).*?\[(.*?)\]", dynamic_stdout)
    host_paths = [x for x in runpaths if "/data/data/com.termux" in x or "/com.termux/" in x]
    log.write_text(
        "$ " + shlex.join(cmd) + "\n\n[stdout]\n" + result.stdout
        + "\n[stderr]\n" + result.stderr
        + "\n[readelf]\n" + dynamic_stdout
        + ("\n[readelf-stderr]\n" + dynamic.stderr if dynamic is not None else "")
    )
    closure_pass = (
        result.returncode == 0 and out.is_file()
        and dynamic is not None and dynamic.returncode == 0
        and "libz.so" in needed and "libz.so.1" not in needed
        and not host_paths
    )
    return {
        "command": cmd,
        "log": str(log),
        "returncode": result.returncode,
        "output": str(out),
        "output_exists": out.is_file(),
        "output_sha256": sha256(out) if out.is_file() else None,
        "readelf": str(readelf),
        "readelf_returncode": dynamic.returncode if dynamic is not None else None,
        "needed": needed,
        "runpath": runpaths,
        "host_runpaths": host_paths,
        "required_android_system_library": "libz.so",
        "forbidden_host_library": "libz.so.1",
        "stderr_tail": result.stderr[-5000:],
        "pass": closure_pass,
    }


def driver_strategies(prebuilt: Path, sysroot: Path, api_libdir: Path) -> list[dict[str, Any]]:
    base_c = prebuilt / "bin/clang"
    base_cxx = prebuilt / "bin/clang++"
    generic_libdir = sysroot / "usr/lib" / HOST
    out: list[dict[str, Any]] = []
    native_c = prebuilt / f"bin/{TARGET}-clang"
    native_cxx = prebuilt / f"bin/{TARGET}-clang++"
    if native_c.is_file() and os.access(native_c, os.X_OK):
        out.append({
            "id": "native-target-wrapper",
            "c_executable": native_c,
            "cxx_executable": native_cxx if native_cxx.is_file() else base_cxx,
            "driver_args": [],
        })
    out.extend([
        {
            "id": "base-clang-target-only",
            "c_executable": base_c,
            "cxx_executable": base_cxx,
            "driver_args": [f"--target={TARGET}"],
        },
        {
            "id": "base-clang-target-explicit-sysroot",
            "c_executable": base_c,
            "cxx_executable": base_cxx,
            "driver_args": [f"--target={TARGET}", f"--sysroot={sysroot}"],
        },
        {
            "id": "base-clang-target-explicit-sysroot-api-libdir",
            "c_executable": base_c,
            "cxx_executable": base_cxx,
            "driver_args": [
                f"--target={TARGET}", f"--sysroot={sysroot}",
                f"-B{api_libdir}", f"-L{api_libdir}", f"-L{generic_libdir}",
            ],
        },
    ])
    return out


def probe_candidate(ndk_entry: Path, probe_root: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "candidate": str(ndk_entry),
        "candidate_is_symlink": ndk_entry.is_symlink(),
        "target": TARGET,
        "required_revision": REQUIRED_REVISION,
        "pass": False,
    }
    try:
        ndk = ndk_entry.resolve()
        record["resolved_path"] = str(ndk)
        revision = revision_of(ndk)
        record["source_properties_revision"] = revision
        if revision != REQUIRED_REVISION:
            record["failure"] = f"revision-not-required-r30-beta2:{revision!r}"
            return record
        platforms = platform_metadata(ndk)
        record["platform_metadata"] = platforms
        if not platforms.get("pass"):
            record["failure"] = platforms.get("failure", "platform-metadata-api36-not-proven")
            return record
        prebuilt = find_prebuilt(ndk)
        if prebuilt is None:
            record["failure"] = "complete-termux-aarch64-host-prebuilt-missing"
            return record
        record["original_toolchain_root"] = str(prebuilt)
        sysroot = (prebuilt / "sysroot").resolve()
        record["sysroot"] = str(sysroot)
        record["sysroot_exists"] = sysroot.is_dir()
        apis = numeric_api_dirs(sysroot)
        record["supported_api_directories"] = apis
        record["maximum_supported_api_directory"] = max(apis) if apis else None
        record["api36_directory_present"] = API in apis
        api_libdir = sysroot / "usr/lib" / HOST / str(API)
        record["api36_library_dir"] = str(api_libdir)
        crt_names = ["crtbegin_dynamic.o", "crtend_android.o", "libc.so"]
        crt_files = {name: (api_libdir / name).is_file() for name in crt_names}
        record["api36_crt_inventory"] = {
            "directory": str(api_libdir),
            "files": crt_files,
            "complete": all(crt_files.values()),
        }
        if not sysroot.is_dir() or API not in apis or not all(crt_files.values()):
            failed = []
            if not sysroot.is_dir(): failed.append("sysroot-missing")
            if API not in apis: failed.append("api36-sysroot-directory-missing")
            if not all(crt_files.values()): failed.append("api36-crt-or-libc-incomplete")
            record["failure"] = ",".join(failed)
            return record

        attempts: list[dict[str, Any]] = []
        selected: dict[str, Any] | None = None
        candidate_root = probe_root / re.sub(r"[^A-Za-z0-9_.-]+", "_", revision)
        for index, strategy in enumerate(driver_strategies(prebuilt, sysroot, api_libdir), start=1):
            strategy_root = candidate_root / f"{index:02d}-{strategy['id']}"
            wrapper = make_wrapper(
                strategy_root / f"{TARGET}-clang",
                Path(strategy["c_executable"]),
                list(strategy["driver_args"]),
            )
            macro, macro_run = macro_value(wrapper)
            linked = link_probe(wrapper, strategy_root / "probe-executable", strategy_root / "link.log")
            system_linked = system_library_probe(
                wrapper, prebuilt / "bin/llvm-readelf",
                strategy_root / "probe-zlib-executable", strategy_root / "zlib-link.log",
            )
            attempt = {
                "id": strategy["id"],
                "c_executable": str(strategy["c_executable"]),
                "cxx_executable": str(strategy["cxx_executable"]),
                "driver_args": list(strategy["driver_args"]),
                "probe_wrapper": str(wrapper),
                "target_macro_api": macro,
                "macro_probe_rc": macro_run.returncode,
                "macro_probe_stderr_tail": macro_run.stderr[-4000:],
                "api36_link_probe": linked,
                "api36_system_library_probe": system_linked,
                "pass": macro == API and linked["pass"] and system_linked["pass"],
            }
            attempts.append(attempt)
            if attempt["pass"]:
                selected = attempt
                break
        record["driver_strategy_attempts"] = attempts
        if selected is None:
            record["failure"] = "no-custom-clang-driver-strategy-passed-api36-executable-and-android-system-library-closure"
            return record
        record["selected_driver_strategy"] = selected
        record["target_macro_api"] = selected["target_macro_api"]
        record["api36_link_probe"] = selected["api36_link_probe"]
        record["api36_system_library_probe"] = selected["api36_system_library_probe"]
        record["pass"] = True
        return record
    except Exception as exc:
        record["failure"] = f"probe-exception:{type(exc).__name__}:{exc}"
        return record


def collect_candidates(home: Path, sdk: Path) -> list[Path]:
    preferred = [
        sdk / "ndk" / REQUIRED_REVISION,
        home / "Android/Sdk/ndk" / REQUIRED_REVISION,
        home / "opt/android-ndk-r30-beta2",
    ]
    for key in ("CPYTHON_ANDROID_NDK", "ANDROID_NDK_HOME", "ANDROID_NDK_ROOT"):
        value = os.environ.get(key)
        if value:
            preferred.append(Path(value))
    preferred.extend(sorted((sdk / "ndk").glob("*"), reverse=True))
    preferred.extend(sorted((home / "opt").glob("android-ndk-r30*"), reverse=True))
    # Baseline is retained only for an explicit diagnostic record, never selection.
    preferred.extend([sdk / "ndk" / BASELINE_REVISION, home / "opt/android-ndk-r27d"])
    seen: set[str] = set()
    out: list[Path] = []
    for item in preferred:
        try:
            key = str(item.resolve())
        except OSError:
            key = str(item)
        if key in seen:
            continue
        seen.add(key)
        if item.is_dir() and (item / "source.properties").is_file():
            out.append(item)
    return out


def resolve_sdk(home: Path) -> Path:
    candidates: list[Path] = []
    for key in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        value = os.environ.get(key)
        if value:
            candidates.append(Path(value))
    candidates.extend([home / "Android/Sdk", home / "opt/android-sdk"])
    for candidate in candidates:
        if candidate.is_dir() and any((candidate / name).exists() for name in ("cmdline-tools", "platform-tools", "build-tools")):
            return candidate.resolve()
    raise RuntimeError("Android SDK not found through ANDROID_HOME, ~/Android/Sdk, or ~/opt/android-sdk")


def symlink_children(source: Path, destination: Path, excluded: set[str]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name in excluded:
            continue
        os.symlink(item, destination / item.name, target_is_directory=item.is_dir())


def create_compat_overlay(selected: dict[str, Any], work_root: Path) -> tuple[Path, Path, dict[str, Any]]:
    source_ndk = Path(selected["resolved_path"])
    source_prebuilt = Path(selected["original_toolchain_root"])
    revision = selected["source_properties_revision"]
    strategy = selected["selected_driver_strategy"]
    compat_ndk = work_root / f"android-ndk-compat-{revision}"
    shutil.rmtree(compat_ndk, ignore_errors=True)
    symlink_children(source_ndk, compat_ndk, {"toolchains"})
    symlink_children(source_ndk / "toolchains/llvm", compat_ndk / "toolchains/llvm", {"prebuilt"})
    compat_prebuilt = compat_ndk / "toolchains/llvm/prebuilt" / source_prebuilt.name
    symlink_children(source_prebuilt, compat_prebuilt, {"bin"})
    symlink_children(source_prebuilt / "bin", compat_prebuilt / "bin", set())

    target_wrapper = compat_prebuilt / f"bin/{TARGET}-clang"
    target_cxx = compat_prebuilt / f"bin/{TARGET}-clang++"
    # Replace any inherited target-prefixed entry only inside the ephemeral overlay.
    target_wrapper.unlink(missing_ok=True)
    target_cxx.unlink(missing_ok=True)
    make_wrapper(target_wrapper, Path(strategy["c_executable"]), list(strategy["driver_args"]))
    make_wrapper(target_cxx, Path(strategy["cxx_executable"]), list(strategy["driver_args"]))
    linker_wrappers: dict[str, str] = {}
    for linker_name in ("ld", "ld.lld"):
        original = source_prebuilt / "bin" / linker_name
        overlay = compat_prebuilt / "bin" / linker_name
        if original.is_file() and os.access(original, os.X_OK):
            overlay.unlink(missing_ok=True)
            make_wrapper(overlay, original, [])
            linker_wrappers[linker_name] = str(overlay)

    marker = {
        "schema_version": 5,
        "selection_policy": "exact-owner-local-r30-beta2-standard-sdk-plus-executable-and-system-library-link",
        "baseline_ndk_revision": BASELINE_REVISION,
        "selected_ndk_revision": revision,
        "release_channel": "pre-release",
        "prerelease": True,
        "revision_suffix": "beta2",
        "official_version_label": "r30 beta 2",
        "ndk_revision_delta": revision != BASELINE_REVISION,
        "original_ndk_path": str(source_ndk),
        "compatibility_ndk_path": str(compat_ndk),
        "original_toolchain_root": str(source_prebuilt),
        "toolchain_root": str(compat_prebuilt),
        "compiler_invocation_mode": "generated-wrapper-from-proven-driver-contract",
        "driver_contract": {
            "selected_strategy": strategy["id"],
            "c_executable": strategy["c_executable"],
            "cxx_executable": strategy["cxx_executable"],
            "driver_args": strategy["driver_args"],
            "strategy_attempts": selected["driver_strategy_attempts"],
            "host_contamination_variables_unset_by_wrapper": HOST_CONTAMINATION_VARIABLES,
            "host_path_argument_filter": {
                "enabled": True,
                "contract_version": 2,
                "implementation": "bash-array-preserving-filter",
                "forbidden_library_paths": FORBIDDEN_HOST_LIBRARY_PATHS,
                "forbidden_include_paths": FORBIDDEN_HOST_INCLUDE_PATHS,
                "filtered_argument_families": FILTERED_ARGUMENT_FAMILIES,
                "linker_wrappers": linker_wrappers,
                "target_arguments_preserved": True,
                "raw_absolute_host_paths_filtered": True,
                "colon_separated_rpath_lists_filtered": True,
                "product_source_semantics_changed": False,
            },
            "api36_system_library_probe": selected["api36_system_library_probe"],
            "pass": True,
        },
        "base_clang": strategy["c_executable"],
        "api36_clang": str(target_wrapper),
        "target": TARGET,
        "target_macro_api": selected["target_macro_api"],
        "sysroot": selected["sysroot"],
        "supported_api_directories": selected["supported_api_directories"],
        "maximum_supported_api_directory": selected["maximum_supported_api_directory"],
        "api36_directory_present": selected["api36_directory_present"],
        "api36_library_dir": selected["api36_library_dir"],
        "api36_crt_inventory": selected["api36_crt_inventory"],
        "api36_link_probe": selected["api36_link_probe"],
        "api36_system_library_probe": selected["api36_system_library_probe"],
        "platform_metadata": selected["platform_metadata"],
        "compatibility_overlay": True,
        "original_ndk_content_mutated": False,
        "pass": True,
    }
    dump(compat_ndk / "HW_T_NDK_COMPAT.json", marker)
    return compat_ndk, compat_prebuilt, marker


def create_android_home_overlay(sdk: Path, ndk: Path, revision: str, work_root: Path) -> Path:
    overlay = work_root / "android-home-overlay"
    shutil.rmtree(overlay, ignore_errors=True)
    overlay.mkdir(parents=True)
    for item in sdk.iterdir():
        if item.name == "ndk":
            continue
        os.symlink(item, overlay / item.name, target_is_directory=item.is_dir())
    ndk_dir = overlay / "ndk"
    ndk_dir.mkdir()
    os.symlink(ndk, ndk_dir / revision, target_is_directory=True)
    return overlay


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--env-out", type=Path, required=True)
    args = parser.parse_args()
    args.work_root.mkdir(parents=True, exist_ok=True)
    args.result_root.mkdir(parents=True, exist_ok=True)
    home = Path.home()
    sdk = resolve_sdk(home)
    attempts: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    selected_entry: Path | None = None
    for candidate in collect_candidates(home, sdk):
        attempt = probe_candidate(candidate, args.work_root / "ndk-probes")
        attempts.append(attempt)
        if attempt.get("source_properties_revision") == REQUIRED_REVISION and attempt["pass"]:
            selected = attempt
            selected_entry = candidate
            break
    if selected is None or selected_entry is None:
        report = {
            "schema_version": 4,
            "resolution_mode": "exact-owner-local-r30-beta2-api36-driver-contract-selection",
            "selection_policy": "local-r30-beta2-only-no-network-fallback",
            "sdk_source_path": str(sdk),
            "expected_standard_ndk_entry": str(sdk / "ndk" / REQUIRED_REVISION),
            "expected_direct_ndk_entry": str(home / "opt/android-ndk-r30-beta2"),
            "baseline_ndk_revision": BASELINE_REVISION,
            "required_ndk_revision": REQUIRED_REVISION,
            "attempts": attempts,
            "pass": False,
            "failure": "owner-local-r30-beta2-did-not-prove-api36-metadata-crt-executable-and-system-library-link-contract",
        }
        dump(args.result_root / "android-toolchain-resolution.json", report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    compat_ndk, toolchain, marker = create_compat_overlay(selected, args.work_root)
    overlay = create_android_home_overlay(sdk, compat_ndk, marker["selected_ndk_revision"], args.work_root)
    standard_entry = sdk / "ndk" / REQUIRED_REVISION
    user_alias = home / "Android/Sdk/ndk" / REQUIRED_REVISION
    report = {
        "schema_version": 4,
        "resolution_mode": "exact-owner-local-r30-beta2-api36-driver-contract-plus-compatibility-overlay",
        "selection_policy": marker["selection_policy"],
        "sdk_source_path": str(sdk),
        "selected_ndk_entry": str(selected_entry),
        "standard_ndk_entry": str(standard_entry),
        "standard_ndk_entry_is_symlink": standard_entry.is_symlink(),
        "standard_ndk_entry_resolved": str(standard_entry.resolve()) if standard_entry.exists() else None,
        "user_sdk_alias_entry": str(user_alias),
        "user_sdk_alias_entry_is_symlink": user_alias.is_symlink(),
        "user_sdk_alias_entry_resolved": str(user_alias.resolve()) if user_alias.exists() else None,
        "ndk_source_path": marker["original_ndk_path"],
        "ndk_compatibility_path": str(compat_ndk),
        "android_home_overlay": str(overlay),
        "baseline_ndk_revision": BASELINE_REVISION,
        "selected_ndk_revision": marker["selected_ndk_revision"],
        "release_channel": marker["release_channel"],
        "prerelease": marker["prerelease"],
        "revision_suffix": marker["revision_suffix"],
        "official_version_label": marker["official_version_label"],
        "ndk_revision_delta": marker["ndk_revision_delta"],
        "source_properties": (compat_ndk / "source.properties").read_text(errors="replace").splitlines(),
        "toolchain_root": str(toolchain),
        "api36_clang": marker["api36_clang"],
        "base_clang": marker["base_clang"],
        "compiler_invocation_mode": marker["compiler_invocation_mode"],
        "driver_contract": marker["driver_contract"],
        "target": marker["target"],
        "target_macro_api": marker["target_macro_api"],
        "sysroot": marker["sysroot"],
        "supported_api_directories": marker["supported_api_directories"],
        "maximum_supported_api_directory": marker["maximum_supported_api_directory"],
        "api36_directory_present": marker["api36_directory_present"],
        "api36_library_dir": marker["api36_library_dir"],
        "api36_crt_inventory": marker["api36_crt_inventory"],
        "api36_link_probe": marker["api36_link_probe"],
        "api36_system_library_probe": marker["api36_system_library_probe"],
        "platform_metadata": marker["platform_metadata"],
        "attempts": attempts,
        "acquisition": {"mode": "owner-local-existing-path", "network": False},
        "compatibility_overlay_created": True,
        "original_ndk_content_mutated": False,
        "provider_reference": {
            "ndk": "HomuHomu833/android-ndk-custom owner-local r30 beta2",
            "sdk": "HomuHomu833/android-sdk-custom owner-local standard layout",
            "identity_scope": "exact beta revision, meta/platforms.json max API, standard symlink resolution, API36 sysroot/CRT inventory, macro, executable link, Android libz.so closure, and compiler/linker host-path argument filtering",
        },
        "pass": True,
    }
    dump(args.result_root / "android-toolchain-resolution.json", report)
    exports = {
        "RESOLVED_ANDROID_SDK": str(sdk),
        "RESOLVED_ANDROID_NDK": str(compat_ndk),
        "NDK_TOOLCHAIN_ROOT": str(toolchain),
        "ANDROID_HOME_OVERLAY": str(overlay),
        "SELECTED_NDK_REVISION": marker["selected_ndk_revision"],
    }
    args.env_out.write_text("".join(f"export {k}={shlex.quote(v)}\n" for k, v in exports.items()))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
