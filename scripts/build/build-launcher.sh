#!/usr/bin/env bash
# Cross-build the Stage 2-C launcher into the canonical repo-local out tree.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../lib/project-env.sh"

: "${ANDROID_CC:?set ANDROID_CC in .local/env}"
: "${CPYTHON_DEV_PREFIX:?set CPYTHON_DEV_PREFIX in .local/env}"

PYTHON_MM="${PYTHON_MM:-3.14}"
INCLUDE_DIR="$CPYTHON_DEV_PREFIX/include/python$PYTHON_MM"
LIB_DIR="$CPYTHON_DEV_PREFIX/lib"
SOURCE="$PROJECT_ROOT/src/launcher/python.c"
OUTPUT="$OUT_BIN/python3.14"

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

mkdir -p "$OUT_BIN" "$OUT_META"

echo "Project root:  $PROJECT_ROOT"
echo "Target:        $TARGET_ID"
echo "Profile:       $BUILD_PROFILE"
echo "Output:        $OUTPUT"
echo

"$ANDROID_CC" \
    -fPIE \
    -pie \
    -O2 \
    -Wall \
    -Wextra \
    -I"$INCLUDE_DIR" \
    "$SOURCE" \
    -L"$LIB_DIR" \
    "-lpython$PYTHON_MM" \
    -ldl \
    -lm \
    -llog \
    '-Wl,-rpath,$ORIGIN/../lib' \
    -o "$OUTPUT"

{
    echo "target=$TARGET_ID"
    echo "profile=$BUILD_PROFILE"
    echo "source=src/launcher/python.c"
    echo "output=out/$TARGET_ID/$BUILD_PROFILE/bin/python3.14"
    echo "sha256=$(sha256sum "$OUTPUT" | awk '{print $1}')"
    echo "compiler=$("$ANDROID_CC" --version | head -n 1)"
} > "$OUT_META/build-info.txt"

file "$OUTPUT"
readelf -d "$OUTPUT" \
    | grep -E 'NEEDED|RPATH|RUNPATH|SONAME' \
    || true

echo
echo "Built:"
echo "  $OUTPUT"
