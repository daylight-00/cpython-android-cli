#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 2: derive exact archive ownership and structural namespace.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

COMPONENT_RESULTS="${COMPONENT_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase1-component-policy}"
PHASE1_FINAL_RESULTS="${PHASE1_FINAL_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase1-runtime-base-final-validation}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RUNTIME_PREFIX="${RUNTIME_PREFIX:-$WORK_ROOT/termux/stage3c-phase1-isolated-variants/runtime-base/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase2-archive-ownership-model}"

EXPECTED_COMPONENT_MANIFEST="${EXPECTED_COMPONENT_MANIFEST:-91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84}"
EXPECTED_CANONICAL_FINGERPRINT="${EXPECTED_CANONICAL_FINGERPRINT:-5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c}"
EXPECTED_RUNTIME_FINGERPRINT="${EXPECTED_RUNTIME_FINGERPRINT:-9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796}"

PYTHON="$CANONICAL_PREFIX/bin/python"
FINGERPRINT="$SCRIPT_DIR/../stage3c-product-role-inventory/fingerprint-product-tree.py"
ANALYZER="$SCRIPT_DIR/analyze-archive-ownership.py"
VERIFIER="$SCRIPT_DIR/verify-archive-ownership.py"
SAFETY_VERIFIER="$SCRIPT_DIR/verify-archive-ownership-safety.py"

[[ -x "$PYTHON" ]] || {
    echo "ERROR: canonical promoted Python is missing: $PYTHON" >&2
    exit 2
}
[[ -x "$RUNTIME_PREFIX/bin/python" ]] || {
    echo "ERROR: frozen runtime-base is missing: $RUNTIME_PREFIX/bin/python" >&2
    exit 2
}

for file in \
    "$COMPONENT_RESULTS/component-inventory.tsv" \
    "$COMPONENT_RESULTS/component-policy.json" \
    "$COMPONENT_RESULTS/component-policy-verification.json" \
    "$PHASE1_FINAL_RESULTS/verification.json" \
    "$FINGERPRINT" \
    "$ANALYZER" \
    "$VERIFIER" \
    "$SAFETY_VERIFIER"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required frozen evidence or tool is missing: $file" >&2
        exit 2
    }
done

rm -rf "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR/input"

cp -a "$COMPONENT_RESULTS/component-inventory.tsv" \
    "$RESULTS_DIR/input/component-inventory.tsv"
cp -a "$COMPONENT_RESULTS/component-policy.json" \
    "$RESULTS_DIR/input/component-policy.json"
cp -a "$COMPONENT_RESULTS/component-policy-verification.json" \
    "$RESULTS_DIR/input/component-policy-verification.json"
cp -a "$PHASE1_FINAL_RESULTS/verification.json" \
    "$RESULTS_DIR/input/phase1-final-verification.json"

printf 'Component inventory:      %s\n' "$COMPONENT_RESULTS/component-inventory.tsv"
printf 'Component manifest:       %s\n' "$EXPECTED_COMPONENT_MANIFEST"
printf 'Canonical prefix:         %s\n' "$CANONICAL_PREFIX"
printf 'Runtime-base prefix:      %s\n' "$RUNTIME_PREFIX"
printf 'Results:                  %s\n\n' "$RESULTS_DIR"

fingerprint_tree() {
    local root="$1"
    local output="$2"
    local expected_count="$3"
    "$PYTHON" -I -B -S \
        "$FINGERPRINT" \
        --runtime-prefix "$root" \
        --output "$output" \
        --expected-entry-count "$expected_count"
}

echo "== Frozen inputs before ownership analysis =="
fingerprint_tree "$CANONICAL_PREFIX" "$RESULTS_DIR/canonical-before.json" 3155
fingerprint_tree "$RUNTIME_PREFIX" "$RESULTS_DIR/runtime-before.json" 714

set +e
"$PYTHON" -I -B -S \
    "$ANALYZER" \
    --component-inventory "$RESULTS_DIR/input/component-inventory.tsv" \
    --component-policy "$RESULTS_DIR/input/component-policy.json" \
    --component-verification "$RESULTS_DIR/input/component-policy-verification.json" \
    --phase1-final-verification "$RESULTS_DIR/input/phase1-final-verification.json" \
    --canonical-fingerprint "$RESULTS_DIR/canonical-before.json" \
    --runtime-fingerprint "$RESULTS_DIR/runtime-before.json" \
    --output-dir "$RESULTS_DIR" \
    --expected-component-manifest "$EXPECTED_COMPONENT_MANIFEST" \
    --expected-canonical-fingerprint "$EXPECTED_CANONICAL_FINGERPRINT" \
    --expected-runtime-fingerprint "$EXPECTED_RUNTIME_FINGERPRINT" \
    --require-pass \
    > "$RESULTS_DIR/analyzer.log" 2>&1
analyzer_rc=$?
set -e
cat "$RESULTS_DIR/analyzer.log"

echo
echo "== Frozen inputs after ownership analysis =="
fingerprint_tree "$CANONICAL_PREFIX" "$RESULTS_DIR/canonical-after.json" 3155
fingerprint_tree "$RUNTIME_PREFIX" "$RESULTS_DIR/runtime-after.json" 714

set +e
"$PYTHON" -I -B -S - \
    "$RESULTS_DIR/canonical-before.json" \
    "$RESULTS_DIR/canonical-after.json" \
    "$RESULTS_DIR/runtime-before.json" \
    "$RESULTS_DIR/runtime-after.json" \
    "$RESULTS_DIR/source-mutation-check.txt" <<'PY'
import json
import sys
from pathlib import Path

canonical_before = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
canonical_after = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
runtime_before = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
runtime_after = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
canonical_pass = (
    canonical_before.get("pass") is True
    and canonical_after.get("pass") is True
    and canonical_before.get("entry_count") == canonical_after.get("entry_count") == 3155
    and canonical_before.get("fingerprint") == canonical_after.get("fingerprint")
)
runtime_pass = (
    runtime_before.get("pass") is True
    and runtime_after.get("pass") is True
    and runtime_before.get("entry_count") == runtime_after.get("entry_count") == 714
    and runtime_before.get("fingerprint") == runtime_after.get("fingerprint")
)
passed = canonical_pass and runtime_pass
text = "\n".join(
    (
        f"canonical_prefix={canonical_before.get('root')}",
        f"canonical_before={canonical_before.get('fingerprint')}",
        f"canonical_after={canonical_after.get('fingerprint')}",
        f"canonical_entry_count={canonical_after.get('entry_count')}",
        f"canonical_pass={'true' if canonical_pass else 'false'}",
        f"runtime_prefix={runtime_before.get('root')}",
        f"runtime_before={runtime_before.get('fingerprint')}",
        f"runtime_after={runtime_after.get('fingerprint')}",
        f"runtime_entry_count={runtime_after.get('entry_count')}",
        f"runtime_pass={'true' if runtime_pass else 'false'}",
        f"pass={'true' if passed else 'false'}",
        "",
    )
)
Path(sys.argv[5]).write_text(text, encoding="utf-8")
print(text, end="")
raise SystemExit(0 if passed else 26)
PY
mutation_rc=$?
set -e

set +e
"$PYTHON" -I -B -S \
    "$VERIFIER" \
    --component-inventory "$RESULTS_DIR/input/component-inventory.tsv" \
    --output-dir "$RESULTS_DIR" \
    --canonical-before "$RESULTS_DIR/canonical-before.json" \
    --canonical-after "$RESULTS_DIR/canonical-after.json" \
    --runtime-before "$RESULTS_DIR/runtime-before.json" \
    --runtime-after "$RESULTS_DIR/runtime-after.json" \
    --expected-component-manifest "$EXPECTED_COMPONENT_MANIFEST" \
    --expected-canonical-fingerprint "$EXPECTED_CANONICAL_FINGERPRINT" \
    --expected-runtime-fingerprint "$EXPECTED_RUNTIME_FINGERPRINT" \
    --output "$RESULTS_DIR/verification.json" \
    > "$RESULTS_DIR/verifier.log" 2>&1
verifier_rc=$?
set -e
cat "$RESULTS_DIR/verifier.log"

set +e
"$PYTHON" -I -B -S \
    "$SAFETY_VERIFIER" \
    --component-inventory "$RESULTS_DIR/input/component-inventory.tsv" \
    --owned-paths "$RESULTS_DIR/artifact-owned-paths.tsv" \
    --excluded-paths "$RESULTS_DIR/excluded-paths.txt" \
    --output "$RESULTS_DIR/safety-verification.json" \
    > "$RESULTS_DIR/safety-verifier.log" 2>&1
safety_rc=$?
set -e
cat "$RESULTS_DIR/safety-verifier.log"

"$PYTHON" -I -B -S - \
    "$RESULTS_DIR/workflow-status.json" \
    "$analyzer_rc" "$mutation_rc" "$verifier_rc" "$safety_rc" <<'PY'
import json
import sys
from pathlib import Path

returncodes = {
    "ownership_analysis": int(sys.argv[2]),
    "source_mutation": int(sys.argv[3]),
    "independent_verification": int(sys.argv[4]),
    "safety_verification": int(sys.argv[5]),
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

printf '\nOwnership model:       %s\n' "$RESULTS_DIR/ownership-model.json"
printf 'Owned paths:          %s\n' "$RESULTS_DIR/artifact-owned-paths.tsv"
printf 'Structural parents:   %s\n' "$RESULTS_DIR/artifact-structural-directories.tsv"
printf 'Shared namespace:     %s\n' "$RESULTS_DIR/shared-namespace-directories.tsv"
printf 'Artifact summary:     %s\n' "$RESULTS_DIR/artifact-ownership-summary.tsv"
printf 'Verification:         %s\n' "$RESULTS_DIR/verification.json"
printf 'Safety verification:  %s\n' "$RESULTS_DIR/safety-verification.json"
printf 'Mutation check:       %s\n\n' "$RESULTS_DIR/source-mutation-check.txt"

final_rc=0
for rc in "$analyzer_rc" "$mutation_rc" "$verifier_rc" "$safety_rc"; do
    if [[ $rc -ne 0 ]]; then
        final_rc=$rc
        break
    fi
done

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE2_ARCHIVE_OWNERSHIP_MODEL=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "ARCHIVE_OWNERSHIP_ACCEPTED_INPUTS=PASS"
echo "ARCHIVE_EXACT_OWNED_PATH_OVERLAP=0 PASS"
echo "ARCHIVE_STRUCTURAL_NAMESPACE_MODEL=PASS"
echo "ARCHIVE_OWNERSHIP_SAFETY_VERIFIER=9/9 PASS"
echo "ARCHIVE_SELECTED_SYMLINK_POLICY=PASS"
echo "ARCHIVE_LICENSE_OWNERSHIP=PASS"
echo "ARCHIVE_OWNERSHIP_SOURCE_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE2_ARCHIVE_OWNERSHIP_MODEL=PASS"
