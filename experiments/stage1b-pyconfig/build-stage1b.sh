#!/usr/bin/env bash
# Build the Stage 1-B launchers on the Linux workstation.
#
# Expected:
#   source ~/tmp/260704/env.sh
#   ./build-stage1b.sh
#
# Outputs:
#   ~/tmp/260704/stage1b/out/python-pyconfig-auto
#   ~/tmp/260704/stage1b/out/python-pyconfig-home
#
# The script does not modify yesterday's build output.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

: "${ANDROID_CC:?source the 260704 host env.sh first}"
: "${PROJECT_TODAY:?source the 260704 host env.sh first}"
: "${PYTHON_MM:=3.14}"

LINK_PREFIX="${LINK_PREFIX:-${CPYTHON_BUILT_PREFIX:-}}"

if [[ -z "$LINK_PREFIX" ]]; then
    echo "ERROR: LINK_PREFIX or CPYTHON_BUILT_PREFIX is required" >&2
    exit 2
fi

INCLUDE_DIR="${INCLUDE_DIR:-$LINK_PREFIX/include/python$PYTHON_MM}"
LIB_DIR="${LIB_DIR:-$LINK_PREFIX/lib}"
OUT_DIR="${STAGE1B_OUT:-$PROJECT_TODAY/stage1b/out}"

[[ -d "$INCLUDE_DIR" ]] || {
    echo "ERROR: Python headers not found: $INCLUDE_DIR" >&2
    exit 2
}

[[ -f "$LIB_DIR/libpython$PYTHON_MM.so" ]] || {
    echo "ERROR: libpython not found: $LIB_DIR/libpython$PYTHON_MM.so" >&2
    exit 2
}

mkdir -p "$OUT_DIR"

build_one() {
    local source="$1"
    local output="$2"

    echo
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
}

build_one \
    "$SCRIPT_DIR/pyconfig-auto.c" \
    "$OUT_DIR/python-pyconfig-auto"

build_one \
    "$SCRIPT_DIR/pyconfig-home.c" \
    "$OUT_DIR/python-pyconfig-home"

echo
echo "Stage 1-B launchers built:"
echo "  $OUT_DIR/python-pyconfig-auto"
echo "  $OUT_DIR/python-pyconfig-home"
