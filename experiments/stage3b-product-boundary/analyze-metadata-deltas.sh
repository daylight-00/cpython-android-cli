#!/usr/bin/env bash
# Stage 3-B Phase 4.1: capture structured deltas in five metadata files.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

: "${CPYTHON_DEV_PREFIX:?set CPYTHON_DEV_PREFIX in .local/env}"

PLAN_JSON="$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-plan.json"
BUILD_RESULT="$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-build-result.json"
OUTPUT_DIR="${OUTPUT_DIR:-$RESULTS_ROOT/workstation/stage3b-product-boundary}"

read_json_field() {
    local file="$1"
    local field="$2"
    python3 - "$file" "$field" <<'PY'
import json, sys
with open(sys.argv[1]) as stream:
    value = json.load(stream)
for key in sys.argv[2].split("."):
    value = value[key]
print(value)
PY
}

DRIVER_PYTHON="$(read_json_field "$PLAN_JSON" driver_python)"
PACKAGE_ARCHIVE="$(read_json_field "$BUILD_RESULT" package_archive)"

exec "$DRIVER_PYTHON" \
    "$SCRIPT_DIR/analyze-metadata-deltas.py" \
    --historical-prefix "$CPYTHON_DEV_PREFIX" \
    --package "$PACKAGE_ARCHIVE" \
    --output-dir "$OUTPUT_DIR"
