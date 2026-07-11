#!/usr/bin/env bash
# Stage 3-B Phase 2: prepare an isolated upstream Android replay worktree.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

PROVENANCE_DIR="${PROVENANCE_DIR:-$RESULTS_ROOT/workstation/stage3b-build-input-provenance}"
REPLAY_ROOT="${REPLAY_ROOT:-$WORK_ROOT/workstation/stage3b-upstream-replay}"
SOURCE_WORKTREE="$REPLAY_ROOT/source"
CROSS_BUILD_DIR="$REPLAY_ROOT/cross-build"
CACHE_DIR="${CACHE_DIR:-$PROJECT_ROOT/cache/stage3b-source-deps}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/workstation/stage3b-upstream-replay}"
PLAN_JSON="$RESULTS_DIR/replay-plan.json"

BUILD_INPUTS="$PROVENANCE_DIR/current-build-inputs.json"
TOOLCHAIN_JSON="$PROVENANCE_DIR/current-toolchain-identity.json"
LINEAGE_JSON="$PROVENANCE_DIR/current-lineage-analysis.json"
SNAPSHOT_DIR="$PROJECT_ROOT/experiments/bootstrap-android-build/android-python-work"

for f in "$BUILD_INPUTS" "$TOOLCHAIN_JSON" "$LINEAGE_JSON"; do
    [[ -f "$f" ]] || {
        echo "ERROR: missing Phase 1 input: $f" >&2
        exit 2
    }
done

read_json_field() {
    local file="$1"
    local expr="$2"
    python3 - "$file" "$expr" <<'PY'
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

PHASE2_READY="$(read_json_field "$LINEAGE_JSON" findings.phase2_ready)"
[[ "$PHASE2_READY" == "True" ]] || {
    echo "ERROR: Phase 1 lineage gate is not ready" >&2
    exit 3
}

SOURCE_REPO="$(read_json_field "$BUILD_INPUTS" cpython_source_git.toplevel)"
SOURCE_HEAD="$(read_json_field "$BUILD_INPUTS" cpython_source_git.head)"
ANDROID_HOME_DERIVED="$(read_json_field "$TOOLCHAIN_JSON" android_sdk_root_derived)"
NDK_VERSION="$(read_json_field "$TOOLCHAIN_JSON" ndk_version_derived)"
TARGET_HOST="$(read_json_field "$BUILD_INPUTS" target.target_host)"

[[ -d "$SOURCE_REPO/.git" || -f "$SOURCE_REPO/.git" ]] || {
    echo "ERROR: source Git worktree not found: $SOURCE_REPO" >&2
    exit 2
}

[[ -d "$ANDROID_HOME_DERIVED/ndk/$NDK_VERSION" ]] || {
    echo "ERROR: expected NDK not found: $ANDROID_HOME_DERIVED/ndk/$NDK_VERSION" >&2
    exit 2
}

mkdir -p "$REPLAY_ROOT" "$CACHE_DIR" "$RESULTS_DIR"

if [[ -e "$SOURCE_WORKTREE" ]]; then
    git -C "$SOURCE_REPO" worktree remove --force "$SOURCE_WORKTREE" 2>/dev/null || rm -rf "$SOURCE_WORKTREE"
fi

git -C "$SOURCE_REPO" worktree add --detach "$SOURCE_WORKTREE" "$SOURCE_HEAD"

ACTUAL_HEAD="$(git -C "$SOURCE_WORKTREE" rev-parse HEAD)"
[[ "$ACTUAL_HEAD" == "$SOURCE_HEAD" ]] || {
    echo "ERROR: detached worktree HEAD mismatch" >&2
    exit 4
}

for name in android.py android-env.sh; do
    cmp -s "$SOURCE_WORKTREE/Android/$name" "$SNAPSHOT_DIR/$name" || {
        echo "ERROR: producer-model drift: Android/$name differs from preserved snapshot" >&2
        exit 5
    }
done

rm -rf "$CROSS_BUILD_DIR"
mkdir -p "$CROSS_BUILD_DIR"

python3 - \
    "$PLAN_JSON" \
    "$SOURCE_REPO" \
    "$SOURCE_HEAD" \
    "$SOURCE_WORKTREE" \
    "$CROSS_BUILD_DIR" \
    "$CACHE_DIR" \
    "$ANDROID_HOME_DERIVED" \
    "$NDK_VERSION" \
    "$TARGET_HOST" <<'PY'
import hashlib, json, sys
from pathlib import Path
(
    out, source_repo, source_head, source_worktree, cross_build_dir,
    cache_dir, android_home, ndk_version, target_host,
) = sys.argv[1:]

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

source = Path(source_worktree)
plan = {
    "schema_version": 1,
    "source_repo": source_repo,
    "source_head": source_head,
    "source_worktree": source_worktree,
    "cross_build_dir": cross_build_dir,
    "cache_dir": cache_dir,
    "android_home": android_home,
    "ndk_version": ndk_version,
    "target_host": target_host,
    "expected_prefix": str(Path(cross_build_dir) / target_host / "prefix"),
    "producer_files": {
        "Android/android.py": sha(source / "Android/android.py"),
        "Android/android-env.sh": sha(source / "Android/android-env.sh"),
    },
    "preflight": {
        "phase1_ready": True,
        "exact_source_head": True,
        "producer_snapshot_match": True,
        "ndk_present": True,
    },
}
Path(out).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
print(json.dumps(plan, indent=2, sort_keys=True))
PY

printf '\nPlan: %s\n' "$PLAN_JSON"
echo "STAGE3B_REPLAY_PREPARE=PASS"
