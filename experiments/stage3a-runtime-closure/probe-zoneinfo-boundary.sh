#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-A zoneinfo non-ELF boundary probe.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RUNTIME_PREFIX="${RUNTIME_PREFIX:-$TERMUX_WORK_ROOT/runtime/prefix}"
PYTHON_BIN="${PYTHON_BIN:-$RUNTIME_PREFIX/bin/python}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3a-runtime-closure}"
TERMUX_PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"

[[ -x "$PYTHON_BIN" ]] || {
    echo "ERROR: runtime Python not executable: $PYTHON_BIN" >&2
    exit 2
}

mkdir -p "$RESULTS_DIR"

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX="$RESULTS_DIR/pycache-zoneinfo-probe" \
"$PYTHON_BIN" \
    "$SCRIPT_DIR/probe-zoneinfo-boundary.py" \
    --python-bin "$PYTHON_BIN" \
    --termux-prefix "$TERMUX_PREFIX" \
    --output-dir "$RESULTS_DIR"

printf '\n'
printf 'Result: %s\n' "$RESULTS_DIR/zoneinfo-boundary-probe.json"
printf '\n'
echo "ZONEINFO_BOUNDARY_PROBE=COMPLETE"
