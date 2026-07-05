#!/usr/bin/env bash
# Stage 1-A runtime helper for CPython Android CLI on Termux.
#
# Usage:
#   source ./runtime-stage1a.sh
#   cpython -V
#   cpython_runtime uv venv --no-python-downloads -p "$CPYTHON_BIN" .venv
#
# Deliberately:
#   - does NOT export PYTHONHOME
#   - does NOT export PYTHONPATH
#   - applies the native library path only to the invoked command

CPYTHON_PREFIX="${CPYTHON_PREFIX:-$HOME/opt/cpython-3.14/prefix}"
CPYTHON_BIN="${CPYTHON_BIN:-$CPYTHON_PREFIX/bin/python}"
CPYTHON_LIB="${CPYTHON_LIB:-$CPYTHON_PREFIX/lib}"

if [[ ! -x "$CPYTHON_BIN" ]]; then
    printf 'CPython executable not found or not executable: %s\n' "$CPYTHON_BIN" >&2
    return 1 2>/dev/null || exit 1
fi

cpython_runtime() {
    env \
        -u PYTHONHOME \
        -u PYTHONPATH \
        LD_LIBRARY_PATH="$CPYTHON_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
        "$@"
}

cpython() {
    cpython_runtime "$CPYTHON_BIN" "$@"
}

printf 'Stage 1-A runtime loaded\n'
printf '  CPYTHON_PREFIX=%s\n' "$CPYTHON_PREFIX"
printf '  CPYTHON_BIN=%s\n' "$CPYTHON_BIN"
