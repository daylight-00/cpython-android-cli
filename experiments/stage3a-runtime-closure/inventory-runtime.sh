#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-A read-only runtime closure census.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RUNTIME_PREFIX="${RUNTIME_PREFIX:-$TERMUX_WORK_ROOT/runtime/prefix}"
PYTHON_BIN="${PYTHON_BIN:-$RUNTIME_PREFIX/bin/python}"
OUTPUT_DIR="${OUTPUT_DIR:-$RESULTS_ROOT/termux/stage3a-runtime-closure}"
INVENTORY_PY="$SCRIPT_DIR/inventory-runtime.py"

[[ -d "$RUNTIME_PREFIX" ]] || {
    echo "ERROR: runtime prefix not found: $RUNTIME_PREFIX" >&2
    exit 2
}

[[ -x "$PYTHON_BIN" ]] || {
    echo "ERROR: runtime Python not executable: $PYTHON_BIN" >&2
    exit 2
}

command -v readelf >/dev/null 2>&1 || {
    echo "ERROR: readelf is required" >&2
    exit 2
}

mkdir -p "$OUTPUT_DIR"

printf 'Runtime prefix: %s\n' "$RUNTIME_PREFIX"
printf 'Runtime Python: %s\n' "$PYTHON_BIN"
printf 'Output:         %s\n' "$OUTPUT_DIR"
printf '\n'

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX="$OUTPUT_DIR/pycache" \
"$PYTHON_BIN" \
    "$INVENTORY_PY" \
    --runtime-prefix "$RUNTIME_PREFIX" \
    --output-dir "$OUTPUT_DIR" \
    --termux-prefix "${PREFIX:-/data/data/com.termux/files/usr}"

printf '\n'
cat "$OUTPUT_DIR/mutation-check.txt"
printf '\n'

if [[ -s "$OUTPUT_DIR/unresolved.tsv" ]]; then
    unresolved_count="$(awk 'NR > 1 {count++} END {print count+0}' "$OUTPUT_DIR/unresolved.tsv")"
else
    unresolved_count=0
fi

printf 'UNRESOLVED_EDGE_COUNT=%s\n' "$unresolved_count"
printf 'Stage 3-A inventory complete.\n'
