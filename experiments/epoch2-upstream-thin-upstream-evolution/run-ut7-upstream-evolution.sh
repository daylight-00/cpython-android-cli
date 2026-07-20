#!/usr/bin/env bash
set -euo pipefail
: "${REPO_ROOT:?}"
: "${CURRENT_ARCHIVE:?}"
: "${PATCH_ARCHIVE:?}"
: "${PREVIEW_ARCHIVE:?}"
: "${CURRENT_MANIFEST:?}"
: "${PATCH_MANIFEST:?}"
: "${PREVIEW_MANIFEST:?}"
: "${UT7_WORK_DIR:?}"
: "${UT7_PREDECESSOR_HEAD:?}"
: "${UT7_PREDECESSOR_TREE:?}"
TARGET="$REPO_ROOT/experiments/epoch2-upstream-thin-upstream-evolution"
cd "$REPO_ROOT"
python3 -B "$TARGET/run_upstream_evolution_experiment.py" \
  --root "$REPO_ROOT" \
  --current-archive "$CURRENT_ARCHIVE" \
  --patch-archive "$PATCH_ARCHIVE" \
  --preview-archive "$PREVIEW_ARCHIVE" \
  --current-manifest "$CURRENT_MANIFEST" \
  --patch-manifest "$PATCH_MANIFEST" \
  --preview-manifest "$PREVIEW_MANIFEST" \
  --work "$UT7_WORK_DIR" \
  --output "$TARGET" \
  --readelf "${UT7_READELF:-readelf}"
python3 -B "$TARGET/audit_upstream_evolution.py" --output "$TARGET"
python3 -B "$TARGET/finalize_upstream_evolution.py" --root "$REPO_ROOT" --predecessor-head "$UT7_PREDECESSOR_HEAD" --predecessor-tree "$UT7_PREDECESSOR_TREE"
python3 -B "$TARGET/verify_upstream_evolution.py" --root "$REPO_ROOT" --expected-predecessor-head "$UT7_PREDECESSOR_HEAD" --expected-predecessor-tree "$UT7_PREDECESSOR_TREE"
