#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-A focused triage of sysconfig path census results.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3a-runtime-closure}"
INPUT_TSV="$RESULTS_DIR/sysconfig-absolute-paths.tsv"
PYTHON_BIN="${PYTHON_BIN:-$TERMUX_WORK_ROOT/runtime/prefix/bin/python}"

[[ -f "$INPUT_TSV" ]] || {
    echo "ERROR: run probe-sysconfig-paths.sh first; missing: $INPUT_TSV" >&2
    exit 2
}

[[ -x "$PYTHON_BIN" ]] || {
    echo "ERROR: runtime Python not executable: $PYTHON_BIN" >&2
    exit 2
}

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX="$RESULTS_DIR/pycache-sysconfig-triage" \
"$PYTHON_BIN" \
    "$SCRIPT_DIR/triage-sysconfig-paths.py" \
    --results-dir "$RESULTS_DIR"

printf '\n'
printf 'Summary:          %s\n' "$RESULTS_DIR/sysconfig-path-triage-summary.json"
printf 'Existing OTHER:   %s\n' "$RESULTS_DIR/sysconfig-existing-other-absolute.tsv"
printf 'Missing OTHER:    %s\n' "$RESULTS_DIR/sysconfig-missing-other-absolute.tsv"
printf 'Missing prefixes: %s\n' "$RESULTS_DIR/sysconfig-missing-other-prefix-counts.tsv"
printf 'Missing runtime:  %s\n' "$RESULTS_DIR/sysconfig-missing-runtime-prefix.tsv"
printf '\n'
echo "SYSCONFIG_PATH_TRIAGE=PASS"
