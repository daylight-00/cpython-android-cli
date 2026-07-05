#!/data/data/com.termux/files/usr/bin/bash
# Stage 1-A validation matrix for Termux.
#
# Profiles:
#   clean   - unset PYTHONHOME, PYTHONPATH, LD_LIBRARY_PATH
#   ldpath  - only prefix/lib is added to LD_LIBRARY_PATH
#   fullenv - PYTHONHOME + PYTHONPATH + LD_LIBRARY_PATH
#
# This script measures the minimum correct runtime contract.
#
# It validates:
#   - base interpreter identity
#   - native stdlib imports
#   - Python HTTPS
#   - uv venv creation
#   - venv identity
#   - venv native stdlib imports
#   - uv pip install into explicit venv
#   - uv run with explicit Android Python and a pure-Python dependency

set -uo pipefail

CPYTHON_PREFIX="${CPYTHON_PREFIX:-$HOME/opt/cpython-3.14/prefix}"
CPYTHON_BIN="${CPYTHON_BIN:-$CPYTHON_PREFIX/bin/python}"
CPYTHON_LIB="${CPYTHON_LIB:-$CPYTHON_PREFIX/lib}"
CPYTHON_MM="${CPYTHON_MM:-3.14}"

UV_BIN="${UV_BIN:-$(command -v uv 2>/dev/null || true)}"
RESULTS_DIR="${RESULTS_DIR:-$PWD/stage1a-results}"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$RESULTS_DIR/validate-$STAMP.log"

mkdir -p "$RESULTS_DIR"

if [[ ! -x "$CPYTHON_BIN" ]]; then
    echo "ERROR: CPython executable not found: $CPYTHON_BIN" >&2
    exit 2
fi

if [[ -z "$UV_BIN" || ! -x "$UV_BIN" ]]; then
    echo "ERROR: uv not found; set UV_BIN or add uv to PATH." >&2
    exit 2
fi

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

base_probe='
import json
import os
import sys
import sysconfig

result = {
    "executable": sys.executable,
    "prefix": sys.prefix,
    "base_prefix": sys.base_prefix,
    "exec_prefix": sys.exec_prefix,
    "base_exec_prefix": sys.base_exec_prefix,
    "is_venv": sys.prefix != sys.base_prefix,
    "platform": sys.platform,
    "sysconfig_platform": sysconfig.get_platform(),
    "env": {
        "PYTHONHOME": os.environ.get("PYTHONHOME"),
        "PYTHONPATH": os.environ.get("PYTHONPATH"),
        "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH"),
    },
    "modules": {},
}

for name in ["_ssl", "ssl", "hashlib", "sqlite3", "ctypes", "bz2", "lzma", "zlib"]:
    try:
        module = __import__(name)
        result["modules"][name] = {
            "ok": True,
            "file": getattr(module, "__file__", None),
        }
        if name == "ssl":
            result["openssl"] = module.OPENSSL_VERSION
            result["verify_paths"] = str(module.get_default_verify_paths())
    except Exception as exc:
        result["modules"][name] = {
            "ok": False,
            "error": repr(exc),
        }

print(json.dumps(result, indent=2, sort_keys=True))
'

network_probe='
import ssl
import urllib.request

print("OpenSSL:", ssl.OPENSSL_VERSION)
print("Verify paths:", ssl.get_default_verify_paths())

with urllib.request.urlopen("https://pypi.org/simple/", timeout=15) as response:
    print("HTTPS status:", response.status)
'

venv_probe='
import json
import sys

result = {
    "executable": sys.executable,
    "prefix": sys.prefix,
    "base_prefix": sys.base_prefix,
    "is_venv": sys.prefix != sys.base_prefix,
    "modules": {},
}

for name in ["ssl", "hashlib", "sqlite3", "ctypes", "bz2", "lzma", "zlib"]:
    try:
        __import__(name)
        result["modules"][name] = "ok"
    except Exception as exc:
        result["modules"][name] = repr(exc)

print(json.dumps(result, indent=2, sort_keys=True))

if sys.prefix == sys.base_prefix:
    raise SystemExit("FAIL: venv identity is not active")
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

    return $rc
}

echo "============================================================"
echo "Stage 1-A validation"
echo "============================================================"
echo "timestamp=$STAMP"
echo "CPYTHON_PREFIX=$CPYTHON_PREFIX"
echo "CPYTHON_BIN=$CPYTHON_BIN"
echo "UV_BIN=$UV_BIN"
echo

for profile in clean ldpath fullenv; do
    echo
    echo "############################################################"
    echo "PROFILE: $profile"
    echo "############################################################"

    run_test "BASE_PROBE" \
        run_profile "$profile" "$CPYTHON_BIN" -c "$base_probe" || true

    run_test "NETWORK_PROBE" \
        run_profile "$profile" "$CPYTHON_BIN" -c "$network_probe" || true

    VENV="$RESULTS_DIR/venv-$profile"
    rm -rf "$VENV"

    if run_test "UV_VENV_CREATE" \
        run_profile "$profile" "$UV_BIN" venv \
            --no-python-downloads \
            --python "$CPYTHON_BIN" \
            "$VENV"
    then
        run_test "VENV_PROBE" \
            run_profile "$profile" "$VENV/bin/python" -c "$venv_probe" || true

        run_test "UV_PIP_INSTALL" \
            run_profile "$profile" "$UV_BIN" pip install \
                --python "$VENV/bin/python" \
                anyio || true

        run_test "VENV_ANYIO_IMPORT" \
            run_profile "$profile" "$VENV/bin/python" \
                -c 'import anyio, sys; print(anyio.__name__); print(sys.prefix); print(sys.base_prefix)' || true
    fi

    run_test "UV_RUN_EPHEMERAL" \
        run_profile "$profile" "$UV_BIN" run \
            --no-project \
            --no-python-downloads \
            --python "$CPYTHON_BIN" \
            --with anyio \
            python -c 'import anyio, sys; print(anyio.__name__); print(sys.executable); print(sys.prefix)' || true
done

echo
echo "============================================================"
echo "Validation complete"
echo "Log: $LOG"
echo "============================================================"
