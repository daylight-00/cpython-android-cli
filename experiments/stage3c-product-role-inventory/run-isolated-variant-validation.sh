#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 1: materialize and validate isolated component variants.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

SOURCE_PREFIX="${SOURCE_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
POLICY_RESULTS="${POLICY_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase1-component-policy}"
VARIANT_ROOT="${VARIANT_ROOT:-$WORK_ROOT/termux/stage3c-phase1-isolated-variants}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase1-isolated-variants}"
EXPECTED_COMPONENT_MANIFEST="${EXPECTED_COMPONENT_MANIFEST:-91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84}"
EXPECTED_SOURCE_FINGERPRINT="${EXPECTED_SOURCE_FINGERPRINT:-5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c}"
TERMUX_PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
SOURCE_PYTHON="$SOURCE_PREFIX/bin/python"
FINGERPRINT="$SCRIPT_DIR/fingerprint-product-tree.py"
MATERIALIZER="$SCRIPT_DIR/materialize-product-variants.py"
FIDELITY_VERIFIER="$SCRIPT_DIR/verify-materialized-variants.py"
CAPABILITY_PROBE="$SCRIPT_DIR/probe-materialized-variant.py"
WORKFLOW_VERIFIER="$SCRIPT_DIR/verify-isolated-variant-workflow.py"
SMOKE_SCRIPT="$PROJECT_ROOT/scripts/test/smoke-termux.sh"
CLANG_BIN="${CLANG_BIN:-$(command -v clang || true)}"

[[ -x "$SOURCE_PYTHON" ]] || {
    echo "ERROR: canonical promoted Python is missing: $SOURCE_PYTHON" >&2
    exit 2
}
for file in \
    "$POLICY_RESULTS/component-inventory.tsv" \
    "$POLICY_RESULTS/component-policy.json" \
    "$POLICY_RESULTS/component-policy-verification.json" \
    "$FINGERPRINT" \
    "$MATERIALIZER" \
    "$FIDELITY_VERIFIER" \
    "$CAPABILITY_PROBE" \
    "$WORKFLOW_VERIFIER" \
    "$SMOKE_SCRIPT"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required policy evidence or tool is missing: $file" >&2
        exit 2
    }
done

rm -rf "$VARIANT_ROOT" "$RESULTS_DIR"
mkdir -p \
    "$RESULTS_DIR" \
    "$RESULTS_DIR/capabilities" \
    "$RESULTS_DIR/fingerprints" \
    "$RESULTS_DIR/pycache"

printf 'Canonical source:     %s\n' "$SOURCE_PREFIX"
printf 'Component policy:     %s\n' "$POLICY_RESULTS"
printf 'Component manifest:   %s\n' "$EXPECTED_COMPONENT_MANIFEST"
printf 'Source fingerprint:   %s\n' "$EXPECTED_SOURCE_FINGERPRINT"
printf 'Variant root:         %s\n' "$VARIANT_ROOT"
printf 'Results:              %s\n\n' "$RESULTS_DIR"

run_clean() {
    local prefix="$1"
    shift
    env \
        -u PYTHONHOME \
        -u PYTHONPATH \
        -u CPYTHON_HOME \
        -u LD_LIBRARY_PATH \
        -u SSL_CERT_FILE \
        -u SSL_CERT_DIR \
        -u PYTHONTZPATH \
        -u VIRTUAL_ENV \
        -u UV_PYTHON \
        PREFIX="$TERMUX_PREFIX" \
        HOME="$HOME" \
        PATH="$TERMUX_PREFIX/bin:/system/bin" \
        TMPDIR="$TERMUX_PREFIX/tmp" \
        TERM="${TERM:-xterm-256color}" \
        PYTHONDONTWRITEBYTECODE=1 \
        "$prefix/bin/python" "$@"
}

fingerprint_variant() {
    local variant="$1"
    local phase="$2"
    local expected_count="$3"
    "$SOURCE_PYTHON" -I -B -S \
        "$FINGERPRINT" \
        --runtime-prefix "$VARIANT_ROOT/$variant/prefix" \
        --output "$RESULTS_DIR/fingerprints/$variant-$phase.json" \
        --expected-entry-count "$expected_count"
}

echo "== Canonical source before =="
"$SOURCE_PYTHON" -I -B -S \
    "$FINGERPRINT" \
    --runtime-prefix "$SOURCE_PREFIX" \
    --output "$RESULTS_DIR/source-before.json" \
    --expected-entry-count 3155

echo
echo "== Materialize exact component variants =="
"$SOURCE_PYTHON" -I -B -S \
    "$MATERIALIZER" \
    --source-prefix "$SOURCE_PREFIX" \
    --component-inventory "$POLICY_RESULTS/component-inventory.tsv" \
    --component-policy "$POLICY_RESULTS/component-policy.json" \
    --component-verification "$POLICY_RESULTS/component-policy-verification.json" \
    --output-root "$VARIANT_ROOT" \
    --output "$RESULTS_DIR/materialization.json" \
    --expected-component-manifest "$EXPECTED_COMPONENT_MANIFEST" \
    | tee "$RESULTS_DIR/materialization.log"

echo
echo "== Verify initial exact-path fidelity =="
"$SOURCE_PYTHON" -I -B -S \
    "$FIDELITY_VERIFIER" \
    --component-inventory "$POLICY_RESULTS/component-inventory.tsv" \
    --materialization "$RESULTS_DIR/materialization.json" \
    --output-root "$VARIANT_ROOT" \
    --output "$RESULTS_DIR/variant-fidelity-before.json" \
    --expected-component-manifest "$EXPECTED_COMPONENT_MANIFEST" \
    | tee "$RESULTS_DIR/variant-fidelity-before.log"

echo
echo "== Variant fingerprints before behavior =="
fingerprint_variant runtime-base before 714
fingerprint_variant runtime-development before 1168
fingerprint_variant runtime-test before 2502
fingerprint_variant runtime-supported before 2956

capability_rc=0
for variant in runtime-base runtime-development runtime-test runtime-supported; do
    echo
    echo "== Capability probe: $variant =="
    set +e
    run_clean "$VARIANT_ROOT/$variant/prefix" \
        -I -B -S \
        "$CAPABILITY_PROBE" \
        --variant "$variant" \
        --prefix "$VARIANT_ROOT/$variant/prefix" \
        --output "$RESULTS_DIR/capabilities/$variant.json" \
        > "$RESULTS_DIR/capabilities/$variant.log" 2>&1
    rc=$?
    set -e
    cat "$RESULTS_DIR/capabilities/$variant.log"
    if [[ $rc -ne 0 && $capability_rc -eq 0 ]]; then
        capability_rc=$rc
    fi
done

echo
echo "== Runtime-base production smoke =="
set +e
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX="$RESULTS_DIR/pycache/runtime-base-smoke" \
RUNTIME_ROOT_OVERRIDE="$VARIANT_ROOT/runtime-base" \
TERMUX_RESULTS_ROOT_OVERRIDE="$RESULTS_DIR/runtime-base-smoke" \
bash "$SMOKE_SCRIPT" \
    > "$RESULTS_DIR/runtime-base-smoke.log" 2>&1
smoke_rc=$?
set -e
cat "$RESULTS_DIR/runtime-base-smoke.log"

echo
echo "== Development-addon native extension probe =="
DEV_PREFIX="$VARIANT_ROOT/runtime-development/prefix"
DEV_BUILD="$RESULTS_DIR/development-extension"
mkdir -p "$DEV_BUILD"
cat > "$DEV_BUILD/stage3c_devprobe.c" <<'C'
#include <Python.h>

static PyObject *answer(PyObject *self, PyObject *args) {
    (void)self;
    (void)args;
    return PyLong_FromLong(42);
}

static PyMethodDef methods[] = {
    {"answer", answer, METH_NOARGS, "Return the Stage 3-C probe value."},
    {NULL, NULL, 0, NULL},
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "stage3c_devprobe",
    NULL,
    -1,
    methods,
};

PyMODINIT_FUNC PyInit_stage3c_devprobe(void) {
    return PyModule_Create(&module);
}
C

ext_suffix="$(run_clean "$DEV_PREFIX" -I -B -S -c 'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX"))')"
dev_extension="$DEV_BUILD/stage3c_devprobe$ext_suffix"
: > "$RESULTS_DIR/development-extension.log"

set +e
if [[ -z "$CLANG_BIN" || ! -x "$CLANG_BIN" ]]; then
    echo "ERROR: clang is unavailable" >> "$RESULTS_DIR/development-extension.log"
    dev_compile_rc=127
else
    {
        echo "clang=$CLANG_BIN"
        echo "extension=$dev_extension"
        "$CLANG_BIN" \
            -shared \
            -fPIC \
            -O2 \
            -I"$DEV_PREFIX/include/python3.14" \
            "$DEV_BUILD/stage3c_devprobe.c" \
            -L"$DEV_PREFIX/lib" \
            -Wl,-rpath-link,"$DEV_PREFIX/lib" \
            -lpython3.14 \
            -o "$dev_extension"
    } >> "$RESULTS_DIR/development-extension.log" 2>&1
    dev_compile_rc=$?
fi
set -e

set +e
if [[ $dev_compile_rc -eq 0 ]]; then
    run_clean "$DEV_PREFIX" \
        -I -B -S -c \
        'import sys; sys.path.insert(0, sys.argv[1]); import stage3c_devprobe; print(f"DEV_EXTENSION_RESULT={stage3c_devprobe.answer()}")' \
        "$DEV_BUILD" \
        >> "$RESULTS_DIR/development-extension.log" 2>&1
    dev_import_rc=$?
else
    dev_import_rc=125
fi
set -e
cat "$RESULTS_DIR/development-extension.log"

echo
echo "== Test-addon representative regression test =="
TEST_PREFIX="$VARIANT_ROOT/runtime-test/prefix"
set +e
run_clean "$TEST_PREFIX" \
    -I -B -m test -j1 test_json \
    > "$RESULTS_DIR/test-addon.log" 2>&1
test_rc=$?
set -e
if [[ $test_rc -eq 0 ]]; then
    echo "STAGE3C_TEST_ADDON_REPRESENTATIVE=PASS" >> "$RESULTS_DIR/test-addon.log"
fi
cat "$RESULTS_DIR/test-addon.log"

echo
echo "== Verify post-behavior exact-path fidelity =="
set +e
"$SOURCE_PYTHON" -I -B -S \
    "$FIDELITY_VERIFIER" \
    --component-inventory "$POLICY_RESULTS/component-inventory.tsv" \
    --materialization "$RESULTS_DIR/materialization.json" \
    --output-root "$VARIANT_ROOT" \
    --output "$RESULTS_DIR/variant-fidelity-after.json" \
    --expected-component-manifest "$EXPECTED_COMPONENT_MANIFEST" \
    > "$RESULTS_DIR/variant-fidelity-after.log" 2>&1
fidelity_after_rc=$?
set -e
cat "$RESULTS_DIR/variant-fidelity-after.log"

echo
echo "== Variant fingerprints after behavior =="
set +e
fingerprint_variant runtime-base after 714
base_fingerprint_rc=$?
fingerprint_variant runtime-development after 1168
development_fingerprint_rc=$?
fingerprint_variant runtime-test after 2502
test_fingerprint_rc=$?
fingerprint_variant runtime-supported after 2956
supported_fingerprint_rc=$?
set -e

echo
echo "== Canonical source after =="
set +e
"$SOURCE_PYTHON" -I -B -S \
    "$FINGERPRINT" \
    --runtime-prefix "$SOURCE_PREFIX" \
    --output "$RESULTS_DIR/source-after.json" \
    --expected-entry-count 3155
source_after_rc=$?
set -e

"$SOURCE_PYTHON" -I -B -S - \
    "$RESULTS_DIR/workflow-status.json" \
    "$capability_rc" \
    "$smoke_rc" \
    "$dev_compile_rc" \
    "$dev_import_rc" \
    "$test_rc" \
    "$fidelity_after_rc" \
    "$base_fingerprint_rc" \
    "$development_fingerprint_rc" \
    "$test_fingerprint_rc" \
    "$supported_fingerprint_rc" \
    "$source_after_rc" <<'PY'
import json
import sys
from pathlib import Path

keys = (
    "capabilities",
    "runtime_base_smoke",
    "development_extension_compile",
    "development_extension_import",
    "test_addon",
    "fidelity_after",
    "runtime_base_fingerprint_after",
    "runtime_development_fingerprint_after",
    "runtime_test_fingerprint_after",
    "runtime_supported_fingerprint_after",
    "source_fingerprint_after",
)
returncodes = {key: int(value) for key, value in zip(keys, sys.argv[2:])}
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

set +e
"$SOURCE_PYTHON" -I -B -S \
    "$WORKFLOW_VERIFIER" \
    --results-dir "$RESULTS_DIR" \
    --output "$RESULTS_DIR/verification.json" \
    --expected-source-fingerprint "$EXPECTED_SOURCE_FINGERPRINT" \
    --expected-component-manifest "$EXPECTED_COMPONENT_MANIFEST" \
    > "$RESULTS_DIR/verifier.log" 2>&1
verify_rc=$?
set -e
cat "$RESULTS_DIR/verifier.log"

printf '\nMaterialization:      %s\n' "$RESULTS_DIR/materialization.json"
printf 'Initial fidelity:    %s\n' "$RESULTS_DIR/variant-fidelity-before.json"
printf 'Final fidelity:      %s\n' "$RESULTS_DIR/variant-fidelity-after.json"
printf 'Capabilities:        %s\n' "$RESULTS_DIR/capabilities"
printf 'Workflow status:     %s\n' "$RESULTS_DIR/workflow-status.json"
printf 'Verification:        %s\n\n' "$RESULTS_DIR/verification.json"

if [[ $verify_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE1_ISOLATED_VARIANTS=FAIL rc=$verify_rc"
    exit "$verify_rc"
fi

echo "RUNTIME_BASE_SMOKE=PASS"
echo "DEVELOPMENT_ADDON_NATIVE_EXTENSION=PASS"
echo "TEST_ADDON_REPRESENTATIVE_TEST=PASS"
echo "ISOLATED_VARIANT_SOURCE_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE1_ISOLATED_VARIANTS=PASS"
