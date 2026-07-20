#!/usr/bin/env bash
set -euo pipefail
: "${REPO_ROOT:?}"
: "${OFFICIAL_ARCHIVE:?}"
: "${UT3_ARTIFACT_DIR:?}"
: "${UT3_WORK_DIR:?}"
: "${UT3_PREDECESSOR_HEAD:?}"
: "${UT3_PREDECESSOR_TREE:?}"
TARGET="$REPO_ROOT/experiments/epoch2-upstream-thin-sysconfig-sdk"
cd "$REPO_ROOT"
python3 -B "$TARGET/run_sysconfig_sdk_experiment.py" \
  --root "$REPO_ROOT" \
  --archive "$OFFICIAL_ARCHIVE" \
  --output "$TARGET" \
  --artifacts "$UT3_ARTIFACT_DIR" \
  --work "$UT3_WORK_DIR" \
  --source-dir "$TARGET" \
  --cc "${UT3_CC:-clang}" \
  --cxx "${UT3_CXX:-clang++}" \
  --ar "${UT3_AR:-llvm-ar}" \
  --patchelf "${UT3_PATCHELF:-patchelf}" \
  --readelf "${UT3_READELF:-readelf}" \
  --pkg-config "${UT3_PKG_CONFIG:-pkg-config}"
python3 -B "$TARGET/audit_sysconfig_sdk.py" --root "$REPO_ROOT" --output "$TARGET" --artifacts "$UT3_ARTIFACT_DIR"
python3 -B "$TARGET/finalize_sysconfig_sdk.py" --root "$REPO_ROOT" --artifact-dir "$UT3_ARTIFACT_DIR" --predecessor-head "$UT3_PREDECESSOR_HEAD" --predecessor-tree "$UT3_PREDECESSOR_TREE"
python3 -B "$TARGET/verify_sysconfig_sdk.py" --root "$REPO_ROOT" --artifact-dir "$UT3_ARTIFACT_DIR" --expected-predecessor-head "$UT3_PREDECESSOR_HEAD" --expected-predecessor-tree "$UT3_PREDECESSOR_TREE"
