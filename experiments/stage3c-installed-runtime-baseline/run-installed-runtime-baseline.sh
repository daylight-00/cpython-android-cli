#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 5 Gate 1: installed runtime-base identity and behavior.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

PHASE4_RESULTS="${PHASE4_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase4-integrated-durability}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase5-installed-runtime-baseline}"
WORK_DIR="${WORK_DIR:-$WORK_ROOT/termux/stage3c-phase5-installed-runtime-baseline}"

TOOL_PYTHON="$CANONICAL_PREFIX/bin/python"
LOCAL_SCRIPT_RUNNER="$PROJECT_ROOT/experiments/stage3c-artifact-manifest/run-isolated-local-script.py"
INPUT_FINGERPRINT="$PROJECT_ROOT/experiments/stage3c-installation-contract/fingerprint-evidence-tree.py"
PRODUCT_FINGERPRINT="$PROJECT_ROOT/experiments/stage3c-product-role-inventory/fingerprint-product-tree.py"
ENGINE="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_engine.py"
PROBE="$SCRIPT_DIR/probe-installed-runtime.py"
VERIFIER="$SCRIPT_DIR/verify-installed-runtime-baseline.py"
SMOKE="$PROJECT_ROOT/scripts/test/smoke-termux.sh"
CLOSURE_DIR_TOOLS="$PROJECT_ROOT/experiments/stage3a-runtime-closure"

INPUT_DIR="$RESULTS_DIR/input/phase4"
CONTRACT_RESULTS="$INPUT_DIR/input/gate5a/input/gate4/input/gate3/input/gate2/input/contract"
MANIFEST="$CONTRACT_RESULTS/input/phase3/input/manifest-schema/manifests/runtime-base.manifest.json"
INSTALL_ROOT="$WORK_DIR/installation"
INSTALLED_PREFIX="$INSTALL_ROOT/prefix"
INSTALLED_PYTHON="$INSTALLED_PREFIX/bin/python"
SMOKE_RESULTS="$RESULTS_DIR/smoke"
CLOSURE_RESULTS="$RESULTS_DIR/closure"

[[ -x "$TOOL_PYTHON" ]] || {
    echo "ERROR: canonical tool Python missing: $TOOL_PYTHON" >&2
    exit 2
}

for file in \
    "$PHASE4_RESULTS/result-index.json" \
    "$PHASE4_RESULTS/verification.json" \
    "$PHASE4_RESULTS/workflow-status.json" \
    "$LOCAL_SCRIPT_RUNNER" \
    "$INPUT_FINGERPRINT" \
    "$PRODUCT_FINGERPRINT" \
    "$ENGINE" \
    "$PROBE" \
    "$VERIFIER" \
    "$SMOKE" \
    "$CLOSURE_DIR_TOOLS/inventory-runtime.sh" \
    "$CLOSURE_DIR_TOOLS/analyze-and-probe.sh" \
    "$CLOSURE_DIR_TOOLS/probe-extension-imports.sh"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required input or tool missing: $file" >&2
        exit 2
    }
done

rm -rf "$RESULTS_DIR" "$WORK_DIR"
mkdir -p "$INPUT_DIR" "$RESULTS_DIR" "$WORK_DIR" "$SMOKE_RESULTS" "$CLOSURE_RESULTS"
cp -a "$PHASE4_RESULTS"/. "$INPUT_DIR"/

[[ -f "$MANIFEST" ]] || {
    echo "ERROR: runtime-base manifest missing from Phase 4 evidence: $MANIFEST" >&2
    exit 2
}

run_local_script() {
    "$TOOL_PYTHON" -I -B -S "$LOCAL_SCRIPT_RUNNER" "$@"
}

fingerprint_input() {
    "$TOOL_PYTHON" -I -B -S \
        "$INPUT_FINGERPRINT" \
        --root "$1" \
        --output "$2"
}

fingerprint_product() {
    "$TOOL_PYTHON" -I -B -S \
        "$PRODUCT_FINGERPRINT" \
        --runtime-prefix "$1" \
        --output "$2" \
        --expected-entry-count 714
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
Path(sys.argv[1]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
PY
}

write_closure_status() {
    "$TOOL_PYTHON" -I -B -S - \
        "$CLOSURE_RESULTS/workflow-status.json" \
        "$closure_inventory_rc" "$closure_analysis_rc" "$closure_extension_rc" <<'PY'
import json
import sys
from pathlib import Path

returncodes = {
    "inventory": int(sys.argv[2]),
    "closure_analysis": int(sys.argv[3]),
    "extension_imports": int(sys.argv[4]),
}
result = {
    "schema_version": 1,
    "pass": all(value == 0 for value in returncodes.values()),
    "returncodes": returncodes,
}
Path(sys.argv[1]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
    "index_kind": "stage3c-phase5-installed-runtime-baseline-result-index",
    "file_count": len(files),
    "files": files,
}
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
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

fingerprint_input "$INPUT_DIR" "$RESULTS_DIR/input-before.json"

set +e
run_local_script \
    "$ENGINE" \
    --contract-results "$CONTRACT_RESULTS" \
    --installation-root "$INSTALL_ROOT" \
    --operation install \
    --artifact runtime-base \
    --output "$RESULTS_DIR/install-result.json" \
    > "$RESULTS_DIR/install.log" 2>&1
install_rc=$?
set -e
cat "$RESULTS_DIR/install.log"

engine_verify_rc=125
base_probe_rc=125
smoke_rc=125
venv_probe_rc=125
uv_run_rc=125
closure_inventory_rc=125
closure_analysis_rc=125
closure_extension_rc=125
final_verify_rc=125

if [[ $install_rc -eq 0 && -x "$INSTALLED_PYTHON" ]]; then
    set +e
    run_local_script \
        "$ENGINE" \
        --installation-root "$INSTALL_ROOT" \
        --operation verify \
        --output "$RESULTS_DIR/engine-verification.json" \
        > "$RESULTS_DIR/engine-verification.log" 2>&1
    engine_verify_rc=$?
    set -e
    cat "$RESULTS_DIR/engine-verification.log"
    cp -a "$INSTALL_ROOT/.cpython-android-cli/registry.json" "$RESULTS_DIR/registry.json"
    fingerprint_product "$INSTALLED_PREFIX" "$RESULTS_DIR/installed-before.json"
fi

if [[ $engine_verify_rc -eq 0 ]]; then
    set +e
    "${clean_env[@]}" \
        "$INSTALLED_PYTHON" -I -B -S \
        "$PROBE" \
        --output "$RESULTS_DIR/base-probe.json" \
        --https \
        > "$RESULTS_DIR/base-probe.log" 2>&1
    base_probe_rc=$?
    set -e
    cat "$RESULTS_DIR/base-probe.log"

    set +e
    RUNTIME_ROOT_OVERRIDE="$INSTALL_ROOT" \
    TERMUX_RESULTS_ROOT_OVERRIDE="$SMOKE_RESULTS" \
    bash "$SMOKE" \
        > "$RESULTS_DIR/smoke.log" 2>&1
    smoke_rc=$?
    set -e
    cat "$RESULTS_DIR/smoke.log"
fi

if [[ $smoke_rc -eq 0 ]]; then
    set +e
    "${clean_env[@]}" \
        "$SMOKE_RESULTS/venv/bin/python" -I -B -S \
        "$PROBE" \
        --output "$SMOKE_RESULTS/venv-probe.json" \
        > "$RESULTS_DIR/venv-probe.log" 2>&1
    venv_probe_rc=$?
    set -e
    cat "$RESULTS_DIR/venv-probe.log"

    set +e
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPYCACHEPREFIX="$SMOKE_RESULTS/uv-run-pycache" \
    "${clean_env[@]}" \
        uv run \
        --no-project \
        --no-python-downloads \
        --python "$INSTALLED_PYTHON" \
        --with anyio \
        python "$PROBE" \
        --output "$SMOKE_RESULTS/uv-run-probe.json" \
        --require-anyio \
        > "$RESULTS_DIR/uv-run-probe.log" 2>&1
    uv_run_rc=$?
    set -e
    cat "$RESULTS_DIR/uv-run-probe.log"
fi

if [[ $engine_verify_rc -eq 0 ]]; then
    set +e
    RUNTIME_PREFIX="$INSTALLED_PREFIX" \
    PYTHON_BIN="$INSTALLED_PYTHON" \
    OUTPUT_DIR="$CLOSURE_RESULTS" \
    bash "$CLOSURE_DIR_TOOLS/inventory-runtime.sh" \
        > "$RESULTS_DIR/closure-inventory.log" 2>&1
    closure_inventory_rc=$?
    set -e
    cat "$RESULTS_DIR/closure-inventory.log"
fi

if [[ $closure_inventory_rc -eq 0 ]]; then
    set +e
    RUNTIME_PREFIX="$INSTALLED_PREFIX" \
    PYTHON_BIN="$INSTALLED_PYTHON" \
    RESULTS_DIR="$CLOSURE_RESULTS" \
    bash "$CLOSURE_DIR_TOOLS/analyze-and-probe.sh" \
        > "$RESULTS_DIR/closure-analysis.log" 2>&1
    closure_analysis_rc=$?
    set -e
    cat "$RESULTS_DIR/closure-analysis.log"
fi

if [[ $closure_inventory_rc -eq 0 && $closure_analysis_rc -eq 0 ]]; then
    set +e
    RUNTIME_PREFIX="$INSTALLED_PREFIX" \
    PYTHON_BIN="$INSTALLED_PYTHON" \
    RESULTS_DIR="$CLOSURE_RESULTS" \
    bash "$CLOSURE_DIR_TOOLS/probe-extension-imports.sh" \
        > "$RESULTS_DIR/closure-extension-imports.log" 2>&1
    closure_extension_rc=$?
    set -e
    cat "$RESULTS_DIR/closure-extension-imports.log"
fi

write_closure_status

if [[ -d "$INSTALLED_PREFIX" ]]; then
    fingerprint_product "$INSTALLED_PREFIX" "$RESULTS_DIR/installed-after.json"
fi
fingerprint_input "$INPUT_DIR" "$RESULTS_DIR/input-after.json"

if [[ $install_rc -eq 0 \
    && $engine_verify_rc -eq 0 \
    && $base_probe_rc -eq 0 \
    && $smoke_rc -eq 0 \
    && $venv_probe_rc -eq 0 \
    && $uv_run_rc -eq 0 \
    && $closure_inventory_rc -eq 0 \
    && $closure_analysis_rc -eq 0 \
    && $closure_extension_rc -eq 0 ]]; then
    set +e
    "$TOOL_PYTHON" -I -B -S \
        "$VERIFIER" \
        --phase4-results "$INPUT_DIR" \
        --installed-prefix "$INSTALLED_PREFIX" \
        --manifest "$MANIFEST" \
        --install-result "$RESULTS_DIR/install-result.json" \
        --engine-verification "$RESULTS_DIR/engine-verification.json" \
        --registry "$RESULTS_DIR/registry.json" \
        --installed-before "$RESULTS_DIR/installed-before.json" \
        --installed-after "$RESULTS_DIR/installed-after.json" \
        --input-before "$RESULTS_DIR/input-before.json" \
        --input-after "$RESULTS_DIR/input-after.json" \
        --base-probe "$RESULTS_DIR/base-probe.json" \
        --venv-probe "$SMOKE_RESULTS/venv-probe.json" \
        --uv-run-probe "$SMOKE_RESULTS/uv-run-probe.json" \
        --smoke-log "$RESULTS_DIR/smoke.log" \
        --closure-dir "$CLOSURE_RESULTS" \
        --output "$RESULTS_DIR/verification.json" \
        > "$RESULTS_DIR/verifier.log" 2>&1
    final_verify_rc=$?
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
    "failed_checks": ["component_gate_blocked"],
}
Path(sys.argv[1]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
fi
cat "$RESULTS_DIR/verifier.log" 2>/dev/null || cat "$RESULTS_DIR/verification.json"

write_status \
    install "$install_rc" \
    engine_verify "$engine_verify_rc" \
    base_probe "$base_probe_rc" \
    smoke "$smoke_rc" \
    venv_probe "$venv_probe_rc" \
    uv_run_probe "$uv_run_rc" \
    closure_inventory "$closure_inventory_rc" \
    closure_analysis "$closure_analysis_rc" \
    closure_extension_imports "$closure_extension_rc" \
    final_verification "$final_verify_rc"

write_result_index > "$RESULTS_DIR/result-index.log" 2>&1
cat "$RESULTS_DIR/result-index.log"

final_rc=0
for rc in \
    "$install_rc" "$engine_verify_rc" "$base_probe_rc" "$smoke_rc" \
    "$venv_probe_rc" "$uv_run_rc" "$closure_inventory_rc" \
    "$closure_analysis_rc" "$closure_extension_rc" "$final_verify_rc"; do
    if [[ $rc -ne 0 ]]; then
        final_rc=$rc
        break
    fi
done

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "INSTALLED_RUNTIME_BASELINE_ACCEPTED_INPUTS=PASS"
echo "INSTALLED_RUNTIME_BASELINE_INSTALL=714/714 PASS"
echo "INSTALLED_RUNTIME_BASELINE_REGISTRY=714/714 PASS"
echo "INSTALLED_RUNTIME_BASELINE_SMOKE=PASS"
echo "INSTALLED_RUNTIME_BASELINE_HTTPS=200 PASS"
echo "INSTALLED_RUNTIME_BASELINE_UV_VENV=PASS"
echo "INSTALLED_RUNTIME_BASELINE_UV_RUN=PASS"
echo "INSTALLED_RUNTIME_BASELINE_NATIVE_CLOSURE=81/329/0 PASS"
echo "INSTALLED_RUNTIME_BASELINE_EXTENSION_IMPORTS=67/67 PASS"
echo "INSTALLED_RUNTIME_BASELINE_VERIFICATION=76/76 PASS"
echo "INSTALLED_RUNTIME_BASELINE_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE=PASS"
