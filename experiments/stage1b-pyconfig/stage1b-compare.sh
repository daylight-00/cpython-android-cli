#!/data/data/com.termux/files/usr/bin/bash
# Stage 1-B launcher comparison on Termux.
#
# The same frozen Stage 1-A runtime contract is used for every launcher:
#   LD_LIBRARY_PATH=<prefix>/lib
#   SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
#
# Launchers compared:
#   stage1a  - existing Py_BytesMain frontend
#   b0-auto  - PyConfig, no config.home override
#   b1-home  - PyConfig, config.home from CPYTHON_HOME
#
# Expected launcher placement:
#   <prefix>/bin/python
#   <prefix>/bin/python-pyconfig-auto
#   <prefix>/bin/python-pyconfig-home

set -uo pipefail

CPYTHON_PREFIX="${CPYTHON_PREFIX:-$HOME/opt/cpython-3.14/prefix}"
CPYTHON_LIB="${CPYTHON_LIB:-$CPYTHON_PREFIX/lib}"

BASE_BIN="${BASE_BIN:-$CPYTHON_PREFIX/bin/python}"
AUTO_BIN="${AUTO_BIN:-$CPYTHON_PREFIX/bin/python-pyconfig-auto}"
HOME_BIN="${HOME_BIN:-$CPYTHON_PREFIX/bin/python-pyconfig-home}"

TERMUX_PREFIX="${TERMUX_PREFIX:-${PREFIX:-/data/data/com.termux/files/usr}}"
TERMUX_CA_FILE="${TERMUX_CA_FILE:-$TERMUX_PREFIX/etc/tls/cert.pem}"

UV_BIN="${UV_BIN:-$(command -v uv 2>/dev/null || true)}"
RESULTS_DIR="${RESULTS_DIR:-$PWD/stage1b-results}"
PYCACHE_ROOT="${PYCACHE_ROOT:-$RESULTS_DIR/pycache}"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$RESULTS_DIR/compare-$STAMP.log"

mkdir -p "$RESULTS_DIR" "$PYCACHE_ROOT"

for bin in "$BASE_BIN" "$AUTO_BIN" "$HOME_BIN"; do
    [[ -x "$bin" ]] || {
        echo "ERROR: launcher not found or not executable: $bin" >&2
        exit 2
    }
done

[[ -n "$UV_BIN" && -x "$UV_BIN" ]] || {
    echo "ERROR: uv not found" >&2
    exit 2
}

[[ -f "$TERMUX_CA_FILE" ]] || {
    echo "ERROR: CA file not found: $TERMUX_CA_FILE" >&2
    exit 2
}

exec > >(tee "$LOG") 2>&1

run_launcher() {
    local variant="$1"
    local bin="$2"
    shift 2

    case "$variant" in
        stage1a|b0-auto)
            env \
                -u PYTHONHOME \
                -u PYTHONPATH \
                -u CPYTHON_HOME \
                LD_LIBRARY_PATH="$CPYTHON_LIB" \
                SSL_CERT_FILE="$TERMUX_CA_FILE" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$variant" \
                "$bin" "$@"
            ;;
        b1-home)
            env \
                -u PYTHONHOME \
                -u PYTHONPATH \
                CPYTHON_HOME="$CPYTHON_PREFIX" \
                LD_LIBRARY_PATH="$CPYTHON_LIB" \
                SSL_CERT_FILE="$TERMUX_CA_FILE" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$variant" \
                "$bin" "$@"
            ;;
        *)
            echo "ERROR: unknown variant: $variant" >&2
            return 64
            ;;
    esac
}

run_uv() {
    local variant="$1"
    local bin="$2"
    shift 2

    case "$variant" in
        stage1a|b0-auto)
            env \
                -u PYTHONHOME \
                -u PYTHONPATH \
                -u CPYTHON_HOME \
                -u VIRTUAL_ENV \
                -u UV_PYTHON \
                LD_LIBRARY_PATH="$CPYTHON_LIB" \
                SSL_CERT_FILE="$TERMUX_CA_FILE" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$variant" \
                "$UV_BIN" "$@"
            ;;
        b1-home)
            env \
                -u PYTHONHOME \
                -u PYTHONPATH \
                -u VIRTUAL_ENV \
                -u UV_PYTHON \
                CPYTHON_HOME="$CPYTHON_PREFIX" \
                LD_LIBRARY_PATH="$CPYTHON_LIB" \
                SSL_CERT_FILE="$TERMUX_CA_FILE" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$variant" \
                "$UV_BIN" "$@"
            ;;
    esac
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

print(json.dumps({
    "executable": sys.executable,
    "prefix": sys.prefix,
    "base_prefix": sys.base_prefix,
    "is_venv": sys.prefix != sys.base_prefix,
    "platform": sys.platform,
    "sysconfig_platform": sysconfig.get_platform(),
    "argv": sys.argv,
    "CPYTHON_HOME": os.environ.get("CPYTHON_HOME"),
    "openssl": ssl.OPENSSL_VERSION,
}, indent=2, sort_keys=True))
'

network_probe='
import urllib.request
with urllib.request.urlopen("https://pypi.org/simple/", timeout=15) as r:
    print("HTTPS status:", r.status)
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

for spec in \
    "stage1a:$BASE_BIN" \
    "b0-auto:$AUTO_BIN" \
    "b1-home:$HOME_BIN"
do
    variant="${spec%%:*}"
    bin="${spec#*:}"
    failures=()

    echo
    echo "############################################################"
    echo "VARIANT: $variant"
    echo "BIN: $bin"
    echo "############################################################"

    run_test "VERSION" \
        run_launcher "$variant" "$bin" -V \
        || failures+=("VERSION")

    run_test "COMMAND_MODE" \
        run_launcher "$variant" "$bin" -c "$probe" alpha beta \
        || failures+=("COMMAND_MODE")

    module_mode() {
        printf '%s\n' '{"stage": "1B"}' \
            | run_launcher "$variant" "$bin" -m json.tool
    }

    run_test "MODULE_MODE" module_mode \
        || failures+=("MODULE_MODE")

    SCRIPT="$RESULTS_DIR/argv-$variant.py"
    cat > "$SCRIPT" <<'PY'
import json
import sys
print(json.dumps(sys.argv))
PY

    run_test "SCRIPT_MODE" \
        run_launcher "$variant" "$bin" "$SCRIPT" one two \
        || failures+=("SCRIPT_MODE")

    run_test "NETWORK" \
        run_launcher "$variant" "$bin" -c "$network_probe" \
        || failures+=("NETWORK")

    VENV="$RESULTS_DIR/venv-$variant"
    rm -rf "$VENV"

    if run_test "UV_VENV" \
        run_uv "$variant" "$bin" venv \
            --no-python-downloads \
            --python "$bin" \
            "$VENV"
    then
        run_test "VENV_IDENTITY" \
            run_launcher "$variant" "$VENV/bin/python" -c '
import sys
import ssl
import sqlite3
print("executable:", sys.executable)
print("prefix:", sys.prefix)
print("base_prefix:", sys.base_prefix)
print("is_venv:", sys.prefix != sys.base_prefix)
assert sys.prefix != sys.base_prefix
' \
            || failures+=("VENV_IDENTITY")

        run_test "UV_PIP_INSTALL" \
            run_uv "$variant" "$bin" pip install \
                --python "$VENV/bin/python" \
                anyio \
            || failures+=("UV_PIP_INSTALL")

        run_test "VENV_PACKAGE_IMPORT" \
            run_launcher "$variant" "$VENV/bin/python" \
                -c 'import anyio; print(anyio.__name__)' \
            || failures+=("VENV_PACKAGE_IMPORT")
    else
        failures+=("UV_VENV")
    fi

    run_test "UV_RUN" \
        run_uv "$variant" "$bin" run \
            --no-project \
            --no-python-downloads \
            --python "$bin" \
            --with anyio \
            python -c '
import anyio
import sys
print(anyio.__name__)
print(sys.executable)
print(sys.prefix)
print(sys.base_prefix)
' \
        || failures+=("UV_RUN")

    echo
    if [[ ${#failures[@]} -eq 0 ]]; then
        echo "VARIANT_RESULT[$variant]=PASS"
    else
        echo "VARIANT_RESULT[$variant]=FAIL"
        printf 'VARIANT_FAILURE[%s]=%s\n' "$variant" "${failures[*]}"
    fi
done

echo
echo "Stage 1-B comparison complete."
echo "Log: $LOG"
