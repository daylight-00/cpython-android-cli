#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 1: observe semantic consumers for candidate archive roles.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RUNTIME_PREFIX="${RUNTIME_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase1-role-semantics}"
EXPECTED_ENTRY_COUNT="${EXPECTED_ENTRY_COUNT:-3155}"
PROBE="$SCRIPT_DIR/probe-role-semantics.py"
VERIFIER="$SCRIPT_DIR/verify-role-semantics.py"
PYTHON="$RUNTIME_PREFIX/bin/python"

[[ -x "$PYTHON" ]] || {
    echo "ERROR: frozen promoted Python is missing: $PYTHON" >&2
    exit 2
}
[[ -f "$PROBE" ]] || {
    echo "ERROR: semantic probe is missing: $PROBE" >&2
    exit 2
}
[[ -f "$VERIFIER" ]] || {
    echo "ERROR: semantic verifier is missing: $VERIFIER" >&2
    exit 2
}

rm -rf "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR"

printf 'Runtime prefix:       %s\n' "$RUNTIME_PREFIX"
printf 'Expected entry count: %s\n' "$EXPECTED_ENTRY_COUNT"
printf 'Results:              %s\n\n' "$RESULTS_DIR"

set +e
"$PYTHON" -I -B -S \
    "$PROBE" \
    --runtime-prefix "$RUNTIME_PREFIX" \
    --output "$RESULTS_DIR/semantic-probes.json" \
    --expected-entry-count "$EXPECTED_ENTRY_COUNT" \
    > "$RESULTS_DIR/probe.log" 2>&1
probe_rc=$?
set -e
cat "$RESULTS_DIR/probe.log"

set +e
"$PYTHON" -I -B -S \
    "$VERIFIER" \
    --input "$RESULTS_DIR/semantic-probes.json" \
    --output "$RESULTS_DIR/verification.json" \
    --runtime-prefix "$RUNTIME_PREFIX" \
    --expected-entry-count "$EXPECTED_ENTRY_COUNT" \
    > "$RESULTS_DIR/verifier.log" 2>&1
verifier_rc=$?
set -e
cat "$RESULTS_DIR/verifier.log"

printf '\nSemantic probes: %s\n' "$RESULTS_DIR/semantic-probes.json"
printf 'Verification:    %s\n\n' "$RESULTS_DIR/verification.json"

final_rc=0
if [[ $probe_rc -ne 0 ]]; then
    final_rc=$probe_rc
elif [[ $verifier_rc -ne 0 ]]; then
    final_rc=$verifier_rc
fi

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE1_ROLE_SEMANTICS=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "ROLE_SEMANTICS_SOURCE_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE1_ROLE_SEMANTICS=PASS"
