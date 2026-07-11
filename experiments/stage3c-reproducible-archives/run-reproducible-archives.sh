#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 3: build and independently verify normalized reproducible archives.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

MANIFEST_RESULTS="${MANIFEST_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase2-artifact-manifest-schema}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RUNTIME_PREFIX="${RUNTIME_PREFIX:-$WORK_ROOT/termux/stage3c-phase1-isolated-variants/runtime-base/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase3-reproducible-archives}"
STAGING_DIR="${STAGING_DIR:-$WORK_ROOT/termux/stage3c-phase3-reproducible-archive-staging}"

PYTHON="$CANONICAL_PREFIX/bin/python"
FINGERPRINT="$SCRIPT_DIR/../stage3c-product-role-inventory/fingerprint-product-tree.py"
LOCAL_SCRIPT_RUNNER="$SCRIPT_DIR/../stage3c-artifact-manifest/run-isolated-local-script.py"
BUILDER="$SCRIPT_DIR/build-reproducible-archives.py"
PREFLIGHT="$SCRIPT_DIR/preflight-archive-safety.py"
VERIFIER="$SCRIPT_DIR/verify-reproducible-archives.py"
INPUT_DIR="$RESULTS_DIR/input/manifest-schema"

[[ -x "$PYTHON" ]] || {
    echo "ERROR: canonical promoted Python is missing: $PYTHON" >&2
    exit 2
}
[[ -x "$RUNTIME_PREFIX/bin/python" ]] || {
    echo "ERROR: frozen runtime-base is missing: $RUNTIME_PREFIX/bin/python" >&2
    exit 2
}

for file in \
    "$MANIFEST_RESULTS/generation.json" \
    "$MANIFEST_RESULTS/verification.json" \
    "$MANIFEST_RESULTS/workflow-status.json" \
    "$MANIFEST_RESULTS/manifest-index.json" \
    "$MANIFEST_RESULTS/input/product-lock.json" \
    "$MANIFEST_RESULTS/canonical-before.json" \
    "$MANIFEST_RESULTS/canonical-after.json" \
    "$MANIFEST_RESULTS/runtime-before.json" \
    "$MANIFEST_RESULTS/runtime-after.json" \
    "$MANIFEST_RESULTS/manifests/runtime-base.manifest.json" \
    "$MANIFEST_RESULTS/manifests/development-addon.manifest.json" \
    "$MANIFEST_RESULTS/manifests/test-addon.manifest.json" \
    "$CANONICAL_PREFIX/lib/python3.14/LICENSE.txt" \
    "$FINGERPRINT" \
    "$LOCAL_SCRIPT_RUNNER" \
    "$BUILDER" \
    "$PREFLIGHT" \
    "$VERIFIER" \
    "$SCRIPT_DIR/archive_serialization_contract.py"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required accepted evidence, product path, or tool is missing: $file" >&2
        exit 2
    }
done

rm -rf "$RESULTS_DIR" "$STAGING_DIR"
mkdir -p "$INPUT_DIR/manifests" "$INPUT_DIR/input"

for name in \
    generation.json \
    verification.json \
    workflow-status.json \
    manifest-index.json \
    canonical-before.json \
    canonical-after.json \
    runtime-before.json \
    runtime-after.json \
    source-mutation-check.txt; do
    [[ ! -f "$MANIFEST_RESULTS/$name" ]] || \
        cp -a "$MANIFEST_RESULTS/$name" "$INPUT_DIR/$name"
done
cp -a "$MANIFEST_RESULTS/input/product-lock.json" "$INPUT_DIR/input/product-lock.json"
cp -a "$MANIFEST_RESULTS/manifests/"*.manifest.json "$INPUT_DIR/manifests/"

printf 'Manifest results:        %s\n' "$MANIFEST_RESULTS"
printf 'Canonical prefix:        %s\n' "$CANONICAL_PREFIX"
printf 'Runtime-base prefix:     %s\n' "$RUNTIME_PREFIX"
printf 'Results:                 %s\n' "$RESULTS_DIR"
printf 'Extraction staging:      %s\n\n' "$STAGING_DIR"

fingerprint_tree() {
    "$PYTHON" -I -B -S \
        "$FINGERPRINT" \
        --runtime-prefix "$1" \
        --output "$2" \
        --expected-entry-count "$3"
}

run_local_script() {
    "$PYTHON" -I -B -S "$LOCAL_SCRIPT_RUNNER" "$@"
}

write_mutation_check() {
    "$PYTHON" -I -B -S - \
        "$RESULTS_DIR/canonical-before.json" \
        "$RESULTS_DIR/canonical-after.json" \
        "$RESULTS_DIR/runtime-before.json" \
        "$RESULTS_DIR/runtime-after.json" \
        "$RESULTS_DIR/source-mutation-check.txt" <<'PY'
import json
import sys
from pathlib import Path

cb, ca, rb, ra = [
    json.loads(Path(path).read_text(encoding="utf-8"))
    for path in sys.argv[1:5]
]
canonical_pass = (
    cb.get("pass") is True
    and ca.get("pass") is True
    and cb.get("entry_count") == ca.get("entry_count") == 3155
    and cb.get("fingerprint") == ca.get("fingerprint")
)
runtime_pass = (
    rb.get("pass") is True
    and ra.get("pass") is True
    and rb.get("entry_count") == ra.get("entry_count") == 714
    and rb.get("fingerprint") == ra.get("fingerprint")
)
passed = canonical_pass and runtime_pass
text = "\n".join(
    (
        f"canonical_prefix={cb.get('root')}",
        f"canonical_before={cb.get('fingerprint')}",
        f"canonical_after={ca.get('fingerprint')}",
        f"canonical_entry_count={ca.get('entry_count')}",
        f"canonical_pass={'true' if canonical_pass else 'false'}",
        f"runtime_prefix={rb.get('root')}",
        f"runtime_before={rb.get('fingerprint')}",
        f"runtime_after={ra.get('fingerprint')}",
        f"runtime_entry_count={ra.get('entry_count')}",
        f"runtime_pass={'true' if runtime_pass else 'false'}",
        f"pass={'true' if passed else 'false'}",
        "",
    )
)
Path(sys.argv[5]).write_text(text, encoding="utf-8")
print(text, end="")
raise SystemExit(0 if passed else 33)
PY
}

write_blocked_json() {
    local output="$1"
    local blocked_by="$2"
    local returncode="$3"
    local failed_check="$4"
    "$PYTHON" -I -B -S - "$output" "$blocked_by" "$returncode" "$failed_check" <<'PY'
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
    "failed_checks": [sys.argv[4]],
    "errors": {},
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
        "$RESULTS_DIR/workflow-status.json" "$1" "$2" "$3" "$4" <<'PY'
import json
import sys
from pathlib import Path

returncodes = {
    "archive_build": int(sys.argv[2]),
    "source_mutation": int(sys.argv[3]),
    "archive_preflight": int(sys.argv[4]),
    "archive_verification": int(sys.argv[5]),
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

echo "== Frozen products before archive serialization =="
fingerprint_tree "$CANONICAL_PREFIX" "$RESULTS_DIR/canonical-before.json" 3155
fingerprint_tree "$RUNTIME_PREFIX" "$RESULTS_DIR/runtime-before.json" 714

set +e
run_local_script \
    "$BUILDER" \
    --manifest-results "$INPUT_DIR" \
    --canonical-prefix "$CANONICAL_PREFIX" \
    --runtime-prefix "$RUNTIME_PREFIX" \
    --output-dir "$RESULTS_DIR" \
    --require-pass \
    > "$RESULTS_DIR/builder.log" 2>&1
builder_rc=$?
set -e
cat "$RESULTS_DIR/builder.log"

echo
echo "== Frozen products after archive serialization =="
fingerprint_tree "$CANONICAL_PREFIX" "$RESULTS_DIR/canonical-after.json" 3155
fingerprint_tree "$RUNTIME_PREFIX" "$RESULTS_DIR/runtime-after.json" 714

set +e
write_mutation_check
mutation_rc=$?
set -e

if [[ $builder_rc -eq 0 ]]; then
    set +e
    run_local_script \
        "$PREFLIGHT" \
        --manifest-results "$INPUT_DIR" \
        --archive-results "$RESULTS_DIR" \
        --output "$RESULTS_DIR/preflight-verification.json" \
        > "$RESULTS_DIR/preflight.log" 2>&1
    preflight_rc=$?
    set -e
else
    preflight_rc=125
    write_blocked_json \
        "$RESULTS_DIR/preflight-verification.json" \
        "reproducible_archive_build" \
        "$builder_rc" \
        "archive_preflight_blocked" \
        > "$RESULTS_DIR/preflight.log" 2>&1
fi
cat "$RESULTS_DIR/preflight.log"

if [[ $builder_rc -eq 0 && $preflight_rc -eq 0 ]]; then
    set +e
    run_local_script \
        "$VERIFIER" \
        --manifest-results "$INPUT_DIR" \
        --archive-results "$RESULTS_DIR" \
        --canonical-prefix "$CANONICAL_PREFIX" \
        --staging-dir "$STAGING_DIR" \
        --output "$RESULTS_DIR/archive-verification.json" \
        > "$RESULTS_DIR/verifier.log" 2>&1
    verifier_rc=$?
    set -e
else
    verifier_rc=125
    blocked_by="reproducible_archive_build"
    blocked_rc="$builder_rc"
    if [[ $builder_rc -eq 0 ]]; then
        blocked_by="archive_preflight"
        blocked_rc="$preflight_rc"
    fi
    write_blocked_json \
        "$RESULTS_DIR/archive-verification.json" \
        "$blocked_by" \
        "$blocked_rc" \
        "archive_verification_blocked" \
        > "$RESULTS_DIR/verifier.log" 2>&1
fi
cat "$RESULTS_DIR/verifier.log"

write_workflow_status "$builder_rc" "$mutation_rc" "$preflight_rc" "$verifier_rc"

printf '\nReproducibility:      %s\n' "$RESULTS_DIR/reproducibility.json"
printf 'Archive preflight:    %s\n' "$RESULTS_DIR/preflight-verification.json"
printf 'Archive verification: %s\n' "$RESULTS_DIR/archive-verification.json"
printf 'Archives:             %s\n' "$RESULTS_DIR/archives"
printf 'Mutation check:       %s\n\n' "$RESULTS_DIR/source-mutation-check.txt"

final_rc=0
for rc in "$builder_rc" "$mutation_rc" "$preflight_rc" "$verifier_rc"; do
    if [[ $rc -ne 0 ]]; then
        final_rc=$rc
        break
    fi
done

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE3_REPRODUCIBLE_ARCHIVES=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "REPRODUCIBLE_ARCHIVE_ACCEPTED_INPUTS=PASS"
echo "REPRODUCIBLE_ARCHIVE_BUILD=31/31 PASS"
echo "REPRODUCIBLE_ARCHIVE_BYTE_IDENTITY=3/3 PASS"
echo "REPRODUCIBLE_ARCHIVE_PREFLIGHT=28/28 PASS"
echo "REPRODUCIBLE_ARCHIVE_VERIFICATION=76/76 PASS"
echo "REPRODUCIBLE_ARCHIVE_SAFE_STAGING_EXTRACTION=3/3 PASS"
echo "REPRODUCIBLE_ARCHIVE_SOURCE_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE3_REPRODUCIBLE_ARCHIVES=PASS"
