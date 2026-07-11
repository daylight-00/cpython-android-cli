#!/usr/bin/env bash
# Verify the complete promoted workstation handoff before synchronization.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../lib/project-env.sh"

PLAN_JSON="$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-plan.json"
DRIVER_PYTHON="$(python3 - "$PLAN_JSON" <<'PY'
import json, sys
with open(sys.argv[1]) as stream:
    print(json.load(stream)["driver_python"])
PY
)"

exec "$DRIVER_PYTHON" \
    "$SCRIPT_DIR/verify-workstation-handoff.py" \
    --out-root "$OUT_ROOT" \
    --promoted-prefix "$PROMOTED_CPYTHON_DEV_PREFIX" \
    --product-lock "$PROJECT_ROOT/config/products/cpython-3.14.6-aarch64-linux-android.lock.json" \
    --output "$RESULTS_ROOT/workstation/stage3b-handoff/workstation-handoff.json"
