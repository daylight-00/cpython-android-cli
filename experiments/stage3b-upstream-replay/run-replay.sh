#!/usr/bin/env bash
# Stage 3-B Phase 2: run the isolated upstream Android producer replay.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/workstation/stage3b-phase2-replay}"
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
DRIVER_PYTHON="$(read_json_field driver_python)"
DRIVER_PYTHON_VERSION="$(read_json_field driver_python_version)"
DIST_DIR="$CROSS_BUILD_DIR/$TARGET_HOST/dist"

[[ "$(git -C "$SOURCE_WORKTREE" rev-parse HEAD)" == "$SOURCE_HEAD" ]] || {
    echo "ERROR: replay source HEAD drifted" >&2
    exit 3
}

[[ -x "$DRIVER_PYTHON" ]] || {
    echo "ERROR: replay driver Python disappeared: $DRIVER_PYTHON" >&2
    exit 3
}

[[ "$("$DRIVER_PYTHON" -c 'import platform; print(platform.python_version())')" == "$DRIVER_PYTHON_VERSION" ]] || {
    echo "ERROR: replay driver Python version drifted" >&2
    exit 3
}

[[ -d "$ANDROID_HOME_DERIVED/ndk/$NDK_VERSION" ]] || {
    echo "ERROR: replay NDK disappeared: $ANDROID_HOME_DERIVED/ndk/$NDK_VERSION" >&2
    exit 3
}

mkdir -p "$RESULTS_DIR" "$CACHE_DIR"
rm -rf "$CROSS_BUILD_DIR"
mkdir -p "$CROSS_BUILD_DIR"
: > "$LOG"

printf 'SOURCE_WORKTREE=%s\n' "$SOURCE_WORKTREE"
printf 'SOURCE_HEAD=%s\n' "$SOURCE_HEAD"
printf 'ANDROID_HOME=%s\n' "$ANDROID_HOME_DERIVED"
printf 'NDK_VERSION=%s\n' "$NDK_VERSION"
printf 'TARGET_HOST=%s\n' "$TARGET_HOST"
printf 'CROSS_BUILD_DIR=%s\n' "$CROSS_BUILD_DIR"
printf 'CACHE_DIR=%s\n' "$CACHE_DIR"
printf 'EXPECTED_PREFIX=%s\n' "$EXPECTED_PREFIX"
printf 'DRIVER_PYTHON=%s\n' "$DRIVER_PYTHON"
printf 'DRIVER_PYTHON_VERSION=%s\n' "$DRIVER_PYTHON_VERSION"
printf '\n'

set +e
(
    cd "$SOURCE_WORKTREE"
    env \
        ANDROID_HOME="$ANDROID_HOME_DERIVED" \
        "$DRIVER_PYTHON" Android/android.py \
            build \
            --cross-build-dir "$CROSS_BUILD_DIR" \
            --cache-dir "$CACHE_DIR" \
            build

    env \
        ANDROID_HOME="$ANDROID_HOME_DERIVED" \
        "$DRIVER_PYTHON" Android/android.py \
            build \
            --cross-build-dir "$CROSS_BUILD_DIR" \
            --cache-dir "$CACHE_DIR" \
            "$TARGET_HOST"
) 2>&1 | tee -a "$LOG"
build_rc=${PIPESTATUS[0]}
set -e

if [[ $build_rc -ne 0 ]]; then
    package_rc=-1
else
    set +e
    (
        cd "$SOURCE_WORKTREE"
        env \
            ANDROID_HOME="$ANDROID_HOME_DERIVED" \
            "$DRIVER_PYTHON" Android/android.py \
                package \
                --cross-build-dir "$CROSS_BUILD_DIR" \
                "$TARGET_HOST"
    ) 2>&1 | tee -a "$LOG"
    package_rc=${PIPESTATUS[0]}
    set -e
fi

PACKAGE_ARCHIVE=""
if [[ -d "$DIST_DIR" ]]; then
    PACKAGE_ARCHIVE="$(find "$DIST_DIR" -maxdepth 1 -type f -name "python-*-$TARGET_HOST.tar.gz" -print | sort | tail -n 1)"
fi

python3 - \
    "$RESULTS_DIR/replay-build-result.json" \
    "$build_rc" \
    "$package_rc" \
    "$LOG" \
    "$EXPECTED_PREFIX" \
    "$PACKAGE_ARCHIVE" <<'PY'
import hashlib, json, sys
from pathlib import Path
out, build_rc, package_rc, log, prefix, archive = sys.argv[1:]
result = {
    "build_returncode": int(build_rc),
    "package_returncode": int(package_rc),
    "log": log,
    "expected_prefix": prefix,
    "expected_prefix_exists": Path(prefix).is_dir(),
    "package_archive": archive or None,
    "package_archive_exists": bool(archive and Path(archive).is_file()),
}
if archive and Path(archive).is_file():
    h = hashlib.sha256()
    with open(archive, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    result["package_archive_sha256"] = h.hexdigest()
    result["package_archive_size_bytes"] = Path(archive).stat().st_size
Path(out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
PY

if [[ $build_rc -ne 0 ]]; then
    echo "STAGE3B_UPSTREAM_REPLAY=FAIL build_rc=$build_rc"
    exit "$build_rc"
fi

if [[ $package_rc -ne 0 ]]; then
    echo "STAGE3B_UPSTREAM_REPLAY=FAIL package_rc=$package_rc"
    exit "$package_rc"
fi

[[ -d "$EXPECTED_PREFIX" ]] || {
    echo "ERROR: replay build returned success but prefix is missing: $EXPECTED_PREFIX" >&2
    exit 4
}

[[ -n "$PACKAGE_ARCHIVE" && -f "$PACKAGE_ARCHIVE" ]] || {
    echo "ERROR: package command returned success but archive was not found under: $DIST_DIR" >&2
    exit 5
}

"$DRIVER_PYTHON" \
    "$SCRIPT_DIR/capture-replay-output.py" \
    --plan "$PLAN_JSON" \
    --output-dir "$RESULTS_DIR"

echo
printf 'Build log: %s\n' "$LOG"
printf 'Build result: %s\n' "$RESULTS_DIR/replay-build-result.json"
printf 'Output summary: %s\n' "$RESULTS_DIR/replay-output-summary.json"
printf 'Package archive: %s\n' "$PACKAGE_ARCHIVE"
echo
echo "STAGE3B_UPSTREAM_REPLAY=PASS"
