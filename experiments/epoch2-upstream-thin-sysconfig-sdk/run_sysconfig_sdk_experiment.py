#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import base64
import csv
import hashlib
import importlib.util
import json
import os
import posixpath
import pprint
import re
import shutil
import subprocess
import sys
import sysconfig as host_sysconfig
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Any

EXPECTED_ARCHIVE_SHA = "38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5"
EXPECTED_ARCHIVE_SIZE = 22358404
EXPECTED_CONTROL_SHA = "6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c"
EXPECTED_ARTIFACT_SHA = "387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306"
EXPECTED_LOADER_SHA = "05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2"
EXPECTED_SELECTED_LAUNCHER_SHA = "94e5d27c9ed421b8cbbeefa2b56a531a9b7f94ea5adc8072911da7bf32b79a17"
PYTHON_MM = "3.14"
TARGET_TRIPLE = "aarch64-linux-android"
ANDROID_API = 24
EXPECTED_PLATFORM = "android-24-arm64_v8a"
EXPECTED_SOABI = "cpython-314-aarch64-linux-android"
EXPECTED_EXT_SUFFIX = ".cpython-314-aarch64-linux-android.so"
PRODUCER_ROOTS = ("/Users/runner/", "/usr/local")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run(cmd: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None,
        timeout: int = 600, check: bool = False) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(cmd, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(
            f"command failed ({p.returncode}): {' '.join(cmd)}\nstdout:\n{p.stdout}\nstderr:\n{p.stderr}"
        )
    return p


def parse_last_json(text: str) -> Any:
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            pass
    return None


def import_ut2_module(root: Path):
    path = root / "experiments/epoch2-upstream-thin-loader-relocation/run_loader_relocation_experiment.py"
    authority = load(root / "experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json")
    expected = authority["file_identities"][path.name]
    if sha256(path) != expected:
        raise RuntimeError("UT-2 runtime preparation script identity mismatch")
    spec = importlib.util.spec_from_file_location("hw_t_ut2_runtime", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import UT-2 runtime preparation module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, authority


def clean_env(prefix: Path, work: Path) -> dict[str, str]:
    env = dict(os.environ)
    for key in (
        "LD_LIBRARY_PATH", "PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV",
        "__PYVENV_LAUNCHER__", "CPYTHON_HOME", "HW_T_LR0_SELF_REEXEC",
        "CFLAGS", "CPPFLAGS", "LDFLAGS", "LDSHARED", "CC", "CXX", "AR",
        "ARCHFLAGS", "SDKROOT", "MACOSX_DEPLOYMENT_TARGET",
    ):
        env.pop(key, None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = str(work / "pycache")
    env["HW_T_EXPECTED_PREFIX"] = str(prefix)
    ca = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr")) / "etc/tls/cert.pem"
    if ca.is_file():
        env["SSL_CERT_FILE"] = str(ca)
    return env


ABS_TOKEN_RE = re.compile(
    r"(?:^|[\s\"'`=(:,\[\{])(/(?![.*])[^\s\"'`;,)\]}]+)"
    r"|(?:-I|-L|--sysroot=)(/(?![.*])[^\s\"'`;,)\]}]+)",
    re.MULTILINE,
)


def absolute_tokens(text: str) -> list[str]:
    out: list[str] = []
    for m in ABS_TOKEN_RE.finditer(text):
        token = (m.group(1) or m.group(2) or "").rstrip(".:]")
        if token and token not in out:
            out.append(token)
    return out


def classify_absolute(token: str, active_prefix: str | None = None) -> str:
    if token.startswith("/Users/runner/Library/Android/"):
        return "producer-ndk"
    if token.startswith("/Users/runner/work/") or token.startswith("/Users/runner/.local"):
        return "producer-workspace"
    if token == "/usr/local" or token.startswith("/usr/local/"):
        return "stale-install-prefix"
    if active_prefix and (token == active_prefix or token.startswith(active_prefix + "/")):
        return "active-runtime-prefix"
    if token.startswith(("/system/", "/apex/", "/dev/", "/data/data/com.termux/", "/data/user/0/com.termux/")):
        return "android-or-termux-system"
    if token.startswith(("/bin/", "/usr/bin/", "/usr/share/", "/usr/lib/", "/usr/include/", "/etc/")):
        return "generic-unix-system"
    return "unknown-absolute"


def scan_text_surfaces(prefix: Path, active_prefix: str | None = None) -> dict[str, Any]:
    candidates = [
        prefix / "lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py",
        prefix / "lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json",
        prefix / "lib/python3.14/build-details.json",
        prefix / "lib/python3.14/config-3.14-aarch64-linux-android/Makefile",
        prefix / "lib/python3.14/config-3.14-aarch64-linux-android/python-config.py",
        prefix / "bin/python3.14-config",
        prefix / "include/python3.14/pyconfig.h",
    ]
    candidates.extend(sorted((prefix / "lib/pkgconfig").glob("*.pc")))
    rows: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for p in candidates:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        # Producer and stale install roots are forbidden even in inert text.
        # Unknown-path classification is limited to active consumer metadata;
        # Makefile recipes and comments are implementation history, not active
        # variable values.
        scan_text = text
        if p.name == "Makefile":
            scan_text = "\n".join(
                line for line in text.splitlines()
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*=", line)
            )
        tokens = absolute_tokens(scan_text)
        for marker in PRODUCER_ROOTS:
            if marker in text and marker not in tokens:
                tokens.append(marker)
        for token in tokens:
            cls = classify_absolute(token, active_prefix)
            counts[cls] = counts.get(cls, 0) + 1
            rows.append({"path": p.relative_to(prefix).as_posix(), "token": token, "classification": cls})
    return {"schema_version": 1, "surface_count": len(candidates), "rows": rows,
            "classification_counts": dict(sorted(counts.items()))}


SYSCONFIG_PROBE = r'''
import json, os, sys, sysconfig
keys = [
 "prefix","exec_prefix","installed_base","installed_platbase","base","platbase","projectbase",
 "BINDIR","BINLIBDEST","LIBDEST","INCLUDEPY","CONFINCLUDEPY","LIBDIR","LIBPL","DESTSHARED",
 "CC","CXX","AR","CFLAGS","CPPFLAGS","LDFLAGS","LDSHARED","BLDSHARED","CCSHARED",
 "SOABI","MULTIARCH","EXT_SUFFIX","ANDROID_API_LEVEL","HOST_GNU_TYPE","BUILD_GNU_TYPE",
 "CONFIG_ARGS","TZPATH","SHELL","LIBPYTHON","BLDLIBRARY","Py_ENABLE_SHARED"
]
vars = {k: sysconfig.get_config_var(k) for k in keys}
print(json.dumps({
 "executable": sys.executable,
 "prefix": sys.prefix,
 "base_prefix": sys.base_prefix,
 "platform": sysconfig.get_platform(),
 "paths": sysconfig.get_paths(),
 "vars": vars,
 "makefile": sysconfig.get_makefile_filename(),
 "config_h": sysconfig.get_config_h_filename(),
}, sort_keys=True))
'''


def runtime_probe(python: Path, prefix: Path, work: Path) -> dict[str, Any]:
    env = clean_env(prefix, work)
    p = run([str(python), "-c", SYSCONFIG_PROBE], env=env, timeout=300)
    data = parse_last_json(p.stdout)
    return {"command": [str(python), "-c", "<sysconfig-probe>"], "returncode": p.returncode,
            "stdout": p.stdout, "stderr": p.stderr, "data": data,
            "pass": p.returncode == 0 and isinstance(data, dict)}


def path_strings(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            out.extend(path_strings(v))
    elif isinstance(value, list):
        for v in value:
            out.extend(path_strings(v))
    return out


def producer_residue(value: Any) -> list[str]:
    return sorted({s for s in path_strings(value) if any(root in s for root in PRODUCER_ROOTS)})


def runtime_paths_within(probe: dict[str, Any], prefix: Path) -> bool:
    data = probe.get("data")
    if not isinstance(data, dict):
        return False
    root = prefix.resolve()
    for value in data.get("paths", {}).values():
        if not isinstance(value, str):
            return False
        p = Path(value).resolve(strict=False)
        if p != root and root not in p.parents:
            return False
    for key in ("makefile", "config_h"):
        value = data.get(key)
        if not isinstance(value, str):
            return False
        p = Path(value).resolve(strict=False)
        if p != root and root not in p.parents:
            return False
    return True


def make_dynamic_normalizer() -> str:
    # The frozen producer dictionary is sanitized before serialization. This
    # runtime block only expands a neutral placeholder and derives active paths
    # from the module location, so the installed source contains no producer or
    # stale install prefix literals.
    return r'''

# BEGIN HW-T CONSUMER NORMALIZATION — E2-R1/UT-3
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
    "prefix": _hw_prefix,
    "exec_prefix": _hw_prefix,
    "base": _hw_prefix,
    "platbase": _hw_prefix,
    "installed_base": _hw_prefix,
    "installed_platbase": _hw_prefix,
    "host_prefix": _hw_prefix,
    "host_exec_prefix": _hw_prefix,
    "projectbase": _hw_os.path.join(_hw_prefix, "bin"),
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
    "srcdir": _hw_config,
    "abs_srcdir": _hw_config,
    "abs_builddir": _hw_config,
    "builddir": _hw_config,
    "CC": "clang",
    "CXX": "clang++",
    "AR": "llvm-ar",
    "ARFLAGS": "rcs",
    "CCSHARED": "-fPIC",
    "CFLAGS": _hw_cflags,
    "PY_CFLAGS": _hw_cflags,
    "PY_STDMODULE_CFLAGS": _hw_cflags + " -fPIC",
    "CPPFLAGS": "",
    "PY_CPPFLAGS": "",
    "LDFLAGS": _hw_ldflags,
    "PY_LDFLAGS": _hw_ldflags,
    "PY_CORE_LDFLAGS": _hw_ldflags,
    "LDSHARED": "clang -shared " + _hw_ldflags,
    "BLDSHARED": "clang -shared " + _hw_ldflags,
    "BLDLIBRARY": "-L" + _hw_lib + " -lpython3.14",
    "LIBPYTHON": "",
    "LIBS": "-ldl -lm",
    "SYSLIBS": "-llog",
    "SHELL": "sh -e",
    "CONFIG_ARGS": "--host=aarch64-linux-android --enable-shared --without-static-libpython --without-ensurepip consumer-normalized-binary-derived",
    "BUILD_GNU_TYPE": "aarch64-linux-android",
    "HOST_GNU_TYPE": "aarch64-linux-android",
    "TZPATH": "",
    "ANDROID_API_LEVEL": 24,
    "SOABI": "cpython-314-aarch64-linux-android",
    "MULTIARCH": "aarch64-linux-android",
    "EXT_SUFFIX": ".cpython-314-aarch64-linux-android.so",
    "HW_T_METADATA_PROFILE": "on-device-sdk",
    "HW_T_CROSS_BUILD_SDK": "unavailable-without-explicit-ndk-authority",
})
for _hw_key, _hw_value in build_time_vars.items():
    if isinstance(_hw_value, str) and _hw_placeholder in _hw_value:
        raise RuntimeError("HW-T sysconfig placeholder residue: %s=%r" % (_hw_key, _hw_value))
del _hw_key, _hw_value, _hw_cflags, _hw_ldflags, _hw_config, _hw_include, _hw_stdlib, _hw_lib, _hw_prefix, _hw_placeholder, _hw_os
# END HW-T CONSUMER NORMALIZATION
'''


def parse_build_time_vars(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "build_time_vars" for t in node.targets):
            value = ast.literal_eval(node.value)
            if not isinstance(value, dict):
                break
            return value
    raise RuntimeError("cannot parse build_time_vars from official sysconfigdata")


def sanitize_sysconfig_vars(values: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in values.items():
        if isinstance(value, str):
            out[key] = sanitize_tokens(value, "@HW_T_PREFIX@")
        else:
            out[key] = value
    return out


def render_sysconfigdata(values: dict[str, Any]) -> str:
    rendered = "# system configuration normalized for relocatable Android consumers\n"
    rendered += "build_time_vars = " + pprint.pformat(values, width=120, sort_dicts=True) + "\n"
    rendered += make_dynamic_normalizer()
    if any(marker in rendered for marker in PRODUCER_ROOTS):
        raise RuntimeError("rendered sysconfigdata contains producer or stale install path")
    compile(rendered, "<normalized-sysconfigdata>", "exec")
    return rendered


def sanitize_tokens(value: str, replacement_prefix: str) -> str:
    value = value.replace("/usr/local", replacement_prefix)
    if "/Users/runner/" not in value:
        return value
    try:
        tokens = re.findall(r"(?:'[^']*'|\"[^\"]*\"|\S+)", value)
    except re.error:
        tokens = value.split()
    kept = [t for t in tokens if "/Users/runner/" not in t]
    value = " ".join(kept)
    value = re.sub(r"/Users/runner/[^\s'\"]+", "", value)
    return " ".join(value.split())


def normalize_makefile(path: Path) -> dict[str, Any]:
    original = path.read_text(encoding="utf-8")
    overrides = {
        "CC": "clang",
        "CXX": "clang++",
        "AR": "llvm-ar",
        "ARFLAGS": "rcs",
        "SHELL": "sh -e",
        "CFLAGS": "-fno-strict-overflow -Wsign-compare -Wunreachable-code -DNDEBUG -O2 -Wall -D__BIONIC_NO_PAGE_SIZE_MACRO",
        "PY_CFLAGS": "$(CFLAGS)",
        "CPPFLAGS": "",
        "PY_CPPFLAGS": "",
        "LDFLAGS": "-Wl,--build-id=sha1 -Wl,--no-rosegment -Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384",
        "PY_LDFLAGS": "$(LDFLAGS)",
        "PY_CORE_LDFLAGS": "$(LDFLAGS)",
        "LDSHARED": "clang -shared $(LDFLAGS)",
        "BLDSHARED": "clang -shared $(LDFLAGS)",
        "BLDLIBRARY": "-L$(LIBDIR) -lpython3.14",
        "CONFIG_ARGS": "--host=aarch64-linux-android --enable-shared --without-static-libpython --without-ensurepip consumer-normalized-binary-derived",
        "BUILD_GNU_TYPE": "aarch64-linux-android",
        "HOST_GNU_TYPE": "aarch64-linux-android",
        "TZPATH": "",
    }
    out: list[str] = []
    seen: set[str] = set()
    for line in original.splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2)
            if key == "prefix":
                out.append("prefix := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../..)")
                seen.add(key)
                continue
            if key in overrides:
                out.append(f"{key}=\t\t{overrides[key]}")
                seen.add(key)
                continue
            value = sanitize_tokens(value, "$(prefix)")
            out.append(f"{key}=\t\t{value}")
            seen.add(key)
        else:
            out.append(sanitize_tokens(line, "$(prefix)"))
    for key, value in overrides.items():
        if key not in seen:
            out.append(f"{key}=\t\t{value}")
    normalized = "\n".join(out) + "\n"
    if "/Users/runner/" in normalized or "/usr/local" in normalized:
        raise RuntimeError("Makefile producer residue remains")
    path.write_text(normalized, encoding="utf-8")
    return {"path": path.name, "before_sha256": hashlib.sha256(original.encode()).hexdigest(),
            "after_sha256": sha256(path), "dynamic_prefix": True}


def normalize_pkgconfig(pkgdir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(pkgdir.glob("*.pc")):
        if path.is_symlink():
            continue
        before = path.read_text(encoding="utf-8")
        lines = []
        for line in before.splitlines():
            if line.startswith("prefix="):
                lines.append("prefix=${pcfiledir}/../..")
            elif "$(BLDLIBRARY)" in line:
                lines.append(line.replace(" $(BLDLIBRARY)", ""))
            else:
                lines.append(line.replace("/usr/local", "${prefix}"))
        after = "\n".join(lines) + "\n"
        if "/usr/local" in after or "/Users/runner/" in after:
            raise RuntimeError(f"pkg-config producer residue: {path}")
        path.write_text(after, encoding="utf-8")
        rows.append({"path": path.name, "before_sha256": hashlib.sha256(before.encode()).hexdigest(),
                     "after_sha256": sha256(path), "prefix": "${pcfiledir}/../.."})
    return rows


def relativize(value: Any, prefix: str) -> Any:
    if isinstance(value, str):
        return value.replace(prefix, "${prefix}")
    if isinstance(value, list):
        return [relativize(v, prefix) for v in value]
    if isinstance(value, dict):
        return {k: relativize(v, prefix) for k, v in value.items()}
    return value


def normalize_build_details(path: Path) -> dict[str, Any]:
    before = load(path)
    data = json.loads(json.dumps(before))
    data["base_interpreter"] = "bin/python3.14"
    data["base_prefix"] = "."
    data["c_api"]["headers"] = "include/python3.14"
    data["c_api"]["pkgconfig_path"] = "lib/pkgconfig"
    data["suffixes"]["extensions"] = [EXPECTED_EXT_SUFFIX, ".abi3.so", ".so"]
    data["libpython"]["dynamic"] = "lib/libpython3.14.so"
    data["libpython"]["dynamic_stableabi"] = "lib/libpython3.so"
    data["hw_t_path_semantics"] = "relative-to-runtime-root"
    dump(path, data)
    return {"before_sha256": hashlib.sha256((json.dumps(before, sort_keys=True)+"\n").encode()).hexdigest(),
            "after_sha256": sha256(path), "path_semantics": "relative-to-runtime-root"}


def normalize_runtime(prefix: Path, python: Path, work: Path) -> dict[str, Any]:
    sysdata = prefix / "lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py"
    sysvars = prefix / "lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json"
    makefile = prefix / "lib/python3.14/config-3.14-aarch64-linux-android/Makefile"
    pyconfig = prefix / "lib/python3.14/config-3.14-aarch64-linux-android/python-config.py"
    build_details = prefix / "lib/python3.14/build-details.json"
    before_sha = sha256(sysdata)
    text = sysdata.read_text(encoding="utf-8")
    if "BEGIN HW-T CONSUMER NORMALIZATION" in text:
        raise RuntimeError("sysconfigdata already normalized")
    official_vars = parse_build_time_vars(sysdata)
    sysdata.write_text(render_sysconfigdata(sanitize_sysconfig_vars(official_vars)), encoding="utf-8")
    pytext = pyconfig.read_text(encoding="utf-8")
    if pytext.startswith("#!"):
        pytext = "\n".join(pytext.splitlines()[1:]) + "\n"
    pyconfig.write_text(pytext, encoding="utf-8")
    os.chmod(pyconfig, 0o644)
    make_row = normalize_makefile(makefile)
    pc_rows = normalize_pkgconfig(prefix / "lib/pkgconfig")
    build_row = normalize_build_details(build_details)
    # Import the normalized module through the target interpreter, then write a
    # location-neutral JSON consumer snapshot. CPython 3.14 loads the .py file;
    # the JSON is preserved as an explicit relative metadata surface.
    probe = runtime_probe(python, prefix, work)
    if not probe["pass"]:
        raise RuntimeError(f"normalized sysconfig probe failed: {probe['stderr']}")
    snapshot = relativize(probe["data"]["vars"], str(prefix))
    snapshot["_HW_T_PATH_SEMANTICS"] = "${prefix}-relative"
    dump(sysvars, snapshot)
    config_script = prefix / "bin/python3.14-config"
    config_script.parent.mkdir(parents=True, exist_ok=True)
    config_script.write_text(
        "#!/system/bin/sh\n"
        "case \"$0\" in /*) _hw_script=\"$0\" ;; *) _hw_script=\"$(pwd)/$0\" ;; esac\n"
        "_hw_bindir=${_hw_script%/*}\n"
        "exec \"$_hw_bindir/python3.14\" \"$_hw_bindir/../lib/python3.14/config-3.14-aarch64-linux-android/python-config.py\" \"$@\"\n",
        encoding="utf-8",
    )
    os.chmod(config_script, 0o755)
    return {
        "schema_version": 1,
        "sysconfigdata": {"before_sha256": before_sha, "after_sha256": sha256(sysdata), "dynamic_prefix": True},
        "sysconfig_vars_json": {"sha256": sha256(sysvars), "path_semantics": "${prefix}-relative"},
        "makefile": make_row,
        "python_config": {"sha256": sha256(pyconfig), "shebang": None, "invocation": "target-interpreter-explicit"},
        "python_config_entry": {"path": "bin/python3.14-config", "sha256": sha256(config_script), "shebang": "#!/system/bin/sh", "dynamic_bindir": True},
        "pkgconfig": pc_rows,
        "build_details": build_row,
    }


def consumer_probe(python: Path, prefix: Path, work: Path, pkg_config: str) -> dict[str, Any]:
    env = clean_env(prefix, work)
    config_py = prefix / "lib/python3.14/config-3.14-aarch64-linux-android/python-config.py"
    options = ["--prefix", "--exec-prefix", "--includes", "--cflags", "--libs", "--ldflags",
               "--extension-suffix", "--configdir"]
    config_rows = []
    config_entry = prefix / "bin/python3.14-config"
    for option in options:
        p = run([str(python), str(config_py), option], env=env, timeout=120)
        q = run([str(config_entry), option], env=env, timeout=120)
        config_rows.append({"option": option,
                            "python_invocation": {"returncode": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()},
                            "direct_entry": {"returncode": q.returncode, "stdout": q.stdout.strip(), "stderr": q.stderr.strip()},
                            "returncode": 0 if p.returncode == 0 and q.returncode == 0 and p.stdout == q.stdout else 1,
                            "stdout": p.stdout.strip(),
                            "stderr": (p.stderr + q.stderr).strip(),
                            "outputs_equal": p.stdout == q.stdout})
    pc_env = dict(env)
    pc_env["PKG_CONFIG_PATH"] = str(prefix / "lib/pkgconfig")
    pc_rows = []
    for package in ("python-3.14", "python-3.14-embed", "openssl", "sqlite3"):
        p = run([pkg_config, "--cflags", "--libs", package], env=pc_env, timeout=120)
        pc_rows.append({"package": package, "returncode": p.returncode,
                        "stdout": p.stdout.strip(), "stderr": p.stderr.strip()})
    all_text = "\n".join(row["stdout"] + "\n" + row["stderr"] for row in config_rows + pc_rows)
    return {"schema_version": 1, "python_config": config_rows, "pkg_config": pc_rows,
            "producer_residue": producer_residue(all_text),
            "pass": all(row["returncode"] == 0 for row in config_rows + pc_rows) and not producer_residue(all_text)}


def wheel_record_hash(data: bytes) -> str:
    return "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()


def rewrite_wheel_without_rpath(wheel: Path, patchelf: str, readelf: str, ut2: Any,
                                work: Path) -> tuple[Path, dict[str, Any]]:
    unpack = work / "wheel-unpack"
    shutil.rmtree(unpack, ignore_errors=True)
    unpack.mkdir(parents=True)
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
        normalized_names = [posixpath.normpath(name) for name in names]
        if (len(set(normalized_names)) != len(normalized_names)
                or any(name.startswith("/") or norm in (".", "..") or norm.startswith("../")
                       for name, norm in zip(names, normalized_names))):
            raise RuntimeError("unsafe or duplicate wheel member")
        zf.extractall(unpack)
    so_files = sorted(unpack.rglob("*.so"))
    if len(so_files) != 1:
        raise RuntimeError(f"expected exactly one extension in wheel, found {len(so_files)}")
    ext = so_files[0]
    before = ut2.elf_surface(ext, readelf)
    command = None
    if before.get("runpath") or before.get("rpath"):
        command = [patchelf, "--page-size", "16384", "--remove-rpath", str(ext)]
        p = run(command, timeout=180)
        if p.returncode:
            raise RuntimeError(f"extension rpath removal failed: {p.stderr}")
    after = ut2.elf_surface(ext, readelf)
    alignment = ut2.alignment_policy(before["load_alignments"], after["load_alignments"])
    exact = (
        before["type"] == after["type"] and before["machine"] == after["machine"]
        and before["needed"] == after["needed"] and before["soname"] == after["soname"]
        and not after["rpath"] and not after["runpath"] and alignment["preserved"]
    )
    if not exact:
        raise RuntimeError("wheel extension normalization changed a protected ELF surface")
    dist_info = next(iter(sorted(unpack.glob("*.dist-info"))), None)
    if dist_info is None:
        raise RuntimeError("wheel dist-info missing")
    record = dist_info / "RECORD"
    rows = []
    for p in sorted(unpack.rglob("*")):
        if not p.is_file() or p == record:
            continue
        rel = p.relative_to(unpack).as_posix()
        data = p.read_bytes()
        rows.append([rel, wheel_record_hash(data), str(len(data))])
    rows.append([record.relative_to(unpack).as_posix(), "", ""])
    with record.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f, lineterminator="\n").writerows(rows)
    normalized = wheel.with_name(wheel.name + ".normalized.tmp")
    with zipfile.ZipFile(normalized, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(unpack.rglob("*")):
            if not p.is_file():
                continue
            info = zipfile.ZipInfo(p.relative_to(unpack).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            zf.writestr(info, p.read_bytes())
    return normalized, {"source_wheel": wheel.name, "normalized_wheel": normalized.name,
                        "extension_path": ext.relative_to(unpack).as_posix(), "before": before,
                        "after": after, "command": command, "alignment_policy": alignment,
                        "exact_normalization": exact}


def inspect_wheel(wheel: Path) -> dict[str, Any]:
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
        wheel_meta_name = next(n for n in names if n.endswith(".dist-info/WHEEL"))
        wheel_meta = zf.read(wheel_meta_name).decode("utf-8", errors="replace")
        tags = [line.split(":", 1)[1].strip() for line in wheel_meta.splitlines() if line.startswith("Tag:")]
        extension = [n for n in names if n.endswith(".so")]
    filename_ok = bool(re.fullmatch(r"hw_t_native_probe-0\.1\.0-cp314-cp314-android_24_arm64_v8a\.whl", wheel.name))
    # The post-normalization suffix is an evidence artifact name. The embedded
    # wheel tag remains the authoritative wheel identity.
    tag_ok = tags == ["cp314-cp314-android_24_arm64_v8a"]
    return {"filename": wheel.name, "sha256": sha256(wheel), "size": wheel.stat().st_size,
            "tags": tags, "extension_members": extension, "filename_ok": filename_ok,
            "tag_ok": tag_ok, "pass": filename_ok and tag_ok and len(extension) == 1}


INSTALL_WHEEL = r'''
import base64, csv, hashlib, io, json, pathlib, posixpath, sys, zipfile
wheel=pathlib.Path(sys.argv[1]); site=pathlib.Path(sys.argv[2]); site.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(wheel) as z:
    names=z.namelist(); normalized=[posixpath.normpath(n) for n in names]
    if len(set(normalized))!=len(normalized) or any(n.startswith('/') or q in ('.','..') or q.startswith('../') for n,q in zip(names,normalized)):
        raise SystemExit(json.dumps({'pass':False,'errors':['unsafe-or-duplicate-member']}))
    record_name=next(n for n in names if n.endswith('.dist-info/RECORD'))
    rows=list(csv.reader(io.StringIO(z.read(record_name).decode())))
    errors=[]
    for name,digest,size in rows:
        if not name or name==record_name: continue
        data=z.read(name)
        got='sha256='+base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
        if digest and digest!=got: errors.append('digest:'+name)
        if size and int(size)!=len(data): errors.append('size:'+name)
    if errors: raise SystemExit(json.dumps({'pass':False,'errors':errors}))
    for name in names:
        if name.endswith('/'): continue
        out=site/name; out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(z.read(name))
print(json.dumps({'pass':True,'wheel':str(wheel),'site_packages':str(site),'member_count':len(names)}))
'''

IMPORT_PROBE = r'''
import json, hw_t_native_probe, sys
print(json.dumps({'meaning':hw_t_native_probe.meaning(),'runtime_prefix':hw_t_native_probe.runtime_prefix(),'sys_prefix':sys.prefix,'base_prefix':sys.base_prefix,'module_file':hw_t_native_probe.__file__},sort_keys=True))
'''


def venv_site(python: Path, prefix: Path, work: Path, venv: Path) -> tuple[Path, Path, dict[str, Any]]:
    env = clean_env(prefix, work)
    p = run([str(python), "-m", "venv", "--without-pip", str(venv)], env=env, timeout=300)
    if p.returncode:
        raise RuntimeError(f"venv creation failed: {p.stdout}\n{p.stderr}")
    vpy = venv / "bin/python"
    q = run([str(vpy), "-c", "import json,sysconfig; print(json.dumps(sysconfig.get_paths()))"], env=env, timeout=120)
    paths = parse_last_json(q.stdout)
    if q.returncode or not isinstance(paths, dict):
        raise RuntimeError(f"venv sysconfig failed: {q.stdout}\n{q.stderr}")
    site = Path(paths["platlib"])
    return vpy, site, {"create_command": [str(python), "-m", "venv", "--without-pip", str(venv)],
                       "python": str(vpy), "site_packages": str(site), "paths": paths}


def install_and_import(wheel: Path, base_python: Path, prefix: Path, work: Path, venv: Path) -> dict[str, Any]:
    env = clean_env(prefix, work)
    vpy, site, meta = venv_site(base_python, prefix, work, venv)
    p = run([str(vpy), "-c", INSTALL_WHEEL, str(wheel), str(site)], env=env, timeout=180)
    install_data = parse_last_json(p.stdout)
    q = run([str(vpy), "-c", IMPORT_PROBE], env=env, timeout=180)
    data = parse_last_json(q.stdout)
    passed = (
        p.returncode == 0 and isinstance(install_data, dict) and install_data.get("pass") is True
        and q.returncode == 0 and isinstance(data, dict) and data.get("meaning") == 42
        and data.get("runtime_prefix") == str(venv)
        and data.get("sys_prefix") == str(venv)
        and data.get("base_prefix") == str(prefix)
        and isinstance(data.get("module_file"), str)
        and str(site) in data.get("module_file")
    )
    return {"venv": meta, "install": {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
                                       "data": install_data},
            "import": {"returncode": q.returncode, "stdout": q.stdout, "stderr": q.stderr, "data": data},
            "pass": passed}


def build_wheel(python: Path, prefix: Path, source_dir: Path, work: Path, artifacts: Path,
                cc: str, cxx: str, ar: str, patchelf: str, readelf: str, ut2: Any) -> dict[str, Any]:
    project = work / "native-project"
    shutil.rmtree(project, ignore_errors=True)
    project.mkdir(parents=True)
    shutil.copy2(source_dir / "native_probe.c", project / "native_probe.c")
    shutil.copy2(source_dir / "setup.py", project / "setup.py")
    setuptools_wheel = prefix / "lib/python3.14/test/wheeldata/setuptools-79.0.1-py3-none-any.whl"
    if not setuptools_wheel.is_file():
        raise RuntimeError("bundled setuptools wheel missing")
    bootstrap = work / "setuptools-bootstrap"
    shutil.rmtree(bootstrap, ignore_errors=True)
    bootstrap.mkdir(parents=True)
    with zipfile.ZipFile(setuptools_wheel) as zf:
        zf.extractall(bootstrap)
    dist = work / "wheel-dist"
    dist.mkdir(parents=True, exist_ok=True)
    env = clean_env(prefix, work)
    env["PYTHONPATH"] = str(bootstrap)
    env["CC"] = cc
    env["CXX"] = cxx
    env["AR"] = ar
    env["SOURCE_DATE_EPOCH"] = "315532800"
    cmd = [str(python), "setup.py", "bdist_wheel", "--dist-dir", str(dist)]
    p = run(cmd, cwd=project, env=env, timeout=1200)
    if p.returncode:
        raise RuntimeError(f"wheel build failed:\n{p.stdout}\n{p.stderr}")
    wheels = sorted(dist.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected one wheel, found {len(wheels)}")
    normalized, mutation = rewrite_wheel_without_rpath(wheels[0], patchelf, readelf, ut2, work)
    artifacts.mkdir(parents=True, exist_ok=True)
    final_name = "hw_t_native_probe-0.1.0-cp314-cp314-android_24_arm64_v8a.whl"
    final = artifacts / final_name
    shutil.copy2(normalized, final)
    identity = inspect_wheel(final)
    return {"build_command": cmd, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
            "setuptools_wheel": {"path": str(setuptools_wheel), "sha256": sha256(setuptools_wheel)},
            "raw_wheel": {"path": str(wheels[0]), "sha256": sha256(wheels[0])},
            "extension_normalization": mutation, "wheel": identity, "artifact_path": str(final)}


def compile_selected_launcher(ut2: Any, source: Path, prefix: Path, build: Path,
                              cc: str, patchelf: str, readelf: str) -> dict[str, Any]:
    build.mkdir(parents=True, exist_ok=True)
    include = prefix / "include/python3.14"
    lib = prefix / "lib"
    out = build / "la_2"
    desired = "$ORIGIN/../lib"
    cmd = [
        cc, "-fPIE", "-pie", "-O2", "-Wall", "-Wextra", "-pthread",
        "-Wl,-z,max-page-size=16384", "-Wl,-z,common-page-size=16384",
        f"-I{include}", str(source), f"-L{lib}", "-lpython3.14", "-ldl", "-lm", "-llog",
        "-Wl,--enable-new-dtags", f"-Wl,-rpath,{desired}", "-o", str(out),
    ]
    p = run(cmd, timeout=300)
    if p.returncode:
        raise RuntimeError(f"LA-2 compile failed:\n{p.stdout}\n{p.stderr}")
    normalization = ut2.normalize_launcher_runpath(out, desired, cc, patchelf, readelf)
    got = sha256(out)
    if got != EXPECTED_SELECTED_LAUNCHER_SHA:
        raise RuntimeError(f"reproduced LA-2 hash mismatch: {got}")
    return {"source": str(source), "source_sha256": sha256(source), "binary": str(out),
            "binary_sha256": got, "build_command": cmd, "runpath_normalization": normalization}


def reroot_pass(a: dict[str, Any], b: dict[str, Any], prefix_a: Path, prefix_b: Path) -> bool:
    if not a.get("pass") or not b.get("pass"):
        return False
    if not runtime_paths_within(a, prefix_a) or not runtime_paths_within(b, prefix_b):
        return False
    b_strings = path_strings(b.get("data"))
    return not any(str(prefix_a) in s for s in b_strings) and any(str(prefix_b) in s for s in b_strings)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--artifacts", type=Path, required=True)
    ap.add_argument("--source-dir", type=Path, required=True)
    ap.add_argument("--cc", default="clang")
    ap.add_argument("--cxx", default="clang++")
    ap.add_argument("--ar", default="llvm-ar")
    ap.add_argument("--patchelf", default="patchelf")
    ap.add_argument("--readelf", default="readelf")
    ap.add_argument("--pkg-config", default="pkg-config")
    args = ap.parse_args()
    root = args.root.resolve(); archive = args.archive.resolve(); work = args.work.resolve()
    out = args.output.resolve(); artifacts = args.artifacts.resolve(); source_dir = args.source_dir.resolve()
    work.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True); artifacts.mkdir(parents=True, exist_ok=True)

    if sha256(archive) != EXPECTED_ARCHIVE_SHA or archive.stat().st_size != EXPECTED_ARCHIVE_SIZE:
        raise SystemExit("official archive identity mismatch")
    authorities = {
        "upstream_control": root / "experiments/epoch2-upstream-thin-control/upstream-control-authority.json",
        "artifact_prototype": root / "experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json",
        "loader_relocation": root / "experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json",
    }
    expected_authorities = {
        "upstream_control": EXPECTED_CONTROL_SHA,
        "artifact_prototype": EXPECTED_ARTIFACT_SHA,
        "loader_relocation": EXPECTED_LOADER_SHA,
    }
    for key, path in authorities.items():
        if sha256(path) != expected_authorities[key]:
            raise SystemExit(f"authority identity mismatch: {key}")

    ut2, loader_authority = import_ut2_module(root)
    official = work / "official"
    shutil.rmtree(official, ignore_errors=True)
    extraction = ut2.safe_extract(archive, official)
    verification = ut2.verify_official_prefix(official, root / "experiments/epoch2-upstream-thin-control")
    if not verification["pass"]:
        raise SystemExit("official extraction verification failed")
    dump(out / "official-extraction-verification.json", {"schema_version": 1, "extraction": extraction, "verification": verification})

    prefix_a = work / "location-a/prefix"
    shutil.rmtree(prefix_a.parent, ignore_errors=True)
    prefix_a.parent.mkdir(parents=True)
    shutil.copytree(official / "prefix", prefix_a, symlinks=True)
    modules = set(load(root / "experiments/epoch2-upstream-thin-control/elf-and-extension-inventory.json")["native_extensions"])
    native_rows = ut2.patch_objects(prefix_a, "lr3", args.patchelf, args.readelf, modules)
    if not all(r["exact_mutation_check"] for r in native_rows):
        raise SystemExit("LR-3 reproduction mutation mismatch")
    launcher_source = root / "experiments/epoch2-upstream-thin-loader-relocation/launcher_la2_programs_python.c"
    launcher_build = compile_selected_launcher(ut2, launcher_source, prefix_a, work / "launcher-build",
                                               args.cc, args.patchelf, args.readelf)
    python_a = ut2.install_launcher(prefix_a, Path(launcher_build["binary"]))
    startup = ut2.execute_runtime_probe(python_a, prefix_a, work, [Path(x).name.split(".", 1)[0] for x in modules])
    if not (startup["startup_pass"] and startup["required_extension_failures"] == 0
            and startup["ld_library_path_absent"] and startup["self_reexec_absent"]):
        raise SystemExit("UT-2 runtime reproduction failed")
    dump(out / "runtime-reproduction.json", {"schema_version": 1, "launcher": launcher_build,
                                              "native_object_count": len(native_rows),
                                              "all_exact_mutations": all(r["exact_mutation_check"] for r in native_rows),
                                              "all_16k": all(r["alignment_16k_compatible"] for r in native_rows),
                                              "startup": startup})

    baseline_runtime = runtime_probe(python_a, prefix_a, work)
    baseline_text = scan_text_surfaces(prefix_a, str(prefix_a))
    baseline = {"schema_version": 1, "phase": "SC-0", "runtime": baseline_runtime,
                "text_surfaces": baseline_text,
                "producer_residue": producer_residue({"runtime": baseline_runtime, "text": baseline_text}),
                "known_producer_roots": list(PRODUCER_ROOTS)}
    dump(out / "absolute-path-census.json", baseline)

    mutations = normalize_runtime(prefix_a, python_a, work)
    normalized_a = runtime_probe(python_a, prefix_a, work)
    text_a = scan_text_surfaces(prefix_a, str(prefix_a))
    consumer_a = consumer_probe(python_a, prefix_a, work, args.pkg_config)
    if not normalized_a["pass"] or not runtime_paths_within(normalized_a, prefix_a):
        raise SystemExit("normalized runtime paths are not rooted in location A")
    if producer_residue({"runtime": normalized_a, "text": text_a, "consumer": consumer_a}):
        raise SystemExit("producer path residue remains after normalization")
    if text_a["classification_counts"].get("unknown-absolute", 0):
        raise SystemExit("unknown absolute path remains after normalization")
    if text_a["classification_counts"].get("stale-install-prefix", 0):
        raise SystemExit("stale /usr/local path remains after normalization")
    if not consumer_a["pass"]:
        raise SystemExit("consumer metadata probe failed at location A")
    dump(out / "normalization-mutations.json", mutations)

    wheel_evidence = build_wheel(python_a, prefix_a, source_dir, work, artifacts,
                                 args.cc, args.cxx, args.ar, args.patchelf, args.readelf, ut2)
    wheel_path = Path(wheel_evidence["artifact_path"])
    if not wheel_evidence["wheel"]["pass"]:
        raise SystemExit("wheel identity failed")
    venv_a = install_and_import(wheel_path, python_a, prefix_a, work, work / "venv-a")
    if not venv_a["pass"]:
        raise SystemExit("wheel install/import failed at location A")

    prefix_b = work / "location-b/prefix"
    prefix_b.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(prefix_a), str(prefix_b))
    python_b = prefix_b / "bin/python3.14"
    normalized_b = runtime_probe(python_b, prefix_b, work)
    text_b = scan_text_surfaces(prefix_b, str(prefix_b))
    consumer_b = consumer_probe(python_b, prefix_b, work, args.pkg_config)
    venv_b = install_and_import(wheel_path, python_b, prefix_b, work, work / "venv-b")
    reroot = reroot_pass(normalized_a, normalized_b, prefix_a, prefix_b)
    residue_b = producer_residue({"runtime": normalized_b, "text": text_b, "consumer": consumer_b})
    stale_a = sorted({s for s in path_strings({"runtime": normalized_b, "text": text_b, "consumer": consumer_b}) if str(prefix_a) in s})
    if not reroot:
        raise SystemExit("runtime paths did not re-root after movement")
    if residue_b or stale_a:
        raise SystemExit("producer or stale active-prefix residue after movement")
    if text_b["classification_counts"].get("unknown-absolute", 0) or text_b["classification_counts"].get("stale-install-prefix", 0):
        raise SystemExit("unknown or stale text metadata after movement")
    if not consumer_b["pass"] or not venv_b["pass"]:
        raise SystemExit("consumer metadata or relocated extension import failed")

    runtime_paths = {"schema_version": 1, "phase": "SC-1", "location_a": normalized_a,
                     "location_b_after_move": normalized_b, "reroot_after_movement": reroot,
                     "stale_location_a_references": stale_a, "producer_residue": residue_b}
    consumer_metadata = {"schema_version": 1, "phase": "SC-2", "location_a": consumer_a,
                         "location_b_after_move": consumer_b, "text_location_a": text_a,
                         "text_location_b": text_b, "pass": consumer_a["pass"] and consumer_b["pass"]}
    wheel_evidence.update({"schema_version": 1, "phase": "SC-3", "location_a": venv_a,
                           "location_b_after_base_move_fresh_venv": venv_b,
                           "relocated_extension_import_pass": venv_b["pass"]})
    sdk_decision = {
        "schema_version": 1, "phase": "SC-4", "product_selectable": False,
        "flavors": {
            "runtime-only": {"status": "representationally-required", "includes_development_metadata": False,
                             "reason": "runtime consumers do not require producer/build surfaces"},
            "on-device-sdk": {"status": "experimentally-supported", "execution_context": "Termux Android app process",
                              "compiler": "clang", "wheel_build_install_import_relocate": True},
            "cross-build-sdk": {"status": "unavailable", "reason": "no explicit relocatable NDK/sysroot authority is packaged"},
        },
        "epoch3_decision_enabled": True,
        "non_claims": ["Epoch 3 product selection", "broad device qualification", "publication"],
    }
    exit_condition = {
        "unknown_producer_absolute_paths": 0,
        "stale_active_install_prefixes": len(stale_a),
        "runtime_paths_reroot_after_movement": reroot,
        "native_extension_wheel_build": wheel_evidence["returncode"] == 0,
        "wheel_identity_correct": wheel_evidence["wheel"]["pass"],
        "relocated_extension_import": venv_b["pass"],
    }
    gate_condition = {
        "unknown_producer_absolute_paths_zero": exit_condition["unknown_producer_absolute_paths"] == 0,
        "stale_active_install_prefixes_zero": exit_condition["stale_active_install_prefixes"] == 0,
        "runtime_paths_reroot_after_movement": exit_condition["runtime_paths_reroot_after_movement"] is True,
        "native_extension_wheel_build": exit_condition["native_extension_wheel_build"] is True,
        "wheel_identity_correct": exit_condition["wheel_identity_correct"] is True,
        "relocated_extension_import": exit_condition["relocated_extension_import"] is True,
        "consumer_metadata_location_a": consumer_a["pass"] is True,
        "consumer_metadata_location_b": consumer_b["pass"] is True,
        "runtime_reproduction": startup["startup_pass"] is True,
        "lr3_exact_and_16k": all(r["exact_mutation_check"] and r["alignment_16k_compatible"] for r in native_rows),
    }
    passed = all(gate_condition.values())
    dump(out / "runtime-path-normalization.json", runtime_paths)
    dump(out / "consumer-metadata-normalization.json", consumer_metadata)
    dump(out / "native-extension-wheel-evidence.json", wheel_evidence)
    dump(out / "sdk-flavor-decision.json", sdk_decision)
    dump(out / "ut3-gate-diagnostics.json", {"schema_version": 1, "pass": passed,
                                               "exit_condition": exit_condition,
                                               "gate_condition": gate_condition,
                                               "failed_gate_conditions": [k for k, v in gate_condition.items() if not v]})
    if not passed:
        raise SystemExit("UT-3 gate failed: " + json.dumps(gate_condition, sort_keys=True))
    print(json.dumps({"pass": True, "exit_condition": exit_condition, "gate_condition": gate_condition,
                      "wheel": wheel_evidence["wheel"], "output": str(out)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
