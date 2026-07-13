#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd -P)"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO/results/local/stage3c-phase5-gate3d-acceptance-freeze}"
mkdir -p "$OUTPUT_DIR"
python3 "$SCRIPT_DIR/verify-gate3d-acceptance-freeze.py" \
  --repo "$REPO" \
  --output "$OUTPUT_DIR/verification.json" \
  | tee "$OUTPUT_DIR/verification.log"
COUNT="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["check_count"])' "$OUTPUT_DIR/verification.json")"
printf 'GATE3D_ACCEPTANCE_FREEZE_VALIDATION=%s/%s PASS\n' "$COUNT" "$COUNT"
printf 'STAGE3C_PHASE5_GATE3D_ACCEPTANCE_FREEZE=PASS\n'
printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
