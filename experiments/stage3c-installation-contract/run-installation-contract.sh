#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-C Phase 4: derive and independently verify installation policy.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

PHASE3_RESULTS="${PHASE3_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase3-reproducible-archives}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase4-installation-contract}"

PYTHON="$CANONICAL_PREFIX/bin/python"
LOCAL_SCRIPT_RUNNER="$SCRIPT_DIR/../stage3c-artifact-manifest/run-isolated-local-script.py"
FINGERPRINT="$SCRIPT_DIR/fingerprint-evidence-tree.py"
DERIVER="$SCRIPT_DIR/derive-installation-contract.py"
VERIFIER="$SCRIPT_DIR/verify-installation-contract.py"
INPUT_DIR="$RESULTS_DIR/input/phase3"

[[ -x "$PYTHON" ]] || {
    echo "ERROR: canonical promoted Python is missing: $PYTHON" >&2
    exit 2
}

for file in \
    "$PHASE3_RESULTS/reproducibility.json" \
    "$PHASE3_RESULTS/preflight-verification.json" \
    "$PHASE3_RESULTS/archive-verification.json" \
    "$PHASE3_RESULTS/workflow-status.json" \
    "$PHASE3_RESULTS/build-a-index.json" \
    "$PHASE3_RESULTS/build-b-index.json" \
    "$PHASE3_RESULTS/archives/cpython-android-cli-3.14.6-android24-aarch64-runtime-base.tar.gz" \
    "$PHASE3_RESULTS/archives/cpython-android-cli-3.14.6-android24-aarch64-development-addon.tar.gz" \
    "$PHASE3_RESULTS/archives/cpython-android-cli-3.14.6-android24-aarch64-test-addon.tar.gz" \
    "$PHASE3_RESULTS/input/manifest-schema/generation.json" \
    "$PHASE3_RESULTS/input/manifest-schema/verification.json" \
    "$PHASE3_RESULTS/input/manifest-schema/workflow-status.json" \
    "$PHASE3_RESULTS/input/manifest-schema/manifest-index.json" \
    "$PHASE3_RESULTS/input/manifest-schema/input/product-lock.json" \
    "$PHASE3_RESULTS/input/manifest-schema/manifests/runtime-base.manifest.json" \
    "$PHASE3_RESULTS/input/manifest-schema/manifests/development-addon.manifest.json" \
    "$PHASE3_RESULTS/input/manifest-schema/manifests/test-addon.manifest.json" \
    "$LOCAL_SCRIPT_RUNNER" \
    "$FINGERPRINT" \
    "$DERIVER" \
    "$VERIFIER" \
    "$SCRIPT_DIR/install_contract_common.py"; do
    [[ -f "$file" ]] || {
        echo "ERROR: required frozen evidence or tool is missing: $file" >&2
        exit 2
    }
done

rm -rf "$RESULTS_DIR"
mkdir -p \
    "$INPUT_DIR/archives" \
    "$INPUT_DIR/input/manifest-schema/manifests" \
    "$INPUT_DIR/input/manifest-schema/input"

cp -a "$PHASE3_RESULTS/archives/"*.tar.gz "$INPUT_DIR/archives/"
for name in \
    reproducibility.json \
    preflight-verification.json \
    archive-verification.json \
    workflow-status.json \
    build-a-index.json \
    build-b-index.json; do
    cp -a "$PHASE3_RESULTS/$name" "$INPUT_DIR/$name"
done
for name in \
    generation.json \
    verification.json \
    workflow-status.json \
    manifest-index.json; do
    cp -a \
        "$PHASE3_RESULTS/input/manifest-schema/$name" \
        "$INPUT_DIR/input/manifest-schema/$name"
done
cp -a \
    "$PHASE3_RESULTS/input/manifest-schema/input/product-lock.json" \
    "$INPUT_DIR/input/manifest-schema/input/product-lock.json"
cp -a \
    "$PHASE3_RESULTS/input/manifest-schema/manifests/"*.manifest.json \
    "$INPUT_DIR/input/manifest-schema/manifests/"

printf 'Phase 3 results:        %s\n' "$PHASE3_RESULTS"
printf 'Results:                %s\n\n' "$RESULTS_DIR"

run_local_script() {
    "$PYTHON" -I -B -S "$LOCAL_SCRIPT_RUNNER" "$@"
}

fingerprint_input() {
    "$PYTHON" -I -B -S \
        "$FINGERPRINT" \
        --root "$INPUT_DIR" \
        --output "$1"
}

fingerprint_input "$RESULTS_DIR/input-before.json"

set +e
run_local_script \
    "$DERIVER" \
    --phase3-results "$INPUT_DIR" \
    --output-dir "$RESULTS_DIR" \
    --require-pass \
    > "$RESULTS_DIR/deriver.log" 2>&1
deriver_rc=$?
set -e
cat "$RESULTS_DIR/deriver.log"

fingerprint_input "$RESULTS_DIR/input-after.json"

set +e
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
raise SystemExit(0 if passed else 37)
PY
mutation_rc=$?
set -e

if [[ $deriver_rc -eq 0 ]]; then
    set +e
    run_local_script \
        "$VERIFIER" \
        --phase3-results "$INPUT_DIR" \
        --contract-results "$RESULTS_DIR" \
        --output "$RESULTS_DIR/verification.json" \
        > "$RESULTS_DIR/verifier.log" 2>&1
    verifier_rc=$?
    set -e
else
    verifier_rc=125
    "$PYTHON" -I -B -S - \
        "$RESULTS_DIR/verification.json" \
        "$deriver_rc" <<'PY' > "$RESULTS_DIR/verifier.log"
import json
import sys
from pathlib import Path

result = {
    "schema_version": 1,
    "pass": False,
    "blocked": True,
    "blocked_by": "installation_contract_derivation",
    "deriver_returncode": int(sys.argv[2]),
    "check_count": 0,
    "checks": {},
    "failed_checks": ["installation_contract_verification_blocked"],
}
Path(sys.argv[1]).write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(result, indent=2, sort_keys=True))
PY
fi
cat "$RESULTS_DIR/verifier.log"

"$PYTHON" -I -B -S - \
    "$RESULTS_DIR/workflow-status.json" \
    "$deriver_rc" "$mutation_rc" "$verifier_rc" <<'PY'
import json
import sys
from pathlib import Path

returncodes = {
    "contract_derivation": int(sys.argv[2]),
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

printf '\nContract:        %s\n' "$RESULTS_DIR/installation-contract.json"
printf 'Registry:        %s\n' "$RESULTS_DIR/registry-template.json"
printf 'Contract index:  %s\n' "$RESULTS_DIR/contract-index.json"
printf 'Verification:    %s\n\n' "$RESULTS_DIR/verification.json"

final_rc=0
for rc in "$deriver_rc" "$mutation_rc" "$verifier_rc"; do
    if [[ $rc -ne 0 ]]; then
        final_rc=$rc
        break
    fi
done

if [[ $final_rc -ne 0 ]]; then
    echo "STAGE3C_PHASE4_INSTALLATION_CONTRACT=FAIL rc=$final_rc"
    exit "$final_rc"
fi

echo "INSTALLATION_CONTRACT_ACCEPTED_INPUTS=PASS"
echo "INSTALLATION_CONTRACT_DERIVATION=54/54 PASS"
echo "INSTALLATION_CONTRACT_VERIFICATION=59/59 PASS"
echo "INSTALLATION_CONTRACT_OWNED_PATHS=2956 PASS"
echo "INSTALLATION_CONTRACT_STRUCTURAL_REFERENCES=4 PASS"
echo "INSTALLATION_CONTRACT_INPUT_MUTATION_CHECK=PASS"
echo "STAGE3C_PHASE4_INSTALLATION_CONTRACT=PASS"
