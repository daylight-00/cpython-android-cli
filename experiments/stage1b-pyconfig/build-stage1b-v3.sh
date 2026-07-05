#!/usr/bin/env bash
# Build Stage 1-B PyConfig launchers using an installed Android CPython
# development prefix that contains both headers and libpython.
#
# Default source:
#   ~/tmp/260703/android-python-work/prefix
#
# Usage:
#   source ~/tmp/260704/env.sh
#   cd ~/tmp/260704/stage1b
#   ./build-stage1b-v3.sh

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

: "${ANDROID_CC:?source ~/tmp/260704/env.sh first}"
: "${PROJECT_TODAY:?PROJECT_TODAY is not set}"

PYTHON_MM="${PYTHON_MM:-3.14}"

DEV_PREFIX="${DEV_PREFIX:-${CPYTHON_STAGE1A_PREV_PREFIX:-$HOME/tmp/260703/android-python-work/prefix}}"
INCLUDE_DIR="${INCLUDE_DIR:-$DEV_PREFIX/include/python$PYTHON_MM}"
LIB_DIR="${LIB_DIR:-$DEV_PREFIX/lib}"
OUT_DIR="${STAGE1B_OUT:-$PROJECT_TODAY/stage1b/out}"

[[ -f "$INCLUDE_DIR/Python.h" ]] || {
    echo "ERROR: Python.h not found:"
    echo "  $INCLUDE_DIR/Python.h"
    exit 2
}

[[ -f "$INCLUDE_DIR/pyconfig.h" ]] || {
    echo "ERROR: pyconfig.h not found:"
    echo "  $INCLUDE_DIR/pyconfig.h"
    exit 2
}

[[ -f "$LIB_DIR/libpython$PYTHON_MM.so" ]] || {
    echo "ERROR: libpython not found:"
    echo "  $LIB_DIR/libpython$PYTHON_MM.so"
    exit 2
}

mkdir -p "$OUT_DIR"

echo "============================================================"
echo "Stage 1-B build configuration"
echo "============================================================"
echo "ANDROID_CC:  $ANDROID_CC"
echo "DEV_PREFIX:  $DEV_PREFIX"
echo "INCLUDE_DIR: $INCLUDE_DIR"
echo "LIB_DIR:     $LIB_DIR"
echo "OUT_DIR:     $OUT_DIR"
echo

echo "== Header/library fingerprints =="
sha256sum \
    "$INCLUDE_DIR/Python.h" \
    "$INCLUDE_DIR/pyconfig.h" \
    "$LIB_DIR/libpython$PYTHON_MM.so"
echo

build_one() {
    local source="$1"
    local output="$2"

    echo "== Build $(basename "$output") =="

    "$ANDROID_CC" \
        -fPIE \
        -pie \
        -O2 \
        -Wall \
        -Wextra \
        -I"$INCLUDE_DIR" \
        "$source" \
        -L"$LIB_DIR" \
        "-lpython$PYTHON_MM" \
        -ldl \
        -lm \
        -llog \
        '-Wl,-rpath,$ORIGIN/../lib' \
        -o "$output"

    file "$output"

    if command -v readelf >/dev/null 2>&1; then
        readelf -d "$output" \
            | grep -E 'NEEDED|RPATH|RUNPATH|SONAME' \
            || true
    fi

    echo
}

build_one \
    "$SCRIPT_DIR/pyconfig-auto.c" \
    "$OUT_DIR/python-pyconfig-auto"

build_one \
    "$SCRIPT_DIR/pyconfig-home.c" \
    "$OUT_DIR/python-pyconfig-home"

echo "Stage 1-B launchers built:"
echo "  $OUT_DIR/python-pyconfig-auto"
echo "  $OUT_DIR/python-pyconfig-home"
