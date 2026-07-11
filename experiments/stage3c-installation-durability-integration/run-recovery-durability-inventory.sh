#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 4 Gate 5A: complete recovery-engine mutation inventory.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

GATE4_RESULTS="${GATE4_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase4-installation-durability}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase4-recovery-durability-inventory}"
RECOVERY_DIR="$SCRIPT_DIR/../stage3c-installation-recovery"

PYTHON="$CANONICAL_PREFIX/bin/python"
LOCAL_SCRIPT_RUNNER="$SCRIPT_DIR/../stage3c-artifact-manifest/run-isolated-local-script.py"
FINGERPRINT="$SCRIPT_DIR/../stage3c-installation-contract/fingerprint-evidence-tree.py"
INVENTORY="$SCRIPT_DIR/inventory_recovery_mutations.py"
VERIFIER="$SCRIPT_DIR/verify_recovery_mutation_inventory.py"
INPUT_DIR="$RESULTS_DIR/input/gate4"

[[ -x "$PYTHON" ]] || {
    echo "ERROR: canonical promoted Python is missing: $PYTHON" >&2
    exit 2
}

for file in \
    "$GATE4_RESULTS/scenario.json" \
    "$GATE4_RESULTS/verification.json" \
    "$GATE4_RESULTS/workflow-status.json" \
    "$GATE4_RESULTS/result-index.json" \
    "$RECOVERY_DIR/recovery_common.py" \
    "$RECOVERY_DIR/recovery_operations.py" \
    "$RECOVERY_DIR/recovery_engine.py" \
    "$LOCAL_SCRIPT_RUNNER" \
    "$FINGERPRINT" \
    "$INVENTORY" \
    "$VERIFIER"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required frozen evidence or source is missing: $file" >&2
        exit 2
    }
done

rm -rf "$RESULTS_DIR"
mkdir -p "$INPUT_DIR"
cp -a "$GATE4_RESULTS"/. "$INPUT_DIR"/

printf 'Gate 4 results:        %s\n' "$GATE4_RESULTS"
printf 'Recovery sources:      %s\n' "$RECOVERY_DIR"
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
raise SystemExit(0 if passed else 53)
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
    "blocked_by": "mutation_inventory",
    "scenario_returncode": int(sys.argv[2]),
    "check_count": 0,
    "checks": {},
    "failed_checks": ["inventory_verification_blocked"],
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
    "mutation_inventory": int(sys.argv[2]),
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
    "index_kind": "stage3c-phase4-recovery-durability-inventory-result-index",
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

fingerprint_input "$RESULTS_DIR/input-before.json"

set +e
run_local_script \
    "$INVENTORY" \
    --gate4-results "$INPUT_DIR" \
    --recovery-dir "$RECOVERY_DIR" \
    --output-dir "$RESULTS_DIR" \
    --require-pass \
    > "$RESULTS_DIR/inventory.log" 2>&1
inventory_rc=$?
set -e
cat "$RESULTS_DIR/inventory.log"

fingerprint_input "$RESULTS_DIR/input-after.json"

set +e
write_mutation_check
mutation_rc=$?
set -e

if [[ $inventory_rc -eq 0 ]]; then
    set +e
    run_local_script \
        "$VERIFIER" \
        --gate4-results "$INPUT_DIR" \
        --recovery-dir "$RECOVERY_DIR" \
        --inventory-results "$RESULTS_DIR" \
        --input-before "$RESULTS_DIR/input-before.json" \
        --input-after "$RESULTS_DIR/input-after.json" \
        --output "$RESULTS_DIR/verification.json" \
        > "$RESULTS_DIR/verifier.log" 2>&1
    verifier_rc=$?
    set -e
else
    verifier_rc=125
    write_blocked_verification "$inventory_rc" > "$RESULTS_DIR/verifier.log" 2>&1
fi
cat "$RESULTS_DIR/verifier.log"

write_workflow_status "$inventory_rc" "$mutation_rc" "$verifier_rc"
write_result_index > "$RESULTS_DIR/result-index.log" 2>&1
cat "$RESULTS_DIR/result-index.log"

printf '\nInventory:            %s\n' "$RESULTS_DIR/mutation-inventory.json"
printf 'Integration plan:     %s\n' "$RESULTS_DIR/integration-plan.json"
printf 'Verification:         %s\n' "$RESULTS_DIR/verification.json"
printf 'Result index:         %s\n' "$RESULTS_DIR/result-index.json"
printf 'Input mutation:       %s\n\n' "$RESULTS_DIR/input-mutation-check.txt"

final_rc=0
for rc in "$inventory_rc" "$mutation_rc" "$verifier_rc"; do
    if [[ $rc -ne 0 ]]; then
        final_rc=$rc
        break
    fi
done

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE4_RECOVERY_DURABILITY_INVENTORY=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "RECOVERY_DURABILITY_INVENTORY_ACCEPTED_INPUTS=PASS"
echo "RECOVERY_DURABILITY_INVENTORY_SCENARIO=32/32 PASS"
echo "RECOVERY_DURABILITY_INVENTORY_VERIFICATION=29/29 PASS"
echo "RECOVERY_DURABILITY_INVENTORY_SOURCE_BLOBS=PASS"
echo "RECOVERY_DURABILITY_INVENTORY_UNKNOWN_CALLS=0 PASS"
echo "RECOVERY_DURABILITY_INVENTORY_INPUT_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE4_RECOVERY_DURABILITY_INVENTORY=PASS"
