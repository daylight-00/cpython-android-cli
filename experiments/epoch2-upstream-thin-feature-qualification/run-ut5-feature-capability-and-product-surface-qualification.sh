#!/usr/bin/env bash
set -euo pipefail
: "${REPO_ROOT:?}"
: "${OFFICIAL_ARCHIVE:?}"
: "${UT5_WORK_DIR:?}"
: "${UT5_PREDECESSOR_HEAD:?}"
: "${UT5_PREDECESSOR_TREE:?}"
TARGET="$REPO_ROOT/experiments/epoch2-upstream-thin-feature-qualification"
cd "$REPO_ROOT"
python3 -B "$TARGET/run_feature_qualification_experiment.py" \
  --root "$REPO_ROOT" --archive "$OFFICIAL_ARCHIVE" --output "$TARGET" --work "$UT5_WORK_DIR" \
  --cc "${UT5_CC:-clang}" --cxx "${UT5_CXX:-clang++}" --ar "${UT5_AR:-llvm-ar}" \
  --patchelf "${UT5_PATCHELF:-patchelf}" --readelf "${UT5_READELF:-readelf}" --pkg-config "${UT5_PKG_CONFIG:-pkg-config}"
python3 -B "$TARGET/audit_feature_qualification.py" --output "$TARGET"
python3 -B "$TARGET/finalize_feature_qualification.py" --root "$REPO_ROOT" --predecessor-head "$UT5_PREDECESSOR_HEAD" --predecessor-tree "$UT5_PREDECESSOR_TREE"
python3 -B "$TARGET/verify_feature_qualification.py" --root "$REPO_ROOT" --expected-predecessor-head "$UT5_PREDECESSOR_HEAD" --expected-predecessor-tree "$UT5_PREDECESSOR_TREE"
