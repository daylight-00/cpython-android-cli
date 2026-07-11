#!/usr/bin/env bash
# Stage 3-B Phase 2: run the isolated upstream Android producer replay.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/workstation/stage3b-upstream-replay}"
PLAN_JSON="$RESULTS_DIR/replay-plan.json"
LOG="$RESULTS_DIR/replay-build.log"

[[ -f "$PLAN_JSON" ]] || {
    echo "ERROR: missing replay plan; run prepare-replay.sh first: $PLAN_JSON" >&2
    exit 2
}

read_json_field() {
    local expr="$1"
    python3 - "$PLAN_JSON" "$expr" <<'PY'
import json, sys
p, expr = sys.argv[1:]
with open(p) as f:
    data = json.load(f)
value = data
for key in expr.split('.'):
    value = value[key]
print(value)
PY
}

SOURCE_WORKTREE="$(read_json_field source_worktree)"
SOURCE_HEAD="$(read_json_field source_head)"
CROSS_BUILD_DIR="$(read_json_field cross_build_dir)"
CACHE_DIR="$(read_json_field cache_dir)"
ANDROID_HOME_DERIVED="$(read_json_field android_home)"
NDK_VERSION="$(read_json_field ndk_version)"
TARGET_HOST="$(read_json_field target_host)"
EXPECTED_PREFIX="$(read_json_field expected_prefix)"

[[ "$(git -C "$SOURCE_WORKTREE" rev-parse HEAD)" == "$SOURCE_HEAD" ]] || {
    echo "ERROR: replay source HEAD drifted" >&2
    exit 3
}

[[ -d "$ANDROID_HOME_DERIVED/ndk/$NDK_VERSION" ]] || {
    echo "ERROR: replay NDK disappeared: $ANDROID_HOME_DERIVED/ndk/$NDK_VERSION" >&2
    exit 3
}

mkdir -p "$RESULTS_DIR" "$CACHE_DIR"
rm -rf "$CROSS_BUILD_DIR"
mkdir -p "$CROSS_BUILD_DIR"

printf 'SOURCE_WORKTREE=%s\n' "$SOURCE_WORKTREE"
printf 'SOURCE_HEAD=%s\n' "$SOURCE_HEAD"
printf 'ANDROID_HOME=%s\n' "$ANDROID_HOME_DERIVED"
printf 'NDK_VERSION=%s\n' "$NDK_VERSION"
printf 'TARGET_HOST=%s\n' "$TARGET_HOST"
printf 'CROSS_BUILD_DIR=%s\n' "$CROSS_BUILD_DIR"
printf 'CACHE_DIR=%s\n' "$CACHE_DIR"
printf 'EXPECTED_PREFIX=%s\n' "$EXPECTED_PREFIX"
printf '\n'

set +e
(
    cd "$SOURCE_WORKTREE"
    env \
        ANDROID_HOME="$ANDROID_HOME_DERIVED" \
        python3 Android/android.py \
            build \
            --cross-build-dir "$CROSS_BUILD_DIR" \
            --cache-dir "$CACHE_DIR" \
            "$TARGET_HOST"
) 2>&1 | tee "$LOG"
build_rc=${PIPESTATUS[0]}
set -e

python3 - "$RESULTS_DIR/replay-build-result.json" "$build_rc" "$LOG" "$EXPECTED_PREFIX" <<'PY'
import json, sys
from pathlib import Path
out, rc, log, prefix = sys.argv[1:]
result = {
    "build_returncode": int(rc),
    "log": log,
    "expected_prefix": prefix,
    "expected_prefix_exists": Path(prefix).is_dir(),
}
Path(out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
PY

if [[ $build_rc -ne 0 ]]; then
    echo "STAGE3B_UPSTREAM_REPLAY=FAIL rc=$build_rc"
    exit "$build_rc"
fi

[[ -d "$EXPECTED_PREFIX" ]] || {
    echo "ERROR: replay build returned success but prefix is missing: $EXPECTED_PREFIX" >&2
    exit 4
}

python3 \
    "$SCRIPT_DIR/capture-replay-output.py" \
    --plan "$PLAN_JSON" \
    --output-dir "$RESULTS_DIR"

echo
printf 'Build log: %s\n' "$LOG"
printf 'Output summary: %s\n' "$RESULTS_DIR/replay-output-summary.json"
echo
echo "STAGE3B_UPSTREAM_REPLAY=PASS"
