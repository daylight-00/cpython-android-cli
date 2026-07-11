#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-B Phase 5: CA and timezone boundary equivalence on the target.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

CANDIDATE_PREFIX="$WORK_ROOT/termux/stage3b-promoted-runtime/prefix"
FROZEN_PREFIX="$TERMUX_WORK_ROOT/runtime/prefix"
RESULTS_DIR="$RESULTS_ROOT/termux/stage3b-promoted-boundaries"
STAGE3A_DIR="$PROJECT_ROOT/experiments/stage3a-runtime-closure"
VERIFY_PY="$SCRIPT_DIR/verify-promoted-boundaries.py"
TERMUX_PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"

[[ -x "$CANDIDATE_PREFIX/bin/python" ]] || {
    echo "ERROR: promoted runtime candidate is not assembled" >&2
    exit 2
}

[[ -x "$FROZEN_PREFIX/bin/python" ]] || {
    echo "ERROR: frozen Stage 2-C runtime is missing: $FROZEN_PREFIX" >&2
    exit 2
}

[[ -x "${UV_BIN:-$(command -v uv || true)}" ]] || {
    echo "ERROR: uv not found" >&2
    exit 2
}

tree_fingerprint() {
    local root="$1"
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

workflow_rc=0
run_step() {
    local runtime_name="$1"
    local probe_name="$2"
    local runtime_prefix="$3"
    local output_dir="$4"
    local script_path="$5"

    printf '\n===== %s: %s =====\n' "$runtime_name" "$probe_name"
    set +e
    env \
        RUNTIME_PREFIX="$runtime_prefix" \
        PYTHON_BIN="$runtime_prefix/bin/python" \
        RESULTS_DIR="$output_dir" \
        TERMUX_PREFIX="$TERMUX_PREFIX" \
        bash "$script_path"
    local rc=$?
    set -e

    printf '%s\t%s\t%s\n' "$runtime_name" "$probe_name" "$rc" \
        >> "$RESULTS_DIR/workflow-status.tsv"
    if [[ $rc -ne 0 && $workflow_rc -eq 0 ]]; then
        workflow_rc=$rc
    fi
}

rm -rf "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR/candidate" "$RESULTS_DIR/frozen"
printf 'runtime\tprobe\treturncode\n' > "$RESULTS_DIR/workflow-status.tsv"

candidate_before="$(tree_fingerprint "$CANDIDATE_PREFIX")"
frozen_before="$(tree_fingerprint "$FROZEN_PREFIX")"

printf 'Candidate prefix: %s\n' "$CANDIDATE_PREFIX"
printf 'Frozen prefix:    %s\n' "$FROZEN_PREFIX"
printf 'Termux prefix:    %s\n' "$TERMUX_PREFIX"
printf 'Results:          %s\n' "$RESULTS_DIR"

run_step \
    candidate ca-boundary "$CANDIDATE_PREFIX" "$RESULTS_DIR/candidate" \
    "$STAGE3A_DIR/probe-ca-boundary.sh"
run_step \
    candidate zoneinfo-boundary "$CANDIDATE_PREFIX" "$RESULTS_DIR/candidate" \
    "$STAGE3A_DIR/probe-zoneinfo-boundary.sh"
run_step \
    candidate uv-tzdata-fallback "$CANDIDATE_PREFIX" "$RESULTS_DIR/candidate" \
    "$STAGE3A_DIR/probe-zoneinfo-with-uv-tzdata.sh"

run_step \
    frozen ca-boundary "$FROZEN_PREFIX" "$RESULTS_DIR/frozen" \
    "$STAGE3A_DIR/probe-ca-boundary.sh"
run_step \
    frozen zoneinfo-boundary "$FROZEN_PREFIX" "$RESULTS_DIR/frozen" \
    "$STAGE3A_DIR/probe-zoneinfo-boundary.sh"
run_step \
    frozen uv-tzdata-fallback "$FROZEN_PREFIX" "$RESULTS_DIR/frozen" \
    "$STAGE3A_DIR/probe-zoneinfo-with-uv-tzdata.sh"

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
"$CANDIDATE_PREFIX/bin/python" \
    -I -B -S \
    "$VERIFY_PY" \
    --results-dir "$RESULTS_DIR" \
    --candidate-prefix "$CANDIDATE_PREFIX" \
    --frozen-prefix "$FROZEN_PREFIX" \
    --termux-prefix "$TERMUX_PREFIX"
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

printf '\nWorkflow status:    %s\n' "$RESULTS_DIR/workflow-status.tsv"
printf 'Candidate mutation: %s\n' "$RESULTS_DIR/candidate-runtime-mutation-check.txt"
printf 'Frozen mutation:    %s\n' "$RESULTS_DIR/frozen-runtime-mutation-check.txt"
printf 'Verification:       %s\n' "$RESULTS_DIR/promoted-boundary-verification.json"
printf '\n'

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3B_PROMOTED_BOUNDARIES=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "CA_BOUNDARY_EQUIVALENCE=PASS"
echo "ZONEINFO_BOUNDARY_EQUIVALENCE=PASS"
echo "TZDATA_FALLBACK_EQUIVALENCE=PASS"
echo "CANDIDATE_RUNTIME_MUTATION_CHECK=PASS"
echo "FROZEN_RUNTIME_MUTATION_CHECK=PASS"
echo "STAGE3B_PROMOTED_BOUNDARIES=PASS"
