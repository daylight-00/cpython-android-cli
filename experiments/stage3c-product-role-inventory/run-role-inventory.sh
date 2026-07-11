#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 1: read-only semantic role inventory for the frozen promoted runtime.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RUNTIME_PREFIX="${RUNTIME_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
OUTPUT_DIR="${OUTPUT_DIR:-$RESULTS_ROOT/termux/stage3c-phase1-role-inventory}"
EXPECTED_ENTRY_COUNT="${EXPECTED_ENTRY_COUNT:-3155}"
EXPECTED_ELF_COUNT="${EXPECTED_ELF_COUNT:-81}"
EXPECTED_SYMLINK_COUNT="${EXPECTED_SYMLINK_COUNT:-5}"
CLASSIFIER="$SCRIPT_DIR/classify-promoted-product.py"
VERIFIER="$SCRIPT_DIR/verify-promoted-product-roles.py"
PYTHON="$RUNTIME_PREFIX/bin/python"

[[ -x "$PYTHON" ]] || {
    echo "ERROR: frozen promoted runtime is missing: $PYTHON" >&2
    exit 2
}
[[ -f "$CLASSIFIER" ]] || {
    echo "ERROR: classifier is missing: $CLASSIFIER" >&2
    exit 2
}
[[ -f "$VERIFIER" ]] || {
    echo "ERROR: verifier is missing: $VERIFIER" >&2
    exit 2
}

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

printf 'Runtime prefix:       %s\n' "$RUNTIME_PREFIX"
printf 'Expected entry count: %s\n' "$EXPECTED_ENTRY_COUNT"
printf 'Expected ELF count:   %s\n' "$EXPECTED_ELF_COUNT"
printf 'Expected symlinks:    %s\n' "$EXPECTED_SYMLINK_COUNT"
printf 'Results:              %s\n\n' "$OUTPUT_DIR"

set +e
"$PYTHON" -I -B -S \
    "$CLASSIFIER" \
    --runtime-prefix "$RUNTIME_PREFIX" \
    --output-dir "$OUTPUT_DIR" \
    --expected-entry-count "$EXPECTED_ENTRY_COUNT" \
    --require-pass \
    > "$OUTPUT_DIR/classifier.log" 2>&1
classifier_rc=$?
set -e
cat "$OUTPUT_DIR/classifier.log"

set +e
"$PYTHON" -I -B -S \
    "$VERIFIER" \
    --results-dir "$OUTPUT_DIR" \
    --runtime-prefix "$RUNTIME_PREFIX" \
    --expected-entry-count "$EXPECTED_ENTRY_COUNT" \
    --expected-elf-count "$EXPECTED_ELF_COUNT" \
    --expected-symlink-count "$EXPECTED_SYMLINK_COUNT" \
    > "$OUTPUT_DIR/verifier.log" 2>&1
verifier_rc=$?
set -e
cat "$OUTPUT_DIR/verifier.log"

printf '\nInventory:         %s\n' "$OUTPUT_DIR/product-role-inventory.tsv"
printf 'Unknown paths:     %s\n' "$OUTPUT_DIR/unknown.tsv"
printf 'Mixed directories: %s\n' "$OUTPUT_DIR/mixed-directories.tsv"
printf 'Rules:             %s\n' "$OUTPUT_DIR/rules.tsv"
printf 'Summary:           %s\n' "$OUTPUT_DIR/role-summary.json"
printf 'Mutation check:    %s\n' "$OUTPUT_DIR/mutation-check.txt"
printf 'Verification:      %s\n\n' "$OUTPUT_DIR/verification.json"

final_rc=0
if [[ $classifier_rc -ne 0 ]]; then
    final_rc=$classifier_rc
elif [[ $verifier_rc -ne 0 ]]; then
    final_rc=$verifier_rc
fi

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE1_ROLE_INVENTORY=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "PRODUCT_ROLE_UNKNOWN_ZERO=PASS"
echo "PRODUCT_ROLE_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE1_ROLE_INVENTORY=PASS"
