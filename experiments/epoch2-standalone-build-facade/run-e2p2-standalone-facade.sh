#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
export PYTHONDONTWRITEBYTECODE=1

python3 "$SCRIPT_DIR/test-e2p2-standalone-facade.py"
python3 "$SCRIPT_DIR/verify-e2p2-standalone-facade.py" --root "$PROJECT_ROOT"

echo "E2P2_GATE1_STANDALONE_FACADE=PASS"
