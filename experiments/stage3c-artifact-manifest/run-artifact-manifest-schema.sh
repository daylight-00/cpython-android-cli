#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 2: generate and independently verify schema-v1 artifact manifests.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

OWNERSHIP_RESULTS="${OWNERSHIP_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase2-archive-ownership-model}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RUNTIME_PREFIX="${RUNTIME_PREFIX:-$WORK_ROOT/termux/stage3c-phase1-isolated-variants/runtime-base/prefix}"
PRODUCT_LOCK="${PRODUCT_LOCK:-$PROJECT_ROOT/config/products/cpython-3.14.6-aarch64-linux-android.lock.json}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase2-artifact-manifest-schema}"

EXPECTED_COMPONENT_MANIFEST="${EXPECTED_COMPONENT_MANIFEST:-91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84}"
EXPECTED_CANONICAL_FINGERPRINT="${EXPECTED_CANONICAL_FINGERPRINT:-5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c}"
EXPECTED_RUNTIME_FINGERPRINT="${EXPECTED_RUNTIME_FINGERPRINT:-9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796}"
EXPECTED_OWNED_MANIFEST="${EXPECTED_OWNED_MANIFEST:-ab2c7374d2a70c7eb48db72dbfd1de86b708167efef151519f25b6a5a65023ea}"
EXPECTED_STRUCTURAL_MANIFEST="${EXPECTED_STRUCTURAL_MANIFEST:-9481da6ffa6bf0f54a10b631a31b81252580e2323bd1c8a92c6899aff26b78b3}"
EXPECTED_SHARED_MANIFEST="${EXPECTED_SHARED_MANIFEST:-cc40599da21dbef18e48b940b77143e44479e821b3273946843a89340052956e}"

PYTHON="$CANONICAL_PREFIX/bin/python"
FINGERPRINT="$SCRIPT_DIR/../stage3c-product-role-inventory/fingerprint-product-tree.py"
LOCAL_SCRIPT_RUNNER="$SCRIPT_DIR/run-isolated-local-script.py"
GENERATOR="$SCRIPT_DIR/generate-artifact-manifests.py"
VERIFIER="$SCRIPT_DIR/verify-artifact-manifests.py"
OWNERSHIP_INPUT="$RESULTS_DIR/input/ownership"

[[ -x "$PYTHON" ]] || {
    echo "ERROR: canonical promoted Python is missing: $PYTHON" >&2
    exit 2
}
[[ -x "$RUNTIME_PREFIX/bin/python" ]] || {
    echo "ERROR: frozen runtime-base is missing: $RUNTIME_PREFIX/bin/python" >&2
    exit 2
}

for file in \
    "$PRODUCT_LOCK" \
    "$OWNERSHIP_RESULTS/ownership-model.json" \
    "$OWNERSHIP_RESULTS/verification.json" \
    "$OWNERSHIP_RESULTS/safety-verification.json" \
    "$OWNERSHIP_RESULTS/workflow-status.json" \
    "$OWNERSHIP_RESULTS/artifact-owned-paths.tsv" \
    "$OWNERSHIP_RESULTS/artifact-structural-directories.tsv" \
    "$OWNERSHIP_RESULTS/shared-namespace-directories.tsv" \
    "$OWNERSHIP_RESULTS/artifact-ownership-summary.tsv" \
    "$OWNERSHIP_RESULTS/excluded-paths.txt" \
    "$OWNERSHIP_RESULTS/canonical-before.json" \
    "$OWNERSHIP_RESULTS/canonical-after.json" \
    "$OWNERSHIP_RESULTS/runtime-before.json" \
    "$OWNERSHIP_RESULTS/runtime-after.json" \
    "$OWNERSHIP_RESULTS/input/component-inventory.tsv" \
    "$OWNERSHIP_RESULTS/input/phase1-final-verification.json" \
    "$FINGERPRINT" \
    "$LOCAL_SCRIPT_RUNNER" \
    "$GENERATOR" \
    "$VERIFIER" \
    "$SCRIPT_DIR/artifact_manifest_contract.py"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required accepted evidence or tool is missing: $file" >&2
        exit 2
    }
done

rm -rf "$RESULTS_DIR"
mkdir -p "$OWNERSHIP_INPUT/input"

for name in \
    ownership-model.json \
    verification.json \
    safety-verification.json \
    workflow-status.json \
    artifact-owned-paths.tsv \
    artifact-structural-directories.tsv \
    shared-namespace-directories.tsv \
    artifact-ownership-summary.tsv \
    excluded-paths.txt \
    source-mutation-check.txt \
    canonical-before.json \
    canonical-after.json \
    runtime-before.json \
    runtime-after.json; do
    [[ ! -f "$OWNERSHIP_RESULTS/$name" ]] || \
        cp -a "$OWNERSHIP_RESULTS/$name" "$OWNERSHIP_INPUT/$name"
done
cp -a "$OWNERSHIP_RESULTS/input/component-inventory.tsv" \
    "$OWNERSHIP_INPUT/input/component-inventory.tsv"
cp -a "$OWNERSHIP_RESULTS/input/phase1-final-verification.json" \
    "$OWNERSHIP_INPUT/input/phase1-final-verification.json"
cp -a "$PRODUCT_LOCK" "$RESULTS_DIR/input/product-lock.json"

# Provenance paths declared by the generated manifests.
cp -a "$OWNERSHIP_RESULTS/ownership-model.json" \
    "$RESULTS_DIR/input/ownership-model.json"
cp -a "$OWNERSHIP_RESULTS/verification.json" \
    "$RESULTS_DIR/input/ownership-verification.json"
cp -a "$OWNERSHIP_RESULTS/safety-verification.json" \
    "$RESULTS_DIR/input/ownership-safety-verification.json"
cp -a "$OWNERSHIP_RESULTS/input/phase1-final-verification.json" \
    "$RESULTS_DIR/input/phase1-final-verification.json"

printf 'Ownership results:       %s\n' "$OWNERSHIP_RESULTS"
printf 'Product lock:            %s\n' "$PRODUCT_LOCK"
printf 'Canonical prefix:        %s\n' "$CANONICAL_PREFIX"
printf 'Runtime-base prefix:     %s\n' "$RUNTIME_PREFIX"
printf 'Results:                 %s\n\n' "$RESULTS_DIR"

fingerprint_tree() {
    "$PYTHON" -I -B -S \
        "$FINGERPRINT" \
        --runtime-prefix "$1" \
        --output "$2" \
        --expected-entry-count "$3"
}

run_local_script() {
    "$PYTHON" -I -B -S "$LOCAL_SCRIPT_RUNNER" "$@"
}

write_mutation_check() {
    "$PYTHON" -I -B -S - \
        "$RESULTS_DIR/canonical-before.json" \
        "$RESULTS_DIR/canonical-after.json" \
        "$RESULTS_DIR/runtime-before.json" \
        "$RESULTS_DIR/runtime-after.json" \
        "$RESULTS_DIR/source-mutation-check.txt" <<'PY'
import json
import sys
from pathlib import Path

cb, ca, rb, ra = [
    json.loads(Path(path).read_text(encoding="utf-8"))
    for path in sys.argv[1:5]
]
canonical_pass = (
    cb.get("pass") is True
    and ca.get("pass") is True
    and cb.get("entry_count") == ca.get("entry_count") == 3155
    and cb.get("fingerprint") == ca.get("fingerprint")
)
runtime_pass = (
    rb.get("pass") is True
    and ra.get("pass") is True
    and rb.get("entry_count") == ra.get("entry_count") == 714
    and rb.get("fingerprint") == ra.get("fingerprint")
)
passed = canonical_pass and runtime_pass
text = "\n".join(
    (
        f"canonical_prefix={cb.get('root')}",
        f"canonical_before={cb.get('fingerprint')}",
        f"canonical_after={ca.get('fingerprint')}",
        f"canonical_entry_count={ca.get('entry_count')}",
        f"canonical_pass={'true' if canonical_pass else 'false'}",
        f"runtime_prefix={rb.get('root')}",
        f"runtime_before={rb.get('fingerprint')}",
        f"runtime_after={ra.get('fingerprint')}",
        f"runtime_entry_count={ra.get('entry_count')}",
        f"runtime_pass={'true' if runtime_pass else 'false'}",
        f"pass={'true' if passed else 'false'}",
        "",
    )
)
Path(sys.argv[5]).write_text(text, encoding="utf-8")
print(text, end="")
raise SystemExit(0 if passed else 30)
PY
}

write_blocked_verification() {
    "$PYTHON" -I -B -S - \
        "$RESULTS_DIR/verification.json" "$1" <<'PY'
import json
import sys
from pathlib import Path

output = Path(sys.argv[1])
generator_rc = int(sys.argv[2])
expected = [
    "generation.json",
    "manifest-index.json",
    "manifests/runtime-base.manifest.json",
    "manifests/development-addon.manifest.json",
    "manifests/test-addon.manifest.json",
]
missing = [str(output.parent / path) for path in expected if not (output.parent / path).is_file()]
result = {
    "schema_version": 1,
    "pass": False,
    "blocked": True,
    "blocked_by": "manifest_generation",
    "generator_returncode": generator_rc,
    "check_count": 0,
    "checks": {},
    "failed_checks": ["independent_verification_blocked"],
    "missing_outputs": missing,
    "parse_errors": {},
    "claim_boundary": {
        "proved": "No manifest-schema claim; generation did not pass.",
        "not_proved": "Artifact manifests, index integrity, and canonical JSON fidelity.",
    },
}
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
PY
}

write_workflow_status() {
    "$PYTHON" -I -B -S - \
        "$RESULTS_DIR/workflow-status.json" "$1" "$2" "$3" <<'PY'
import json
import sys
from pathlib import Path

returncodes = {
    "manifest_generation": int(sys.argv[2]),
    "source_mutation": int(sys.argv[3]),
    "independent_verification": int(sys.argv[4]),
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
}

echo "== Frozen products before manifest generation =="
fingerprint_tree "$CANONICAL_PREFIX" "$RESULTS_DIR/canonical-before.json" 3155
fingerprint_tree "$RUNTIME_PREFIX" "$RESULTS_DIR/runtime-before.json" 714

set +e
run_local_script \
    "$GENERATOR" \
    --ownership-dir "$OWNERSHIP_INPUT" \
    --product-lock "$RESULTS_DIR/input/product-lock.json" \
    --output-dir "$RESULTS_DIR" \
    --expected-component-manifest "$EXPECTED_COMPONENT_MANIFEST" \
    --expected-canonical-fingerprint "$EXPECTED_CANONICAL_FINGERPRINT" \
    --expected-runtime-fingerprint "$EXPECTED_RUNTIME_FINGERPRINT" \
    --expected-owned-manifest "$EXPECTED_OWNED_MANIFEST" \
    --expected-structural-manifest "$EXPECTED_STRUCTURAL_MANIFEST" \
    --expected-shared-manifest "$EXPECTED_SHARED_MANIFEST" \
    --require-pass \
    > "$RESULTS_DIR/generator.log" 2>&1
generator_rc=$?
set -e
cat "$RESULTS_DIR/generator.log"

echo
echo "== Frozen products after manifest generation =="
fingerprint_tree "$CANONICAL_PREFIX" "$RESULTS_DIR/canonical-after.json" 3155
fingerprint_tree "$RUNTIME_PREFIX" "$RESULTS_DIR/runtime-after.json" 714

set +e
write_mutation_check
mutation_rc=$?
set -e

if [[ $generator_rc -eq 0 ]]; then
    set +e
    run_local_script \
        "$VERIFIER" \
        --ownership-dir "$OWNERSHIP_INPUT" \
        --manifest-output-dir "$RESULTS_DIR" \
        --product-lock "$RESULTS_DIR/input/product-lock.json" \
        --canonical-before "$RESULTS_DIR/canonical-before.json" \
        --canonical-after "$RESULTS_DIR/canonical-after.json" \
        --runtime-before "$RESULTS_DIR/runtime-before.json" \
        --runtime-after "$RESULTS_DIR/runtime-after.json" \
        --expected-component-manifest "$EXPECTED_COMPONENT_MANIFEST" \
        --expected-canonical-fingerprint "$EXPECTED_CANONICAL_FINGERPRINT" \
        --expected-runtime-fingerprint "$EXPECTED_RUNTIME_FINGERPRINT" \
        --expected-owned-manifest "$EXPECTED_OWNED_MANIFEST" \
        --expected-structural-manifest "$EXPECTED_STRUCTURAL_MANIFEST" \
        --expected-shared-manifest "$EXPECTED_SHARED_MANIFEST" \
        --output "$RESULTS_DIR/verification.json" \
        > "$RESULTS_DIR/verifier.log" 2>&1
    verifier_rc=$?
    set -e
    cat "$RESULTS_DIR/verifier.log"
else
    verifier_rc=125
    write_blocked_verification "$generator_rc" \
        > "$RESULTS_DIR/verifier.log" 2>&1
    cat "$RESULTS_DIR/verifier.log"
fi

write_workflow_status "$generator_rc" "$mutation_rc" "$verifier_rc"

printf '\nGeneration:      %s\n' "$RESULTS_DIR/generation.json"
printf 'Manifest index: %s\n' "$RESULTS_DIR/manifest-index.json"
printf 'Manifests:      %s\n' "$RESULTS_DIR/manifests"
printf 'Verification:   %s\n' "$RESULTS_DIR/verification.json"
printf 'Mutation check: %s\n\n' "$RESULTS_DIR/source-mutation-check.txt"

final_rc=0
for rc in "$generator_rc" "$mutation_rc" "$verifier_rc"; do
    if [[ $rc -ne 0 ]]; then
        final_rc=$rc
        break
    fi
done

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE2_ARTIFACT_MANIFEST_SCHEMA=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "ARTIFACT_MANIFEST_ACCEPTED_INPUTS=PASS"
echo "ARTIFACT_MANIFEST_GENERATION=42/42 PASS"
echo "ARTIFACT_MANIFEST_VERIFICATION=48/48 PASS"
echo "ARTIFACT_MANIFEST_CANONICAL_JSON=PASS"
echo "ARTIFACT_MANIFEST_INDEX_INTEGRITY=PASS"
echo "ARTIFACT_MANIFEST_SOURCE_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE2_ARTIFACT_MANIFEST_SCHEMA=PASS"
