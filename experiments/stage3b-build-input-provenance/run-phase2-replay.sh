#!/usr/bin/env bash
# Execute Stage 3-B Phase 2 clean Android producer replay.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

REPLAY_ROOT="${REPLAY_ROOT:-$WORK_ROOT/workstation/stage3b-phase2-replay}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/workstation/stage3b-phase2-replay}"
SOURCE_WORKTREE="$REPLAY_ROOT/source"
CROSS_BUILD_DIR="$REPLAY_ROOT/cross-build"
CACHE_DIR="${CACHE_DIR:-$CACHE_ROOT/workstation/stage3b-source-deps}"
PLAN_JSON="$RESULTS_DIR/replay-plan.json"
TARGET_HOST="aarch64-linux-android"

[[ -f "$PLAN_JSON" ]] || {
    echo "ERROR: run prepare-phase2-replay.sh first; missing: $PLAN_JSON" >&2
    exit 2
}

readarray -t plan < <(python3 - "$PLAN_JSON" <<'PY'
import json, sys
p=json.load(open(sys.argv[1]))
print(p["android_home"])
print(p["source_head"])
print(p["source_worktree"])
print(p["cross_build_dir"])
print(p["cache_dir"])
PY
)

ANDROID_HOME_RESOLVED="${plan[0]}"
SOURCE_HEAD="${plan[1]}"
PLAN_SOURCE_WORKTREE="${plan[2]}"
PLAN_CROSS_BUILD_DIR="${plan[3]}"
PLAN_CACHE_DIR="${plan[4]}"

[[ "$PLAN_SOURCE_WORKTREE" == "$SOURCE_WORKTREE" ]] || {
    echo "ERROR: replay plan source worktree mismatch" >&2
    exit 3
}
[[ "$PLAN_CROSS_BUILD_DIR" == "$CROSS_BUILD_DIR" ]] || {
    echo "ERROR: replay plan cross-build dir mismatch" >&2
    exit 3
}
[[ "$PLAN_CACHE_DIR" == "$CACHE_DIR" ]] || {
    echo "ERROR: replay plan cache dir mismatch" >&2
    exit 3
}

[[ -x "$SOURCE_WORKTREE/Android/android.py" ]] || {
    echo "ERROR: source Android producer missing: $SOURCE_WORKTREE/Android/android.py" >&2
    exit 3
}

actual_head="$(git -C "$SOURCE_WORKTREE" rev-parse HEAD)"
[[ "$actual_head" == "$SOURCE_HEAD" ]] || {
    echo "ERROR: source worktree HEAD drift: expected=$SOURCE_HEAD actual=$actual_head" >&2
    exit 3
}

mkdir -p "$RESULTS_DIR" "$CACHE_DIR"
BUILD_LOG="$RESULTS_DIR/replay-build.log"
PACKAGE_LOG="$RESULTS_DIR/replay-package.log"

export ANDROID_HOME="$ANDROID_HOME_RESOLVED"

printf 'SOURCE_HEAD=%s\n' "$SOURCE_HEAD"
printf 'SOURCE_WORKTREE=%s\n' "$SOURCE_WORKTREE"
printf 'CROSS_BUILD_DIR=%s\n' "$CROSS_BUILD_DIR"
printf 'CACHE_DIR=%s\n' "$CACHE_DIR"
printf 'ANDROID_HOME=%s\n' "$ANDROID_HOME"
printf 'TARGET_HOST=%s\n' "$TARGET_HOST"

echo
echo "== Clean Android producer replay =="
set +e
python3 "$SOURCE_WORKTREE/Android/android.py" \
    build \
    --cross-build-dir "$CROSS_BUILD_DIR" \
    --cache-dir "$CACHE_DIR" \
    --clean \
    "$TARGET_HOST" \
    2>&1 | tee "$BUILD_LOG"
build_rc=${PIPESTATUS[0]}
set -e

if [[ $build_rc -ne 0 ]]; then
    echo "STAGE3B_PHASE2_BUILD_REPLAY=FAIL rc=$build_rc"
    exit "$build_rc"
fi

PREFIX_DIR="$CROSS_BUILD_DIR/$TARGET_HOST/prefix"
EXPECTED=(
    "$PREFIX_DIR/include/python3.14/Python.h"
    "$PREFIX_DIR/include/python3.14/pyconfig.h"
    "$PREFIX_DIR/lib/libpython3.14.so"
    "$PREFIX_DIR/lib/python3.14"
)
for path in "${EXPECTED[@]}"; do
    [[ -e "$path" ]] || {
        echo "ERROR: expected replay product missing: $path" >&2
        exit 4
    }
done

echo
echo "== Package replay product =="
set +e
python3 "$SOURCE_WORKTREE/Android/android.py" \
    package \
    --cross-build-dir "$CROSS_BUILD_DIR" \
    "$TARGET_HOST" \
    2>&1 | tee "$PACKAGE_LOG"
package_rc=${PIPESTATUS[0]}
set -e

if [[ $package_rc -ne 0 ]]; then
    echo "STAGE3B_PHASE2_PACKAGE_REPLAY=FAIL rc=$package_rc"
    exit "$package_rc"
fi

PACKAGE_PATH="$(find "$CROSS_BUILD_DIR/$TARGET_HOST/dist" -maxdepth 1 -type f -name '*.tar.gz' -print | sort | tail -n 1)"
[[ -n "$PACKAGE_PATH" && -f "$PACKAGE_PATH" ]] || {
    echo "ERROR: replay package archive not found" >&2
    exit 5
}

python3 - "$RESULTS_DIR/replay-result.json" "$PREFIX_DIR" "$PACKAGE_PATH" "$SOURCE_HEAD" <<'PY'
import hashlib, json, os, sys
from pathlib import Path

out=Path(sys.argv[1]); prefix=Path(sys.argv[2]); package=Path(sys.argv[3]); head=sys.argv[4]

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

result={
  "source_head": head,
  "prefix_dir": str(prefix),
  "prefix_exists": prefix.is_dir(),
  "package_path": str(package),
  "package_size_bytes": package.stat().st_size,
  "package_sha256": sha256(package),
  "required_products": {
    "Python.h": (prefix/"include/python3.14/Python.h").is_file(),
    "pyconfig.h": (prefix/"include/python3.14/pyconfig.h").is_file(),
    "libpython3.14.so": (prefix/"lib/libpython3.14.so").is_file(),
    "stdlib": (prefix/"lib/python3.14").is_dir(),
  },
}
out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
print(json.dumps(result, indent=2, sort_keys=True))
PY

echo
echo "STAGE3B_PHASE2_BUILD_REPLAY=PASS"
echo "STAGE3B_PHASE2_PACKAGE_REPLAY=PASS"
