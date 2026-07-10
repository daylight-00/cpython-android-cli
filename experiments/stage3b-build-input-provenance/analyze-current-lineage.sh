#!/usr/bin/env bash
# Stage 3-B Phase 1 current-lineage analysis wrapper.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

INPUT_DIR="${INPUT_DIR:-$RESULTS_ROOT/workstation/stage3b-build-input-provenance}"

python3 \
    "$SCRIPT_DIR/analyze-current-lineage.py" \
    --input-dir "$INPUT_DIR"
