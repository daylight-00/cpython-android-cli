#!/usr/bin/env bash
# Stage 3-B Phase 3: capture immutable identities of replay dependency inputs.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

PLAN_JSON="${PLAN_JSON:-$RESULTS_ROOT/workstation/stage3b-phase2-replay/replay-plan.json}"
OUTPUT_DIR="${OUTPUT_DIR:-$RESULTS_ROOT/workstation/stage3b-dependency-promotion}"

[[ -f "$PLAN_JSON" ]] || {
    echo "ERROR: missing frozen Phase 2 replay plan: $PLAN_JSON" >&2
    exit 2
}

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
    "$SCRIPT_DIR/capture-dependency-inputs.py" \
    --plan "$PLAN_JSON" \
    --output-dir "$OUTPUT_DIR"
