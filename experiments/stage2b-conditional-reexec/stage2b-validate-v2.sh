#!/data/data/com.termux/files/usr/bin/bash
# Stage 2-B R2 validation.
#
# Profiles:
#   clean       no LD_LIBRARY_PATH / SSL_CERT_FILE
#   ready       correct LD_LIBRARY_PATH and CA already present
#   wrong-ld    wrong LD_LIBRARY_PATH that R2 must repair via re-exec
#   wrong-ca    correct LD path, nonexistent CA path; repair in-process
#   duplicate   duplicated required libdir; normalize without re-exec
#
# Additional:
#   unrelated cwd
#   external symlink invocation
#   subprocess re-entry
#   uv venv and venv clean launch
#   uv run

set -uo pipefail

: "${CPYTHON_PREFIX:?source STAGE2B_TEST_PREFIX.env first}"
: "${S2_R2_BIN:?source STAGE2B_TEST_PREFIX.env first}"

TERMUX_PREFIX="${TERMUX_PREFIX:-${PREFIX:-/data/data/com.termux/files/usr}}"
TERMUX_CA="$TERMUX_PREFIX/etc/tls/cert.pem"
UV_BIN="${UV_BIN:-$(command -v uv 2>/dev/null || true)}"

RESULTS_DIR="${RESULTS_DIR:-$PWD/stage2b-results}"
PYCACHE_ROOT="$RESULTS_DIR/pycache"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$RESULTS_DIR/validate-$STAMP.log"

mkdir -p "$RESULTS_DIR" "$PYCACHE_ROOT"
exec > >(tee "$LOG") 2>&1

[[ -n "$UV_BIN" && -x "$UV_BIN" ]] || {
    echo "ERROR: uv not found" >&2
    exit 2
}

[[ -f "$TERMUX_CA" ]] || {
    echo "ERROR: Termux CA bundle not found: $TERMUX_CA" >&2
    exit 2
}

base_unsets=(
    -u PYTHONHOME
    -u PYTHONPATH
    -u CPYTHON_HOME
    -u SSL_CERT_DIR
    -u VIRTUAL_ENV
    -u UV_PYTHON
)

base_assignments=(
    PREFIX="$TERMUX_PREFIX"
    HOME="$HOME"
    PATH="$TERMUX_PREFIX/bin:/system/bin"
    TMPDIR="$TERMUX_PREFIX/tmp"
    TERM="${TERM:-xterm-256color}"
)

run_profile() {
    local profile="$1"
    shift

    case "$profile" in
        clean)
            env \
                "${base_unsets[@]}" \
                -u LD_LIBRARY_PATH \
                -u SSL_CERT_FILE \
                "${base_assignments[@]}" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$profile" \
                "$S2_R2_BIN" "$@"
            ;;
        ready)
            env \
                "${base_unsets[@]}" \
                "${base_assignments[@]}" \
                LD_LIBRARY_PATH="$CPYTHON_PREFIX/lib" \
                SSL_CERT_FILE="$TERMUX_CA" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$profile" \
                "$S2_R2_BIN" "$@"
            ;;
        wrong-ld)
            env \
                "${base_unsets[@]}" \
                "${base_assignments[@]}" \
                LD_LIBRARY_PATH="$RESULTS_DIR/not-the-python-lib" \
                SSL_CERT_FILE="$TERMUX_CA" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$profile" \
                "$S2_R2_BIN" "$@"
            ;;
        wrong-ca)
            env \
                "${base_unsets[@]}" \
                "${base_assignments[@]}" \
                LD_LIBRARY_PATH="$CPYTHON_PREFIX/lib" \
                SSL_CERT_FILE="$RESULTS_DIR/missing-ca.pem" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$profile" \
                "$S2_R2_BIN" "$@"
            ;;
        duplicate)
            env \
                "${base_unsets[@]}" \
                "${base_assignments[@]}" \
                LD_LIBRARY_PATH="$CPYTHON_PREFIX/lib:$CPYTHON_PREFIX/lib" \
                SSL_CERT_FILE="$TERMUX_CA" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$profile" \
                "$S2_R2_BIN" "$@"
            ;;
        *)
            echo "unknown profile: $profile" >&2
            return 64
            ;;
    esac
}

run_uv_clean() {
    env \
        "${base_unsets[@]}" \
        -u LD_LIBRARY_PATH \
        -u SSL_CERT_FILE \
        "${base_assignments[@]}" \
        PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/uv" \
        "$UV_BIN" "$@"
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

probe='
import json
import os
import ssl
import sqlite3
import ctypes
import bz2
import lzma
import zlib
import sys
import sysconfig
import urllib.request

with urllib.request.urlopen("https://pypi.org/simple/", timeout=15) as r:
    https_status = r.status

print(json.dumps({
    "executable": sys.executable,
    "prefix": sys.prefix,
    "base_prefix": sys.base_prefix,
    "is_venv": sys.prefix != sys.base_prefix,
    "platform": sys.platform,
    "sysconfig_platform": sysconfig.get_platform(),
    "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH"),
    "SSL_CERT_FILE": os.environ.get("SSL_CERT_FILE"),
    "https_status": https_status,
}, indent=2, sort_keys=True))
'

for profile in clean ready wrong-ld wrong-ca duplicate; do
    failures=()

    echo
    echo "################################################################"
    echo "PROFILE: $profile"
    echo "################################################################"

    test_one "PROBE" \
        run_profile "$profile" -c "$probe" \
        || failures+=("PROBE")

    if [[ ${#failures[@]} -eq 0 ]]; then
        echo "PROFILE_RESULT[$profile]=PASS"
    else
        echo "PROFILE_RESULT[$profile]=FAIL"
        printf 'PROFILE_FAILURE[%s]=%s\n' \
            "$profile" "${failures[*]}"
    fi
done

echo
echo "################################################################"
echo "TEST: clean debug trace"
echo "################################################################"

env \
    "${base_unsets[@]}" \
    -u LD_LIBRARY_PATH \
    -u SSL_CERT_FILE \
    "${base_assignments[@]}" \
    CPYTHON_STAGE2_DEBUG=1 \
    "$S2_R2_BIN" \
    -c 'print("clean-trace-ok")' \
    2>&1 | tee "$RESULTS_DIR/trace-clean.log"

echo
echo "################################################################"
echo "TEST: ready debug trace"
echo "################################################################"

env \
    "${base_unsets[@]}" \
    "${base_assignments[@]}" \
    LD_LIBRARY_PATH="$CPYTHON_PREFIX/lib" \
    SSL_CERT_FILE="$TERMUX_CA" \
    CPYTHON_STAGE2_DEBUG=1 \
    "$S2_R2_BIN" \
    -c 'print("ready-trace-ok")' \
    2>&1 | tee "$RESULTS_DIR/trace-ready.log"

echo
echo "################################################################"
echo "TEST: unrelated cwd"
echo "################################################################"

mkdir -p "$RESULTS_DIR/unrelated-cwd"

(
    cd "$RESULTS_DIR/unrelated-cwd" || exit 1

    env \
        "${base_unsets[@]}" \
        -u LD_LIBRARY_PATH \
        -u SSL_CERT_FILE \
        "${base_assignments[@]}" \
        "$S2_R2_BIN" \
        -c "$probe"
)
cwd_rc=$?
echo "UNRELATED_CWD_RC=$cwd_rc"

echo
echo "################################################################"
echo "TEST: external symlink invocation"
echo "################################################################"

mkdir -p "$RESULTS_DIR/external-link"
SYMLINK_BIN="$RESULTS_DIR/external-link/python-r2-link"
ln -sfn "$S2_R2_BIN" "$SYMLINK_BIN"

env \
    "${base_unsets[@]}" \
    -u LD_LIBRARY_PATH \
    -u SSL_CERT_FILE \
    "${base_assignments[@]}" \
    "$SYMLINK_BIN" \
    -c "$probe"
symlink_rc=$?
echo "SYMLINK_RC=$symlink_rc"

echo
echo "################################################################"
echo "TEST: subprocess re-entry"
echo "################################################################"

subprocess_code='
import os
import subprocess
import sys

print("parent:", sys.executable)
print("parent LD_LIBRARY_PATH:", os.environ.get("LD_LIBRARY_PATH"))

subprocess.run(
    [
        sys.executable,
        "-c",
        """
import os
import ssl
import sqlite3
import sys

print("child:", sys.executable)
print("child prefix:", sys.prefix)
print("child base_prefix:", sys.base_prefix)
print("child LD_LIBRARY_PATH:", os.environ.get("LD_LIBRARY_PATH"))
""",
    ],
    check=True,
)
'

env \
    "${base_unsets[@]}" \
    -u LD_LIBRARY_PATH \
    -u SSL_CERT_FILE \
    "${base_assignments[@]}" \
    CPYTHON_STAGE2_DEBUG=1 \
    "$S2_R2_BIN" \
    -c "$subprocess_code" \
    2>&1 | tee "$RESULTS_DIR/subprocess.log"

subprocess_rc=${PIPESTATUS[0]}
echo "SUBPROCESS_RC=$subprocess_rc"

echo
echo "################################################################"
echo "TEST: uv venv"
echo "################################################################"

VENV="$RESULTS_DIR/venv-r2"
rm -rf "$VENV"

run_uv_clean \
    venv \
    --no-python-downloads \
    --python "$S2_R2_BIN" \
    "$VENV"
uv_venv_rc=$?
echo "UV_VENV_RC=$uv_venv_rc"

if [[ $uv_venv_rc -eq 0 ]]; then
    echo
    echo "== venv clean launch =="

    env \
        "${base_unsets[@]}" \
        -u LD_LIBRARY_PATH \
        -u SSL_CERT_FILE \
        "${base_assignments[@]}" \
        CPYTHON_STAGE2_DEBUG=1 \
        "$VENV/bin/python" \
        -c '
import ssl
import sqlite3
import sys

print("executable:", sys.executable)
print("prefix:", sys.prefix)
print("base_prefix:", sys.base_prefix)
print("is_venv:", sys.prefix != sys.base_prefix)
assert sys.prefix != sys.base_prefix
' \
        2>&1 | tee "$RESULTS_DIR/venv-clean.log"

    venv_clean_rc=${PIPESTATUS[0]}
    echo "VENV_CLEAN_RC=$venv_clean_rc"
fi

echo
echo "################################################################"
echo "TEST: uv run"
echo "################################################################"

run_uv_clean \
    run \
    --no-project \
    --no-python-downloads \
    --python "$S2_R2_BIN" \
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
echo "UV_RUN_RC=$uv_run_rc"

echo
echo "################################################################"
echo "Stage 2-B validation complete"
echo "Log: $LOG"
echo "################################################################"
