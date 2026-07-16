#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
python3 -B "$(dirname "$0")/test-verify-gate5-independent-freeze.py"
python3 -B "$(dirname "$0")/verify-gate5-independent-freeze.py"
