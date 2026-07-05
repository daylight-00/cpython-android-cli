#!/data/data/com.termux/files/usr/bin/bash
# Stage 2 comparison validator.
#
# Profiles:
#   b0-external   Stage 1-B selected frontend + external Stage 1-A contract
#   b0-clean      negative control: B0 without external runtime integration
#   s2-setenv     self-location + setenv only
#   s2-update     self-location + bionic linker update
#   s2-reexec     self-location + env bootstrap + execv
#
# Run after:
#   source pristine-test/STAGE2_TEST_PREFIX.env

set -uo pipefail

: "${CPYTHON_PREFIX:?source STAGE2_TEST_PREFIX.env first}"
: "${B0_BIN:?source STAGE2_TEST_PREFIX.env first}"
: "${S2_SETENV_BIN:?source STAGE2_TEST_PREFIX.env first}"
: "${S2_UPDATE_BIN:?source STAGE2_TEST_PREFIX.env first}"
: "${S2_REEXEC_BIN:?source STAGE2_TEST_PREFIX.env first}"

TERMUX_PREFIX="${TERMUX_PREFIX:-${PREFIX:-/data/data/com.termux/files/usr}}"
TERMUX_CA="$TERMUX_PREFIX/etc/tls/cert.pem"
UV_BIN="${UV_BIN:-$(command -v uv 2>/dev/null || true)}"

RESULTS_DIR="${RESULTS_DIR:-$PWD/stage2-results}"
PYCACHE_ROOT="$RESULTS_DIR/pycache"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$RESULTS_DIR/compare-$STAMP.log"

mkdir -p "$RESULTS_DIR" "$PYCACHE_ROOT"
exec > >(tee "$LOG") 2>&1

[[ -n "$UV_BIN" && -x "$UV_BIN" ]] || {
    echo "ERROR: uv not found" >&2
    exit 2
}

run_profile() {
    local profile="$1"
    local bin="$2"
    shift 2

    case "$profile" in
        b0-external)
            env \
                -u PYTHONHOME \
                -u PYTHONPATH \
                -u CPYTHON_HOME \
                -u VIRTUAL_ENV \
                -u UV_PYTHON \
                LD_LIBRARY_PATH="$CPYTHON_PREFIX/lib" \
                SSL_CERT_FILE="$TERMUX_CA" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$profile" \
                "$bin" "$@"
            ;;
        b0-clean|s2-setenv|s2-update|s2-reexec)
            env \
                -u PYTHONHOME \
                -u PYTHONPATH \
                -u CPYTHON_HOME \
                -u LD_LIBRARY_PATH \
                -u SSL_CERT_FILE \
                -u SSL_CERT_DIR \
                -u VIRTUAL_ENV \
                -u UV_PYTHON \
                PREFIX="$TERMUX_PREFIX" \
                HOME="$HOME" \
                PATH="$TERMUX_PREFIX/bin:/system/bin" \
                TMPDIR="$TERMUX_PREFIX/tmp" \
                TERM="${TERM:-xterm-256color}" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$profile" \
                "$bin" "$@"
            ;;
        *)
            echo "unknown profile: $profile" >&2
            return 64
            ;;
    esac
}

run_uv_profile() {
    local profile="$1"
    local bin="$2"
    shift 2

    case "$profile" in
        b0-external)
            env \
                -u PYTHONHOME \
                -u PYTHONPATH \
                -u CPYTHON_HOME \
                -u VIRTUAL_ENV \
                -u UV_PYTHON \
                LD_LIBRARY_PATH="$CPYTHON_PREFIX/lib" \
                SSL_CERT_FILE="$TERMUX_CA" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$profile" \
                "$UV_BIN" "$@"
            ;;
        b0-clean|s2-setenv|s2-update|s2-reexec)
            env \
                -u PYTHONHOME \
                -u PYTHONPATH \
                -u CPYTHON_HOME \
                -u LD_LIBRARY_PATH \
                -u SSL_CERT_FILE \
                -u SSL_CERT_DIR \
                -u VIRTUAL_ENV \
                -u UV_PYTHON \
                PREFIX="$TERMUX_PREFIX" \
                HOME="$HOME" \
                PATH="$TERMUX_PREFIX/bin:/system/bin" \
                TMPDIR="$TERMUX_PREFIX/tmp" \
                TERM="${TERM:-xterm-256color}" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$profile" \
                "$UV_BIN" "$@"
            ;;
    esac
}

test_one() {
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

native_probe='
import json
import os
import sys
import sysconfig

mods = [
    "_ssl", "ssl",
    "_hashlib", "hashlib",
    "_sqlite3", "sqlite3",
    "_ctypes", "ctypes",
    "_bz2", "bz2",
    "_lzma", "lzma",
    "zlib",
]

for name in mods:
    __import__(name)
    print("import", name, "OK")

print(json.dumps({
    "executable": sys.executable,
    "prefix": sys.prefix,
    "base_prefix": sys.base_prefix,
    "platform": sys.platform,
    "sysconfig_platform": sysconfig.get_platform(),
    "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH"),
    "SSL_CERT_FILE": os.environ.get("SSL_CERT_FILE"),
}, indent=2, sort_keys=True))
'

network_probe='
import urllib.request
with urllib.request.urlopen("https://pypi.org/simple/", timeout=15) as r:
    print("HTTPS status:", r.status)
'

subprocess_probe='
import subprocess
import sys
print("parent:", sys.executable)
subprocess.run(
    [sys.executable, "-c",
     "import ssl,sqlite3,sys; print(\"child:\", sys.executable); print(sys.prefix); print(sys.base_prefix)"],
    check=True,
)
'

for spec in \
    "b0-external:$B0_BIN" \
    "b0-clean:$B0_BIN" \
    "s2-setenv:$S2_SETENV_BIN" \
    "s2-update:$S2_UPDATE_BIN" \
    "s2-reexec:$S2_REEXEC_BIN"
do
    profile="${spec%%:*}"
    bin="${spec#*:}"
    failures=()

    echo
    echo "################################################################"
    echo "PROFILE: $profile"
    echo "BIN: $bin"
    echo "################################################################"

    test_one "VERSION" \
        run_profile "$profile" "$bin" -V \
        || failures+=("VERSION")

    test_one "NATIVE" \
        run_profile "$profile" "$bin" -c "$native_probe" \
        || failures+=("NATIVE")

    test_one "NETWORK" \
        run_profile "$profile" "$bin" -c "$network_probe" \
        || failures+=("NETWORK")

    test_one "SUBPROCESS" \
        run_profile "$profile" "$bin" -c "$subprocess_probe" \
        || failures+=("SUBPROCESS")

    VENV="$RESULTS_DIR/venv-$profile"
    rm -rf "$VENV"

    if test_one "UV_VENV" \
        run_uv_profile "$profile" "$bin" venv \
            --no-python-downloads \
            --python "$bin" \
            "$VENV"
    then
        test_one "VENV_NATIVE" \
            run_profile "$profile" "$VENV/bin/python" -c '
import ssl
import sqlite3
import ctypes
import bz2
import lzma
import zlib
import sys
print("executable:", sys.executable)
print("prefix:", sys.prefix)
print("base_prefix:", sys.base_prefix)
assert sys.prefix != sys.base_prefix
' \
            || failures+=("VENV_NATIVE")
    else
        failures+=("UV_VENV")
    fi

    test_one "UV_RUN" \
        run_uv_profile "$profile" "$bin" run \
            --no-project \
            --no-python-downloads \
            --python "$bin" \
            --with anyio \
            python -c '
import anyio
import ssl
import sqlite3
import sys
print(anyio.__name__)
print(sys.executable)
print(sys.prefix)
print(sys.base_prefix)
' \
        || failures+=("UV_RUN")

    echo
    if [[ ${#failures[@]} -eq 0 ]]; then
        echo "PROFILE_RESULT[$profile]=PASS"
    else
        echo "PROFILE_RESULT[$profile]=FAIL"
        printf 'PROFILE_FAILURE[%s]=%s\n' \
            "$profile" "${failures[*]}"
    fi
done

echo
echo "Stage 2 comparison complete."
echo "Log: $LOG"
