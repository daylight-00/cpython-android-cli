#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-A analysis of sysconfig absolute-path census output.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3a-runtime-closure}"
INPUT_TSV="$RESULTS_DIR/sysconfig-absolute-paths.tsv"

[[ -f "$INPUT_TSV" ]] || {
    echo "ERROR: run probe-sysconfig-paths.sh first; missing: $INPUT_TSV" >&2
    exit 2
}

PYTHON_BIN="${PYTHON_BIN:-$TERMUX_WORK_ROOT/runtime/prefix/bin/python}"

[[ -x "$PYTHON_BIN" ]] || {
    echo "ERROR: runtime Python not executable: $PYTHON_BIN" >&2
    exit 2
}

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX="$RESULTS_DIR/pycache-sysconfig-analysis" \
"$PYTHON_BIN" \
    "$SCRIPT_DIR/analyze-sysconfig-paths.py" \
    --results-dir "$RESULTS_DIR"

printf '\n'
printf 'Summary:       %s\n' "$RESULTS_DIR/sysconfig-path-analysis-summary.json"
printf 'Other roots:   %s\n' "$RESULTS_DIR/sysconfig-other-prefix-counts.tsv"
printf 'Residue keys:  %s\n' "$RESULTS_DIR/sysconfig-build-residue-key-counts.tsv"
printf 'Key counts:    %s\n' "$RESULTS_DIR/sysconfig-path-key-counts.tsv"
printf '\n'
echo "SYSCONFIG_PATH_ANALYSIS=PASS"
