#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-B Phase 5: closure equivalence for the isolated promoted runtime.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

CANDIDATE_PREFIX="$WORK_ROOT/termux/stage3b-promoted-runtime/prefix"
FROZEN_PREFIX="$TERMUX_WORK_ROOT/runtime/prefix"
RESULTS_DIR="$RESULTS_ROOT/termux/stage3b-promoted-closure"
STAGE3A_DIR="$PROJECT_ROOT/experiments/stage3a-runtime-closure"
VERIFY_PY="$SCRIPT_DIR/verify-promoted-closure.py"

[[ -x "$CANDIDATE_PREFIX/bin/python" ]] || {
    echo "ERROR: promoted runtime candidate is not assembled" >&2
    exit 2
}

[[ -d "$FROZEN_PREFIX" ]] || {
    echo "ERROR: frozen Stage 2-C runtime is missing: $FROZEN_PREFIX" >&2
    exit 2
}

tree_fingerprint() {
    local root="$1"
    if [[ ! -d "$root" ]]; then
        echo "ABSENT"
        return
    fi
    find "$root" -xdev -mindepth 1 \
        -printf '%P\t%y\t%m\t%s\t%T@\t%l\n' \
        | LC_ALL=C sort \
        | sha256sum \
        | awk '{print $1}'
}

write_mutation_result() {
    local path="$1"
    local runtime_prefix="$2"
    local before="$3"
    local after="$4"

    {
        echo "runtime_prefix=$runtime_prefix"
        echo "before=$before"
        echo "after=$after"
        if [[ "$before" == "$after" ]]; then
            echo "pass=true"
        else
            echo "pass=false"
        fi
    } > "$path"
}

mkdir -p "$RESULTS_DIR"
candidate_before="$(tree_fingerprint "$CANDIDATE_PREFIX")"
frozen_before="$(tree_fingerprint "$FROZEN_PREFIX")"

printf 'Candidate prefix: %s\n' "$CANDIDATE_PREFIX"
printf 'Frozen prefix:    %s\n' "$FROZEN_PREFIX"
printf 'Results:          %s\n' "$RESULTS_DIR"
printf '\n'

set +e
RUNTIME_PREFIX="$CANDIDATE_PREFIX" \
PYTHON_BIN="$CANDIDATE_PREFIX/bin/python" \
OUTPUT_DIR="$RESULTS_DIR" \
bash "$STAGE3A_DIR/inventory-runtime.sh"
workflow_rc=$?
set -e

if [[ $workflow_rc -eq 0 ]]; then
    set +e
    RUNTIME_PREFIX="$CANDIDATE_PREFIX" \
    PYTHON_BIN="$CANDIDATE_PREFIX/bin/python" \
    RESULTS_DIR="$RESULTS_DIR" \
    bash "$STAGE3A_DIR/analyze-and-probe.sh"
    workflow_rc=$?
    set -e
fi

if [[ $workflow_rc -eq 0 ]]; then
    set +e
    RUNTIME_PREFIX="$CANDIDATE_PREFIX" \
    PYTHON_BIN="$CANDIDATE_PREFIX/bin/python" \
    RESULTS_DIR="$RESULTS_DIR" \
    bash "$STAGE3A_DIR/probe-extension-imports.sh"
    workflow_rc=$?
    set -e
fi

candidate_after="$(tree_fingerprint "$CANDIDATE_PREFIX")"
frozen_after="$(tree_fingerprint "$FROZEN_PREFIX")"

write_mutation_result \
    "$RESULTS_DIR/candidate-runtime-mutation-check.txt" \
    "$CANDIDATE_PREFIX" \
    "$candidate_before" \
    "$candidate_after"
write_mutation_result \
    "$RESULTS_DIR/frozen-runtime-mutation-check.txt" \
    "$FROZEN_PREFIX" \
    "$frozen_before" \
    "$frozen_after"

mutation_rc=0
if [[ "$candidate_before" != "$candidate_after" ]]; then
    echo "ERROR: promoted runtime candidate metadata fingerprint changed" >&2
    mutation_rc=3
fi

if [[ "$frozen_before" != "$frozen_after" ]]; then
    echo "ERROR: frozen Stage 2-C runtime metadata fingerprint changed" >&2
    mutation_rc=3
fi

set +e
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX="$RESULTS_DIR/pycache-verification" \
"$CANDIDATE_PREFIX/bin/python" \
    "$VERIFY_PY" \
    --results-dir "$RESULTS_DIR" \
    --expected-runtime-prefix "$CANDIDATE_PREFIX" \
    --frozen-runtime-prefix "$FROZEN_PREFIX"
verify_rc=$?
set -e

final_rc=0
if [[ $workflow_rc -ne 0 ]]; then
    final_rc=$workflow_rc
elif [[ $mutation_rc -ne 0 ]]; then
    final_rc=$mutation_rc
elif [[ $verify_rc -ne 0 ]]; then
    final_rc=$verify_rc
fi

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3B_PROMOTED_CLOSURE=FAIL rc=$final_rc"
    exit "$final_rc"
fi

printf '\n'
echo "Candidate mutation: $RESULTS_DIR/candidate-runtime-mutation-check.txt"
echo "Frozen mutation:    $RESULTS_DIR/frozen-runtime-mutation-check.txt"
echo "Verification:       $RESULTS_DIR/promoted-closure-verification.json"
printf '\n'
echo "CANDIDATE_RUNTIME_MUTATION_CHECK=PASS"
echo "FROZEN_RUNTIME_MUTATION_CHECK=PASS"
echo "STAGE3B_PROMOTED_CLOSURE=PASS"
