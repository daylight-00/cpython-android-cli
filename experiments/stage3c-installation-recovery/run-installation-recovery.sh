#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 4 Gate 3: process-crash recovery and lock contention.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

GATE2_RESULTS="${GATE2_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase4-installation-transaction}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase4-installation-recovery}"
RECOVERY_WORK="${RECOVERY_WORK:-$WORK_ROOT/termux/stage3c-phase4-installation-recovery}"

PYTHON="$CANONICAL_PREFIX/bin/python"
LOCAL_SCRIPT_RUNNER="$SCRIPT_DIR/../stage3c-artifact-manifest/run-isolated-local-script.py"
FINGERPRINT="$SCRIPT_DIR/../stage3c-installation-contract/fingerprint-evidence-tree.py"
ENGINE="$SCRIPT_DIR/recovery_engine.py"
SCENARIOS="$SCRIPT_DIR/run-recovery-scenarios.py"
VERIFIER="$SCRIPT_DIR/verify-recovery-scenarios.py"
INPUT_DIR="$RESULTS_DIR/input/gate2"

[[ -x "$PYTHON" ]] || {
    echo "ERROR: canonical promoted Python is missing: $PYTHON" >&2
    exit 2
}

for file in \
    "$GATE2_RESULTS/scenario.json" \
    "$GATE2_RESULTS/verification.json" \
    "$GATE2_RESULTS/workflow-status.json" \
    "$GATE2_RESULTS/result-index.json" \
    "$GATE2_RESULTS/input/contract/contract-index.json" \
    "$GATE2_RESULTS/input/contract/input/phase3/archives/cpython-android-cli-3.14.6-android24-aarch64-runtime-base.tar.gz" \
    "$GATE2_RESULTS/input/contract/input/phase3/archives/cpython-android-cli-3.14.6-android24-aarch64-development-addon.tar.gz" \
    "$LOCAL_SCRIPT_RUNNER" \
    "$FINGERPRINT" \
    "$SCRIPT_DIR/recovery_common.py" \
    "$SCRIPT_DIR/recovery_operations.py" \
    "$ENGINE" \
    "$SCRIPT_DIR/recovery_scenario_support.py" \
    "$SCRIPT_DIR/recovery_scenario_context.py" \
    "$SCRIPT_DIR/recovery_scenario_seed.py" \
    "$SCRIPT_DIR/recovery_scenario_applying.py" \
    "$SCRIPT_DIR/recovery_scenario_finalize.py" \
    "$SCENARIOS" \
    "$SCRIPT_DIR/recovery_verify_support.py" \
    "$VERIFIER"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required frozen evidence or tool is missing: $file" >&2
        exit 2
    }
done

rm -rf "$RESULTS_DIR" "$RECOVERY_WORK"
mkdir -p "$INPUT_DIR"
cp -a "$GATE2_RESULTS"/. "$INPUT_DIR"/

printf 'Gate 2 results:         %s\n' "$GATE2_RESULTS"
printf 'Recovery work:         %s\n' "$RECOVERY_WORK"
printf 'Results:               %s\n\n' "$RESULTS_DIR"

run_local_script() {
    "$PYTHON" -I -B -S "$LOCAL_SCRIPT_RUNNER" "$@"
}

fingerprint_input() {
    "$PYTHON" -I -B -S \
        "$FINGERPRINT" \
        --root "$INPUT_DIR" \
        --output "$1"
}

write_mutation_check() {
    "$PYTHON" -I -B -S - \
        "$RESULTS_DIR/input-before.json" \
        "$RESULTS_DIR/input-after.json" \
        "$RESULTS_DIR/input-mutation-check.txt" <<'PY'
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
raise SystemExit(0 if passed else 47)
PY
}

write_blocked_verification() {
    "$PYTHON" -I -B -S - \
        "$RESULTS_DIR/verification.json" "$1" <<'PY'
import json
import sys
from pathlib import Path

result = {
    "schema_version": 1,
    "pass": False,
    "blocked": True,
    "blocked_by": "recovery_scenarios",
    "scenario_returncode": int(sys.argv[2]),
    "check_count": 0,
    "checks": {},
    "failed_checks": ["recovery_verification_blocked"],
}
Path(sys.argv[1]).write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
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
    "recovery_scenarios": int(sys.argv[2]),
    "input_mutation": int(sys.argv[3]),
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
        files.append({
            "path": relative,
            "type": "symlink",
            "mode": f"{stat.S_IMODE(observed.st_mode):04o}",
            "target": os.readlink(path),
        })
    elif path.is_file():
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        files.append({
            "path": relative,
            "type": "regular",
            "mode": f"{stat.S_IMODE(observed.st_mode):04o}",
            "size": observed.st_size,
            "sha256": digest.hexdigest(),
        })
    else:
        raise SystemExit(f"unsupported result entry: {path}")
result = {
    "schema_version": 1,
    "index_kind": "stage3c-phase4-installation-recovery-result-index",
    "file_count": len(files),
    "files": files,
}
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
PY
}

fingerprint_input "$RESULTS_DIR/input-before.json"

set +e
run_local_script \
    "$SCENARIOS" \
    --gate2-results "$INPUT_DIR" \
    --engine "$ENGINE" \
    --work-root "$RECOVERY_WORK" \
    --output-dir "$RESULTS_DIR" \
    --require-pass \
    > "$RESULTS_DIR/scenarios.log" 2>&1
scenario_rc=$?
set -e
cat "$RESULTS_DIR/scenarios.log"

fingerprint_input "$RESULTS_DIR/input-after.json"

set +e
write_mutation_check
mutation_rc=$?
set -e

if [[ $scenario_rc -eq 0 ]]; then
    set +e
    run_local_script \
        "$VERIFIER" \
        --gate2-results "$INPUT_DIR" \
        --scenario-results "$RESULTS_DIR" \
        --work-root "$RECOVERY_WORK" \
        --input-before "$RESULTS_DIR/input-before.json" \
        --input-after "$RESULTS_DIR/input-after.json" \
        --output "$RESULTS_DIR/verification.json" \
        > "$RESULTS_DIR/verifier.log" 2>&1
    verifier_rc=$?
    set -e
else
    verifier_rc=125
    write_blocked_verification "$scenario_rc" > "$RESULTS_DIR/verifier.log" 2>&1
fi
cat "$RESULTS_DIR/verifier.log"

write_workflow_status "$scenario_rc" "$mutation_rc" "$verifier_rc"
write_result_index > "$RESULTS_DIR/result-index.log" 2>&1
cat "$RESULTS_DIR/result-index.log"

printf '\nScenario result:     %s\n' "$RESULTS_DIR/scenario.json"
printf 'Verification:        %s\n' "$RESULTS_DIR/verification.json"
printf 'Result index:        %s\n' "$RESULTS_DIR/result-index.json"
printf 'Input mutation:      %s\n\n' "$RESULTS_DIR/input-mutation-check.txt"

final_rc=0
for rc in "$scenario_rc" "$mutation_rc" "$verifier_rc"; do
    if [[ $rc -ne 0 ]]; then
        final_rc=$rc
        break
    fi
done

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE4_INSTALLATION_RECOVERY=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "INSTALLATION_RECOVERY_ACCEPTED_INPUTS=PASS"
echo "INSTALLATION_RECOVERY_SCENARIOS=55/55 PASS"
echo "INSTALLATION_RECOVERY_VERIFICATION=82/82 PASS"
echo "INSTALLATION_RECOVERY_PREPARED=PASS"
echo "INSTALLATION_RECOVERY_INTENT=PASS"
echo "INSTALLATION_RECOVERY_APPLYING=PASS"
echo "INSTALLATION_RECOVERY_REGISTRY_PRECOMMIT=PASS"
echo "INSTALLATION_RECOVERY_COMMITTED_CLEANUP=PASS"
echo "INSTALLATION_RECOVERY_LOCK_CONTENTION=PASS"
echo "INSTALLATION_RECOVERY_INPUT_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE4_INSTALLATION_RECOVERY=PASS"
