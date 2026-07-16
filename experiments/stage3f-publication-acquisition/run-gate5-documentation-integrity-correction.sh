#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
baseline="$(mktemp)"
trap 'rm -f "$baseline"' EXIT
python3 -B - "$PWD" "$baseline" <<'PY_BASELINE'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve(); entries=set()
for p in root.rglob('__pycache__'):
    if '.git' not in p.parts: entries.add(str(p.relative_to(root)) + '/')
for p in root.rglob('*.pyc'):
    if '.git' not in p.parts: entries.add(str(p.relative_to(root)))
json.dump({'entries':sorted(entries)},open(sys.argv[2],'w'),indent=2);open(sys.argv[2],'a').write('\n')
PY_BASELINE
python3 -B experiments/stage3f-publication-acquisition/test-verify-gate5-documentation-integrity-correction.py
STAGE3F_BYTECODE_BASELINE="$baseline" python3 -B experiments/stage3f-publication-acquisition/verify-gate5-documentation-integrity-correction.py
