#!/usr/bin/env bash
# Build Stage 1-B PyConfig launchers on the Linux workstation.
#
# Header model:
#   - public CPython headers:  <CPYTHON_SRC>/Include
#   - generated pyconfig.h:    <CPYTHON_SRC>/cross-build/<HOST>
#   - link library:            <built-prefix>/lib/libpython3.14.so
#
# Usage:
#   source ~/tmp/260704/env.sh
#   cd ~/tmp/260704/stage1b
#   ./build-stage1b-v2.sh

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

: "${ANDROID_CC:?source ~/tmp/260704/env.sh first}"
: "${CPYTHON_SRC:?CPYTHON_SRC is not set}"
: "${PROJECT_TODAY:?PROJECT_TODAY is not set}"

PYTHON_MM="${PYTHON_MM:-3.14}"
ANDROID_TARGET="${ANDROID_TARGET:-aarch64-linux-android}"

# Link against yesterday's built Android prefix unless explicitly overridden.
LINK_PREFIX="${LINK_PREFIX:-${CPYTHON_BUILT_PREFIX:-}}"

if [[ -z "$LINK_PREFIX" ]]; then
    echo "ERROR: LINK_PREFIX or CPYTHON_BUILT_PREFIX is required" >&2
    exit 2
fi

SOURCE_INCLUDE="$CPYTHON_SRC/Include"
LIB_DIR="$LINK_PREFIX/lib"
OUT_DIR="${STAGE1B_OUT:-$PROJECT_TODAY/stage1b/out}"

# Prefer the expected upstream Android host-build directory.
HOST_BUILD_DIR="${CPYTHON_HOST_BUILD:-$CPYTHON_SRC/cross-build/$ANDROID_TARGET}"

# If the expected path does not contain pyconfig.h, discover the Android host build.
if [[ ! -f "$HOST_BUILD_DIR/pyconfig.h" ]]; then
    mapfile -t _pyconfig_candidates < <(
        find "$CPYTHON_SRC/cross-build" \
            -maxdepth 3 \
            -type f \
            -name pyconfig.h \
            2>/dev/null \
        | sort
    )

    HOST_BUILD_DIR=""

    for candidate in "${_pyconfig_candidates[@]}"; do
        case "$candidate" in
            *"$ANDROID_TARGET"*)
                HOST_BUILD_DIR="$(dirname "$candidate")"
                break
                ;;
        esac
    done

    # Final fallback: use the only discovered candidate if unambiguous.
    if [[ -z "$HOST_BUILD_DIR" && ${#_pyconfig_candidates[@]} -eq 1 ]]; then
        HOST_BUILD_DIR="$(dirname "${_pyconfig_candidates[0]}")"
    fi
fi

[[ -d "$SOURCE_INCLUDE" ]] || {
    echo "ERROR: source include directory not found: $SOURCE_INCLUDE" >&2
    exit 2
}

[[ -n "$HOST_BUILD_DIR" && -f "$HOST_BUILD_DIR/pyconfig.h" ]] || {
    echo "ERROR: generated Android pyconfig.h not found." >&2
    echo
    echo "Expected near:"
    echo "  $CPYTHON_SRC/cross-build/$ANDROID_TARGET/pyconfig.h"
    echo
    echo "Available candidates:"
    find "$CPYTHON_SRC/cross-build" \
        -maxdepth 3 \
        -type f \
        -name pyconfig.h \
        -print 2>/dev/null || true
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
echo "ANDROID_CC:     $ANDROID_CC"
echo "CPYTHON_SRC:    $CPYTHON_SRC"
echo "SOURCE_INCLUDE: $SOURCE_INCLUDE"
echo "HOST_BUILD_DIR: $HOST_BUILD_DIR"
echo "LINK_PREFIX:    $LINK_PREFIX"
echo "LIB_DIR:        $LIB_DIR"
echo "OUT_DIR:        $OUT_DIR"
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
        -I"$HOST_BUILD_DIR" \
        -I"$SOURCE_INCLUDE" \
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
