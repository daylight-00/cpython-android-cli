#!/data/data/com.termux/files/usr/bin/bash
# Narrow Phase 4 intervention for recovery-safe repair of missing registered leaves.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

PHASE4_RESULTS="${PHASE4_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase4-integrated-durability}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase4-missing-leaf-repair-intervention}"
WORK_DIR="${WORK_DIR:-$WORK_ROOT/termux/stage3c-phase4-missing-leaf-repair-intervention}"

PYTHON="$CANONICAL_PREFIX/bin/python"
LOCAL_RUNNER="$PROJECT_ROOT/experiments/stage3c-artifact-manifest/run-isolated-local-script.py"
FINGERPRINT="$PROJECT_ROOT/experiments/stage3c-installation-contract/fingerprint-evidence-tree.py"
ENGINE_DIR="$PROJECT_ROOT/experiments/stage3c-installation-recovery"
ENGINE="$ENGINE_DIR/recovery_engine_missing_leaf.py"
SCENARIOS="$SCRIPT_DIR/run-missing-leaf-repair-intervention.py"
VERIFIER="$SCRIPT_DIR/verify-missing-leaf-repair-intervention.py"

INPUT_DIR="$RESULTS_DIR/input/phase4"
CONTRACT_RESULTS="$INPUT_DIR/input/gate5a/input/gate4/input/gate3/input/gate2/input/contract"
MANIFEST="$CONTRACT_RESULTS/input/phase3/input/manifest-schema/manifests/runtime-base.manifest.json"
SCENARIO_RESULTS="$RESULTS_DIR/scenarios"
SCENARIO_WORK="$WORK_DIR/scenarios"

[[ -x "$PYTHON" ]] || { echo "ERROR: canonical Python missing: $PYTHON" >&2; exit 2; }
for file in \
    "$PHASE4_RESULTS/result-index.json" \
    "$LOCAL_RUNNER" \
    "$FINGERPRINT" \
    "$ENGINE_DIR/recovery_common.py" \
    "$ENGINE_DIR/recovery_durability.py" \
    "$ENGINE_DIR/recovery_operations.py" \
    "$ENGINE_DIR/recovery_engine.py" \
    "$ENGINE_DIR/recovery_operations_missing_leaf.py" \
    "$ENGINE" \
    "$SCENARIOS" \
    "$VERIFIER"; do
    [[ -f "$file" ]] || { echo "ERROR: required input or tool missing: $file" >&2; exit 2; }
done

rm -rf "$RESULTS_DIR" "$WORK_DIR"
mkdir -p "$INPUT_DIR" "$SCENARIO_RESULTS" "$SCENARIO_WORK"
cp -a "$PHASE4_RESULTS"/. "$INPUT_DIR"/
[[ -f "$MANIFEST" ]] || { echo "ERROR: manifest missing: $MANIFEST" >&2; exit 2; }

fingerprint_input() {
    "$PYTHON" -I -B -S "$FINGERPRINT" --root "$INPUT_DIR" --output "$1"
}

write_status() {
    "$PYTHON" -I -B -S - "$RESULTS_DIR/workflow-status.json" "$@" <<'PY'
import json, sys
from pathlib import Path
pairs=sys.argv[2:]
rc={pairs[i]:int(pairs[i+1]) for i in range(0,len(pairs),2)}
result={"schema_version":1,"pass":bool(rc) and all(v==0 for v in rc.values()),"returncodes":rc}
Path(sys.argv[1]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True))
PY
}

write_index() {
    "$PYTHON" -I -B -S - "$RESULTS_DIR" "$RESULTS_DIR/result-index.json" <<'PY'
import hashlib,json,os,stat,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve(); files=[]
for path in sorted(root.rglob("*"),key=lambda p:p.relative_to(root).as_posix()):
    if path==output or path.is_dir() or path.name=="result-index.log": continue
    rel=path.relative_to(root).as_posix(); st=path.lstat(); mode=f"{stat.S_IMODE(st.st_mode):04o}"
    if path.is_symlink(): files.append({"path":rel,"type":"symlink","mode":mode,"target":os.readlink(path)})
    elif path.is_file():
        h=hashlib.sha256()
        with path.open("rb") as f:
            for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
        files.append({"path":rel,"type":"regular","mode":mode,"size":st.st_size,"sha256":h.hexdigest()})
    else: raise SystemExit(f"unsupported result entry: {path}")
result={"schema_version":1,"index_kind":"stage3c-phase4-missing-leaf-repair-intervention-result-index","file_count":len(files),"files":files}
output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True))
PY
}

fingerprint_input "$RESULTS_DIR/input-before.json"

set +e
"$PYTHON" -I -B -S "$LOCAL_RUNNER" "$SCENARIOS" \
    --phase4-results "$INPUT_DIR" \
    --contract-results "$CONTRACT_RESULTS" \
    --manifest "$MANIFEST" \
    --local-script-runner "$LOCAL_RUNNER" \
    --engine "$ENGINE" \
    --work-root "$SCENARIO_WORK" \
    --output-dir "$SCENARIO_RESULTS" \
    --require-pass \
    > "$RESULTS_DIR/scenarios.log" 2>&1
scenario_rc=$?
set -e
cat "$RESULTS_DIR/scenarios.log"

fingerprint_input "$RESULTS_DIR/input-after.json"

set +e
"$PYTHON" -I -B -S - "$RESULTS_DIR/input-before.json" "$RESULTS_DIR/input-after.json" "$RESULTS_DIR/input-mutation-check.json" <<'PY'
import json,sys
from pathlib import Path
before=json.loads(Path(sys.argv[1]).read_text()); after=json.loads(Path(sys.argv[2]).read_text())
passed=before.get("pass") is True and after.get("pass") is True and before.get("entry_count")==after.get("entry_count") and before.get("fingerprint")==after.get("fingerprint")
result={"schema_version":1,"pass":passed,"before_entry_count":before.get("entry_count"),"after_entry_count":after.get("entry_count"),"before_fingerprint":before.get("fingerprint"),"after_fingerprint":after.get("fingerprint")}
Path(sys.argv[3]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0 if passed else 83)
PY
mutation_rc=$?
set -e

verifier_rc=125
if [[ $scenario_rc -eq 0 ]]; then
    set +e
    "$PYTHON" -I -B -S "$VERIFIER" \
        --phase4-results "$INPUT_DIR" \
        --results-dir "$SCENARIO_RESULTS" \
        --output "$RESULTS_DIR/verification.json" \
        > "$RESULTS_DIR/verifier.log" 2>&1
    verifier_rc=$?
    set -e
else
    "$PYTHON" -I -B -S - "$RESULTS_DIR/verification.json" "$scenario_rc" <<'PY'
import json,sys
from pathlib import Path
result={"schema_version":1,"pass":False,"blocked":True,"scenario_returncode":int(sys.argv[2]),"check_count":0,"checks":{},"failed_checks":["scenario_gate_blocked"]}
Path(sys.argv[1]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
fi
cat "$RESULTS_DIR/verifier.log" 2>/dev/null || cat "$RESULTS_DIR/verification.json"

write_status scenarios "$scenario_rc" input_mutation "$mutation_rc" verification "$verifier_rc"
write_index > "$RESULTS_DIR/result-index.log" 2>&1
cat "$RESULTS_DIR/result-index.log"

final_rc=0
for rc in "$scenario_rc" "$mutation_rc" "$verifier_rc"; do
    if [[ $rc -ne 0 ]]; then final_rc=$rc; break; fi
done
if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "PHASE4I_EXACT_REINSTALL_NOOP=PASS"
echo "PHASE4I_IN_PLACE_REPAIR_REGRESSION=4/4 PASS"
echo "PHASE4I_MISSING_LEAF_REPAIR=2/2 PASS"
echo "PHASE4I_CRASH_RECOVERY=12/12 PASS"
echo "PHASE4I_INTERVENTION_VERIFICATION=51/51 PASS"
echo "PHASE4I_GATE3A_PRODUCT_ACCEPTANCE=NOT_CLAIMED"
echo "STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION=PASS"
