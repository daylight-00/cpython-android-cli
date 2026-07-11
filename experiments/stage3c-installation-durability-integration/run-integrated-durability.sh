#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 4 Gate 5B: integrated durability and complete replay.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

GATE5A_RESULTS="${GATE5A_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase4-recovery-durability-inventory}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase4-integrated-durability}"
INTEGRATION_WORK="${INTEGRATION_WORK:-$WORK_ROOT/termux/stage3c-phase4-integrated-durability}"

PYTHON="$CANONICAL_PREFIX/bin/python"
LOCAL_SCRIPT_RUNNER="$SCRIPT_DIR/../stage3c-artifact-manifest/run-isolated-local-script.py"
FINGERPRINT="$SCRIPT_DIR/../stage3c-installation-contract/fingerprint-evidence-tree.py"
RECOVERY_DIR="$SCRIPT_DIR/../stage3c-installation-recovery"
DURABILITY_DIR="$SCRIPT_DIR/../stage3c-installation-durability"
SOURCE_VERIFIER="$SCRIPT_DIR/verify_integrated_recovery_sources.py"
TRACE_VERIFIER="$SCRIPT_DIR/verify_integrated_durability_traces.py"
EXERCISES="$SCRIPT_DIR/run_integrated_durability_exercises.py"
OVERALL_VERIFIER="$SCRIPT_DIR/verify_integrated_durability_gate.py"

INPUT_DIR="$RESULTS_DIR/input/gate5a"
GATE4_INPUT="$INPUT_DIR/input/gate4"
GATE3_INPUT="$GATE4_INPUT/input/gate3"
GATE2_INPUT="$GATE3_INPUT/input/gate2"
CONTRACT_INPUT="$GATE2_INPUT/input/contract"
RECOVERY_RESULTS="$RESULTS_DIR/recovery-replay"
DURABILITY_RESULTS="$RESULTS_DIR/durability-replay"
EXERCISE_RESULTS="$RESULTS_DIR/exercises"
TRACE_DIR="$RESULTS_DIR/integration-traces"
RECOVERY_WORK="$INTEGRATION_WORK/recovery"
DURABILITY_WORK="$INTEGRATION_WORK/durability"
EXERCISE_WORK="$INTEGRATION_WORK/exercises"

[[ -x "$PYTHON" ]] || {
    echo "ERROR: canonical promoted Python is missing: $PYTHON" >&2
    exit 2
}

for file in \
    "$GATE5A_RESULTS/scenario.json" \
    "$GATE5A_RESULTS/verification.json" \
    "$GATE5A_RESULTS/workflow-status.json" \
    "$GATE5A_RESULTS/result-index.json" \
    "$GATE5A_RESULTS/mutation-inventory.json" \
    "$GATE5A_RESULTS/integration-plan.json" \
    "$LOCAL_SCRIPT_RUNNER" \
    "$FINGERPRINT" \
    "$RECOVERY_DIR/recovery_common.py" \
    "$RECOVERY_DIR/recovery_durability.py" \
    "$RECOVERY_DIR/recovery_operations.py" \
    "$RECOVERY_DIR/recovery_engine.py" \
    "$RECOVERY_DIR/run-recovery-scenarios.py" \
    "$RECOVERY_DIR/verify-recovery-scenarios.py" \
    "$DURABILITY_DIR/run-durability-scenarios.py" \
    "$DURABILITY_DIR/verify-durability-scenarios.py" \
    "$SOURCE_VERIFIER" \
    "$TRACE_VERIFIER" \
    "$EXERCISES" \
    "$OVERALL_VERIFIER"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required frozen evidence or tool is missing: $file" >&2
        exit 2
    }
done

rm -rf "$RESULTS_DIR" "$INTEGRATION_WORK"
mkdir -p \
    "$INPUT_DIR" \
    "$TRACE_DIR" \
    "$RECOVERY_RESULTS" \
    "$DURABILITY_RESULTS" \
    "$EXERCISE_RESULTS"
cp -a "$GATE5A_RESULTS"/. "$INPUT_DIR"/

printf 'Gate 5A results:        %s\n' "$GATE5A_RESULTS"
printf 'Integrated work:       %s\n' "$INTEGRATION_WORK"
printf 'Results:               %s\n\n' "$RESULTS_DIR"

run_local_script() {
    "$PYTHON" -I -B -S "$LOCAL_SCRIPT_RUNNER" "$@"
}

fingerprint_tree() {
    "$PYTHON" -I -B -S \
        "$FINGERPRINT" \
        --root "$1" \
        --output "$2"
}

write_mutation_check() {
    "$PYTHON" -I -B -S - "$1" "$2" "$3" <<'PY'
import json
import sys
from pathlib import Path

before = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
after = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
passed = (
    before.get("pass") is True
    and after.get("pass") is True
    and before.get("entry_count") == after.get("entry_count")
    and before.get("fingerprint") == after.get("fingerprint")
)
text = "\n".join(
    (
        f"before={before.get('fingerprint')}",
        f"after={after.get('fingerprint')}",
        f"entry_count={after.get('entry_count')}",
        f"pass={'true' if passed else 'false'}",
        "",
    )
)
Path(sys.argv[3]).write_text(text, encoding="utf-8")
print(text, end="")
raise SystemExit(0 if passed else 58)
PY
}

write_blocked() {
    "$PYTHON" -I -B -S - "$1" "$2" "$3" <<'PY'
import json
import sys
from pathlib import Path

result = {
    "schema_version": 1,
    "pass": False,
    "blocked": True,
    "blocked_by": sys.argv[2],
    "blocked_returncode": int(sys.argv[3]),
    "check_count": 0,
    "checks": {},
    "failed_checks": ["blocked"],
}
path = Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
PY
}

write_workflow_status() {
    "$PYTHON" -I -B -S - \
        "$RESULTS_DIR/workflow-status.json" \
        "$source_rc" \
        "$recovery_scenario_rc" \
        "$recovery_mutation_rc" \
        "$recovery_verifier_rc" \
        "$exercise_rc" \
        "$trace_rc" \
        "$durability_scenario_rc" \
        "$durability_mutation_rc" \
        "$durability_verifier_rc" \
        "$input_mutation_rc" \
        "$overall_rc" <<'PY'
import json
import sys
from pathlib import Path

names = (
    "source_integration",
    "recovery_scenarios",
    "recovery_input_mutation",
    "recovery_independent_verification",
    "integrated_exercises",
    "integrated_trace_verification",
    "durability_scenarios",
    "durability_input_mutation",
    "durability_independent_verification",
    "gate5a_input_mutation",
    "overall_verification",
)
returncodes = {name: int(value) for name, value in zip(names, sys.argv[2:])}
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

write_result_index() {
    "$PYTHON" -I -B -S - "$RESULTS_DIR" "$RESULTS_DIR/result-index.json" <<'PY'
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
files = []
for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
    if path == output or path.is_dir() or path.name == "result-index.log":
        continue
    relative = path.relative_to(root).as_posix()
    observed = path.lstat()
    if path.is_symlink():
        files.append(
            {
                "path": relative,
                "type": "symlink",
                "mode": f"{stat.S_IMODE(observed.st_mode):04o}",
                "target": os.readlink(path),
            }
        )
    elif path.is_file():
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        files.append(
            {
                "path": relative,
                "type": "regular",
                "mode": f"{stat.S_IMODE(observed.st_mode):04o}",
                "size": observed.st_size,
                "sha256": digest.hexdigest(),
            }
        )
    else:
        raise SystemExit(f"unsupported result entry: {path}")
result = {
    "schema_version": 1,
    "index_kind": "stage3c-phase4-integrated-durability-result-index",
    "file_count": len(files),
    "files": files,
}
output.write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(result, indent=2, sort_keys=True))
PY
}

fingerprint_tree "$INPUT_DIR" "$RESULTS_DIR/input-before.json"

set +e
run_local_script \
    "$SOURCE_VERIFIER" \
    --gate5a-results "$INPUT_DIR" \
    --recovery-dir "$RECOVERY_DIR" \
    --output "$RESULTS_DIR/source-integration.json" \
    > "$RESULTS_DIR/source-integration.log" 2>&1
source_rc=$?
set -e
cat "$RESULTS_DIR/source-integration.log"

fingerprint_tree "$GATE2_INPUT" "$RESULTS_DIR/recovery-input-before.json"
export CPYTHON_ANDROID_CLI_DURABILITY_TRACE_DIR="$TRACE_DIR"

set +e
run_local_script \
    "$RECOVERY_DIR/run-recovery-scenarios.py" \
    --gate2-results "$GATE2_INPUT" \
    --engine "$RECOVERY_DIR/recovery_engine.py" \
    --work-root "$RECOVERY_WORK" \
    --output-dir "$RECOVERY_RESULTS" \
    --require-pass \
    > "$RESULTS_DIR/recovery-scenarios.log" 2>&1
recovery_scenario_rc=$?
set -e
cat "$RESULTS_DIR/recovery-scenarios.log"

fingerprint_tree "$GATE2_INPUT" "$RESULTS_DIR/recovery-input-after.json"
set +e
write_mutation_check \
    "$RESULTS_DIR/recovery-input-before.json" \
    "$RESULTS_DIR/recovery-input-after.json" \
    "$RESULTS_DIR/recovery-input-mutation-check.txt"
recovery_mutation_rc=$?
set -e

if [[ $recovery_scenario_rc -eq 0 && $recovery_mutation_rc -eq 0 ]]; then
    set +e
    run_local_script \
        "$RECOVERY_DIR/verify-recovery-scenarios.py" \
        --gate2-results "$GATE2_INPUT" \
        --scenario-results "$RECOVERY_RESULTS" \
        --work-root "$RECOVERY_WORK" \
        --input-before "$RESULTS_DIR/recovery-input-before.json" \
        --input-after "$RESULTS_DIR/recovery-input-after.json" \
        --output "$RECOVERY_RESULTS/verification.json" \
        > "$RESULTS_DIR/recovery-verifier.log" 2>&1
    recovery_verifier_rc=$?
    set -e
else
    recovery_verifier_rc=125
    write_blocked \
        "$RECOVERY_RESULTS/verification.json" \
        "recovery_scenarios_or_input" \
        "$recovery_scenario_rc" \
        > "$RESULTS_DIR/recovery-verifier.log" 2>&1
fi
cat "$RESULTS_DIR/recovery-verifier.log"

if [[ $source_rc -eq 0 ]]; then
    set +e
    run_local_script \
        "$EXERCISES" \
        --contract-results "$CONTRACT_INPUT" \
        --engine "$RECOVERY_DIR/recovery_engine.py" \
        --work-root "$EXERCISE_WORK" \
        --output-dir "$EXERCISE_RESULTS" \
        --require-pass \
        > "$RESULTS_DIR/exercises.log" 2>&1
    exercise_rc=$?
    set -e
else
    exercise_rc=125
    write_blocked "$EXERCISE_RESULTS/exercise.json" "source_integration" "$source_rc" \
        > "$RESULTS_DIR/exercises.log" 2>&1
fi
cat "$RESULTS_DIR/exercises.log"

if [[ $recovery_scenario_rc -eq 0 && $recovery_verifier_rc -eq 0 && $exercise_rc -eq 0 ]]; then
    set +e
    run_local_script \
        "$TRACE_VERIFIER" \
        --trace-dir "$TRACE_DIR" \
        --output "$RESULTS_DIR/trace-verification.json" \
        > "$RESULTS_DIR/trace-verifier.log" 2>&1
    trace_rc=$?
    set -e
else
    trace_rc=125
    write_blocked \
        "$RESULTS_DIR/trace-verification.json" \
        "recovery_or_exercise" \
        "$recovery_scenario_rc" \
        > "$RESULTS_DIR/trace-verifier.log" 2>&1
fi
cat "$RESULTS_DIR/trace-verifier.log"
unset CPYTHON_ANDROID_CLI_DURABILITY_TRACE_DIR 2>/dev/null || true

fingerprint_tree "$GATE3_INPUT" "$RESULTS_DIR/durability-input-before.json"
set +e
run_local_script \
    "$DURABILITY_DIR/run-durability-scenarios.py" \
    --gate3-results "$GATE3_INPUT" \
    --work-root "$DURABILITY_WORK" \
    --output-dir "$DURABILITY_RESULTS" \
    --require-pass \
    > "$RESULTS_DIR/durability-scenarios.log" 2>&1
durability_scenario_rc=$?
set -e
cat "$RESULTS_DIR/durability-scenarios.log"

fingerprint_tree "$GATE3_INPUT" "$RESULTS_DIR/durability-input-after.json"
set +e
write_mutation_check \
    "$RESULTS_DIR/durability-input-before.json" \
    "$RESULTS_DIR/durability-input-after.json" \
    "$RESULTS_DIR/durability-input-mutation-check.txt"
durability_mutation_rc=$?
set -e

if [[ $durability_scenario_rc -eq 0 && $durability_mutation_rc -eq 0 ]]; then
    set +e
    run_local_script \
        "$DURABILITY_DIR/verify-durability-scenarios.py" \
        --gate3-results "$GATE3_INPUT" \
        --scenario-results "$DURABILITY_RESULTS" \
        --work-root "$DURABILITY_WORK" \
        --input-before "$RESULTS_DIR/durability-input-before.json" \
        --input-after "$RESULTS_DIR/durability-input-after.json" \
        --output "$DURABILITY_RESULTS/verification.json" \
        > "$RESULTS_DIR/durability-verifier.log" 2>&1
    durability_verifier_rc=$?
    set -e
else
    durability_verifier_rc=125
    write_blocked \
        "$DURABILITY_RESULTS/verification.json" \
        "durability_scenarios_or_input" \
        "$durability_scenario_rc" \
        > "$RESULTS_DIR/durability-verifier.log" 2>&1
fi
cat "$RESULTS_DIR/durability-verifier.log"

fingerprint_tree "$INPUT_DIR" "$RESULTS_DIR/input-after.json"
set +e
write_mutation_check \
    "$RESULTS_DIR/input-before.json" \
    "$RESULTS_DIR/input-after.json" \
    "$RESULTS_DIR/input-mutation-check.txt"
input_mutation_rc=$?
set -e

if [[ $source_rc -eq 0 \
    && $recovery_scenario_rc -eq 0 \
    && $recovery_mutation_rc -eq 0 \
    && $recovery_verifier_rc -eq 0 \
    && $exercise_rc -eq 0 \
    && $trace_rc -eq 0 \
    && $durability_scenario_rc -eq 0 \
    && $durability_mutation_rc -eq 0 \
    && $durability_verifier_rc -eq 0 \
    && $input_mutation_rc -eq 0 ]]; then
    set +e
    run_local_script \
        "$OVERALL_VERIFIER" \
        --gate5a-results "$INPUT_DIR" \
        --source-integration "$RESULTS_DIR/source-integration.json" \
        --recovery-results "$RECOVERY_RESULTS" \
        --durability-results "$DURABILITY_RESULTS" \
        --exercise-results "$EXERCISE_RESULTS" \
        --trace-verification "$RESULTS_DIR/trace-verification.json" \
        --input-before "$RESULTS_DIR/input-before.json" \
        --input-after "$RESULTS_DIR/input-after.json" \
        --output "$RESULTS_DIR/verification.json" \
        > "$RESULTS_DIR/overall-verifier.log" 2>&1
    overall_rc=$?
    set -e
else
    overall_rc=125
    write_blocked "$RESULTS_DIR/verification.json" "component_gate" 125 \
        > "$RESULTS_DIR/overall-verifier.log" 2>&1
fi
cat "$RESULTS_DIR/overall-verifier.log"

write_workflow_status
write_result_index > "$RESULTS_DIR/result-index.log" 2>&1
cat "$RESULTS_DIR/result-index.log"

printf '\nSource integration:    %s\n' "$RESULTS_DIR/source-integration.json"
printf 'Recovery replay:      %s\n' "$RECOVERY_RESULTS/scenario.json"
printf 'Durability replay:    %s\n' "$DURABILITY_RESULTS/scenario.json"
printf 'Focused exercises:    %s\n' "$EXERCISE_RESULTS/exercise.json"
printf 'Trace verification:   %s\n' "$RESULTS_DIR/trace-verification.json"
printf 'Overall verification: %s\n' "$RESULTS_DIR/verification.json"
printf 'Result index:         %s\n\n' "$RESULTS_DIR/result-index.json"

final_rc=0
for rc in \
    "$source_rc" \
    "$recovery_scenario_rc" \
    "$recovery_mutation_rc" \
    "$recovery_verifier_rc" \
    "$exercise_rc" \
    "$trace_rc" \
    "$durability_scenario_rc" \
    "$durability_mutation_rc" \
    "$durability_verifier_rc" \
    "$input_mutation_rc" \
    "$overall_rc"; do
    if [[ $rc -ne 0 ]]; then
        final_rc=$rc
        break
    fi
done

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE4_INTEGRATED_DURABILITY=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "INTEGRATED_DURABILITY_ACCEPTED_INPUTS=PASS"
echo "INTEGRATED_DURABILITY_SOURCE_INTEGRATION=29/29 PASS"
echo "INTEGRATED_DURABILITY_RECOVERY_REPLAY=55/55 PASS"
echo "INTEGRATED_DURABILITY_RECOVERY_VERIFICATION=82/82 PASS"
echo "INTEGRATED_DURABILITY_DURABILITY_REPLAY=64/64 PASS"
echo "INTEGRATED_DURABILITY_DURABILITY_VERIFICATION=53/53 PASS"
echo "INTEGRATED_DURABILITY_EXERCISES=20/20 PASS"
echo "INTEGRATED_DURABILITY_TRACE_VERIFICATION=29/29 PASS"
echo "INTEGRATED_DURABILITY_OVERALL_VERIFICATION=36/36 PASS"
echo "INTEGRATED_DURABILITY_INPUT_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE4_INTEGRATED_DURABILITY=PASS"
