#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 1: decompose the accepted role inventory without touching the product.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RUNTIME_PREFIX="${RUNTIME_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase1-role-inventory}"
EXPECTED_MANIFEST_SHA256="${EXPECTED_MANIFEST_SHA256:-092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f}"
EXPECTED_ENTRY_COUNT="${EXPECTED_ENTRY_COUNT:-3155}"
EXPECTED_ELF_COUNT="${EXPECTED_ELF_COUNT:-81}"
EXPECTED_SYMLINK_COUNT="${EXPECTED_SYMLINK_COUNT:-5}"
ANALYZER="$SCRIPT_DIR/analyze-role-inventory.py"
PYTHON="$RUNTIME_PREFIX/bin/python"

[[ -x "$PYTHON" ]] || {
    echo "ERROR: frozen promoted Python is missing: $PYTHON" >&2
    exit 2
}
[[ -f "$ANALYZER" ]] || {
    echo "ERROR: analyzer is missing: $ANALYZER" >&2
    exit 2
}
for file in \
    "$RESULTS_DIR/product-role-inventory.tsv" \
    "$RESULTS_DIR/role-summary.json" \
    "$RESULTS_DIR/verification.json"; do
    [[ -f "$file" ]] || {
        echo "ERROR: accepted role-inventory evidence is missing: $file" >&2
        exit 2
    }
done

"$PYTHON" -I -B -S \
    "$ANALYZER" \
    --results-dir "$RESULTS_DIR" \
    --expected-manifest-sha256 "$EXPECTED_MANIFEST_SHA256" \
    --expected-entry-count "$EXPECTED_ENTRY_COUNT" \
    --expected-elf-count "$EXPECTED_ELF_COUNT" \
    --expected-symlink-count "$EXPECTED_SYMLINK_COUNT" \
    | tee "$RESULTS_DIR/role-review.log"

printf '\nRole overview:       %s\n' "$RESULTS_DIR/role-overview.tsv"
printf 'Role by rule:        %s\n' "$RESULTS_DIR/role-by-rule.tsv"
printf 'Role by type:        %s\n' "$RESULTS_DIR/role-by-type.tsv"
printf 'Role by top level:   %s\n' "$RESULTS_DIR/role-by-top-level.tsv"
printf 'Python subtrees:     %s\n' "$RESULTS_DIR/python-subtree-summary.tsv"
printf 'Optional components: %s\n' "$RESULTS_DIR/optional-component-summary.tsv"
printf 'Optional roots:      %s\n' "$RESULTS_DIR/optional-root-summary.tsv"
printf 'Development:         %s\n' "$RESULTS_DIR/development-surface-summary.tsv"
printf 'Runtime:             %s\n' "$RESULTS_DIR/runtime-surface-summary.tsv"
printf 'Boundary rows:       %s\n' "$RESULTS_DIR/selected-boundary-rows.tsv"
printf 'Largest files:       %s\n' "$RESULTS_DIR/largest-regular-files.tsv"
printf 'Review JSON:         %s\n\n' "$RESULTS_DIR/role-review.json"

echo "STAGE3C_PHASE1_ROLE_DECOMPOSITION=PASS"
