#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-B Phase 5: production-shape whole-prefix relocation for the promoted runtime.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

CANDIDATE_PREFIX="$WORK_ROOT/termux/stage3b-promoted-runtime/prefix"
FROZEN_PREFIX="$TERMUX_WORK_ROOT/runtime/prefix"
RELOCATION_ROOT="$WORK_ROOT/termux/stage3b-promoted-relocation"
RESULTS_DIR="$RESULTS_ROOT/termux/stage3b-promoted-relocation"
RECONFIRM_SCRIPT="$PROJECT_ROOT/experiments/stage3a-runtime-closure/reconfirm-production-relocation.sh"
VERIFY_PY="$SCRIPT_DIR/verify-promoted-relocation.py"
A_PREFIX="$RELOCATION_ROOT/location-a/prefix"
B_PREFIX="$RELOCATION_ROOT/location-b/prefix"

[[ -x "$CANDIDATE_PREFIX/bin/python" ]] || {
    echo "ERROR: promoted runtime candidate is not assembled" >&2
    exit 2
}

[[ -x "$FROZEN_PREFIX/bin/python" ]] || {
    echo "ERROR: frozen Stage 2-C runtime is missing: $FROZEN_PREFIX" >&2
    exit 2
}

[[ -f "$RECONFIRM_SCRIPT" ]] || {
    echo "ERROR: relocation engine is missing: $RECONFIRM_SCRIPT" >&2
    exit 2
}

[[ -f "$VERIFY_PY" ]] || {
    echo "ERROR: relocation verifier is missing: $VERIFY_PY" >&2
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

write_comparison() {
    local path="$1"
    local subject_key="$2"
    local subject_value="$3"
    local before="$4"
    local after="$5"

    {
        printf '%s=%s\n' "$subject_key" "$subject_value"
        printf 'before=%s\n' "$before"
        printf 'after=%s\n' "$after"
        if [[ "$before" == "$after" ]]; then
            echo 'pass=true'
        else
            echo 'pass=false'
        fi
    } > "$path"
}

rm -rf "$RELOCATION_ROOT" "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR"

candidate_before="$(tree_fingerprint "$CANDIDATE_PREFIX")"
frozen_before="$(tree_fingerprint "$FROZEN_PREFIX")"

printf 'Candidate prefix:  %s\n' "$CANDIDATE_PREFIX"
printf 'Frozen prefix:     %s\n' "$FROZEN_PREFIX"
printf 'Relocation root:   %s\n' "$RELOCATION_ROOT"
printf 'Location A prefix: %s\n' "$A_PREFIX"
printf 'Location B prefix: %s\n' "$B_PREFIX"
printf 'Results:           %s\n' "$RESULTS_DIR"
printf '\n'

set +e
SOURCE_PREFIX="$CANDIDATE_PREFIX" \
ROOT="$RELOCATION_ROOT" \
RESULTS_DIR="$RESULTS_DIR/reconfirm" \
bash "$RECONFIRM_SCRIPT"
workflow_rc=$?
set -e

candidate_after="$(tree_fingerprint "$CANDIDATE_PREFIX")"
frozen_after="$(tree_fingerprint "$FROZEN_PREFIX")"
relocated_after="$(tree_fingerprint "$B_PREFIX")"

{
    echo "returncode=$workflow_rc"
    echo "engine=$RECONFIRM_SCRIPT"
} > "$RESULTS_DIR/workflow-status.txt"

write_comparison \
    "$RESULTS_DIR/candidate-runtime-mutation-check.txt" \
    candidate_prefix \
    "$CANDIDATE_PREFIX" \
    "$candidate_before" \
    "$candidate_after"

write_comparison \
    "$RESULTS_DIR/frozen-runtime-mutation-check.txt" \
    frozen_prefix \
    "$FROZEN_PREFIX" \
    "$frozen_before" \
    "$frozen_after"

write_comparison \
    "$RESULTS_DIR/relocated-runtime-fidelity-check.txt" \
    relocated_prefix \
    "$B_PREFIX" \
    "$candidate_before" \
    "$relocated_after"

{
    if [[ -e "$A_PREFIX" ]]; then
        echo 'a_prefix_exists=true'
    else
        echo 'a_prefix_exists=false'
    fi
    if [[ -d "$B_PREFIX" ]]; then
        echo 'b_prefix_exists=true'
    else
        echo 'b_prefix_exists=false'
    fi
    if [[ -x "$B_PREFIX/bin/python" ]]; then
        echo 'b_python_executable=true'
    else
        echo 'b_python_executable=false'
    fi
} > "$RESULTS_DIR/relocation-location-state.txt"

mutation_rc=0
if [[ "$candidate_before" != "$candidate_after" ]]; then
    echo "ERROR: promoted source candidate metadata fingerprint changed" >&2
    mutation_rc=3
fi
if [[ "$frozen_before" != "$frozen_after" ]]; then
    echo "ERROR: frozen Stage 2-C runtime metadata fingerprint changed" >&2
    mutation_rc=3
fi

fidelity_rc=0
if [[ "$candidate_before" != "$relocated_after" ]]; then
    echo "ERROR: relocated B runtime fingerprint differs from source candidate" >&2
    fidelity_rc=4
fi

set +e
"$CANDIDATE_PREFIX/bin/python" \
    -I -B -S \
    "$VERIFY_PY" \
    --results-dir "$RESULTS_DIR" \
    --candidate-prefix "$CANDIDATE_PREFIX" \
    --frozen-prefix "$FROZEN_PREFIX" \
    --relocation-root "$RELOCATION_ROOT"
verify_rc=$?
set -e

final_rc=0
if [[ $workflow_rc -ne 0 ]]; then
    final_rc=$workflow_rc
elif [[ $mutation_rc -ne 0 ]]; then
    final_rc=$mutation_rc
elif [[ $fidelity_rc -ne 0 ]]; then
    final_rc=$fidelity_rc
elif [[ $verify_rc -ne 0 ]]; then
    final_rc=$verify_rc
fi

printf '\nWorkflow:            %s\n' "$RESULTS_DIR/workflow-status.txt"
printf 'Candidate mutation:  %s\n' "$RESULTS_DIR/candidate-runtime-mutation-check.txt"
printf 'Frozen mutation:     %s\n' "$RESULTS_DIR/frozen-runtime-mutation-check.txt"
printf 'Relocated fidelity:  %s\n' "$RESULTS_DIR/relocated-runtime-fidelity-check.txt"
printf 'Location state:      %s\n' "$RESULTS_DIR/relocation-location-state.txt"
printf 'Verification:        %s\n' "$RESULTS_DIR/promoted-relocation-verification.json"
printf '\n'

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3B_PROMOTED_RELOCATION=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "LOCATION_RECONFIRM[A]=PASS"
echo "LOCATION_RECONFIRM[B]=PASS"
echo "STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS"
echo "RELOCATED_RUNTIME_FIDELITY_CHECK=PASS"
echo "CANDIDATE_RUNTIME_MUTATION_CHECK=PASS"
echo "FROZEN_RUNTIME_MUTATION_CHECK=PASS"
echo "STAGE3B_PROMOTED_RELOCATION=PASS"
