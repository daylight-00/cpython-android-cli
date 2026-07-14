#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"
python3 "$SCRIPT_DIR/verify-gate4a-a2b-termux-native-toolchain-authority.py"
printf '%s\n' 'STAGE3C_PHASE5_GATE4A_A2B_TERMUX_NATIVE_TOOLCHAIN_AUTHORITY=PASS'
