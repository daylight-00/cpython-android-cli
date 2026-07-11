#!/usr/bin/env bash
# Stage 3-B Phase 4.2: promote replay package into canonical generated products.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

PLAN_JSON="$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-plan.json"
BUILD_RESULT="$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-build-result.json"
LOCK_JSON="$PROJECT_ROOT/config/products/cpython-3.14.6-aarch64-linux-android.lock.json"
CANONICAL_ARCHIVE_DIR="$OUT_ROOT/cpython"
DERIVED_PRODUCT_ROOT="$WORK_ROOT/workstation/stage3b-promoted-cpython/prefix"
MANIFEST="$OUT_META/cpython-product.json"

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
SOURCE_ARCHIVE="$(read_json_field "$BUILD_RESULT" package_archive)"

exec "$DRIVER_PYTHON" \
    "$SCRIPT_DIR/promote-cpython-product.py" \
    --lock "$LOCK_JSON" \
    --source-archive "$SOURCE_ARCHIVE" \
    --canonical-archive-dir "$CANONICAL_ARCHIVE_DIR" \
    --derived-product-root "$DERIVED_PRODUCT_ROOT" \
    --manifest "$MANIFEST"
