#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-A isolated extension-module import sweep.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RUNTIME_PREFIX="${RUNTIME_PREFIX:-$TERMUX_WORK_ROOT/runtime/prefix}"
PYTHON_BIN="${PYTHON_BIN:-$RUNTIME_PREFIX/bin/python}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3a-runtime-closure}"

[[ -x "$PYTHON_BIN" ]] || {
    echo "ERROR: runtime Python not executable: $PYTHON_BIN" >&2
    exit 2
}

mkdir -p "$RESULTS_DIR"

set +e
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX="$RESULTS_DIR/pycache-extension-probe" \
"$PYTHON_BIN" \
    "$SCRIPT_DIR/probe-extension-imports.py" \
    --python-bin "$PYTHON_BIN" \
    --output-dir "$RESULTS_DIR"
probe_rc=$?
set -e

printf '\n'
printf 'Summary: %s\n' "$RESULTS_DIR/extension-import-probe-summary.json"
printf 'Details: %s\n' "$RESULTS_DIR/extension-import-probe.tsv"
printf '\n'

if [[ $probe_rc -ne 0 ]]; then
    echo "EXTENSION_IMPORT_PROBE=FAIL rc=$probe_rc"
    exit "$probe_rc"
fi

echo "EXTENSION_IMPORT_PROBE=PASS"
