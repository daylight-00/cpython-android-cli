#!/usr/bin/env bash
# Stage 3-B Phase 4.1: mechanically classify package-prefix differences.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

OUTPUT_DIR="${OUTPUT_DIR:-$RESULTS_ROOT/workstation/stage3b-product-boundary}"
HISTORICAL_INVENTORY="$OUTPUT_DIR/historical-prefix-inventory.tsv"
PACKAGE_INVENTORY="$OUTPUT_DIR/replay-package-prefix-inventory.tsv"
DIFF="$OUTPUT_DIR/historical-package-prefix-diff.tsv"
REVIEW="$OUTPUT_DIR/package-prefix-difference-review.json"

for file in "$HISTORICAL_INVENTORY" "$PACKAGE_INVENTORY" "$DIFF"; do
    [[ -f "$file" ]] || {
        echo "ERROR: missing package-prefix comparison evidence: $file" >&2
        exit 2
    }
done

PLAN_JSON="$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-plan.json"
DRIVER_PYTHON="$(python3 - "$PLAN_JSON" <<'PY'
import json, sys
with open(sys.argv[1]) as stream:
    print(json.load(stream)["driver_python"])
PY
)"

exec "$DRIVER_PYTHON" \
    "$SCRIPT_DIR/review-package-differences.py" \
    --historical-inventory "$HISTORICAL_INVENTORY" \
    --package-inventory "$PACKAGE_INVENTORY" \
    --diff "$DIFF" \
    --output "$REVIEW"
