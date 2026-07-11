#!/usr/bin/env bash
# Stage 3-B Phase 4.1: compare regenerated ELF semantic surfaces.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

: "${CPYTHON_DEV_PREFIX:?set CPYTHON_DEV_PREFIX in .local/env}"

BOUNDARY_DIR="${BOUNDARY_DIR:-$RESULTS_ROOT/workstation/stage3b-product-boundary}"
PLAN_JSON="$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-plan.json"
BUILD_RESULT="$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-build-result.json"

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
    "$SCRIPT_DIR/compare-regenerated-surfaces.py" \
    --historical-prefix "$CPYTHON_DEV_PREFIX" \
    --package "$PACKAGE_ARCHIVE" \
    --review "$BOUNDARY_DIR/package-prefix-difference-review.json" \
    --diff "$BOUNDARY_DIR/historical-package-prefix-diff.tsv" \
    --historical-inventory "$BOUNDARY_DIR/historical-prefix-inventory.tsv" \
    --package-inventory "$BOUNDARY_DIR/replay-package-prefix-inventory.tsv" \
    --output-dir "$BOUNDARY_DIR"
