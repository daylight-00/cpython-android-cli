#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
: "${REPO_ROOT:?}" "${OFFICIAL_ARCHIVE:?}" "${CPYTHON_SOURCE_ARCHIVE:?}" "${API36_WORK_DIR:?}" "${API36_PREDECESSOR_HEAD:?}" "${API36_PREDECESSOR_TREE:?}" "${ANDROID_HOME:?}" "${API36_NDK_PATH:?}" "${API36_NDK_REVISION:?}"
OUT="$REPO_ROOT/experiments/epoch2-upstream-thin-api36-controlled-comparison"
python3 -B "$OUT/run_api36_controlled_comparison.py" --repo "$REPO_ROOT" --official-archive "$OFFICIAL_ARCHIVE" --source-archive "$CPYTHON_SOURCE_ARCHIVE" --work "$API36_WORK_DIR" --output "$OUT" --android-home "$ANDROID_HOME" --ndk-path "$API36_NDK_PATH" --ndk-revision "$API36_NDK_REVISION"
python3 -B "$OUT/audit_api36_comparison.py" --output "$OUT"
python3 -B "$OUT/finalize_api36_comparison.py" --root "$REPO_ROOT" --predecessor-head "$API36_PREDECESSOR_HEAD" --predecessor-tree "$API36_PREDECESSOR_TREE"
python3 -B "$OUT/verify_api36_comparison.py" --root "$REPO_ROOT" --expected-predecessor-head "$API36_PREDECESSOR_HEAD" --expected-predecessor-tree "$API36_PREDECESSOR_TREE"
python3 -B "$OUT/test_verify_api36_comparison.py" --root "$REPO_ROOT"
