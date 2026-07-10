#!/usr/bin/env bash
# Prepare a detached exact-source worktree for Stage 3-B Phase 2 replay.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

INPUT_DIR="${INPUT_DIR:-$RESULTS_ROOT/workstation/stage3b-build-input-provenance}"
REPLAY_ROOT="${REPLAY_ROOT:-$WORK_ROOT/workstation/stage3b-phase2-replay}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/workstation/stage3b-phase2-replay}"
SOURCE_WORKTREE="$REPLAY_ROOT/source"
CROSS_BUILD_DIR="$REPLAY_ROOT/cross-build"
CACHE_DIR="${CACHE_DIR:-$CACHE_ROOT/workstation/stage3b-source-deps}"

INPUT_JSON="$INPUT_DIR/current-build-inputs.json"
TOOLCHAIN_JSON="$INPUT_DIR/current-toolchain-identity.json"
LINEAGE_JSON="$INPUT_DIR/current-lineage-analysis.json"

for f in "$INPUT_JSON" "$TOOLCHAIN_JSON" "$LINEAGE_JSON"; do
    [[ -f "$f" ]] || {
        echo "ERROR: missing Phase 1 result: $f" >&2
        exit 2
    }
done

readarray -t meta < <(python3 - "$INPUT_JSON" "$TOOLCHAIN_JSON" "$LINEAGE_JSON" <<'PY'
import json, sys
inputs=json.load(open(sys.argv[1]))
tool=json.load(open(sys.argv[2]))
lineage=json.load(open(sys.argv[3]))
source=inputs["cpython_source_git"]
print(source.get("toplevel") or "")
print(source.get("head") or "")
print(tool.get("android_sdk_root_derived") or "")
print(tool.get("ndk_version_derived") or "")
print("true" if lineage["findings"].get("phase2_ready") else "false")
PY
)

SOURCE_TOPLEVEL="${meta[0]}"
SOURCE_HEAD="${meta[1]}"
ANDROID_HOME_DERIVED="${meta[2]}"
ACTIVE_NDK_VERSION="${meta[3]}"
PHASE2_READY="${meta[4]}"

[[ "$PHASE2_READY" == "true" ]] || {
    echo "ERROR: Phase 1 lineage analysis is not Phase-2 ready" >&2
    exit 3
}

[[ -n "$SOURCE_TOPLEVEL" && -d "$SOURCE_TOPLEVEL/.git" || -f "$SOURCE_TOPLEVEL/.git" ]] || {
    echo "ERROR: exact source Git toplevel unavailable: $SOURCE_TOPLEVEL" >&2
    exit 3
}

[[ -n "$SOURCE_HEAD" ]] || {
    echo "ERROR: exact source Git HEAD unavailable" >&2
    exit 3
}

[[ "$ACTIVE_NDK_VERSION" == "27.3.13750724" ]] || {
    echo "ERROR: unexpected active NDK version: $ACTIVE_NDK_VERSION" >&2
    exit 3
}

mkdir -p "$REPLAY_ROOT" "$RESULTS_DIR" "$CACHE_DIR"

if git -C "$SOURCE_TOPLEVEL" worktree list --porcelain | grep -Fqx "worktree $SOURCE_WORKTREE"; then
    git -C "$SOURCE_TOPLEVEL" worktree remove --force "$SOURCE_WORKTREE"
fi
rm -rf "$SOURCE_WORKTREE" "$CROSS_BUILD_DIR"

git -C "$SOURCE_TOPLEVEL" worktree add --detach "$SOURCE_WORKTREE" "$SOURCE_HEAD"

PRESERVED="$PROJECT_ROOT/experiments/bootstrap-android-build/android-python-work"
for rel in android.py android-env.sh; do
    source_file="$SOURCE_WORKTREE/Android/$rel"
    preserved_file="$PRESERVED/$rel"
    [[ -f "$source_file" && -f "$preserved_file" ]] || {
        echo "ERROR: missing producer model file: $rel" >&2
        exit 4
    }
    if ! cmp -s "$source_file" "$preserved_file"; then
        echo "ERROR: producer model drift detected: Android/$rel differs from preserved snapshot" >&2
        exit 4
    fi
done

ANDROID_HOME_RESOLVED="${ANDROID_HOME:-$ANDROID_HOME_DERIVED}"
[[ -n "$ANDROID_HOME_RESOLVED" && -d "$ANDROID_HOME_RESOLVED" ]] || {
    echo "ERROR: Android SDK root not found: $ANDROID_HOME_RESOLVED" >&2
    exit 5
}

python3 - "$RESULTS_DIR/replay-plan.json" <<PY
import json, hashlib
from pathlib import Path

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

plan={
  "source_toplevel": "$SOURCE_TOPLEVEL",
  "source_head": "$SOURCE_HEAD",
  "source_worktree": "$SOURCE_WORKTREE",
  "cross_build_dir": "$CROSS_BUILD_DIR",
  "cache_dir": "$CACHE_DIR",
  "android_home": "$ANDROID_HOME_RESOLVED",
  "active_ndk_version": "$ACTIVE_NDK_VERSION",
  "target_host": "aarch64-linux-android",
  "producer_model_alignment": {
    "android_py": "MATCH",
    "android_env_sh": "MATCH"
  },
  "source_android_py_sha256": sha256(Path("$SOURCE_WORKTREE/Android/android.py")),
  "source_android_env_sha256": sha256(Path("$SOURCE_WORKTREE/Android/android-env.sh"))
}
Path("$RESULTS_DIR/replay-plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True)+"\n")
PY

cat "$RESULTS_DIR/replay-plan.json"
echo
echo "STAGE3B_PHASE2_REPLAY_PREPARE=PASS"
