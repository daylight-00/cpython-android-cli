#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_ROOT/results/local/stage3c-phase5-gate4a-second-product-authority-design}"
PYTHON="${PYTHON:-python3}"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
cp "$SCRIPT_DIR/gate4a-second-product-authority-input.json" "$OUTPUT_DIR/selected-input.json"
cp "$SCRIPT_DIR/gate4a-second-product-authority-matrix.json" "$OUTPUT_DIR/matrix.json"
"$PYTHON" -I -B -S "$SCRIPT_DIR/verify-gate4a-second-product-authority-design.py" \
  --project-root "$PROJECT_ROOT" \
  --input "$SCRIPT_DIR/gate4a-second-product-authority-input.json" \
  --matrix "$SCRIPT_DIR/gate4a-second-product-authority-matrix.json" \
  --output "$OUTPUT_DIR/verification.json" \
  --require-pass
"$PYTHON" -I -B -S - "$OUTPUT_DIR" "$OUTPUT_DIR/result-index.json" <<'PY'
import hashlib,json,os,stat,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve(); files=[]
for path in sorted(root.rglob('*'),key=lambda p:p.relative_to(root).as_posix()):
    if path==output or path.is_dir(): continue
    rel=path.relative_to(root).as_posix(); st=path.lstat(); mode=f'{stat.S_IMODE(st.st_mode):04o}'
    if path.is_symlink(): files.append({'path':rel,'type':'symlink','mode':mode,'target':os.readlink(path)})
    elif path.is_file(): files.append({'path':rel,'type':'regular','mode':mode,'size':st.st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    else: raise SystemExit(f'unsupported result entry: {path}')
output.write_text(json.dumps({'schema_version':1,'index_kind':'stage3c-phase5-gate4a-second-product-authority-design-result-index','file_count':len(files),'files':files},indent=2,sort_keys=True)+'\n')
PY
printf 'STAGE3C_PHASE5_GATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN=PASS\n'
printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
