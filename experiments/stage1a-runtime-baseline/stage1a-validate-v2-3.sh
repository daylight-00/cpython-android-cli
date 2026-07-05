#!/data/data/com.termux/files/usr/bin/bash
# Stage 1-A validation matrix v2.
#
# Fixes v1 behavior: native-module failures now make probes fail.
# Profiles:
#   clean   - no PYTHONHOME, PYTHONPATH, LD_LIBRARY_PATH
#   ldpath  - LD_LIBRARY_PATH=<prefix>/lib only
#   fullenv - PYTHONHOME + PYTHONPATH + LD_LIBRARY_PATH
#
# A profile is a Stage 1-A runtime candidate only if all required probes pass.

set -uo pipefail

CPYTHON_PREFIX="${CPYTHON_PREFIX:-$HOME/opt/cpython-3.14/prefix}"
CPYTHON_BIN="${CPYTHON_BIN:-$CPYTHON_PREFIX/bin/python}"
CPYTHON_LIB="${CPYTHON_LIB:-$CPYTHON_PREFIX/lib}"
CPYTHON_MM="${CPYTHON_MM:-3.14}"

UV_BIN="${UV_BIN:-$(command -v uv 2>/dev/null || true)}"
RESULTS_DIR="${RESULTS_DIR:-$PWD/stage1a-results-v2}"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$RESULTS_DIR/validate-v2-$STAMP.log"

mkdir -p "$RESULTS_DIR"

[[ -x "$CPYTHON_BIN" ]] || {
    echo "ERROR: CPython executable not found: $CPYTHON_BIN" >&2
    exit 2
}

[[ -n "$UV_BIN" && -x "$UV_BIN" ]] || {
    echo "ERROR: uv not found; set UV_BIN or add uv to PATH." >&2
    exit 2
}

exec > >(tee "$LOG") 2>&1

run_profile() {
    local profile="$1"
    shift

    case "$profile" in
        clean)
            env \
                -u PYTHONHOME \
                -u PYTHONPATH \
                -u LD_LIBRARY_PATH \
                "$@"
            ;;
        ldpath)
            env \
                -u PYTHONHOME \
                -u PYTHONPATH \
                LD_LIBRARY_PATH="$CPYTHON_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
                "$@"
            ;;
        fullenv)
            env \
                PYTHONHOME="$CPYTHON_PREFIX" \
                PYTHONPATH="$CPYTHON_PREFIX/lib/python$CPYTHON_MM" \
                LD_LIBRARY_PATH="$CPYTHON_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
                "$@"
            ;;
        *)
            echo "ERROR: unknown profile: $profile" >&2
            return 64
            ;;
    esac
}

probe_code='
import json
import os
import sys
import sysconfig

required = [
    "_ssl",
    "ssl",
    "_hashlib",
    "hashlib",
    "_sqlite3",
    "sqlite3",
    "_ctypes",
    "ctypes",
    "_bz2",
    "bz2",
    "_lzma",
    "lzma",
    "zlib",
]

result = {
    "executable": sys.executable,
    "prefix": sys.prefix,
    "base_prefix": sys.base_prefix,
    "is_venv": sys.prefix != sys.base_prefix,
    "platform": sys.platform,
    "sysconfig_platform": sysconfig.get_platform(),
    "environment": {
        "PYTHONHOME": os.environ.get("PYTHONHOME"),
        "PYTHONPATH": os.environ.get("PYTHONPATH"),
        "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH"),
    },
    "modules": {},
}

failed = []

for name in required:
    try:
        module = __import__(name)
        entry = {
            "ok": True,
            "file": getattr(module, "__file__", None),
        }
        if name == "ssl":
            entry["openssl"] = module.OPENSSL_VERSION
            entry["verify_paths"] = str(module.get_default_verify_paths())
        result["modules"][name] = entry
    except Exception as exc:
        result["modules"][name] = {
            "ok": False,
            "error": repr(exc),
        }
        failed.append(name)

print(json.dumps(result, indent=2, sort_keys=True))

if failed:
    raise SystemExit("required module failures: " + ", ".join(failed))
'

venv_probe_code='
import json
import sys

required = [
    "ssl",
    "hashlib",
    "sqlite3",
    "ctypes",
    "bz2",
    "lzma",
    "zlib",
]

result = {
    "executable": sys.executable,
    "prefix": sys.prefix,
    "base_prefix": sys.base_prefix,
    "is_venv": sys.prefix != sys.base_prefix,
    "modules": {},
}

failed = []

for name in required:
    try:
        __import__(name)
        result["modules"][name] = {"ok": True}
    except Exception as exc:
        result["modules"][name] = {
            "ok": False,
            "error": repr(exc),
        }
        failed.append(name)

print(json.dumps(result, indent=2, sort_keys=True))

if sys.prefix == sys.base_prefix:
    raise SystemExit("venv identity failure: sys.prefix == sys.base_prefix")

if failed:
    raise SystemExit("venv module failures: " + ", ".join(failed))
'

network_probe_code='
import ssl
import urllib.request

print("OpenSSL:", ssl.OPENSSL_VERSION)
print("Verify paths:", ssl.get_default_verify_paths())

with urllib.request.urlopen("https://pypi.org/simple/", timeout=15) as response:
    print("HTTPS status:", response.status)
'

run_test() {
    local label="$1"
    shift

    echo
    echo "-- $label --"

    "$@"
    local rc=$?

    if [[ $rc -eq 0 ]]; then
        echo "$label=PASS"
    else
        echo "$label=FAIL rc=$rc"
    fi

    return "$rc"
}

profile_summary() {
    local profile="$1"
    shift
    local failures=("$@")

    echo
    if [[ ${#failures[@]} -eq 0 ]]; then
        echo "PROFILE_RESULT[$profile]=PASS"
    else
        echo "PROFILE_RESULT[$profile]=FAIL"
        printf 'PROFILE_FAILURE[%s]=%s\n' "$profile" "${failures[*]}"
    fi
}

echo "============================================================"
echo "Stage 1-A validation v2"
echo "============================================================"
echo "timestamp=$STAMP"
echo "CPYTHON_PREFIX=$CPYTHON_PREFIX"
echo "CPYTHON_BIN=$CPYTHON_BIN"
echo "UV_BIN=$UV_BIN"

for profile in clean ldpath fullenv; do
    failures=()

    echo
    echo "############################################################"
    echo "PROFILE: $profile"
    echo "############################################################"

    run_test "BASE_NATIVE_PROBE" \
        run_profile "$profile" "$CPYTHON_BIN" -c "$probe_code" \
        || failures+=("BASE_NATIVE_PROBE")

    run_test "NETWORK_PROBE" \
        run_profile "$profile" "$CPYTHON_BIN" -c "$network_probe_code" \
        || failures+=("NETWORK_PROBE")

    VENV="$RESULTS_DIR/venv-$profile"
    rm -rf "$VENV"

    if run_test "UV_VENV_CREATE" \
        run_profile "$profile" "$UV_BIN" venv \
            --no-python-downloads \
            --python "$CPYTHON_BIN" \
            "$VENV"
    then
        run_test "VENV_NATIVE_PROBE" \
            run_profile "$profile" "$VENV/bin/python" -c "$venv_probe_code" \
            || failures+=("VENV_NATIVE_PROBE")

        run_test "UV_PIP_INSTALL" \
            run_profile "$profile" "$UV_BIN" pip install \
                --python "$VENV/bin/python" \
                anyio \
            || failures+=("UV_PIP_INSTALL")

        run_test "VENV_ANYIO_IMPORT" \
            run_profile "$profile" "$VENV/bin/python" \
                -c 'import anyio, sys; print(anyio.__name__); print(sys.prefix); print(sys.base_prefix)' \
            || failures+=("VENV_ANYIO_IMPORT")
    else
        failures+=("UV_VENV_CREATE")
    fi

    run_test "UV_RUN_EPHEMERAL" \
        run_profile "$profile" "$UV_BIN" run \
            --no-project \
            --no-python-downloads \
            --python "$CPYTHON_BIN" \
            --with anyio \
            python -c 'import anyio, sys; print(anyio.__name__); print(sys.executable); print(sys.prefix)' \
        || failures+=("UV_RUN_EPHEMERAL")

    profile_summary "$profile" "${failures[@]}"
done

echo
echo "============================================================"
echo "Validation complete"
echo "Log: $LOG"
echo "============================================================"
