#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-B Phase 5: canonical smoke on isolated promoted runtime.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

CANDIDATE_ROOT="$WORK_ROOT/termux/stage3b-promoted-runtime"
CANDIDATE_PREFIX="$CANDIDATE_ROOT/prefix"
CANDIDATE_RESULTS="$RESULTS_ROOT/termux/stage3b-promoted-smoke"
FROZEN_PREFIX="$TERMUX_WORK_ROOT/runtime/prefix"
MUTATION_RESULT="$CANDIDATE_RESULTS/frozen-runtime-mutation-check.txt"

[[ -x "$CANDIDATE_PREFIX/bin/python" ]] || {
    echo "ERROR: promoted runtime candidate is not assembled" >&2
    exit 2
}

tree_fingerprint() {
    local root="$1"
    if [[ ! -d "$root" ]]; then
        echo "ABSENT"
        return
    fi
    find "$root" -xdev -mindepth 1 \
        -printf '%P\t%y\t%s\t%T@\t%l\n' \
        | LC_ALL=C sort \
        | sha256sum \
        | awk '{print $1}'
}

mkdir -p "$CANDIDATE_RESULTS"
frozen_before="$(tree_fingerprint "$FROZEN_PREFIX")"

RUNTIME_ROOT_OVERRIDE="$CANDIDATE_ROOT" \
TERMUX_RESULTS_ROOT_OVERRIDE="$CANDIDATE_RESULTS" \
bash "$PROJECT_ROOT/scripts/test/smoke-termux.sh"

frozen_after="$(tree_fingerprint "$FROZEN_PREFIX")"

{
    echo "frozen_prefix=$FROZEN_PREFIX"
    echo "before=$frozen_before"
    echo "after=$frozen_after"
    if [[ "$frozen_before" == "$frozen_after" ]]; then
        echo "pass=true"
    else
        echo "pass=false"
    fi
} > "$MUTATION_RESULT"

[[ "$frozen_before" == "$frozen_after" ]] || {
    echo "ERROR: frozen runtime metadata fingerprint changed" >&2
    exit 3
}

echo
echo "FROZEN_RUNTIME_MUTATION_CHECK=PASS"
echo "STAGE3B_PROMOTED_SMOKE=PASS"
