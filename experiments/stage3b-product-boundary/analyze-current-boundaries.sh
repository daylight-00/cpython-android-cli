#!/usr/bin/env bash
# Stage 3-B Phase 4.1: read-only CPython product-boundary census.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

: "${CPYTHON_DEV_PREFIX:?set CPYTHON_DEV_PREFIX in .local/env}"

PLAN_JSON="${PLAN_JSON:-$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-plan.json}"
BUILD_RESULT="${BUILD_RESULT:-$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-build-result.json}"
OUTPUT_DIR="${OUTPUT_DIR:-$RESULTS_ROOT/workstation/stage3b-product-boundary}"

for file in "$PLAN_JSON" "$BUILD_RESULT"; do
    [[ -f "$file" ]] || {
        echo "ERROR: missing frozen replay evidence: $file" >&2
        exit 2
    }
done

DRIVER_PYTHON="$(python3 - "$PLAN_JSON" <<'PY'
import json, sys
with open(sys.argv[1]) as stream:
    print(json.load(stream)["driver_python"])
PY
)"

[[ -x "$DRIVER_PYTHON" ]] || {
    echo "ERROR: replay driver Python disappeared: $DRIVER_PYTHON" >&2
    exit 2
}

exec "$DRIVER_PYTHON" \
    "$SCRIPT_DIR/analyze-product-boundaries.py" \
    --plan "$PLAN_JSON" \
    --build-result "$BUILD_RESULT" \
    --historical-dev-prefix "$CPYTHON_DEV_PREFIX" \
    --output-dir "$OUTPUT_DIR"
