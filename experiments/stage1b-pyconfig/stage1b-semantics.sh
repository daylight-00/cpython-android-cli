#!/data/data/com.termux/files/usr/bin/bash
# Stage 1-B semantic differential test.
#
# Compares:
#   stage1a  - Py_BytesMain baseline
#   b0-auto  - PyConfig without config.home override
#   b1-home  - PyConfig with config.home from CPYTHON_HOME
#
# Focus:
#   CLI/config semantics rather than repeating Stage 1-A native/HTTPS coverage.
#
# Prerequisite:
#   source pristine-test/STAGE1B_TEST_PREFIX.env

set -uo pipefail

: "${CPYTHON_PREFIX:?source STAGE1B_TEST_PREFIX.env first}"
: "${BASE_BIN:?source STAGE1B_TEST_PREFIX.env first}"
: "${AUTO_BIN:?source STAGE1B_TEST_PREFIX.env first}"
: "${HOME_BIN:?source STAGE1B_TEST_PREFIX.env first}"

CPYTHON_LIB="${CPYTHON_LIB:-$CPYTHON_PREFIX/lib}"
TERMUX_PREFIX="${TERMUX_PREFIX:-${PREFIX:-/data/data/com.termux/files/usr}}"
TERMUX_CA_FILE="${TERMUX_CA_FILE:-$TERMUX_PREFIX/etc/tls/cert.pem}"

RESULTS_DIR="${RESULTS_DIR:-$PWD/stage1b-semantics-results}"
PYCACHE_ROOT="$RESULTS_DIR/pycache"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$RESULTS_DIR/semantics-$STAMP.log"

mkdir -p "$RESULTS_DIR" "$PYCACHE_ROOT"
exec > >(tee "$LOG") 2>&1

run_variant() {
    local variant="$1"
    local bin="$2"
    shift 2

    case "$variant" in
        stage1a|b0-auto)
            env \
                -u PYTHONHOME \
                -u CPYTHON_HOME \
                LD_LIBRARY_PATH="$CPYTHON_LIB" \
                SSL_CERT_FILE="$TERMUX_CA_FILE" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$variant" \
                "$bin" "$@"
            ;;
        b1-home)
            env \
                -u PYTHONHOME \
                CPYTHON_HOME="$CPYTHON_PREFIX" \
                LD_LIBRARY_PATH="$CPYTHON_LIB" \
                SSL_CERT_FILE="$TERMUX_CA_FILE" \
                PYTHONPYCACHEPREFIX="$PYCACHE_ROOT/$variant" \
                "$bin" "$@"
            ;;
        *)
            echo "unknown variant: $variant" >&2
            return 64
            ;;
    esac
}

capture() {
    local name="$1"
    shift
    "$@" > "$RESULTS_DIR/$name.out" 2> "$RESULTS_DIR/$name.err"
    echo $? > "$RESULTS_DIR/$name.rc"
}

compare_triplet() {
    local label="$1"
    local code="$2"
    shift 2
    local args=("$@")

    echo
    echo "================================================================"
    echo "TEST: $label"
    echo "================================================================"

    capture "${label}.stage1a" \
        run_variant stage1a "$BASE_BIN" "${args[@]}" -c "$code"

    capture "${label}.b0-auto" \
        run_variant b0-auto "$AUTO_BIN" "${args[@]}" -c "$code"

    capture "${label}.b1-home" \
        run_variant b1-home "$HOME_BIN" "${args[@]}" -c "$code"

    for variant in stage1a b0-auto b1-home; do
        echo
        echo "--- $variant rc=$(cat "$RESULTS_DIR/${label}.${variant}.rc")"
        cat "$RESULTS_DIR/${label}.${variant}.out"
        if [[ -s "$RESULTS_DIR/${label}.${variant}.err" ]]; then
            echo "[stderr]"
            cat "$RESULTS_DIR/${label}.${variant}.err"
        fi
    done
}

snapshot_code='
import json
import os
import sys

print(json.dumps({
    "argv": sys.argv,
    "orig_argv": sys.orig_argv,
    "flags": {
        "isolated": sys.flags.isolated,
        "ignore_environment": sys.flags.ignore_environment,
        "no_site": sys.flags.no_site,
        "no_user_site": sys.flags.no_user_site,
        "dont_write_bytecode": sys.flags.dont_write_bytecode,
        "utf8_mode": sys.flags.utf8_mode,
        "safe_path": sys.flags.safe_path,
    },
    "xoptions": sys._xoptions,
    "prefix": sys.prefix,
    "base_prefix": sys.base_prefix,
    "path": sys.path,
    "PYTHONPATH": os.environ.get("PYTHONPATH"),
}, indent=2, sort_keys=True))
'

compare_triplet "default" "$snapshot_code"
compare_triplet "isolated" "$snapshot_code" -I
compare_triplet "ignore-env" "$snapshot_code" -E
compare_triplet "no-site" "$snapshot_code" -S
compare_triplet "no-bytecode" "$snapshot_code" -B
compare_triplet "utf8" "$snapshot_code" -X utf8

echo
echo "================================================================"
echo "TEST: PYTHONPATH behavior"
echo "================================================================"

EXTRA_PATH="$RESULTS_DIR/pythonpath-sentinel"
mkdir -p "$EXTRA_PATH"

for spec in \
    "stage1a:$BASE_BIN" \
    "b0-auto:$AUTO_BIN" \
    "b1-home:$HOME_BIN"
do
    variant="${spec%%:*}"
    bin="${spec#*:}"

    echo
    echo "--- $variant"

    case "$variant" in
        stage1a|b0-auto)
            env \
                -u PYTHONHOME \
                -u CPYTHON_HOME \
                PYTHONPATH="$EXTRA_PATH" \
                LD_LIBRARY_PATH="$CPYTHON_LIB" \
                SSL_CERT_FILE="$TERMUX_CA_FILE" \
                "$bin" -c \
                'import os,sys; print(os.environ["PYTHONPATH"]); print(sys.path)'
            ;;
        b1-home)
            env \
                -u PYTHONHOME \
                PYTHONPATH="$EXTRA_PATH" \
                CPYTHON_HOME="$CPYTHON_PREFIX" \
                LD_LIBRARY_PATH="$CPYTHON_LIB" \
                SSL_CERT_FILE="$TERMUX_CA_FILE" \
                "$bin" -c \
                'import os,sys; print(os.environ["PYTHONPATH"]); print(sys.path)'
            ;;
    esac
done

echo
echo "================================================================"
echo "TEST: subprocess sys.executable round trip"
echo "================================================================"

subprocess_code='
import subprocess
import sys

print("parent:", sys.executable)
subprocess.run(
    [sys.executable, "-c", "import sys; print(\"child:\", sys.executable); print(sys.prefix); print(sys.base_prefix)"],
    check=True,
)
'

for spec in \
    "stage1a:$BASE_BIN" \
    "b0-auto:$AUTO_BIN" \
    "b1-home:$HOME_BIN"
do
    variant="${spec%%:*}"
    bin="${spec#*:}"
    echo
    echo "--- $variant"
    run_variant "$variant" "$bin" -c "$subprocess_code"
    echo "SUBPROCESS[$variant]=PASS"
done

echo
echo "================================================================"
echo "TEST: exit-code behavior"
echo "================================================================"

for spec in \
    "stage1a:$BASE_BIN" \
    "b0-auto:$AUTO_BIN" \
    "b1-home:$HOME_BIN"
do
    variant="${spec%%:*}"
    bin="${spec#*:}"

    echo
    echo "--- $variant"

    run_variant "$variant" "$bin" -c 'raise SystemExit(7)'
    rc=$?
    echo "SystemExit(7) rc=$rc"

    run_variant "$variant" "$bin" --definitely-invalid-option \
        >/dev/null 2>&1
    rc=$?
    echo "invalid-option rc=$rc"

    run_variant "$variant" "$bin" --help \
        >/dev/null 2>&1
    rc=$?
    echo "--help rc=$rc"
done

echo
echo "================================================================"
echo "TEST: venv launcher linkage"
echo "================================================================"

for variant in stage1a b0-auto b1-home; do
    venv="$PWD/stage1b-results/venv-$variant"

    echo
    echo "--- $variant"
    if [[ -e "$venv/bin/python" ]]; then
        ls -l "$venv/bin/python"
        readlink "$venv/bin/python" || true
        readlink -f "$venv/bin/python" || true
        echo
        echo "pyvenv.cfg:"
        cat "$venv/pyvenv.cfg"
    else
        echo "missing venv: $venv"
    fi
done

echo
echo "================================================================"
echo "TEST: B1 wrong-home negative control"
echo "================================================================"

BAD_HOME="$RESULTS_DIR/does-not-exist"

env \
    -u PYTHONHOME \
    CPYTHON_HOME="$BAD_HOME" \
    LD_LIBRARY_PATH="$CPYTHON_LIB" \
    SSL_CERT_FILE="$TERMUX_CA_FILE" \
    "$HOME_BIN" -c \
    'import sys; print(sys.prefix); print(sys.path)' \
    > "$RESULTS_DIR/b1-wrong-home.out" \
    2> "$RESULTS_DIR/b1-wrong-home.err"

bad_rc=$?

echo "B1_WRONG_HOME_RC=$bad_rc"
echo "[stdout]"
cat "$RESULTS_DIR/b1-wrong-home.out"
echo "[stderr]"
cat "$RESULTS_DIR/b1-wrong-home.err"

echo
echo "================================================================"
echo "Semantic differential test complete"
echo "Log: $LOG"
echo "================================================================"
