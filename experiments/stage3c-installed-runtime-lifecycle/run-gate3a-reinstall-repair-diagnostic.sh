#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 5 Gate 3A diagnostic census:
# exact same-version NOOP, in-place registered repair, and missing-leaf behavior.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

PHASE4_RESULTS="${PHASE4_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase4-integrated-durability}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase5-gate3a-reinstall-repair-diagnostic}"
WORK_DIR="${WORK_DIR:-$WORK_ROOT/termux/stage3c-phase5-gate3a-reinstall-repair-diagnostic}"

TOOL_PYTHON="$CANONICAL_PREFIX/bin/python"
LOCAL_SCRIPT_RUNNER="$PROJECT_ROOT/experiments/stage3c-artifact-manifest/run-isolated-local-script.py"
INPUT_FINGERPRINT="$PROJECT_ROOT/experiments/stage3c-installation-contract/fingerprint-evidence-tree.py"
ENGINE="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_engine.py"
SCENARIO_RUNNER="$SCRIPT_DIR/run-gate3a-reinstall-repair-diagnostic.py"
VERIFIER="$SCRIPT_DIR/verify-gate3a-reinstall-repair-diagnostic.py"

INPUT_DIR="$RESULTS_DIR/input/phase4"
CONTRACT_RESULTS="$INPUT_DIR/input/gate5a/input/gate4/input/gate3/input/gate2/input/contract"
MANIFEST="$CONTRACT_RESULTS/input/phase3/input/manifest-schema/manifests/runtime-base.manifest.json"
DIAGNOSTIC_RESULTS="$RESULTS_DIR/diagnostic"
DIAGNOSTIC_WORK="$WORK_DIR/scenarios"

[[ -x "$TOOL_PYTHON" ]] || {
    echo "ERROR: canonical tool Python missing: $TOOL_PYTHON" >&2
    exit 2
}

for file in \
    "$PHASE4_RESULTS/result-index.json" \
    "$PHASE4_RESULTS/verification.json" \
    "$LOCAL_SCRIPT_RUNNER" \
    "$INPUT_FINGERPRINT" \
    "$ENGINE" \
    "$SCENARIO_RUNNER" \
    "$VERIFIER"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required input or tool missing: $file" >&2
        exit 2
    }
done

rm -rf "$RESULTS_DIR" "$WORK_DIR"
mkdir -p "$INPUT_DIR" "$DIAGNOSTIC_RESULTS" "$DIAGNOSTIC_WORK"
cp -a "$PHASE4_RESULTS"/. "$INPUT_DIR"/

[[ -f "$MANIFEST" ]] || {
    echo "ERROR: runtime-base manifest missing: $MANIFEST" >&2
    exit 2
}

fingerprint_input() {
    "$TOOL_PYTHON" -I -B -S \
        "$INPUT_FINGERPRINT" \
        --root "$1" \
        --output "$2"
}

write_status() {
    "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR/workflow-status.json" "$@" <<'PY'
import json
import sys
from pathlib import Path

pairs = sys.argv[2:]
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

write_result_index() {
    "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR" "$RESULTS_DIR/result-index.json" <<'PY'
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
    "index_kind": "stage3c-phase5-gate3a-reinstall-repair-diagnostic-result-index",
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

fingerprint_input "$INPUT_DIR" "$RESULTS_DIR/input-before.json"

set +e
"$TOOL_PYTHON" -I -B -S \
    "$SCENARIO_RUNNER" \
    --phase4-results "$INPUT_DIR" \
    --contract-results "$CONTRACT_RESULTS" \
    --manifest "$MANIFEST" \
    --local-script-runner "$LOCAL_SCRIPT_RUNNER" \
    --engine "$ENGINE" \
    --work-root "$DIAGNOSTIC_WORK" \
    --output-dir "$DIAGNOSTIC_RESULTS" \
    --require-pass \
    > "$RESULTS_DIR/diagnostic.log" 2>&1
scenario_rc=$?
set -e
cat "$RESULTS_DIR/diagnostic.log"

fingerprint_input "$INPUT_DIR" "$RESULTS_DIR/input-after.json"

verification_rc=125
if [[ $scenario_rc -eq 0 ]]; then
    set +e
    "$TOOL_PYTHON" -I -B -S \
        "$VERIFIER" \
        --phase4-results "$INPUT_DIR" \
        --results-dir "$DIAGNOSTIC_RESULTS" \
        --output "$RESULTS_DIR/verification.json" \
        > "$RESULTS_DIR/verifier.log" 2>&1
    verification_rc=$?
    set -e
else
    "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR/verification.json" <<'PY'
import json
import sys
from pathlib import Path

result = {
    "schema_version": 1,
    "pass": False,
    "blocked": True,
    "check_count": 0,
    "checks": {},
    "failed_checks": ["scenario_gate_blocked"],
}
Path(sys.argv[1]).write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
fi
cat "$RESULTS_DIR/verifier.log" 2>/dev/null || cat "$RESULTS_DIR/verification.json"

input_mutation_rc=0
set +e
"$TOOL_PYTHON" -I -B -S - \
    "$RESULTS_DIR/input-before.json" \
    "$RESULTS_DIR/input-after.json" \
    "$RESULTS_DIR/input-mutation-check.json" <<'PY'
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
result = {
    "schema_version": 1,
    "pass": passed,
    "before_entry_count": before.get("entry_count"),
    "after_entry_count": after.get("entry_count"),
    "before_fingerprint": before.get("fingerprint"),
    "after_fingerprint": after.get("fingerprint"),
}
Path(sys.argv[3]).write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if passed else 73)
PY
input_mutation_rc=$?
set -e

write_status \
    diagnostic "$scenario_rc" \
    verification "$verification_rc" \
    input_mutation "$input_mutation_rc"

write_result_index > "$RESULTS_DIR/result-index.log" 2>&1
cat "$RESULTS_DIR/result-index.log"

final_rc=0
for rc in "$scenario_rc" "$verification_rc" "$input_mutation_rc"; do
    if [[ $rc -ne 0 ]]; then
        final_rc=$rc
        break
    fi
done

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "GATE3A_EXACT_REINSTALL_NOOP=714/714 PASS"
echo "GATE3A_IN_PLACE_REPAIRS=4/4 CLASSIFIED"
echo "GATE3A_MISSING_LEAF_REPAIR=2/2 UNSUPPORTED_CLASSIFIED"
echo "GATE3A_RECOVERY_RESIDUE=2/2 CLASSIFIED"
echo "GATE3A_DIAGNOSTIC_VERIFICATION=31/31 PASS"
echo "GATE3A_PRODUCT_ACCEPTANCE=NOT_CLAIMED"
echo "STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC=PASS"
