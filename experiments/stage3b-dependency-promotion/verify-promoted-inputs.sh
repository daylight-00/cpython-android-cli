#!/usr/bin/env bash
# Stage 3-B Phase 3: recapture dependency inputs and verify promoted identities.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

PLAN_JSON="${PLAN_JSON:-$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-plan.json}"
OUTPUT_DIR="${OUTPUT_DIR:-$RESULTS_ROOT/workstation/stage3b-dependency-promotion}"
LOCK_JSON="${LOCK_JSON:-$PROJECT_ROOT/config/dependencies/android-source-deps-aarch64-linux-android.lock.json}"
OBSERVED_JSON="$OUTPUT_DIR/dependency-input-manifest.json"
VERIFY_JSON="$OUTPUT_DIR/dependency-input-verification.json"

bash "$SCRIPT_DIR/capture-current-inputs.sh"

DRIVER_PYTHON="$(python3 - "$PLAN_JSON" <<'PY'
import json, sys
with open(sys.argv[1]) as stream:
    print(json.load(stream)["driver_python"])
PY
)"

exec "$DRIVER_PYTHON" \
    "$SCRIPT_DIR/verify-dependency-inputs.py" \
    --lock "$LOCK_JSON" \
    --observed "$OBSERVED_JSON" \
    --output "$VERIFY_JSON"
