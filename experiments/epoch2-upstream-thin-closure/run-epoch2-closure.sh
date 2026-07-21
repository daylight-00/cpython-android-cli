#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
: "${REPO_ROOT:?}" "${E2_CLOSURE_PREDECESSOR_HEAD:?}" "${E2_CLOSURE_PREDECESSOR_TREE:?}"
OUT="$REPO_ROOT/experiments/epoch2-upstream-thin-closure"
python3 -B "$OUT/build_epoch2_closure.py" --root "$REPO_ROOT"
python3 -B "$OUT/audit_epoch2_closure.py" --root "$REPO_ROOT"
python3 -B "$OUT/finalize_epoch2_closure.py" --root "$REPO_ROOT" --predecessor-head "$E2_CLOSURE_PREDECESSOR_HEAD" --predecessor-tree "$E2_CLOSURE_PREDECESSOR_TREE"
