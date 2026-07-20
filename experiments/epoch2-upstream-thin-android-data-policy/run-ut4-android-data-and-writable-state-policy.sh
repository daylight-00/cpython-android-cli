#!/usr/bin/env bash
set -euo pipefail
: "${REPO_ROOT:?}"
: "${OFFICIAL_ARCHIVE:?}"
: "${UT4_WORK_DIR:?}"
: "${UT4_PREDECESSOR_HEAD:?}"
: "${UT4_PREDECESSOR_TREE:?}"
TARGET="$REPO_ROOT/experiments/epoch2-upstream-thin-android-data-policy"
cd "$REPO_ROOT"
python3 -B "$TARGET/run_android_data_policy_experiment.py" \
  --root "$REPO_ROOT" --archive "$OFFICIAL_ARCHIVE" --output "$TARGET" --work "$UT4_WORK_DIR" \
  --cc "${UT4_CC:-clang}" --patchelf "${UT4_PATCHELF:-patchelf}" --readelf "${UT4_READELF:-readelf}"
python3 -B "$TARGET/audit_android_data_policy.py" --root "$REPO_ROOT" --output "$TARGET"
python3 -B "$TARGET/finalize_android_data_policy.py" --root "$REPO_ROOT" --predecessor-head "$UT4_PREDECESSOR_HEAD" --predecessor-tree "$UT4_PREDECESSOR_TREE"
python3 -B "$TARGET/verify_android_data_policy.py" --root "$REPO_ROOT" --expected-predecessor-head "$UT4_PREDECESSOR_HEAD" --expected-predecessor-tree "$UT4_PREDECESSOR_TREE"
