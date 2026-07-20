#!/usr/bin/env bash
set -euo pipefail
: "${REPO_ROOT:?}"
: "${OFFICIAL_ARCHIVE:?}"
: "${UT2_ARTIFACT_DIR:?}"
: "${UT2_WORK_DIR:?}"
: "${UT2_PREDECESSOR_HEAD:?}"
: "${UT2_PREDECESSOR_TREE:?}"
TARGET="$REPO_ROOT/experiments/epoch2-upstream-thin-loader-relocation"
python3 -B "$TARGET/run_loader_relocation_experiment.py" \
  --root "$REPO_ROOT" \
  --archive "$OFFICIAL_ARCHIVE" \
  --output-dir "$TARGET" \
  --artifact-dir "$UT2_ARTIFACT_DIR" \
  --work-dir "$UT2_WORK_DIR" \
  --source-dir "$TARGET" \
  --cc "${UT2_CC:-clang}" \
  --patchelf "${UT2_PATCHELF:-patchelf}" \
  --readelf "${UT2_READELF:-readelf}"
python3 -B "$TARGET/audit_loader_relocation.py" --output-dir "$TARGET" --artifact-dir "$UT2_ARTIFACT_DIR"
python3 -B "$TARGET/finalize_loader_relocation.py" --root "$REPO_ROOT" --artifact-dir "$UT2_ARTIFACT_DIR" --predecessor-head "$UT2_PREDECESSOR_HEAD" --predecessor-tree "$UT2_PREDECESSOR_TREE"
python3 -B "$TARGET/verify_loader_relocation.py" --root "$REPO_ROOT" --artifact-dir "$UT2_ARTIFACT_DIR"
