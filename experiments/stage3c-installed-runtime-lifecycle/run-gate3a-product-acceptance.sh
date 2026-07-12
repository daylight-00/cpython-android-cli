#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 5 Gate 3A: corrected reinstall and repair product acceptance.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

PHASE4_RESULTS="${PHASE4_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase4-integrated-durability}"
PHASE4I_RESULTS="${PHASE4I_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase4-missing-leaf-repair-intervention}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase5-gate3a-reinstall-repair-acceptance}"
WORK_DIR="${WORK_DIR:-$WORK_ROOT/termux/stage3c-phase5-gate3a-reinstall-repair-acceptance}"

TOOL_PYTHON="$CANONICAL_PREFIX/bin/python"
LOCAL_RUNNER="$PROJECT_ROOT/experiments/stage3c-artifact-manifest/run-isolated-local-script.py"
INPUT_FINGERPRINT="$PROJECT_ROOT/experiments/stage3c-installation-contract/fingerprint-evidence-tree.py"
STRICT_FINGERPRINT="$PROJECT_ROOT/experiments/stage3c-product-role-inventory/fingerprint-product-tree.py"
PORTABLE_FINGERPRINT="$PROJECT_ROOT/experiments/stage3c-installed-runtime-baseline/fingerprint-installed-payload.py"
ENGINE="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_engine_missing_leaf.py"
PROBE="$PROJECT_ROOT/experiments/stage3c-installed-runtime-baseline/probe-installed-runtime.py"
GATE1_VERIFIER="$PROJECT_ROOT/experiments/stage3c-installed-runtime-baseline/verify-installed-runtime-baseline.py"
SCENARIO_RUNNER="$SCRIPT_DIR/run-gate3a-product-acceptance.py"
VERIFIER="$SCRIPT_DIR/verify-gate3a-product-acceptance.py"
SMOKE="$PROJECT_ROOT/scripts/test/smoke-termux.sh"
CLOSURE_TOOLS="$PROJECT_ROOT/experiments/stage3a-runtime-closure"

INPUT_DIR="$RESULTS_DIR/input"
PHASE4_INPUT="$INPUT_DIR/phase4"
PHASE4I_INPUT="$INPUT_DIR/phase4i"
CONTRACT_RESULTS="$PHASE4_INPUT/input/gate5a/input/gate4/input/gate3/input/gate2/input/contract"
MANIFEST="$CONTRACT_RESULTS/input/phase3/input/manifest-schema/manifests/runtime-base.manifest.json"
SCENARIO_RESULTS="$RESULTS_DIR/repair-scenarios"
SCENARIO_WORK="$WORK_DIR/scenarios"
SEQUENTIAL_ROOT="$SCENARIO_WORK/sequential"
INSTALLED_PREFIX="$SEQUENTIAL_ROOT/prefix"
INSTALLED_PYTHON="$INSTALLED_PREFIX/bin/python"
RUNTIME_RESULTS="$RESULTS_DIR/runtime"
SMOKE_RESULTS="$RUNTIME_RESULTS/smoke"
CLOSURE_RESULTS="$RUNTIME_RESULTS/closure"

[[ -x "$TOOL_PYTHON" ]] || { echo "ERROR: canonical tool Python missing: $TOOL_PYTHON" >&2; exit 2; }
for file in \
    "$PHASE4_RESULTS/result-index.json" \
    "$PHASE4I_RESULTS/result-index.json" \
    "$LOCAL_RUNNER" \
    "$INPUT_FINGERPRINT" \
    "$STRICT_FINGERPRINT" \
    "$PORTABLE_FINGERPRINT" \
    "$ENGINE" \
    "$PROBE" \
    "$GATE1_VERIFIER" \
    "$SCENARIO_RUNNER" \
    "$VERIFIER" \
    "$SMOKE" \
    "$CLOSURE_TOOLS/inventory-runtime.sh" \
    "$CLOSURE_TOOLS/analyze-and-probe.sh" \
    "$CLOSURE_TOOLS/probe-extension-imports.sh"; do
    [[ -f "$file" ]] || { echo "ERROR: required input or tool missing: $file" >&2; exit 2; }
done

rm -rf "$RESULTS_DIR" "$WORK_DIR"
mkdir -p "$PHASE4_INPUT" "$PHASE4I_INPUT" "$SCENARIO_RESULTS" "$SCENARIO_WORK" "$RUNTIME_RESULTS" "$SMOKE_RESULTS" "$CLOSURE_RESULTS"
cp -a "$PHASE4_RESULTS"/. "$PHASE4_INPUT"/
cp -a "$PHASE4I_RESULTS"/. "$PHASE4I_INPUT"/
[[ -f "$MANIFEST" ]] || { echo "ERROR: runtime-base manifest missing: $MANIFEST" >&2; exit 2; }

run_local() {
    "$TOOL_PYTHON" -I -B -S "$LOCAL_RUNNER" "$@"
}

fingerprint_input() {
    "$TOOL_PYTHON" -I -B -S "$INPUT_FINGERPRINT" --root "$INPUT_DIR" --output "$1"
}

fingerprint_strict() {
    "$TOOL_PYTHON" -I -B -S "$STRICT_FINGERPRINT" --runtime-prefix "$INSTALLED_PREFIX" --output "$1" --expected-entry-count 714
}

fingerprint_portable() {
    "$TOOL_PYTHON" -I -B -S "$PORTABLE_FINGERPRINT" --installed-prefix "$INSTALLED_PREFIX" --output "$1"
}

write_closure_status() {
    "$TOOL_PYTHON" -I -B -S - "$CLOSURE_RESULTS/workflow-status.json" "$closure_inventory_rc" "$closure_analysis_rc" "$closure_extension_rc" <<'PY'
import json, sys
from pathlib import Path
rc={"inventory":int(sys.argv[2]),"closure_analysis":int(sys.argv[3]),"extension_imports":int(sys.argv[4])}
result={"schema_version":1,"pass":all(v==0 for v in rc.values()),"returncodes":rc}
Path(sys.argv[1]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True))
PY
}

write_status() {
    "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR/workflow-status.json" "$@" <<'PY'
import json,sys
from pathlib import Path
pairs=sys.argv[2:]
rc={pairs[i]:int(pairs[i+1]) for i in range(0,len(pairs),2)}
result={"schema_version":1,"pass":bool(rc) and all(v==0 for v in rc.values()),"returncodes":rc}
Path(sys.argv[1]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True))
PY
}

write_index() {
    "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR" "$RESULTS_DIR/result-index.json" <<'PY'
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
result={"schema_version":1,"index_kind":"stage3c-phase5-gate3a-product-acceptance-result-index","file_count":len(files),"files":files}
output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True))
PY
}

clean_env=(
    env
    -u PYTHONHOME
    -u PYTHONPATH
    -u CPYTHON_HOME
    -u LD_LIBRARY_PATH
    -u SSL_CERT_FILE
    -u SSL_CERT_DIR
    -u VIRTUAL_ENV
    -u UV_PYTHON
    PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
    HOME="$HOME"
    PATH="${PREFIX:-/data/data/com.termux/files/usr}/bin:/system/bin"
    TMPDIR="${PREFIX:-/data/data/com.termux/files/usr}/tmp"
    TERM="${TERM:-xterm-256color}"
)

fingerprint_input "$RESULTS_DIR/input-before.json"

scenario_rc=125
engine_verify_rc=125
base_probe_rc=125
smoke_rc=125
venv_probe_rc=125
uv_run_rc=125
closure_inventory_rc=125
closure_analysis_rc=125
closure_extension_rc=125
gate1_verify_rc=125
acceptance_verify_rc=125
input_mutation_rc=125

set +e
run_local "$SCENARIO_RUNNER" \
    --phase4-results "$PHASE4_INPUT" \
    --phase4i-results "$PHASE4I_INPUT" \
    --contract-results "$CONTRACT_RESULTS" \
    --manifest "$MANIFEST" \
    --local-script-runner "$LOCAL_RUNNER" \
    --engine "$ENGINE" \
    --strict-fingerprint "$STRICT_FINGERPRINT" \
    --portable-fingerprint "$PORTABLE_FINGERPRINT" \
    --work-root "$SCENARIO_WORK" \
    --output-dir "$SCENARIO_RESULTS" \
    --require-pass \
    > "$RESULTS_DIR/repair-scenarios.log" 2>&1
scenario_rc=$?
set -e
cat "$RESULTS_DIR/repair-scenarios.log"

if [[ $scenario_rc -eq 0 && -x "$INSTALLED_PYTHON" ]]; then
    set +e
    run_local "$ENGINE" --installation-root "$SEQUENTIAL_ROOT" --operation verify --output "$RUNTIME_RESULTS/engine-verification.json" > "$RUNTIME_RESULTS/engine-verification.log" 2>&1
    engine_verify_rc=$?
    set -e
    cat "$RUNTIME_RESULTS/engine-verification.log"
    cp -a "$SEQUENTIAL_ROOT/.cpython-android-cli/registry.json" "$RUNTIME_RESULTS/registry.json"
    fingerprint_strict "$RUNTIME_RESULTS/installed-before.json"
    fingerprint_portable "$RUNTIME_RESULTS/installed-portable-before.json"
fi

if [[ $engine_verify_rc -eq 0 ]]; then
    set +e
    "${clean_env[@]}" "$INSTALLED_PYTHON" -I -B -S "$PROBE" --output "$RUNTIME_RESULTS/base-probe.json" --https > "$RUNTIME_RESULTS/base-probe.log" 2>&1
    base_probe_rc=$?
    set -e
    cat "$RUNTIME_RESULTS/base-probe.log"

    set +e
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPYCACHEPREFIX="$SMOKE_RESULTS/pycache" \
    RUNTIME_ROOT_OVERRIDE="$SEQUENTIAL_ROOT" \
    TERMUX_RESULTS_ROOT_OVERRIDE="$SMOKE_RESULTS" \
    bash "$SMOKE" > "$RUNTIME_RESULTS/smoke.log" 2>&1
    smoke_rc=$?
    set -e
    cat "$RUNTIME_RESULTS/smoke.log"
fi

if [[ $smoke_rc -eq 0 ]]; then
    set +e
    "${clean_env[@]}" "$SMOKE_RESULTS/venv/bin/python" -I -B -S "$PROBE" --output "$SMOKE_RESULTS/venv-probe.json" > "$RUNTIME_RESULTS/venv-probe.log" 2>&1
    venv_probe_rc=$?
    set -e
    cat "$RUNTIME_RESULTS/venv-probe.log"

    set +e
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPYCACHEPREFIX="$SMOKE_RESULTS/uv-run-pycache" \
    "${clean_env[@]}" uv run --no-project --no-python-downloads --python "$INSTALLED_PYTHON" --with anyio python "$PROBE" --output "$SMOKE_RESULTS/uv-run-probe.json" --require-anyio > "$RUNTIME_RESULTS/uv-run-probe.log" 2>&1
    uv_run_rc=$?
    set -e
    cat "$RUNTIME_RESULTS/uv-run-probe.log"
fi

rm -rf "$SMOKE_RESULTS/venv" "$SMOKE_RESULTS/pycache" "$SMOKE_RESULTS/uv-run-pycache"

if [[ $engine_verify_rc -eq 0 ]]; then
    set +e
    RUNTIME_PREFIX="$INSTALLED_PREFIX" PYTHON_BIN="$INSTALLED_PYTHON" OUTPUT_DIR="$CLOSURE_RESULTS" bash "$CLOSURE_TOOLS/inventory-runtime.sh" > "$RUNTIME_RESULTS/closure-inventory.log" 2>&1
    closure_inventory_rc=$?
    set -e
    cat "$RUNTIME_RESULTS/closure-inventory.log"
fi

if [[ $closure_inventory_rc -eq 0 ]]; then
    set +e
    RUNTIME_PREFIX="$INSTALLED_PREFIX" PYTHON_BIN="$INSTALLED_PYTHON" RESULTS_DIR="$CLOSURE_RESULTS" bash "$CLOSURE_TOOLS/analyze-and-probe.sh" > "$RUNTIME_RESULTS/closure-analysis.log" 2>&1
    closure_analysis_rc=$?
    set -e
    cat "$RUNTIME_RESULTS/closure-analysis.log"
fi

if [[ $closure_inventory_rc -eq 0 && $closure_analysis_rc -eq 0 ]]; then
    set +e
    RUNTIME_PREFIX="$INSTALLED_PREFIX" PYTHON_BIN="$INSTALLED_PYTHON" RESULTS_DIR="$CLOSURE_RESULTS" bash "$CLOSURE_TOOLS/probe-extension-imports.sh" > "$RUNTIME_RESULTS/closure-extension-imports.log" 2>&1
    closure_extension_rc=$?
    set -e
    cat "$RUNTIME_RESULTS/closure-extension-imports.log"
fi
write_closure_status

if [[ -d "$INSTALLED_PREFIX" ]]; then
    fingerprint_strict "$RUNTIME_RESULTS/installed-after.json"
    fingerprint_portable "$RUNTIME_RESULTS/installed-portable-after.json"
fi
fingerprint_input "$RESULTS_DIR/input-after.json"

set +e
"$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR/input-before.json" "$RESULTS_DIR/input-after.json" "$RESULTS_DIR/input-mutation-check.json" <<'PY'
import json,sys
from pathlib import Path
before=json.loads(Path(sys.argv[1]).read_text()); after=json.loads(Path(sys.argv[2]).read_text())
passed=before.get("pass") is True and after.get("pass") is True and before.get("entry_count")==after.get("entry_count") and before.get("fingerprint")==after.get("fingerprint")
result={"schema_version":1,"pass":passed,"before_entry_count":before.get("entry_count"),"after_entry_count":after.get("entry_count"),"before_fingerprint":before.get("fingerprint"),"after_fingerprint":after.get("fingerprint")}
Path(sys.argv[3]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0 if passed else 94)
PY
input_mutation_rc=$?
set -e

if [[ $scenario_rc -eq 0 && $engine_verify_rc -eq 0 && $base_probe_rc -eq 0 && $smoke_rc -eq 0 && $venv_probe_rc -eq 0 && $uv_run_rc -eq 0 && $closure_inventory_rc -eq 0 && $closure_analysis_rc -eq 0 && $closure_extension_rc -eq 0 && $input_mutation_rc -eq 0 ]]; then
    set +e
    "$TOOL_PYTHON" -I -B -S "$GATE1_VERIFIER" \
        --phase4-results "$PHASE4_INPUT" \
        --installed-prefix "$INSTALLED_PREFIX" \
        --manifest "$MANIFEST" \
        --install-result "$SCENARIO_RESULTS/sequential/install.json" \
        --engine-verification "$RUNTIME_RESULTS/engine-verification.json" \
        --registry "$RUNTIME_RESULTS/registry.json" \
        --installed-before "$RUNTIME_RESULTS/installed-before.json" \
        --installed-after "$RUNTIME_RESULTS/installed-after.json" \
        --installed-portable-before "$RUNTIME_RESULTS/installed-portable-before.json" \
        --installed-portable-after "$RUNTIME_RESULTS/installed-portable-after.json" \
        --input-before "$RESULTS_DIR/input-before.json" \
        --input-after "$RESULTS_DIR/input-after.json" \
        --base-probe "$RUNTIME_RESULTS/base-probe.json" \
        --venv-probe "$SMOKE_RESULTS/venv-probe.json" \
        --uv-run-probe "$SMOKE_RESULTS/uv-run-probe.json" \
        --smoke-log "$RUNTIME_RESULTS/smoke.log" \
        --closure-dir "$CLOSURE_RESULTS" \
        --output "$RESULTS_DIR/gate1-regression-verification.json" \
        > "$RESULTS_DIR/gate1-regression-verifier.log" 2>&1
    gate1_verify_rc=$?
    set -e
else
    "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR/gate1-regression-verification.json" <<'PY'
import json
from pathlib import Path
result={"schema_version":1,"pass":False,"blocked":True,"check_count":0,"checks":{},"failed_checks":["component_gate_blocked"]}
Path(__import__('sys').argv[1]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
fi
cat "$RESULTS_DIR/gate1-regression-verifier.log" 2>/dev/null || cat "$RESULTS_DIR/gate1-regression-verification.json"

if [[ $gate1_verify_rc -eq 0 ]]; then
    set +e
    "$TOOL_PYTHON" -I -B -S "$VERIFIER" \
        --phase4-results "$PHASE4_INPUT" \
        --phase4i-results "$PHASE4I_INPUT" \
        --scenario-results "$SCENARIO_RESULTS" \
        --runtime-results "$RUNTIME_RESULTS" \
        --gate1-verification "$RESULTS_DIR/gate1-regression-verification.json" \
        --input-before "$RESULTS_DIR/input-before.json" \
        --input-after "$RESULTS_DIR/input-after.json" \
        --output "$RESULTS_DIR/verification.json" \
        > "$RESULTS_DIR/verifier.log" 2>&1
    acceptance_verify_rc=$?
    set -e
else
    "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR/verification.json" <<'PY'
import json
from pathlib import Path
result={"schema_version":1,"pass":False,"blocked":True,"check_count":0,"checks":{},"failed_checks":["gate1_regression_blocked"]}
Path(__import__('sys').argv[1]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
fi
cat "$RESULTS_DIR/verifier.log" 2>/dev/null || cat "$RESULTS_DIR/verification.json"

write_status \
    repair_scenarios "$scenario_rc" \
    engine_verify "$engine_verify_rc" \
    base_probe "$base_probe_rc" \
    smoke "$smoke_rc" \
    venv_probe "$venv_probe_rc" \
    uv_run "$uv_run_rc" \
    closure_inventory "$closure_inventory_rc" \
    closure_analysis "$closure_analysis_rc" \
    closure_extension "$closure_extension_rc" \
    input_mutation "$input_mutation_rc" \
    gate1_regression "$gate1_verify_rc" \
    acceptance_verification "$acceptance_verify_rc"

write_index > "$RESULTS_DIR/result-index.log" 2>&1
cat "$RESULTS_DIR/result-index.log"

final_rc=0
for rc in "$scenario_rc" "$engine_verify_rc" "$base_probe_rc" "$smoke_rc" "$venv_probe_rc" "$uv_run_rc" "$closure_inventory_rc" "$closure_analysis_rc" "$closure_extension_rc" "$input_mutation_rc" "$gate1_verify_rc" "$acceptance_verify_rc"; do
    if [[ $rc -ne 0 ]]; then final_rc=$rc; break; fi
done
if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_ACCEPTANCE=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "GATE3A_ACCEPTANCE_EXACT_REINSTALL_NOOP=PASS"
echo "GATE3A_ACCEPTANCE_ISOLATED_REPAIRS=6/6 PASS"
echo "GATE3A_ACCEPTANCE_SEQUENTIAL_REPAIRS=6/6 PASS"
echo "GATE3A_ACCEPTANCE_REGISTRY_AND_PAYLOAD=PASS"
echo "GATE3A_ACCEPTANCE_HTTPS=200 PASS"
echo "GATE3A_ACCEPTANCE_UV_VENV=PASS"
echo "GATE3A_ACCEPTANCE_UV_RUN=PASS"
echo "GATE3A_ACCEPTANCE_NATIVE_CLOSURE=81/329/0 PASS"
echo "GATE3A_ACCEPTANCE_EXTENSION_IMPORTS=67/67 PASS"
echo "GATE3A_ACCEPTANCE_GATE1_REGRESSION=80/80 PASS"
echo "GATE3A_ACCEPTANCE_VERIFICATION=69/69 PASS"
echo "STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_ACCEPTANCE=PASS"
