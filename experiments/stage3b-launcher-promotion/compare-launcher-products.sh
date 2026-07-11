#!/usr/bin/env bash
# Stage 3-B Phase 4.2: build launcher from historical and promoted dev inputs.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

: "${CPYTHON_DEV_PREFIX:?historical CPYTHON_DEV_PREFIX missing from .local/env}"

HISTORICAL_PREFIX="$CPYTHON_DEV_PREFIX"
PROMOTED_PREFIX="$WORK_ROOT/workstation/stage3b-promoted-cpython/prefix"
COMPARE_ROOT="$WORK_ROOT/workstation/stage3b-launcher-comparison"
RESULT_DIR="$RESULTS_ROOT/workstation/stage3b-launcher-comparison"

[[ -d "$PROMOTED_PREFIX" ]] || {
    echo "ERROR: promoted CPython prefix missing; run product promotion first" >&2
    exit 2
}

rm -rf "$COMPARE_ROOT"
mkdir -p \
    "$COMPARE_ROOT/historical/bin" \
    "$COMPARE_ROOT/historical/metadata" \
    "$COMPARE_ROOT/promoted/bin" \
    "$COMPARE_ROOT/promoted/metadata" \
    "$RESULT_DIR"

CPYTHON_DEV_PREFIX_OVERRIDE="$HISTORICAL_PREFIX" \
LAUNCHER_OUTPUT="$COMPARE_ROOT/historical/bin/python3.14" \
LAUNCHER_BUILD_INFO="$COMPARE_ROOT/historical/metadata/build-info.txt" \
bash "$PROJECT_ROOT/scripts/build/build-launcher.sh"

CPYTHON_DEV_PREFIX_OVERRIDE="$PROMOTED_PREFIX" \
LAUNCHER_OUTPUT="$COMPARE_ROOT/promoted/bin/python3.14" \
LAUNCHER_BUILD_INFO="$COMPARE_ROOT/promoted/metadata/build-info.txt" \
bash "$PROJECT_ROOT/scripts/build/build-launcher.sh"

PLAN_JSON="$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-plan.json"
DRIVER_PYTHON="$(python3 - "$PLAN_JSON" <<'PY'
import json, sys
with open(sys.argv[1]) as stream:
    print(json.load(stream)["driver_python"])
PY
)"

exec "$DRIVER_PYTHON" \
    "$SCRIPT_DIR/compare-launcher-products.py" \
    --historical "$COMPARE_ROOT/historical/bin/python3.14" \
    --promoted "$COMPARE_ROOT/promoted/bin/python3.14" \
    --historical-build-info "$COMPARE_ROOT/historical/metadata/build-info.txt" \
    --promoted-build-info "$COMPARE_ROOT/promoted/metadata/build-info.txt" \
    --output "$RESULT_DIR/launcher-product-comparison.json"
