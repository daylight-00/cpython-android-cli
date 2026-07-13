#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARCHIVE="${1:?usage: $0 RESULT_ARCHIVE [OUTPUT_JSON]}"
OUTPUT="${2:-$ROOT/results/stage3c-gate4-second-product-authority/gate4a-a2a-remote-input-capture-external-audit.json}"
mkdir -p "$(dirname "$OUTPUT")"
python3 "$ROOT/experiments/stage3c-gate4-second-product-authority/verify-gate4a-a2a-remote-input-capture.py" \
  --repo "$ROOT" \
  --archive "$ARCHIVE" \
  --output "$OUTPUT"
python3 - "$OUTPUT" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
print(f"GATE4A_A2A_REMOTE_INPUT_CAPTURE_EXTERNAL_AUDIT={r['pass_count']}/{r['check_count']} " + ("PASS" if r["pass"] else "FAIL"))
raise SystemExit(0 if r["pass"] else 41)
PY
