#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-A second-step analysis:
#   1. aggregate DT_NEEDED edges by unique SONAME
#   2. probe ANDROID_SYSTEM SONAMEs through fresh runtime-Python subprocesses

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RUNTIME_PREFIX="${RUNTIME_PREFIX:-$TERMUX_WORK_ROOT/runtime/prefix}"
PYTHON_BIN="${PYTHON_BIN:-$RUNTIME_PREFIX/bin/python}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3a-runtime-closure}"

CLASSIFICATION_TSV="$RESULTS_DIR/closure-classification.tsv"

[[ -f "$CLASSIFICATION_TSV" ]] || {
    echo "ERROR: run inventory-runtime.sh first; missing: $CLASSIFICATION_TSV" >&2
    exit 2
}

[[ -x "$PYTHON_BIN" ]] || {
    echo "ERROR: runtime Python not executable: $PYTHON_BIN" >&2
    exit 2
}

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX="$RESULTS_DIR/pycache-analysis" \
"$PYTHON_BIN" \
    "$SCRIPT_DIR/analyze-closure.py" \
    --results-dir "$RESULTS_DIR"

printf '\n'

set +e
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX="$RESULTS_DIR/pycache-probe" \
"$PYTHON_BIN" \
    "$SCRIPT_DIR/probe-system-sonames.py" \
    --classification-tsv "$CLASSIFICATION_TSV" \
    --python-bin "$PYTHON_BIN" \
    --output-dir "$RESULTS_DIR"
probe_rc=$?
set -e

printf '\n'
printf 'Closure analysis: %s\n' "$RESULTS_DIR/closure-analysis-summary.json"
printf 'System probe:     %s\n' "$RESULTS_DIR/system-soname-probe-summary.json"
printf 'Probe details:    %s\n' "$RESULTS_DIR/system-soname-probe.tsv"
printf '\n'

if [[ $probe_rc -ne 0 ]]; then
    echo "SYSTEM_SONAME_PROBE=FAIL rc=$probe_rc"
    exit "$probe_rc"
fi

echo "SYSTEM_SONAME_PROBE=PASS"
