#!/usr/bin/env bash
# Build Stage 2-B R2 launcher on the Linux workstation.
#
# Usage:
#   source ~/tmp/260704/env.sh
#   cd ~/tmp/260704/stage2b
#
#   DEV_PREFIX="$HOME/tmp/260703/android-python-work/prefix" \
#     ./build-stage2b.sh

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

: "${ANDROID_CC:?source ~/tmp/260704/env.sh first}"
: "${PROJECT_TODAY:?PROJECT_TODAY is not set}"

PYTHON_MM="${PYTHON_MM:-3.14}"
DEV_PREFIX="${DEV_PREFIX:-${CPYTHON_STAGE1A_PREV_PREFIX:-$HOME/tmp/260703/android-python-work/prefix}}"

INCLUDE_DIR="$DEV_PREFIX/include/python$PYTHON_MM"
LIB_DIR="$DEV_PREFIX/lib"
OUT_DIR="${STAGE2B_OUT:-$PROJECT_TODAY/stage2b/out}"

[[ -f "$INCLUDE_DIR/Python.h" ]] || {
    echo "ERROR: Python.h not found: $INCLUDE_DIR/Python.h" >&2
    exit 2
}

[[ -f "$INCLUDE_DIR/pyconfig.h" ]] || {
    echo "ERROR: pyconfig.h not found: $INCLUDE_DIR/pyconfig.h" >&2
    exit 2
}

[[ -f "$LIB_DIR/libpython$PYTHON_MM.so" ]] || {
    echo "ERROR: libpython not found: $LIB_DIR/libpython$PYTHON_MM.so" >&2
    exit 2
}

mkdir -p "$OUT_DIR"

echo "============================================================"
echo "Stage 2-B build configuration"
echo "============================================================"
echo "ANDROID_CC:  $ANDROID_CC"
echo "DEV_PREFIX:  $DEV_PREFIX"
echo "INCLUDE_DIR: $INCLUDE_DIR"
echo "LIB_DIR:     $LIB_DIR"
echo "OUT_DIR:     $OUT_DIR"
echo

OUTPUT="$OUT_DIR/python-s2-r2"

"$ANDROID_CC" \
    -fPIE \
    -pie \
    -O2 \
    -Wall \
    -Wextra \
    -I"$SCRIPT_DIR" \
    -I"$INCLUDE_DIR" \
    "$SCRIPT_DIR/python-s2-r2.c" \
    -L"$LIB_DIR" \
    "-lpython$PYTHON_MM" \
    -ldl \
    -lm \
    -llog \
    '-Wl,-rpath,$ORIGIN/../lib' \
    -o "$OUTPUT"

file "$OUTPUT"

echo
readelf -d "$OUTPUT" \
    | grep -E 'NEEDED|RPATH|RUNPATH|SONAME' \
    || true

echo
echo "Built:"
echo "  $OUTPUT"
