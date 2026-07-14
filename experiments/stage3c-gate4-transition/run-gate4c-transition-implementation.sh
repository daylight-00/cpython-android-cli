#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT="${1:-$REPO_ROOT/results/stage3c-gate4c-transition-implementation-verification.json}"
PYTHON="${PYTHON:-python3}"
mkdir -p "$(dirname "$OUTPUT")"
"$PYTHON" -B "$SCRIPT_DIR/verify-gate4c-transition-implementation.py" --output "$OUTPUT"
