#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 1 final gates:
#   1. native closure and 67/67 extension imports for runtime-base
#   2. production-shape whole-prefix relocation with portable fidelity

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RUNTIME_PREFIX="${RUNTIME_PREFIX:-$WORK_ROOT/termux/stage3c-phase1-isolated-variants/runtime-base/prefix}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
POLICY_RESULTS="${POLICY_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase1-component-policy}"
REASSESSMENT_RESULTS="${REASSESSMENT_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase1-isolated-variant-capability-reassessment}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase1-runtime-base-final-validation}"
RELOCATION_ROOT="${RELOCATION_ROOT:-$WORK_ROOT/termux/stage3c-phase1-runtime-base-relocation}"

EXPECTED_COMPONENT_MANIFEST="${EXPECTED_COMPONENT_MANIFEST:-91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84}"
EXPECTED_RUNTIME_FINGERPRINT="${EXPECTED_RUNTIME_FINGERPRINT:-9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796}"
EXPECTED_CANONICAL_FINGERPRINT="${EXPECTED_CANONICAL_FINGERPRINT:-5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c}"

TOOL_PYTHON="$CANONICAL_PREFIX/bin/python"
RUNTIME_PYTHON="$RUNTIME_PREFIX/bin/python"
FINGERPRINT="$SCRIPT_DIR/fingerprint-product-tree.py"
INPUT_VERIFY="$SCRIPT_DIR/verify-runtime-base-final-inputs.py"
CLOSURE_VERIFY="$SCRIPT_DIR/verify-runtime-base-closure.py"
RELOCATION_VERIFY="$SCRIPT_DIR/verify-runtime-base-relocation.py"
FINAL_VERIFY="$SCRIPT_DIR/verify-runtime-base-final-validation.py"
STAGE3A_DIR="$PROJECT_ROOT/experiments/stage3a-runtime-closure"
RECONFIRM="$STAGE3A_DIR/reconfirm-production-relocation.sh"
DIAGNOSE="$PROJECT_ROOT/experiments/stage3b-target-validation/diagnose-promoted-relocation-fidelity.py"
RELOCATION_ENGINE_VERIFY="$PROJECT_ROOT/experiments/stage3b-target-validation/verify-promoted-relocation.py"

INPUT_DIR="$RESULTS_DIR/input"
CLOSURE_DIR="$RESULTS_DIR/closure"
RELOCATION_DIR="$RESULTS_DIR/relocation"
B_PREFIX="$RELOCATION_ROOT/location-b/prefix"

[[ -x "$RUNTIME_PYTHON" ]] || {
    echo "ERROR: isolated runtime-base is missing: $RUNTIME_PYTHON" >&2
    exit 2
}
[[ -x "$TOOL_PYTHON" ]] || {
    echo "ERROR: canonical promoted Python is missing: $TOOL_PYTHON" >&2
    exit 2
}

for file in \
    "$POLICY_RESULTS/component-policy.json" \
    "$POLICY_RESULTS/component-policy-verification.json" \
    "$REASSESSMENT_RESULTS/verification.json" \
    "$FINGERPRINT" \
    "$INPUT_VERIFY" \
    "$CLOSURE_VERIFY" \
    "$RELOCATION_VERIFY" \
    "$FINAL_VERIFY" \
    "$STAGE3A_DIR/inventory-runtime.sh" \
    "$STAGE3A_DIR/analyze-and-probe.sh" \
    "$STAGE3A_DIR/probe-extension-imports.sh" \
    "$RECONFIRM" \
    "$DIAGNOSE" \
    "$RELOCATION_ENGINE_VERIFY"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required accepted evidence or tool is missing: $file" >&2
        exit 2
    }
done

rm -rf "$RESULTS_DIR" "$RELOCATION_ROOT"
mkdir -p "$INPUT_DIR" "$CLOSURE_DIR" "$RELOCATION_DIR"

cp -a "$POLICY_RESULTS/component-policy.json" \
    "$INPUT_DIR/component-policy.json"
cp -a "$POLICY_RESULTS/component-policy-verification.json" \
    "$INPUT_DIR/component-policy-verification.json"
cp -a "$REASSESSMENT_RESULTS/verification.json" \
    "$INPUT_DIR/phello-reassessment-verification.json"

printf 'Runtime-base prefix:      %s\n' "$RUNTIME_PREFIX"
printf 'Canonical prefix:         %s\n' "$CANONICAL_PREFIX"
printf 'Component manifest:       %s\n' "$EXPECTED_COMPONENT_MANIFEST"
printf 'Runtime fingerprint:      %s\n' "$EXPECTED_RUNTIME_FINGERPRINT"
printf 'Canonical fingerprint:    %s\n' "$EXPECTED_CANONICAL_FINGERPRINT"
printf 'Relocation root:          %s\n' "$RELOCATION_ROOT"
printf 'Results:                  %s\n\n' "$RESULTS_DIR"

fingerprint_tree() {
    local root="$1"
    local output="$2"
    local expected_count="$3"
    "$TOOL_PYTHON" -I -B -S \
        "$FINGERPRINT" \
        --runtime-prefix "$root" \
        --output "$output" \
        --expected-entry-count "$expected_count"
}

write_status_json() {
    local output="$1"
    shift
    "$TOOL_PYTHON" -I -B -S - "$output" "$@" <<'PY'
import json
import sys
from pathlib import Path

pairs = sys.argv[2:]
if len(pairs) % 2:
    raise SystemExit("status key/value arguments must be paired")
returncodes = {
    pairs[index]: int(pairs[index + 1])
    for index in range(0, len(pairs), 2)
}
result = {
    "schema_version": 1,
    "pass": bool(returncodes) and all(value == 0 for value in returncodes.values()),
    "returncodes": returncodes,
}
Path(sys.argv[1]).write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(result, indent=2, sort_keys=True))
PY
}

write_mutation_check() {
    local before_json="$1"
    local after_json="$2"
    local output="$3"
    local subject_key="$4"
    local subject_value="$5"
    "$TOOL_PYTHON" -I -B -S - \
        "$before_json" "$after_json" "$output" \
        "$subject_key" "$subject_value" <<'PY'
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
        f"{sys.argv[4]}={sys.argv[5]}",
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
raise SystemExit(0 if passed else 23)
PY
}

first_nonzero() {
    local rc
    for rc in "$@"; do
        if [[ "$rc" -ne 0 ]]; then
            printf '%s\n' "$rc"
            return
        fi
    done
    echo 0
}

echo "== Final input identity =="
fingerprint_tree \
    "$RUNTIME_PREFIX" \
    "$RESULTS_DIR/runtime-base-input-fingerprint.json" \
    714
fingerprint_tree \
    "$CANONICAL_PREFIX" \
    "$RESULTS_DIR/canonical-input-fingerprint.json" \
    3155

set +e
"$TOOL_PYTHON" -I -B -S \
    "$INPUT_VERIFY" \
    --policy "$INPUT_DIR/component-policy.json" \
    --policy-verification "$INPUT_DIR/component-policy-verification.json" \
    --reassessment-verification "$INPUT_DIR/phello-reassessment-verification.json" \
    --runtime-fingerprint "$RESULTS_DIR/runtime-base-input-fingerprint.json" \
    --canonical-fingerprint "$RESULTS_DIR/canonical-input-fingerprint.json" \
    --output "$RESULTS_DIR/input-verification.json" \
    --expected-component-manifest "$EXPECTED_COMPONENT_MANIFEST" \
    --expected-runtime-fingerprint "$EXPECTED_RUNTIME_FINGERPRINT" \
    --expected-canonical-fingerprint "$EXPECTED_CANONICAL_FINGERPRINT" \
    --expected-runtime-entry-count 714 \
    --expected-canonical-entry-count 3155 \
    > "$RESULTS_DIR/input-verifier.log" 2>&1
input_rc=$?
set -e
cat "$RESULTS_DIR/input-verifier.log"

closure_inventory_rc=125
closure_analysis_rc=125
closure_extension_rc=125
closure_verify_rc=125
closure_workflow_rc=125
relocation_workflow_rc=125
relocation_engine_verify_rc=125
relocation_verify_rc=125

if [[ $input_rc -eq 0 ]]; then
    echo
    echo "== Runtime-base native closure =="
    fingerprint_tree \
        "$RUNTIME_PREFIX" \
        "$CLOSURE_DIR/runtime-before.json" \
        714
    fingerprint_tree \
        "$CANONICAL_PREFIX" \
        "$CLOSURE_DIR/canonical-before.json" \
        3155

    set +e
    RUNTIME_PREFIX="$RUNTIME_PREFIX" \
    PYTHON_BIN="$RUNTIME_PYTHON" \
    OUTPUT_DIR="$CLOSURE_DIR" \
    bash "$STAGE3A_DIR/inventory-runtime.sh" \
        > "$CLOSURE_DIR/inventory.log" 2>&1
    closure_inventory_rc=$?
    set -e
    cat "$CLOSURE_DIR/inventory.log"

    if [[ $closure_inventory_rc -eq 0 ]]; then
        set +e
        RUNTIME_PREFIX="$RUNTIME_PREFIX" \
        PYTHON_BIN="$RUNTIME_PYTHON" \
        RESULTS_DIR="$CLOSURE_DIR" \
        bash "$STAGE3A_DIR/analyze-and-probe.sh" \
            > "$CLOSURE_DIR/analysis.log" 2>&1
        closure_analysis_rc=$?
        set -e
        cat "$CLOSURE_DIR/analysis.log"
    fi

    if [[ $closure_inventory_rc -eq 0 && $closure_analysis_rc -eq 0 ]]; then
        set +e
        RUNTIME_PREFIX="$RUNTIME_PREFIX" \
        PYTHON_BIN="$RUNTIME_PYTHON" \
        RESULTS_DIR="$CLOSURE_DIR" \
        bash "$STAGE3A_DIR/probe-extension-imports.sh" \
            > "$CLOSURE_DIR/extension-imports.log" 2>&1
        closure_extension_rc=$?
        set -e
        cat "$CLOSURE_DIR/extension-imports.log"
    fi

    closure_workflow_rc="$(first_nonzero \
        "$closure_inventory_rc" \
        "$closure_analysis_rc" \
        "$closure_extension_rc")"
    write_status_json \
        "$CLOSURE_DIR/workflow-status.json" \
        inventory "$closure_inventory_rc" \
        closure_analysis "$closure_analysis_rc" \
        extension_imports "$closure_extension_rc"

    fingerprint_tree \
        "$RUNTIME_PREFIX" \
        "$CLOSURE_DIR/runtime-after.json" \
        714
    fingerprint_tree \
        "$CANONICAL_PREFIX" \
        "$CLOSURE_DIR/canonical-after.json" \
        3155

    set +e
    "$RUNTIME_PYTHON" -I -B -S \
        "$CLOSURE_VERIFY" \
        --results-dir "$CLOSURE_DIR" \
        --input-verification "$RESULTS_DIR/input-verification.json" \
        --runtime-prefix "$RUNTIME_PREFIX" \
        --canonical-prefix "$CANONICAL_PREFIX" \
        --runtime-before "$CLOSURE_DIR/runtime-before.json" \
        --runtime-after "$CLOSURE_DIR/runtime-after.json" \
        --canonical-before "$CLOSURE_DIR/canonical-before.json" \
        --canonical-after "$CLOSURE_DIR/canonical-after.json" \
        --expected-runtime-fingerprint "$EXPECTED_RUNTIME_FINGERPRINT" \
        --expected-canonical-fingerprint "$EXPECTED_CANONICAL_FINGERPRINT" \
        > "$CLOSURE_DIR/verifier.log" 2>&1
    closure_verify_rc=$?
    set -e
    cat "$CLOSURE_DIR/verifier.log"
fi

if [[ $input_rc -eq 0 && $closure_workflow_rc -eq 0 && $closure_verify_rc -eq 0 ]]; then
    echo
    echo "== Runtime-base production relocation =="
    fingerprint_tree \
        "$RUNTIME_PREFIX" \
        "$RELOCATION_DIR/runtime-before.json" \
        714
    fingerprint_tree \
        "$CANONICAL_PREFIX" \
        "$RELOCATION_DIR/canonical-before.json" \
        3155

    set +e
    SOURCE_PREFIX="$RUNTIME_PREFIX" \
    ROOT="$RELOCATION_ROOT" \
    RESULTS_DIR="$RELOCATION_DIR/reconfirm" \
    bash "$RECONFIRM" \
        > "$RELOCATION_DIR/workflow.log" 2>&1
    relocation_workflow_rc=$?
    set -e
    cat "$RELOCATION_DIR/workflow.log"

    fingerprint_tree \
        "$RUNTIME_PREFIX" \
        "$RELOCATION_DIR/runtime-after.json" \
        714
    fingerprint_tree \
        "$CANONICAL_PREFIX" \
        "$RELOCATION_DIR/canonical-after.json" \
        3155

    set +e
    fingerprint_tree \
        "$B_PREFIX" \
        "$RELOCATION_DIR/relocated-fingerprint.json" \
        714
    relocated_fingerprint_rc=$?
    set -e

    {
        echo "returncode=$relocation_workflow_rc"
        echo "engine=$RECONFIRM"
    } > "$RELOCATION_DIR/workflow-status.txt"

    set +e
    write_mutation_check \
        "$RELOCATION_DIR/runtime-before.json" \
        "$RELOCATION_DIR/runtime-after.json" \
        "$RELOCATION_DIR/candidate-runtime-mutation-check.txt" \
        candidate_prefix \
        "$RUNTIME_PREFIX"
    runtime_mutation_rc=$?
    write_mutation_check \
        "$RELOCATION_DIR/canonical-before.json" \
        "$RELOCATION_DIR/canonical-after.json" \
        "$RELOCATION_DIR/frozen-runtime-mutation-check.txt" \
        frozen_prefix \
        "$CANONICAL_PREFIX"
    canonical_mutation_rc=$?
    set -e

    set +e
    "$RUNTIME_PYTHON" -I -B -S \
        "$DIAGNOSE" \
        --source "$RUNTIME_PREFIX" \
        --relocated "$B_PREFIX" \
        --output-dir "$RELOCATION_DIR/fidelity-diagnosis" \
        --require-portable-pass \
        > "$RELOCATION_DIR/fidelity.log" 2>&1
    fidelity_rc=$?
    set -e
    cat "$RELOCATION_DIR/fidelity.log"

    "$TOOL_PYTHON" -I -B -S - \
        "$RELOCATION_DIR/runtime-before.json" \
        "$RELOCATION_DIR/relocated-fingerprint.json" \
        "$RELOCATION_DIR/fidelity-diagnosis/fidelity-status.txt" \
        "$RELOCATION_DIR/relocated-runtime-fidelity-check.txt" <<'PY'
import json
import sys
from pathlib import Path

source = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
relocated = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
status_path = Path(sys.argv[3])
status = (
    status_path.read_text(encoding="utf-8")
    if status_path.is_file()
    else "fidelity_status_missing=true\nportable_pass=false\npass=false\n"
)
strict_equal = source.get("fingerprint") == relocated.get("fingerprint")
text = "\n".join(
    (
        "comparison=portable-tree-manifest-v2",
        f"source_prefix={source.get('root')}",
        f"relocated_prefix={relocated.get('root')}",
        f"source_same_tree_strict_fingerprint={source.get('fingerprint')}",
        f"relocated_strict_fingerprint={relocated.get('fingerprint')}",
        f"strict_fingerprint_equal={'true' if strict_equal else 'false'}",
        status.rstrip("\n"),
        "",
    )
)
Path(sys.argv[4]).write_text(text, encoding="utf-8")
print(text, end="")
PY

    {
        if [[ -e "$RELOCATION_ROOT/location-a/prefix" ]]; then
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
    } > "$RELOCATION_DIR/relocation-location-state.txt"

    set +e
    "$RUNTIME_PYTHON" -I -B -S \
        "$RELOCATION_ENGINE_VERIFY" \
        --results-dir "$RELOCATION_DIR" \
        --candidate-prefix "$RUNTIME_PREFIX" \
        --frozen-prefix "$CANONICAL_PREFIX" \
        --relocation-root "$RELOCATION_ROOT" \
        > "$RELOCATION_DIR/engine-verifier.log" 2>&1
    relocation_engine_verify_rc=$?
    set -e
    cat "$RELOCATION_DIR/engine-verifier.log"

    set +e
    "$RUNTIME_PYTHON" -I -B -S \
        "$RELOCATION_VERIFY" \
        --results-dir "$RELOCATION_DIR" \
        --input-verification "$RESULTS_DIR/input-verification.json" \
        --closure-verification "$CLOSURE_DIR/runtime-base-closure-verification.json" \
        --runtime-prefix "$RUNTIME_PREFIX" \
        --canonical-prefix "$CANONICAL_PREFIX" \
        --relocation-root "$RELOCATION_ROOT" \
        --runtime-before "$RELOCATION_DIR/runtime-before.json" \
        --runtime-after "$RELOCATION_DIR/runtime-after.json" \
        --canonical-before "$RELOCATION_DIR/canonical-before.json" \
        --canonical-after "$RELOCATION_DIR/canonical-after.json" \
        --expected-runtime-fingerprint "$EXPECTED_RUNTIME_FINGERPRINT" \
        --expected-canonical-fingerprint "$EXPECTED_CANONICAL_FINGERPRINT" \
        > "$RELOCATION_DIR/verifier.log" 2>&1
    relocation_verify_rc=$?
    set -e
    cat "$RELOCATION_DIR/verifier.log"

    relocation_workflow_rc="$(first_nonzero \
        "$relocation_workflow_rc" \
        "$relocated_fingerprint_rc" \
        "$runtime_mutation_rc" \
        "$canonical_mutation_rc" \
        "$fidelity_rc")"
fi

write_status_json \
    "$RESULTS_DIR/workflow-status.json" \
    input_verification "$input_rc" \
    closure_workflow "$closure_workflow_rc" \
    closure_verification "$closure_verify_rc" \
    relocation_workflow "$relocation_workflow_rc" \
    relocation_engine_verification "$relocation_engine_verify_rc" \
    relocation_verification "$relocation_verify_rc"

set +e
"$TOOL_PYTHON" -I -B -S \
    "$FINAL_VERIFY" \
    --results-dir "$RESULTS_DIR" \
    --output "$RESULTS_DIR/verification.json" \
    --expected-component-manifest "$EXPECTED_COMPONENT_MANIFEST" \
    --expected-runtime-fingerprint "$EXPECTED_RUNTIME_FINGERPRINT" \
    --expected-canonical-fingerprint "$EXPECTED_CANONICAL_FINGERPRINT" \
    > "$RESULTS_DIR/final-verifier.log" 2>&1
final_verify_rc=$?
set -e
cat "$RESULTS_DIR/final-verifier.log"

printf '\nInput verification:      %s\n' "$RESULTS_DIR/input-verification.json"
printf 'Closure verification:    %s\n' "$CLOSURE_DIR/runtime-base-closure-verification.json"
printf 'Relocation engine:       %s\n' "$RELOCATION_DIR/promoted-relocation-verification.json"
printf 'Relocation verification: %s\n' "$RELOCATION_DIR/runtime-base-relocation-verification.json"
printf 'Final verification:      %s\n\n' "$RESULTS_DIR/verification.json"

if [[ $final_verify_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE1_RUNTIME_BASE_FINAL_VALIDATION=FAIL rc=$final_verify_rc"
    exit "$final_verify_rc"
fi

echo "RUNTIME_BASE_FINAL_INPUT_CONTRACT=PASS"
echo "RUNTIME_BASE_NATIVE_CLOSURE=PASS"
echo "RUNTIME_BASE_EXTENSION_IMPORTS=67/67 PASS"
echo "RUNTIME_BASE_RELOCATION_ENGINE=31/31 PASS"
echo "RUNTIME_BASE_RELOCATION_PORTABLE_FIDELITY=PASS"
echo "RUNTIME_BASE_SOURCE_MUTATION_CHECK=PASS"
echo "CANONICAL_SOURCE_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE1_RUNTIME_BASE_FINAL_VALIDATION=PASS"
