#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-A production-shape whole-prefix relocation reconfirmation.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

SOURCE_PREFIX="${SOURCE_PREFIX:-$TERMUX_WORK_ROOT/runtime/prefix}"
TERMUX_PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
UV_BIN="${UV_BIN:-$(command -v uv || true)}"
ROOT="${ROOT:-$TERMUX_WORK_ROOT/stage3a-relocation-reconfirm}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3a-runtime-closure/relocation-reconfirm}"

A_PREFIX="$ROOT/location-a/prefix"
B_PREFIX="$ROOT/location-b/prefix"
PYCACHE_ROOT="$RESULTS_DIR/pycache"
LOG="$RESULTS_DIR/reconfirm.log"

[[ -x "$SOURCE_PREFIX/bin/python" ]] || {
    echo "ERROR: source runtime not found: $SOURCE_PREFIX/bin/python" >&2
    exit 2
}

[[ -n "$UV_BIN" && -x "$UV_BIN" ]] || {
    echo "ERROR: uv not found" >&2
    exit 2
}

rm -rf "$ROOT" "$RESULTS_DIR"
mkdir -p "$ROOT/location-a" "$ROOT/location-b" "$RESULTS_DIR" "$PYCACHE_ROOT"
exec > >(tee "$LOG") 2>&1

printf 'SOURCE_PREFIX=%s\n' "$SOURCE_PREFIX"
printf 'A_PREFIX=%s\n' "$A_PREFIX"
printf 'B_PREFIX=%s\n' "$B_PREFIX"

echo "== Copy canonical runtime to location A =="
cp -a "$SOURCE_PREFIX" "$A_PREFIX"

run_clean() {
    local python_bin="$1"
    shift

    env \
        -u PYTHONHOME \
        -u PYTHONPATH \
        -u CPYTHON_HOME \
        -u LD_LIBRARY_PATH \
        -u SSL_CERT_FILE \
        -u SSL_CERT_DIR \
        -u PYTHONTZPATH \
        -u VIRTUAL_ENV \
        -u UV_PYTHON \
        PREFIX="$TERMUX_PREFIX" \
        HOME="$HOME" \
        PATH="$TERMUX_PREFIX/bin:/system/bin" \
        TMPDIR="$TERMUX_PREFIX/tmp" \
        TERM="${TERM:-xterm-256color}" \
        PYTHONDONTWRITEBYTECODE=1 \
        PYTHONPYCACHEPREFIX="$PYCACHE_ROOT" \
        "$python_bin" "$@"
}

run_uv_clean() {
    env \
        -u PYTHONHOME \
        -u PYTHONPATH \
        -u CPYTHON_HOME \
        -u LD_LIBRARY_PATH \
        -u SSL_CERT_FILE \
        -u SSL_CERT_DIR \
        -u PYTHONTZPATH \
        -u VIRTUAL_ENV \
        -u UV_PYTHON \
        PREFIX="$TERMUX_PREFIX" \
        HOME="$HOME" \
        PATH="$TERMUX_PREFIX/bin:/system/bin" \
        TMPDIR="$TERMUX_PREFIX/tmp" \
        TERM="${TERM:-xterm-256color}" \
        PYTHONDONTWRITEBYTECODE=1 \
        PYTHONPYCACHEPREFIX="$PYCACHE_ROOT" \
        UV_PYTHON_DOWNLOADS=never \
        "$UV_BIN" "$@"
}

validate_location() {
    local label="$1"
    local prefix="$2"
    local forbidden_prefix="$3"
    local python_bin="$prefix/bin/python"
    local venv="$RESULTS_DIR/venv-$label"

    echo
    echo "============================================================"
    echo "LOCATION=$label"
    echo "PREFIX=$prefix"
    echo "============================================================"

    LOCATION_LABEL="$label" \
    EXPECTED_PREFIX="$prefix" \
    FORBIDDEN_PREFIX="$forbidden_prefix" \
    run_clean "$python_bin" - <<'PY'
import ctypes
import json
import lzma
import os
import sqlite3
import ssl
import subprocess
import sys
import sysconfig
import urllib.request

expected = os.environ["EXPECTED_PREFIX"]
forbidden = os.environ["FORBIDDEN_PREFIX"]

assert sys.prefix == expected, (sys.prefix, expected)
assert sys.base_prefix == expected, (sys.base_prefix, expected)
assert sys.executable.startswith(expected + "/bin/"), sys.executable
assert all(forbidden not in entry for entry in sys.path), sys.path
assert all(forbidden not in value for value in sysconfig.get_paths().values())

ctypes.CDLL("libc.so")
with sqlite3.connect(":memory:") as db:
    assert db.execute("select 1").fetchone() == (1,)

with urllib.request.urlopen("https://pypi.org/simple/", timeout=20) as response:
    assert response.status == 200

child = subprocess.check_output(
    [
        sys.executable,
        "-c",
        "import json,sys; print(json.dumps([sys.executable,sys.prefix,sys.base_prefix]))",
    ],
    text=True,
)
child_identity = json.loads(child)
assert all(forbidden not in value for value in child_identity), child_identity

print(json.dumps({
    "label": os.environ["LOCATION_LABEL"],
    "sys_executable": sys.executable,
    "sys_prefix": sys.prefix,
    "sys_base_prefix": sys.base_prefix,
    "https_status": 200,
    "child_identity": child_identity,
    "active_sysconfig_paths": sysconfig.get_paths(),
}, indent=2, sort_keys=True))
PY

    rm -rf "$venv"
    run_uv_clean \
        venv \
        --no-python-downloads \
        --python "$python_bin" \
        "$venv"

    EXPECTED_BASE="$prefix" \
    FORBIDDEN_PREFIX="$forbidden_prefix" \
    run_clean "$venv/bin/python" - <<'PY'
import os
import sqlite3
import ssl
import sys
import sysconfig

expected_base = os.environ["EXPECTED_BASE"]
forbidden = os.environ["FORBIDDEN_PREFIX"]
assert sys.prefix != sys.base_prefix
assert sys.base_prefix == expected_base, (sys.base_prefix, expected_base)
assert forbidden not in sys.base_prefix
assert all(forbidden not in entry for entry in sys.path)
assert all(forbidden not in value for value in sysconfig.get_paths().values())
print("VENV_RECONFIRM=PASS")
PY

    EXPECTED_BASE="$prefix" \
    FORBIDDEN_PREFIX="$forbidden_prefix" \
    run_uv_clean \
        run \
        --no-project \
        --no-python-downloads \
        --python "$python_bin" \
        --with anyio \
        python - <<'PY'
import anyio
import os
import sqlite3
import ssl
import sys
import sysconfig

expected_base = os.environ["EXPECTED_BASE"]
forbidden = os.environ["FORBIDDEN_PREFIX"]
assert sys.base_prefix == expected_base, (sys.base_prefix, expected_base)
assert forbidden not in sys.base_prefix
assert all(forbidden not in entry for entry in sys.path)
assert all(forbidden not in value for value in sysconfig.get_paths().values())
print(anyio.__name__)
print("UV_RUN_RECONFIRM=PASS")
PY

    echo "LOCATION_RECONFIRM[$label]=PASS"
}

# At A, use an impossible sentinel as the forbidden stale prefix.
validate_location "A" "$A_PREFIX" "/__stage3a_impossible_stale_prefix__"

echo
echo "== Move whole runtime A -> B =="
mv "$A_PREFIX" "$B_PREFIX"

# At B, the old A prefix is the forbidden stale path.
validate_location "B" "$B_PREFIX" "$A_PREFIX"

echo
echo "STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS"
echo "STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS"
