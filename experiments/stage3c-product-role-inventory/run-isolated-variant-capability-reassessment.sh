#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 1: targeted reassessment of the frozen __phello__ capability contract.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

SOURCE_PREFIX="${SOURCE_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
VARIANT_ROOT="${VARIANT_ROOT:-$WORK_ROOT/termux/stage3c-phase1-isolated-variants}"
ORIGINAL_RESULTS="${ORIGINAL_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase1-isolated-variants}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase1-isolated-variant-capability-reassessment}"
EXPECTED_SOURCE_FINGERPRINT="${EXPECTED_SOURCE_FINGERPRINT:-5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c}"
EXPECTED_COMPONENT_MANIFEST="${EXPECTED_COMPONENT_MANIFEST:-91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84}"
TERMUX_PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
SOURCE_PYTHON="$SOURCE_PREFIX/bin/python"
FINGERPRINT="$SCRIPT_DIR/fingerprint-product-tree.py"
CAPABILITY_PROBE="$SCRIPT_DIR/probe-materialized-variant.py"
VERIFY="$SCRIPT_DIR/verify-isolated-variant-capability-reassessment.py"

VARIANTS=(
    runtime-base
    runtime-development
    runtime-test
    runtime-supported
)
COUNTS=(714 1168 2502 2956)

[[ -x "$SOURCE_PYTHON" ]] || {
    echo "ERROR: canonical promoted Python is missing: $SOURCE_PYTHON" >&2
    exit 2
}

for file in \
    "$FINGERPRINT" \
    "$CAPABILITY_PROBE" \
    "$VERIFY" \
    "$ORIGINAL_RESULTS/verification.json" \
    "$ORIGINAL_RESULTS/workflow-status.json" \
    "$ORIGINAL_RESULTS/materialization.json" \
    "$ORIGINAL_RESULTS/variant-fidelity-before.json" \
    "$ORIGINAL_RESULTS/variant-fidelity-after.json" \
    "$ORIGINAL_RESULTS/source-before.json" \
    "$ORIGINAL_RESULTS/source-after.json"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required first-run evidence or tool is missing: $file" >&2
        exit 2
    }
done

for variant in "${VARIANTS[@]}"; do
    [[ -x "$VARIANT_ROOT/$variant/prefix/bin/python" ]] || {
        echo "ERROR: isolated variant is missing: $variant" >&2
        exit 2
    }
    for phase in before after; do
        [[ -f "$ORIGINAL_RESULTS/fingerprints/$variant-$phase.json" ]] || {
            echo "ERROR: original fingerprint evidence is missing: $variant-$phase" >&2
            exit 2
        }
    done
    [[ -f "$ORIGINAL_RESULTS/capabilities/$variant.json" ]] || {
        echo "ERROR: original capability evidence is missing: $variant" >&2
        exit 2
    }
done

rm -rf "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR/capabilities" "$RESULTS_DIR/fingerprints"

printf 'Canonical source:          %s\n' "$SOURCE_PREFIX"
printf 'Isolated variants:         %s\n' "$VARIANT_ROOT"
printf 'Original first-run result: %s\n' "$ORIGINAL_RESULTS"
printf 'Reassessment result:       %s\n\n' "$RESULTS_DIR"

run_clean() {
    local prefix="$1"
    shift
    env \
        -u PYTHONHOME \
        -u PYTHONPATH \
        -u CPYTHON_HOME \
        -u LD_LIBRARY_PATH \
        -u SSL_CERT_FILE \
        -u SSL_CERT_DIR \
        -u PYTHONTZPATH \
        -u VIRTUAL_ENV \
        -u UV_PYTHON \
        PREFIX="$TERMUX_PREFIX" \
        HOME="$HOME" \
        PATH="$TERMUX_PREFIX/bin:/system/bin" \
        TMPDIR="$TERMUX_PREFIX/tmp" \
        TERM="${TERM:-xterm-256color}" \
        PYTHONDONTWRITEBYTECODE=1 \
        "$prefix/bin/python" "$@"
}

fingerprint_tree() {
    local root="$1"
    local output="$2"
    local expected_count="$3"
    "$SOURCE_PYTHON" -I -B -S \
        "$FINGERPRINT" \
        --runtime-prefix "$root" \
        --output "$output" \
        --expected-entry-count "$expected_count"
}

echo "== Current source and variants before reassessment =="
fingerprint_tree "$SOURCE_PREFIX" "$RESULTS_DIR/source-before.json" 3155
for index in "${!VARIANTS[@]}"; do
    variant="${VARIANTS[$index]}"
    count="${COUNTS[$index]}"
    fingerprint_tree \
        "$VARIANT_ROOT/$variant/prefix" \
        "$RESULTS_DIR/fingerprints/$variant-before.json" \
        "$count"
done

capability_rc=0
for variant in "${VARIANTS[@]}"; do
    echo
    echo "== Corrected capability probe: $variant =="
    set +e
    run_clean "$VARIANT_ROOT/$variant/prefix" \
        -I -B -S \
        "$CAPABILITY_PROBE" \
        --variant "$variant" \
        --prefix "$VARIANT_ROOT/$variant/prefix" \
        --output "$RESULTS_DIR/capabilities/$variant.json" \
        > "$RESULTS_DIR/capabilities/$variant.log" 2>&1
    rc=$?
    set -e
    cat "$RESULTS_DIR/capabilities/$variant.log"
    if [[ $rc -ne 0 && $capability_rc -eq 0 ]]; then
        capability_rc=$rc
    fi
done

echo
echo "== Current source and variants after reassessment =="
set +e
fingerprint_tree "$SOURCE_PREFIX" "$RESULTS_DIR/source-after.json" 3155
source_after_rc=$?
variant_fingerprint_rc=0
for index in "${!VARIANTS[@]}"; do
    variant="${VARIANTS[$index]}"
    count="${COUNTS[$index]}"
    fingerprint_tree \
        "$VARIANT_ROOT/$variant/prefix" \
        "$RESULTS_DIR/fingerprints/$variant-after.json" \
        "$count"
    rc=$?
    if [[ $rc -ne 0 && $variant_fingerprint_rc -eq 0 ]]; then
        variant_fingerprint_rc=$rc
    fi
done
set -e

"$SOURCE_PYTHON" -I -B -S - \
    "$RESULTS_DIR/reassessment-status.json" \
    "$capability_rc" \
    "$source_after_rc" \
    "$variant_fingerprint_rc" <<'PY'
import json
import sys
from pathlib import Path

returncodes = {
    "corrected_capabilities": int(sys.argv[2]),
    "source_fingerprint_after": int(sys.argv[3]),
    "variant_fingerprints_after": int(sys.argv[4]),
}
result = {
    "schema_version": 1,
    "pass": all(value == 0 for value in returncodes.values()),
    "returncodes": returncodes,
}
Path(sys.argv[1]).write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(result, indent=2, sort_keys=True))
PY

set +e
"$SOURCE_PYTHON" -I -B -S \
    "$VERIFY" \
    --original-results "$ORIGINAL_RESULTS" \
    --reassessment-results "$RESULTS_DIR" \
    --output "$RESULTS_DIR/verification.json" \
    --expected-source-fingerprint "$EXPECTED_SOURCE_FINGERPRINT" \
    --expected-component-manifest "$EXPECTED_COMPONENT_MANIFEST" \
    > "$RESULTS_DIR/verifier.log" 2>&1
verify_rc=$?
set -e
cat "$RESULTS_DIR/verifier.log"

printf '\nOriginal evidence:    %s\n' "$ORIGINAL_RESULTS/verification.json"
printf 'Corrected capabilities: %s\n' "$RESULTS_DIR/capabilities"
printf 'Reassessment status:  %s\n' "$RESULTS_DIR/reassessment-status.json"
printf 'Verification:         %s\n\n' "$RESULTS_DIR/verification.json"

if [[ $verify_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE1_PHELLO_REASSESSMENT=FAIL rc=$verify_rc"
    exit "$verify_rc"
fi

echo "FIRST_RUN_FAILURE_PRESERVED=PASS"
echo "PHELLO_FROZEN_CONTRACT_CORRECTED=PASS"
echo "ISOLATED_VARIANT_CAPABILITIES_REASSESSED=PASS"
echo "ISOLATED_VARIANT_REASSESSMENT_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE1_PHELLO_REASSESSMENT=PASS"
