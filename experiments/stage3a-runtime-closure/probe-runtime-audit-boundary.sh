#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-A representative non-ELF runtime boundary audit.

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

env \
    -u PYTHONHOME \
    -u PYTHONPATH \
    -u SSL_CERT_FILE \
    -u SSL_CERT_DIR \
    -u PYTHONTZPATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPYCACHEPREFIX="$RESULTS_DIR/pycache-runtime-audit" \
    "$PYTHON_BIN" \
        "$SCRIPT_DIR/probe-runtime-audit-boundary.py" \
        --runtime-prefix "$RUNTIME_PREFIX" \
        --termux-prefix "$TERMUX_PREFIX" \
        --output-dir "$RESULTS_DIR"

printf '\n'
printf 'Summary:      %s\n' "$RESULTS_DIR/runtime-audit-boundary-summary.json"
printf 'Unique paths: %s\n' "$RESULTS_DIR/runtime-audit-unique-paths.tsv"
printf 'Path events:  %s\n' "$RESULTS_DIR/runtime-audit-path-events.tsv"
printf 'Special:      %s\n' "$RESULTS_DIR/runtime-audit-special-events.tsv"
printf '\n'
echo "RUNTIME_AUDIT_BOUNDARY_PROBE=COMPLETE"
