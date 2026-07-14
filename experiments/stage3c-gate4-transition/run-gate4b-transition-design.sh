#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT="${1:-$ROOT/results/design/stage3c-phase5-gate4b-transition-contract-design-verification.json}"
exec python3 "$SCRIPT_DIR/verify-gate4b-transition-design.py" \
  --repository "$ROOT" \
  --matrix "$SCRIPT_DIR/gate4b-transition-matrix.json" \
  --inventory "$SCRIPT_DIR/gate4b-cross-version-inventory.json" \
  --output "$OUTPUT" \
  --require-pass
