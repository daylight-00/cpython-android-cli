#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 5 Gate 2: relocate a complete installed runtime root and revalidate it.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

PHASE4_RESULTS="${PHASE4_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase4-integrated-durability}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase5-installed-runtime-relocation}"
WORK_DIR="${WORK_DIR:-$WORK_ROOT/termux/stage3c-phase5-installed-runtime-relocation}"

TOOL_PYTHON="$CANONICAL_PREFIX/bin/python"
LOCAL_SCRIPT_RUNNER="$PROJECT_ROOT/experiments/stage3c-artifact-manifest/run-isolated-local-script.py"
BASELINE_RUNNER="$PROJECT_ROOT/experiments/stage3c-installed-runtime-baseline/run-installed-runtime-baseline.sh"
BASELINE_VERIFIER="$PROJECT_ROOT/experiments/stage3c-installed-runtime-baseline/verify-installed-runtime-baseline.py"
INPUT_FINGERPRINT="$PROJECT_ROOT/experiments/stage3c-installation-contract/fingerprint-evidence-tree.py"
PRODUCT_FINGERPRINT="$PROJECT_ROOT/experiments/stage3c-product-role-inventory/fingerprint-product-tree.py"
PORTABLE_FINGERPRINT="$PROJECT_ROOT/experiments/stage3c-installed-runtime-baseline/fingerprint-installed-payload.py"
ENGINE="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_engine.py"
PROBE="$PROJECT_ROOT/experiments/stage3c-installed-runtime-baseline/probe-installed-runtime.py"
VERIFIER="$SCRIPT_DIR/verify-installed-runtime-relocation.py"
SMOKE="$PROJECT_ROOT/scripts/test/smoke-termux.sh"
CLOSURE_DIR_TOOLS="$PROJECT_ROOT/experiments/stage3a-runtime-closure"

BASELINE_RESULTS="$RESULTS_DIR/baseline"
BASELINE_WORK="$WORK_DIR/baseline"
A_INSTALL_ROOT="$BASELINE_WORK/installation"
A_PREFIX="$A_INSTALL_ROOT/prefix"
B_INSTALL_ROOT="$WORK_DIR/relocated/location-b/installation"
B_PREFIX="$B_INSTALL_ROOT/prefix"
RELOCATED_RESULTS="$RESULTS_DIR/relocated"
SMOKE_RESULTS="$RELOCATED_RESULTS/smoke"
CLOSURE_RESULTS="$RELOCATED_RESULTS/closure"
CONTRACT_RESULTS="$BASELINE_RESULTS/input/phase4/input/gate5a/input/gate4/input/gate3/input/gate2/input/contract"
MANIFEST="$CONTRACT_RESULTS/input/phase3/input/manifest-schema/manifests/runtime-base.manifest.json"

[[ -x "$TOOL_PYTHON" ]] || {
    echo "ERROR: canonical tool Python missing: $TOOL_PYTHON" >&2
    exit 2
}

for file in \
    "$BASELINE_RUNNER" \
    "$BASELINE_VERIFIER" \
    "$LOCAL_SCRIPT_RUNNER" \
    "$INPUT_FINGERPRINT" \
    "$PRODUCT_FINGERPRINT" \
    "$PORTABLE_FINGERPRINT" \
    "$ENGINE" \
    "$PROBE" \
    "$VERIFIER" \
    "$SMOKE" \
    "$CLOSURE_DIR_TOOLS/inventory-runtime.sh" \
    "$CLOSURE_DIR_TOOLS/analyze-and-probe.sh" \
    "$CLOSURE_DIR_TOOLS/probe-extension-imports.sh"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required tool missing: $file" >&2
        exit 2
    }
done

rm -rf "$RESULTS_DIR" "$WORK_DIR"
mkdir -p "$RESULTS_DIR" "$WORK_DIR" "$RELOCATED_RESULTS" "$SMOKE_RESULTS" "$CLOSURE_RESULTS"

run_local_script() {
    "$TOOL_PYTHON" -I -B -S "$LOCAL_SCRIPT_RUNNER" "$@"
}

fingerprint_product() {
    "$TOOL_PYTHON" -I -B -S \
        "$PRODUCT_FINGERPRINT" \
        --runtime-prefix "$1" \
        --output "$2" \
        --expected-entry-count 714
}

fingerprint_portable() {
    "$TOOL_PYTHON" -I -B -S \
        "$PORTABLE_FINGERPRINT" \
        --installed-prefix "$1" \
        --output "$2"
}

fingerprint_root() {
    "$TOOL_PYTHON" -I -B -S \
        "$INPUT_FINGERPRINT" \
        --root "$1" \
        --output "$2"
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

write_status() {
    "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR/workflow-status.json" "$@" <<'PY'
import json
import sys
from pathlib import Path

pairs = sys.argv[2:]
if len(pairs) % 2:
    raise SystemExit("status arguments must be key/value pairs")
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
    "index_kind": "stage3c-phase5-installed-runtime-relocation-result-index",
    "file_count": len(files),
    "files": files,
}
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
PY
}

write_blocked_verification() {
    local failed_check="$1"
    "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR/verification.json" "$failed_check" <<'PY'
import json
import sys
from pathlib import Path

result = {
    "schema_version": 1,
    "pass": False,
    "blocked": True,
    "check_count": 0,
    "checks": {},
    "failed_checks": [sys.argv[2]],
}
Path(sys.argv[1]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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

baseline_rc=125
move_rc=125
engine_verify_rc=125
base_probe_rc=125
smoke_rc=125
venv_probe_rc=125
uv_run_rc=125
closure_inventory_rc=125
closure_analysis_rc=125
closure_extension_rc=125
stale_scan_rc=125
relocated_baseline_verify_rc=125
final_verify_rc=125

set +e
PHASE4_RESULTS="$PHASE4_RESULTS" \
CANONICAL_PREFIX="$CANONICAL_PREFIX" \
RESULTS_DIR="$BASELINE_RESULTS" \
WORK_DIR="$BASELINE_WORK" \
bash "$BASELINE_RUNNER" \
    > "$RESULTS_DIR/baseline.log" 2>&1
baseline_rc=$?
set -e
cat "$RESULTS_DIR/baseline.log"

if [[ $baseline_rc -eq 0 ]]; then
    for path in "$A_PREFIX/bin/python" "$BASELINE_RESULTS/verification.json" "$MANIFEST"; do
        [[ -e "$path" ]] || {
            echo "ERROR: Gate 1 prerequisite output missing: $path" >&2
            baseline_rc=2
        }
    done
fi

if [[ $baseline_rc -eq 0 ]]; then
    fingerprint_product "$A_PREFIX" "$RESULTS_DIR/a-installed-strict.json"
    fingerprint_portable "$A_PREFIX" "$RESULTS_DIR/a-installed-portable.json"
    fingerprint_root "$A_INSTALL_ROOT" "$RESULTS_DIR/a-installation-root.json"
    cp -a "$A_INSTALL_ROOT/.cpython-android-cli/registry.json" "$RESULTS_DIR/a-registry.json"

    a_device="$(stat -c %d "$A_INSTALL_ROOT")"
    a_inode="$(stat -c %i "$A_INSTALL_ROOT")"
    mkdir -p "$(dirname "$B_INSTALL_ROOT")"
    target_device="$(stat -c %d "$(dirname "$B_INSTALL_ROOT")")"

    set +e
    mv "$A_INSTALL_ROOT" "$B_INSTALL_ROOT"
    move_rc=$?
    set -e

    if [[ $move_rc -eq 0 ]]; then
        b_device="$(stat -c %d "$B_INSTALL_ROOT")"
        b_inode="$(stat -c %i "$B_INSTALL_ROOT")"
        set +e
        "$TOOL_PYTHON" -I -B -S - \
            "$RESULTS_DIR/relocation-state.json" \
            "$A_INSTALL_ROOT" "$B_INSTALL_ROOT" \
            "$a_device" "$target_device" "$b_device" \
            "$a_inode" "$b_inode" <<'PY'
import json
import sys
from pathlib import Path

output = Path(sys.argv[1]).resolve()
a_root = Path(sys.argv[2]).resolve()
b_root = Path(sys.argv[3]).resolve()
a_device = int(sys.argv[4])
target_device = int(sys.argv[5])
b_device = int(sys.argv[6])
a_inode = int(sys.argv[7])
b_inode = int(sys.argv[8])
result = {
    "schema_version": 1,
    "a_installation_root": str(a_root),
    "b_installation_root": str(b_root),
    "a_exists_after_move": a_root.exists(),
    "b_exists_after_move": b_root.is_dir(),
    "a_prefix_exists_after_move": (a_root / "prefix").exists(),
    "b_python_executable_after_move": (b_root / "prefix/bin/python").is_file(),
    "source_device": a_device,
    "target_parent_device": target_device,
    "relocated_device": b_device,
    "source_inode": a_inode,
    "relocated_inode": b_inode,
    "same_filesystem": a_device == target_device == b_device,
    "inode_preserved": a_inode == b_inode,
}
result["pass"] = (
    not result["a_exists_after_move"]
    and result["b_exists_after_move"]
    and not result["a_prefix_exists_after_move"]
    and result["b_python_executable_after_move"]
    and result["same_filesystem"]
    and result["inode_preserved"]
)
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result["pass"] else 63)
PY
        move_rc=$?
        set -e
    fi
fi

if [[ $move_rc -eq 0 ]]; then
    fingerprint_root "$B_INSTALL_ROOT" "$RESULTS_DIR/b-installation-root-after-move.json"
    fingerprint_product "$B_PREFIX" "$RESULTS_DIR/b-installed-strict-before.json"
    fingerprint_portable "$B_PREFIX" "$RESULTS_DIR/b-installed-portable-before.json"

    set +e
    run_local_script \
        "$ENGINE" \
        --installation-root "$B_INSTALL_ROOT" \
        --operation verify \
        --output "$RELOCATED_RESULTS/engine-verification.json" \
        > "$RELOCATED_RESULTS/engine-verification.log" 2>&1
    engine_verify_rc=$?
    set -e
    cat "$RELOCATED_RESULTS/engine-verification.log"
    cp -a "$B_INSTALL_ROOT/.cpython-android-cli/registry.json" "$RESULTS_DIR/b-registry.json"
fi

if [[ $engine_verify_rc -eq 0 ]]; then
    set +e
    "${clean_env[@]}" \
        "$B_PREFIX/bin/python" -I -B -S \
        "$PROBE" \
        --output "$RELOCATED_RESULTS/base-probe.json" \
        --https \
        > "$RELOCATED_RESULTS/base-probe.log" 2>&1
    base_probe_rc=$?
    set -e
    cat "$RELOCATED_RESULTS/base-probe.log"

    set +e
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPYCACHEPREFIX="$SMOKE_RESULTS/pycache" \
    RUNTIME_ROOT_OVERRIDE="$B_INSTALL_ROOT" \
    TERMUX_RESULTS_ROOT_OVERRIDE="$SMOKE_RESULTS" \
    bash "$SMOKE" \
        > "$RELOCATED_RESULTS/smoke.log" 2>&1
    smoke_rc=$?
    set -e
    cat "$RELOCATED_RESULTS/smoke.log"
fi

if [[ $smoke_rc -eq 0 ]]; then
    set +e
    "${clean_env[@]}" \
        "$SMOKE_RESULTS/venv/bin/python" -I -B -S \
        "$PROBE" \
        --output "$SMOKE_RESULTS/venv-probe.json" \
        > "$RELOCATED_RESULTS/venv-probe.log" 2>&1
    venv_probe_rc=$?
    set -e
    cat "$RELOCATED_RESULTS/venv-probe.log"

    set +e
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPYCACHEPREFIX="$SMOKE_RESULTS/uv-run-pycache" \
    "${clean_env[@]}" \
        uv run \
        --no-project \
        --no-python-downloads \
        --python "$B_PREFIX/bin/python" \
        --with anyio \
        python "$PROBE" \
        --output "$SMOKE_RESULTS/uv-run-probe.json" \
        --require-anyio \
        > "$RELOCATED_RESULTS/uv-run-probe.log" 2>&1
    uv_run_rc=$?
    set -e
    cat "$RELOCATED_RESULTS/uv-run-probe.log"
fi

rm -rf \
    "$SMOKE_RESULTS/venv" \
    "$SMOKE_RESULTS/pycache" \
    "$SMOKE_RESULTS/uv-run-pycache"

if [[ $engine_verify_rc -eq 0 ]]; then
    set +e
    RUNTIME_PREFIX="$B_PREFIX" \
    PYTHON_BIN="$B_PREFIX/bin/python" \
    OUTPUT_DIR="$CLOSURE_RESULTS" \
    bash "$CLOSURE_DIR_TOOLS/inventory-runtime.sh" \
        > "$RELOCATED_RESULTS/closure-inventory.log" 2>&1
    closure_inventory_rc=$?
    set -e
    cat "$RELOCATED_RESULTS/closure-inventory.log"
fi

if [[ $closure_inventory_rc -eq 0 ]]; then
    set +e
    RUNTIME_PREFIX="$B_PREFIX" \
    PYTHON_BIN="$B_PREFIX/bin/python" \
    RESULTS_DIR="$CLOSURE_RESULTS" \
    bash "$CLOSURE_DIR_TOOLS/analyze-and-probe.sh" \
        > "$RELOCATED_RESULTS/closure-analysis.log" 2>&1
    closure_analysis_rc=$?
    set -e
    cat "$RELOCATED_RESULTS/closure-analysis.log"
fi

if [[ $closure_inventory_rc -eq 0 && $closure_analysis_rc -eq 0 ]]; then
    set +e
    RUNTIME_PREFIX="$B_PREFIX" \
    PYTHON_BIN="$B_PREFIX/bin/python" \
    RESULTS_DIR="$CLOSURE_RESULTS" \
    bash "$CLOSURE_DIR_TOOLS/probe-extension-imports.sh" \
        > "$RELOCATED_RESULTS/closure-extension-imports.log" 2>&1
    closure_extension_rc=$?
    set -e
    cat "$RELOCATED_RESULTS/closure-extension-imports.log"
fi

write_closure_status

if [[ -d "$B_PREFIX" ]]; then
    fingerprint_product "$B_PREFIX" "$RESULTS_DIR/b-installed-strict-after.json"
    fingerprint_portable "$B_PREFIX" "$RESULTS_DIR/b-installed-portable-after.json"
    fingerprint_root "$B_INSTALL_ROOT" "$RESULTS_DIR/b-installation-root-after-probes.json"
fi

if [[ -d "$B_INSTALL_ROOT" ]]; then
    set +e
    "$TOOL_PYTHON" -I -B -S - \
        "$RESULTS_DIR/stale-prefix-scan.json" \
        "$A_INSTALL_ROOT" "$A_PREFIX" "$B_INSTALL_ROOT" \
        "$RELOCATED_RESULTS/base-probe.json" \
        "$SMOKE_RESULTS/venv-probe.json" \
        "$SMOKE_RESULTS/uv-run-probe.json" <<'PY'
import json
import os
import sys
from pathlib import Path
from typing import Any

output = Path(sys.argv[1]).resolve()
a_root = Path(sys.argv[2]).resolve()
a_prefix = Path(sys.argv[3]).resolve()
b_root = Path(sys.argv[4]).resolve()
probe_paths = [Path(value).resolve() for value in sys.argv[5:]]
needles = (str(a_root), str(a_prefix))
byte_needles = tuple(value.encode("utf-8") for value in needles)
regular_matches: list[str] = []
symlink_matches: list[dict[str, str]] = []
probe_matches: list[dict[str, str]] = []

for path in sorted(b_root.rglob("*"), key=lambda item: item.relative_to(b_root).as_posix()):
    relative = path.relative_to(b_root).as_posix()
    if path.is_symlink():
        target = os.readlink(path)
        if any(needle in target for needle in needles):
            symlink_matches.append({"path": relative, "target": target})
    elif path.is_file():
        data = path.read_bytes()
        if any(needle in data for needle in byte_needles):
            regular_matches.append(relative)

def walk(value: Any, where: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            walk(child, f"{where}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk(child, f"{where}[{index}]")
    elif isinstance(value, str) and any(needle in value for needle in needles):
        probe_matches.append({"location": where, "value": value})

for path in probe_paths:
    if path.is_file():
        walk(json.loads(path.read_text(encoding="utf-8")), path.name)

result = {
    "schema_version": 1,
    "a_installation_root": str(a_root),
    "a_prefix": str(a_prefix),
    "b_installation_root": str(b_root),
    "a_root_absent": not a_root.exists(),
    "b_root_present": b_root.is_dir(),
    "regular_file_matches": regular_matches,
    "symlink_matches": symlink_matches,
    "probe_matches": probe_matches,
}
result["pass"] = (
    result["a_root_absent"]
    and result["b_root_present"]
    and not regular_matches
    and not symlink_matches
    and not probe_matches
)
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result["pass"] else 64)
PY
    stale_scan_rc=$?
    set -e
fi

if [[ $baseline_rc -eq 0 \
    && $move_rc -eq 0 \
    && $engine_verify_rc -eq 0 \
    && $base_probe_rc -eq 0 \
    && $smoke_rc -eq 0 \
    && $venv_probe_rc -eq 0 \
    && $uv_run_rc -eq 0 \
    && $closure_inventory_rc -eq 0 \
    && $closure_analysis_rc -eq 0 \
    && $closure_extension_rc -eq 0 \
    && $stale_scan_rc -eq 0 ]]; then
    set +e
    "$TOOL_PYTHON" -I -B -S \
        "$BASELINE_VERIFIER" \
        --phase4-results "$BASELINE_RESULTS/input/phase4" \
        --installed-prefix "$B_PREFIX" \
        --manifest "$MANIFEST" \
        --install-result "$BASELINE_RESULTS/install-result.json" \
        --engine-verification "$RELOCATED_RESULTS/engine-verification.json" \
        --registry "$RESULTS_DIR/b-registry.json" \
        --installed-before "$RESULTS_DIR/b-installed-strict-before.json" \
        --installed-after "$RESULTS_DIR/b-installed-strict-after.json" \
        --installed-portable-before "$RESULTS_DIR/b-installed-portable-before.json" \
        --installed-portable-after "$RESULTS_DIR/b-installed-portable-after.json" \
        --input-before "$BASELINE_RESULTS/input-before.json" \
        --input-after "$BASELINE_RESULTS/input-after.json" \
        --base-probe "$RELOCATED_RESULTS/base-probe.json" \
        --venv-probe "$SMOKE_RESULTS/venv-probe.json" \
        --uv-run-probe "$SMOKE_RESULTS/uv-run-probe.json" \
        --smoke-log "$RELOCATED_RESULTS/smoke.log" \
        --closure-dir "$CLOSURE_RESULTS" \
        --output "$RESULTS_DIR/relocated-baseline-verification.json" \
        > "$RESULTS_DIR/relocated-baseline-verifier.log" 2>&1
    relocated_baseline_verify_rc=$?
    set -e
    cat "$RESULTS_DIR/relocated-baseline-verifier.log"
fi

if [[ $relocated_baseline_verify_rc -eq 0 ]]; then
    set +e
    "$TOOL_PYTHON" -I -B -S \
        "$VERIFIER" \
        --results-dir "$RESULTS_DIR" \
        --a-installation-root "$A_INSTALL_ROOT" \
        --b-installation-root "$B_INSTALL_ROOT" \
        --output "$RESULTS_DIR/verification.json" \
        > "$RESULTS_DIR/verifier.log" 2>&1
    final_verify_rc=$?
    set -e
else
    write_blocked_verification "relocated_baseline_verification_blocked"
fi
cat "$RESULTS_DIR/verifier.log" 2>/dev/null || cat "$RESULTS_DIR/verification.json"

write_status \
    baseline "$baseline_rc" \
    move "$move_rc" \
    engine_verify "$engine_verify_rc" \
    base_probe "$base_probe_rc" \
    smoke "$smoke_rc" \
    venv_probe "$venv_probe_rc" \
    uv_run_probe "$uv_run_rc" \
    closure_inventory "$closure_inventory_rc" \
    closure_analysis "$closure_analysis_rc" \
    closure_extension_imports "$closure_extension_rc" \
    stale_prefix_scan "$stale_scan_rc" \
    relocated_baseline_verification "$relocated_baseline_verify_rc" \
    final_verification "$final_verify_rc"

write_result_index > "$RESULTS_DIR/result-index.log" 2>&1
cat "$RESULTS_DIR/result-index.log"

final_rc=0
for rc in \
    "$baseline_rc" "$move_rc" "$engine_verify_rc" "$base_probe_rc" "$smoke_rc" \
    "$venv_probe_rc" "$uv_run_rc" "$closure_inventory_rc" "$closure_analysis_rc" \
    "$closure_extension_rc" "$stale_scan_rc" "$relocated_baseline_verify_rc" \
    "$final_verify_rc"; do
    if [[ $rc -ne 0 ]]; then
        final_rc=$rc
        break
    fi
done

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "INSTALLED_RUNTIME_RELOCATION_GATE1_PREREQUISITE=80/80 PASS"
echo "INSTALLED_RUNTIME_RELOCATION_WHOLE_ROOT_MOVE=PASS"
echo "INSTALLED_RUNTIME_RELOCATION_REGISTRY=714/714 PASS"
echo "INSTALLED_RUNTIME_RELOCATION_PORTABLE_FIDELITY=PASS"
echo "INSTALLED_RUNTIME_RELOCATION_STRICT_MUTATION_CHECK=PASS"
echo "INSTALLED_RUNTIME_RELOCATION_STALE_PREFIX=0 PASS"
echo "INSTALLED_RUNTIME_RELOCATION_SMOKE=PASS"
echo "INSTALLED_RUNTIME_RELOCATION_HTTPS=200 PASS"
echo "INSTALLED_RUNTIME_RELOCATION_UV_VENV=PASS"
echo "INSTALLED_RUNTIME_RELOCATION_UV_RUN=PASS"
echo "INSTALLED_RUNTIME_RELOCATION_NATIVE_CLOSURE=81/329/0 PASS"
echo "INSTALLED_RUNTIME_RELOCATION_EXTENSION_IMPORTS=67/67 PASS"
echo "INSTALLED_RUNTIME_RELOCATION_REVALIDATION=80/80 PASS"
echo "STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION=PASS"
