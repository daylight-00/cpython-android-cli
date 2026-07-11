#!/data/data/com.termux/files/usr/bin/bash
# Stage 2-C production-shape smoke validation.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../lib/project-env.sh"

RUNTIME_ROOT="${RUNTIME_ROOT_OVERRIDE:-$TERMUX_WORK_ROOT/runtime}"
RUNTIME_PREFIX="$RUNTIME_ROOT/prefix"
PYTHON_BIN="$RUNTIME_PREFIX/bin/python"
SMOKE_RESULTS_ROOT="${TERMUX_RESULTS_ROOT_OVERRIDE:-$TERMUX_RESULTS_ROOT}"

TERMUX_PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
UV_BIN="${UV_BIN:-$(command -v uv)}"

[[ -x "$PYTHON_BIN" ]] || {
    echo "ERROR: prepared runtime not found; run prepare-runtime.sh first" >&2
    exit 2
}

mkdir -p "$SMOKE_RESULTS_ROOT"

clean_env=(
    env
    -u PYTHONHOME
    -u PYTHONPATH
    -u CPYTHON_HOME
    -u LD_LIBRARY_PATH
    -u SSL_CERT_FILE
    -u SSL_CERT_DIR
    -u VIRTUAL_ENV
    -u UV_PYTHON
    PREFIX="$TERMUX_PREFIX"
    HOME="$HOME"
    PATH="$TERMUX_PREFIX/bin:/system/bin"
    TMPDIR="$TERMUX_PREFIX/tmp"
    TERM="${TERM:-xterm-256color}"
)

echo "== Base runtime =="

"${clean_env[@]}" \
    "$PYTHON_BIN" - <<'PY'
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
PY

echo
echo "== uv venv =="

VENV="$SMOKE_RESULTS_ROOT/venv"
rm -rf "$VENV"

"${clean_env[@]}" \
    "$UV_BIN" venv \
    --no-python-downloads \
    --python "$PYTHON_BIN" \
    "$VENV"

"${clean_env[@]}" \
    "$VENV/bin/python" - <<'PY'
import ssl
import sqlite3
import sys

print("executable:", sys.executable)
print("prefix:", sys.prefix)
print("base_prefix:", sys.base_prefix)

assert sys.prefix != sys.base_prefix
PY

echo
echo "== uv run =="

"${clean_env[@]}" \
    "$UV_BIN" run \
    --no-project \
    --no-python-downloads \
    --python "$PYTHON_BIN" \
    --with anyio \
    python - <<'PY'
import anyio
import ssl
import sqlite3
import sys

print(anyio.__name__)
print(sys.executable)
print(sys.prefix)
print(sys.base_prefix)
PY

echo
echo "STAGE2C_SMOKE=PASS"
