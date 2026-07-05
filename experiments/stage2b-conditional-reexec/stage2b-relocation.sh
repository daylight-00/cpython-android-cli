#!/data/data/com.termux/files/usr/bin/bash
# Stage 2-B whole-prefix relocation test.
#
# This script:
#   1. copies the prepared pristine prefix to location A,
#   2. validates R2 from A,
#   3. moves the entire prefix from A to B,
#   4. validates R2 again from B,
#   5. checks native imports, HTTPS, subprocess, uv venv, and uv run.

set -uo pipefail

: "${CPYTHON_PREFIX:?source STAGE2B_TEST_PREFIX.env first}"

TERMUX_PREFIX="${TERMUX_PREFIX:-${PREFIX:-/data/data/com.termux/files/usr}}"
UV_BIN="${UV_BIN:-$(command -v uv 2>/dev/null || true)}"

ROOT="${ROOT:-$PWD/stage2b-relocation}"
A_PARENT="$ROOT/location-a"
B_PARENT="$ROOT/location-b"
A_PREFIX="$A_PARENT/prefix"
B_PREFIX="$B_PARENT/prefix"

RESULTS_DIR="$ROOT/results"
PYCACHE_ROOT="$ROOT/pycache"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$RESULTS_DIR/relocation-$STAMP.log"

mkdir -p "$RESULTS_DIR" "$PYCACHE_ROOT"
exec > >(tee "$LOG") 2>&1

rm -rf "$A_PARENT" "$B_PARENT"
mkdir -p "$A_PARENT" "$B_PARENT"

echo "== Copy pristine Stage 2-B prefix to A =="
cp -a "$CPYTHON_PREFIX" "$A_PREFIX"

run_clean() {
    local bin="$1"
    shift

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
        PYTHONPYCACHEPREFIX="$PYCACHE_ROOT" \
        "$bin" "$@"
}

run_uv_clean() {
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
        PYTHONPYCACHEPREFIX="$PYCACHE_ROOT" \
        "$UV_BIN" "$@"
}

probe='
import os
import ssl
import sqlite3
import ctypes
import bz2
import lzma
import zlib
import subprocess
import sys
import urllib.request

print("executable:", sys.executable)
print("prefix:", sys.prefix)
print("base_prefix:", sys.base_prefix)
print("LD_LIBRARY_PATH:", os.environ.get("LD_LIBRARY_PATH"))
print("SSL_CERT_FILE:", os.environ.get("SSL_CERT_FILE"))

with urllib.request.urlopen("https://pypi.org/simple/", timeout=15) as r:
    print("HTTPS status:", r.status)

subprocess.run(
    [
        sys.executable,
        "-c",
        "import ssl,sqlite3,sys; print(sys.executable); print(sys.prefix); print(sys.base_prefix)",
    ],
    check=True,
)
'

validate_location() {
    local label="$1"
    local prefix="$2"
    local bin="$prefix/bin/python-s2-r2"
    local venv="$RESULTS_DIR/venv-$label"

    echo
    echo "################################################################"
    echo "LOCATION: $label"
    echo "PREFIX: $prefix"
    echo "################################################################"

    run_clean "$bin" -c "$probe"
    probe_rc=$?
    echo "RELOCATION_PROBE[$label]=$probe_rc"

    rm -rf "$venv"

    run_uv_clean \
        venv \
        --no-python-downloads \
        --python "$bin" \
        "$venv"
    uv_venv_rc=$?
    echo "RELOCATION_UV_VENV[$label]=$uv_venv_rc"

    if [[ $uv_venv_rc -eq 0 ]]; then
        run_clean "$venv/bin/python" -c '
import ssl
import sqlite3
import sys
print(sys.executable)
print(sys.prefix)
print(sys.base_prefix)
assert sys.prefix != sys.base_prefix
'
        venv_rc=$?
        echo "RELOCATION_VENV_RUN[$label]=$venv_rc"
    fi

    run_uv_clean \
        run \
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
'
    uv_run_rc=$?
    echo "RELOCATION_UV_RUN[$label]=$uv_run_rc"
}

validate_location "A" "$A_PREFIX"

echo
echo "== Move entire prefix A -> B =="
mv "$A_PREFIX" "$B_PREFIX"

validate_location "B" "$B_PREFIX"

echo
echo "Stage 2-B relocation test complete."
echo "Log: $LOG"
