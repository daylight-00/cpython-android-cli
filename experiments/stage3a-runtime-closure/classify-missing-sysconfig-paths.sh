#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-A classification of missing absolute-path sysconfig metadata.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3a-runtime-closure}"
PYTHON_BIN="${PYTHON_BIN:-$TERMUX_WORK_ROOT/runtime/prefix/bin/python}"
INPUT_TSV="$RESULTS_DIR/sysconfig-missing-other-absolute.tsv"

[[ -f "$INPUT_TSV" ]] || {
    echo "ERROR: run triage-sysconfig-paths.sh first; missing: $INPUT_TSV" >&2
    exit 2
}

[[ -x "$PYTHON_BIN" ]] || {
    echo "ERROR: runtime Python not executable: $PYTHON_BIN" >&2
    exit 2
}

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX="$RESULTS_DIR/pycache-sysconfig-classify" \
"$PYTHON_BIN" \
    "$SCRIPT_DIR/classify-missing-sysconfig-paths.py" \
    --results-dir "$RESULTS_DIR"

printf '\n'
printf 'Summary:    %s\n' "$RESULTS_DIR/sysconfig-missing-other-classification-summary.json"
printf 'Categories: %s\n' "$RESULTS_DIR/sysconfig-missing-other-category-counts.tsv"
printf 'Details:    %s\n' "$RESULTS_DIR/sysconfig-missing-other-classified.tsv"
printf '\n'
echo "SYSCONFIG_MISSING_PATH_CLASSIFICATION=PASS"
