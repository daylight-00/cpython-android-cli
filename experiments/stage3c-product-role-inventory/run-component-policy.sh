#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 1: assign every accepted product path to one candidate component.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RUNTIME_PREFIX="${RUNTIME_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
ROLE_RESULTS="${ROLE_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase1-role-inventory}"
SEMANTIC_RESULTS="${SEMANTIC_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase1-role-semantics}"
OUTPUT_DIR="${OUTPUT_DIR:-$RESULTS_ROOT/termux/stage3c-phase1-component-policy}"
EXPECTED_SOURCE_MANIFEST="${EXPECTED_SOURCE_MANIFEST:-092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f}"
EXPECTED_ENTRY_COUNT="${EXPECTED_ENTRY_COUNT:-3155}"
EXPECTED_ELF_COUNT="${EXPECTED_ELF_COUNT:-81}"
EXPECTED_SYMLINK_COUNT="${EXPECTED_SYMLINK_COUNT:-5}"
FINGERPRINT="$SCRIPT_DIR/fingerprint-product-tree.py"
INPUT_VERIFIER="$SCRIPT_DIR/verify-component-policy-inputs.py"
SELECTOR="$SCRIPT_DIR/select-product-components.py"
VERIFIER="$SCRIPT_DIR/verify-product-components.py"
PYTHON="$RUNTIME_PREFIX/bin/python"

[[ -x "$PYTHON" ]] || {
    echo "ERROR: frozen promoted Python is missing: $PYTHON" >&2
    exit 2
}
for file in \
    "$ROLE_RESULTS/product-role-inventory.tsv" \
    "$ROLE_RESULTS/role-summary.json" \
    "$ROLE_RESULTS/verification.json" \
    "$SEMANTIC_RESULTS/semantic-probes.json" \
    "$SEMANTIC_RESULTS/verification.json" \
    "$FINGERPRINT" \
    "$INPUT_VERIFIER" \
    "$SELECTOR" \
    "$VERIFIER"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required accepted evidence or tool is missing: $file" >&2
        exit 2
    }
done

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

printf 'Runtime prefix:       %s\n' "$RUNTIME_PREFIX"
printf 'Role evidence:        %s\n' "$ROLE_RESULTS"
printf 'Semantic evidence:    %s\n' "$SEMANTIC_RESULTS"
printf 'Expected manifest:    %s\n' "$EXPECTED_SOURCE_MANIFEST"
printf 'Expected entries:     %s\n' "$EXPECTED_ENTRY_COUNT"
printf 'Results:              %s\n\n' "$OUTPUT_DIR"

set +e
"$PYTHON" -I -B -S \
    "$FINGERPRINT" \
    --runtime-prefix "$RUNTIME_PREFIX" \
    --output "$OUTPUT_DIR/source-before.json" \
    --expected-entry-count "$EXPECTED_ENTRY_COUNT" \
    > "$OUTPUT_DIR/source-before.log" 2>&1
before_rc=$?
set -e
cat "$OUTPUT_DIR/source-before.log"

set +e
"$PYTHON" -I -B -S \
    "$INPUT_VERIFIER" \
    --inventory "$ROLE_RESULTS/product-role-inventory.tsv" \
    --role-summary "$ROLE_RESULTS/role-summary.json" \
    --role-verification "$ROLE_RESULTS/verification.json" \
    --semantic-probes "$SEMANTIC_RESULTS/semantic-probes.json" \
    --semantic-verification "$SEMANTIC_RESULTS/verification.json" \
    --tree-fingerprint "$OUTPUT_DIR/source-before.json" \
    --output "$OUTPUT_DIR/input-verification.json" \
    --expected-source-manifest "$EXPECTED_SOURCE_MANIFEST" \
    --expected-entry-count "$EXPECTED_ENTRY_COUNT" \
    > "$OUTPUT_DIR/input-verifier.log" 2>&1
input_rc=$?
set -e
cat "$OUTPUT_DIR/input-verifier.log"

set +e
"$PYTHON" -I -B -S \
    "$SELECTOR" \
    --inventory "$ROLE_RESULTS/product-role-inventory.tsv" \
    --role-summary "$ROLE_RESULTS/role-summary.json" \
    --semantic-probes "$SEMANTIC_RESULTS/semantic-probes.json" \
    --semantic-verification "$SEMANTIC_RESULTS/verification.json" \
    --output-dir "$OUTPUT_DIR" \
    --expected-source-manifest "$EXPECTED_SOURCE_MANIFEST" \
    --expected-entry-count "$EXPECTED_ENTRY_COUNT" \
    --require-pass \
    > "$OUTPUT_DIR/selector.log" 2>&1
selector_rc=$?
set -e
cat "$OUTPUT_DIR/selector.log"

set +e
"$PYTHON" -I -B -S \
    "$VERIFIER" \
    --inventory "$ROLE_RESULTS/product-role-inventory.tsv" \
    --output-dir "$OUTPUT_DIR" \
    --semantic-verification "$SEMANTIC_RESULTS/verification.json" \
    --expected-entry-count "$EXPECTED_ENTRY_COUNT" \
    --expected-elf-count "$EXPECTED_ELF_COUNT" \
    --expected-symlink-count "$EXPECTED_SYMLINK_COUNT" \
    > "$OUTPUT_DIR/verifier.log" 2>&1
verifier_rc=$?
set -e
cat "$OUTPUT_DIR/verifier.log"

set +e
"$PYTHON" -I -B -S \
    "$FINGERPRINT" \
    --runtime-prefix "$RUNTIME_PREFIX" \
    --output "$OUTPUT_DIR/source-after.json" \
    --expected-entry-count "$EXPECTED_ENTRY_COUNT" \
    > "$OUTPUT_DIR/source-after.log" 2>&1
after_rc=$?
set -e
cat "$OUTPUT_DIR/source-after.log"

set +e
"$PYTHON" -I -B -S - \
    "$OUTPUT_DIR/source-before.json" \
    "$OUTPUT_DIR/source-after.json" \
    "$OUTPUT_DIR/source-mutation-check.txt" <<'PY'
import json
import sys
from pathlib import Path

before = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
after = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
passed = (
    before.get("pass") is True
    and after.get("pass") is True
    and before.get("fingerprint") == after.get("fingerprint")
    and before.get("entry_count") == after.get("entry_count")
)
text = "\n".join(
    (
        f"runtime_prefix={before.get('root')}",
        f"before={before.get('fingerprint')}",
        f"after={after.get('fingerprint')}",
        f"before_entry_count={before.get('entry_count')}",
        f"after_entry_count={after.get('entry_count')}",
        f"pass={'true' if passed else 'false'}",
        "",
    )
)
Path(sys.argv[3]).write_text(text, encoding="utf-8")
print(text, end="")
raise SystemExit(0 if passed else 13)
PY
mutation_rc=$?
set -e

printf '\nInput verification:  %s\n' "$OUTPUT_DIR/input-verification.json"
printf 'Component inventory: %s\n' "$OUTPUT_DIR/component-inventory.tsv"
printf 'Component summary:   %s\n' "$OUTPUT_DIR/component-summary.tsv"
printf 'Artifact policy:     %s\n' "$OUTPUT_DIR/artifact-composition.json"
printf 'Policy result:       %s\n' "$OUTPUT_DIR/component-policy.json"
printf 'Verification:        %s\n' "$OUTPUT_DIR/component-policy-verification.json"
printf 'Source mutation:     %s\n\n' "$OUTPUT_DIR/source-mutation-check.txt"

final_rc=0
for rc in "$before_rc" "$input_rc" "$selector_rc" "$verifier_rc" "$after_rc" "$mutation_rc"; do
    if [[ $rc -ne 0 ]]; then
        final_rc=$rc
        break
    fi
done

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE1_COMPONENT_POLICY_WORKFLOW=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "COMPONENT_POLICY_INPUT_CONTRACT=PASS"
echo "COMPONENT_POLICY_COMPLETE_PARTITION=PASS"
echo "COMPONENT_POLICY_SOURCE_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE1_COMPONENT_POLICY_WORKFLOW=PASS"
