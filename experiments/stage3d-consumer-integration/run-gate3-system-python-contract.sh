#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARCHIVE="${1:-}"
if [[ -n "$ARCHIVE" ]]; then
  python3 "$ROOT/experiments/stage3d-consumer-integration/verify-gate2-consumer-census.py" "$ARCHIVE"
fi
python3 "$ROOT/experiments/stage3d-consumer-integration/verify-gate3-system-python-contract.py"
