#!/usr/bin/env bash
set -euo pipefail
D="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
  echo "usage: $0 BASELINE.tar.zst CORRECTIVE.tar.zst [OUTPUT.json]" >&2; exit 2
fi
args=(--baseline "$1" --corrective "$2")
[ "$#" -eq 3 ] && args+=(--output "$3")
python3 -B "$D/verify-gate4e-transition-freeze.py" "${args[@]}"
