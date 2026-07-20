#!/usr/bin/env bash
set -euo pipefail
: "${REPO_ROOT:?}"
: "${OFFICIAL_ARCHIVE:?}"
: "${UT6_WORK_DIR:?}"
: "${UT6_ARTIFACT_DIR:?}"
: "${UT6_PREDECESSOR_HEAD:?}"
: "${UT6_PREDECESSOR_TREE:?}"
TARGET="$REPO_ROOT/experiments/epoch2-upstream-thin-platform-portability"
cd "$REPO_ROOT"
python3 -B "$TARGET/run_platform_portability_experiment.py" --root "$REPO_ROOT" --archive "$OFFICIAL_ARCHIVE" --work "$UT6_WORK_DIR" --output "$TARGET" --artifacts "$UT6_ARTIFACT_DIR" --cc "${UT6_CC:-clang}" --cxx "${UT6_CXX:-clang++}" --ar "${UT6_AR:-llvm-ar}" --patchelf "${UT6_PATCHELF:-patchelf}" --readelf "${UT6_READELF:-readelf}" --pkg-config "${UT6_PKG_CONFIG:-pkg-config}"
python3 -B "$TARGET/audit_platform_portability.py" --output "$TARGET"
python3 -B "$TARGET/finalize_platform_portability.py" --root "$REPO_ROOT" --predecessor-head "$UT6_PREDECESSOR_HEAD" --predecessor-tree "$UT6_PREDECESSOR_TREE"
python3 -B "$TARGET/verify_platform_portability.py" --root "$REPO_ROOT" --expected-predecessor-head "$UT6_PREDECESSOR_HEAD" --expected-predecessor-tree "$UT6_PREDECESSOR_TREE"
