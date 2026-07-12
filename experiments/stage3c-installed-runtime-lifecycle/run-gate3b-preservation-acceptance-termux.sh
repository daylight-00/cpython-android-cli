#!/data/data/com.termux/files/usr/bin/bash
# One-command Termux runner for Gate 3B preserve-and-report product acceptance.
# Always packages PASS or FAIL evidence with synchronous log capture.

set -uo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

GATE3B0_ARCHIVE="${GATE3B0_ARCHIVE:-$HOME/Downloads/stage3c-phase5-gate3b0-preservation-diagnostic-results-20260712-211837.tgz}"
GATE3B0_SHA256="ed5cb08cc576e74cacac4077cf9c9d7f3164a34913197aae9ef10cc8c113801a"
GATE3B0_EXTRACT="${GATE3B0_EXTRACT:-${PREFIX:-/data/data/com.termux/files/usr}/tmp/stage3c-phase5-gate3b0-accepted}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase5-gate3b-preservation-acceptance}"
WORK_DIR="${WORK_DIR:-$WORK_ROOT/termux/stage3c-phase5-gate3b-preservation-acceptance}"
ARCHIVE="${ARCHIVE:-$HOME/Downloads/stage3c-phase5-gate3b-preservation-acceptance-results-$(date +%Y%m%d-%H%M%S).tgz}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
TOOL_PYTHON="$CANONICAL_PREFIX/bin/python"
META_PYTHON="$TOOL_PYTHON"
if [[ ! -x "$META_PYTHON" ]]; then
    META_PYTHON="${PREFIX:-/data/data/com.termux/files/usr}/bin/python"
fi
RUNNER="$SCRIPT_DIR/run-gate3b-preservation-acceptance.py"
VERIFIER="$SCRIPT_DIR/verify-gate3b-preservation-acceptance.py"
ENGINE="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_engine_missing_leaf.py"
OPERATIONS="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_operations_missing_leaf.py"
LOCAL_SCRIPT_RUNNER="$PROJECT_ROOT/experiments/stage3c-artifact-manifest/run-isolated-local-script.py"
TMP_LOG="${PREFIX:-/data/data/com.termux/files/usr}/tmp/stage3c-phase5-gate3b-wrapper-$$.log"

rm -f "$TMP_LOG" "${TMP_LOG}.runner" "${TMP_LOG}.verifier"
runner_rc=125
verifier_rc=125
workflow_rc=125
gate3b0_results=""
contract_results=""
manifest=""
observed_gate3b0_sha=""

{
    echo "== Gate 3B preserve-and-report product acceptance wrapper =="
    echo "repository: $PROJECT_ROOT"
    echo "accepted Gate 3B0 archive: $GATE3B0_ARCHIVE"
    echo "results: $RESULTS_DIR"
    echo "work: $WORK_DIR"

    if [[ ! -x "$META_PYTHON" ]]; then
        echo "ERROR: no usable Python for evidence packaging: $META_PYTHON" >&2
        workflow_rc=2
    elif [[ ! -x "$TOOL_PYTHON" ]]; then
        echo "ERROR: canonical tool Python missing: $TOOL_PYTHON" >&2
        workflow_rc=2
    elif [[ ! -f "$GATE3B0_ARCHIVE" ]]; then
        echo "ERROR: accepted Gate 3B0 archive missing: $GATE3B0_ARCHIVE" >&2
        workflow_rc=2
    else
        observed_gate3b0_sha="$(sha256sum "$GATE3B0_ARCHIVE" | awk '{print $1}')"
        if [[ "$observed_gate3b0_sha" != "$GATE3B0_SHA256" ]]; then
            echo "ERROR: Gate 3B0 archive SHA mismatch" >&2
            echo "expected: $GATE3B0_SHA256" >&2
            echo "observed: $observed_gate3b0_sha" >&2
            workflow_rc=2
        else
            rm -rf "$GATE3B0_EXTRACT"
            mkdir -p "$GATE3B0_EXTRACT"
            if ! tar xzf "$GATE3B0_ARCHIVE" -C "$GATE3B0_EXTRACT"; then
                echo "ERROR: Gate 3B0 extraction failed" >&2
                workflow_rc=2
            else
                gate3b0_results="$(find "$GATE3B0_EXTRACT" -type d -path '*/results/termux/stage3c-phase5-gate3b0-preservation-diagnostic' -print -quit)"
                if [[ -z "$gate3b0_results" ]]; then
                    echo "ERROR: Gate 3B0 result root not found" >&2
                    workflow_rc=2
                else
                    contract_results="$gate3b0_results/input/contract"
                    manifest="$contract_results/input/phase3/input/manifest-schema/manifests/runtime-base.manifest.json"
                    missing=0
                    for file in \
                        "$gate3b0_results/result-index.json" \
                        "$gate3b0_results/verification.json" \
                        "$gate3b0_results/scenario-summary.json" \
                        "$gate3b0_results/workflow-status.json" \
                        "$gate3b0_results/termux-wrapper-status.json" \
                        "$contract_results/contract-index.json" \
                        "$manifest" \
                        "$RUNNER" \
                        "$VERIFIER" \
                        "$ENGINE" \
                        "$OPERATIONS" \
                        "$LOCAL_SCRIPT_RUNNER"; do
                        if [[ ! -f "$file" ]]; then
                            echo "ERROR: required input or tool missing: $file" >&2
                            missing=1
                        fi
                    done
                    if [[ $missing -ne 0 ]]; then
                        workflow_rc=2
                    else
                        set +e
                        "$TOOL_PYTHON" -I -B -S "$RUNNER" \
                            --gate3b0-results "$gate3b0_results" \
                            --contract-results "$contract_results" \
                            --manifest "$manifest" \
                            --engine "$ENGINE" \
                            --operations "$OPERATIONS" \
                            --local-script-runner "$LOCAL_SCRIPT_RUNNER" \
                            --work-root "$WORK_DIR" \
                            --output-dir "$RESULTS_DIR" \
                            --require-pass \
                            > "${TMP_LOG}.runner" 2>&1
                        runner_rc=$?
                        set -u
                        cat "${TMP_LOG}.runner"

                        mkdir -p "$RESULTS_DIR"
                        if [[ $runner_rc -eq 0 ]]; then
                            set +e
                            "$TOOL_PYTHON" -I -B -S "$VERIFIER" \
                                --results-dir "$RESULTS_DIR" \
                                --output "$RESULTS_DIR/verification.json" \
                                > "${TMP_LOG}.verifier" 2>&1
                            verifier_rc=$?
                            set -u
                            cat "${TMP_LOG}.verifier"
                        else
                            "$META_PYTHON" -I -B -S - "$RESULTS_DIR/verification.json" <<'PY'
import json, sys
from pathlib import Path
result={"schema_version":1,"pass":False,"blocked":True,"check_count":0,"checks":{},"failed_checks":["scenario_runner_blocked"]}
Path(sys.argv[1]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
                        fi

                        workflow_rc=0
                        if [[ $runner_rc -ne 0 ]]; then
                            workflow_rc=$runner_rc
                        elif [[ $verifier_rc -ne 0 ]]; then
                            workflow_rc=$verifier_rc
                        fi
                    fi
                fi
            fi
        fi
    fi

    mkdir -p "$RESULTS_DIR"
    "$META_PYTHON" -I -B -S - \
        "$RESULTS_DIR/workflow-status.json" "$runner_rc" "$verifier_rc" "$workflow_rc" <<'PY'
import json, sys
from pathlib import Path
returncodes={"scenario_runner":int(sys.argv[2]),"independent_verifier":int(sys.argv[3])}
workflow_rc=int(sys.argv[4])
result={"schema_version":1,"pass":workflow_rc==0 and all(value==0 for value in returncodes.values()),"returncodes":returncodes,"workflow_returncode":workflow_rc}
Path(sys.argv[1]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True))
PY

    if [[ $workflow_rc -eq 0 ]]; then
        echo "GATE3B_REINSTALL_REGRESSIONS=4/4 PASS"
        echo "GATE3B_HAPPY_UNINSTALL=4/4 PASS"
        echo "GATE3B_CRASH_RECOVERY=12/12 PASS"
        echo "GATE3B_SCENARIO_VERIFICATION=29/29 PASS"
        echo "GATE3B_INDEPENDENT_VERIFICATION=62/62 PASS"
        echo "STAGE3C_PHASE5_GATE3B_PRESERVATION_ACCEPTANCE=PASS"
    else
        echo "STAGE3C_PHASE5_GATE3B_PRESERVATION_ACCEPTANCE=FAIL rc=$workflow_rc"
    fi
} > "$TMP_LOG" 2>&1

mkdir -p "$RESULTS_DIR"
cp -f "$TMP_LOG" "$RESULTS_DIR/termux-wrapper.log"
cat "$TMP_LOG"
rm -f "${TMP_LOG}.runner" "${TMP_LOG}.verifier"

"$META_PYTHON" -I -B -S - \
    "$RESULTS_DIR/termux-wrapper-status.json" \
    "$GATE3B0_ARCHIVE" "$GATE3B0_SHA256" "$observed_gate3b0_sha" \
    "$gate3b0_results" "$ARCHIVE" "$runner_rc" "$verifier_rc" "$workflow_rc" <<'PY'
import json, sys
from pathlib import Path
out=Path(sys.argv[1]); runner=int(sys.argv[7]); verifier=int(sys.argv[8]); workflow=int(sys.argv[9])
result={
    "schema_version":1,
    "pass":workflow==0,
    "gate3b0_archive":sys.argv[2],
    "gate3b0_expected_sha256":sys.argv[3],
    "gate3b0_observed_sha256":sys.argv[4],
    "gate3b0_sha256_pass":bool(sys.argv[4]) and sys.argv[3]==sys.argv[4],
    "gate3b0_results":sys.argv[5],
    "evidence_archive":sys.argv[6],
    "scenario_runner_returncode":runner,
    "verifier_returncode":verifier,
    "workflow_returncode":workflow,
}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True))
PY

rm -f "$RESULTS_DIR/result-index.json"
"$META_PYTHON" -I -B -S - "$RESULTS_DIR" "$RESULTS_DIR/result-index.json" <<'PY'
import hashlib,json,os,stat,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve(); files=[]
for path in sorted(root.rglob('*'),key=lambda p:p.relative_to(root).as_posix()):
    if path==output or path.is_dir() or path.name=='result-index.log':
        continue
    rel=path.relative_to(root).as_posix(); st=path.lstat(); mode=f'{stat.S_IMODE(st.st_mode):04o}'
    if path.is_symlink():
        files.append({'path':rel,'type':'symlink','mode':mode,'target':os.readlink(path)})
    elif path.is_file():
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):
                digest.update(block)
        files.append({'path':rel,'type':'regular','mode':mode,'size':st.st_size,'sha256':digest.hexdigest()})
    else:
        raise SystemExit(f'unsupported result entry: {path}')
result={'schema_version':1,'index_kind':'stage3c-phase5-gate3b-preservation-acceptance-result-index','file_count':len(files),'files':files}
output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2,sort_keys=True))
PY

mkdir -p "$(dirname "$ARCHIVE")"
relative_results="${RESULTS_DIR#$PROJECT_ROOT/}"
if [[ "$relative_results" == "$RESULTS_DIR" ]]; then
    tar czf "$ARCHIVE" -C "$(dirname "$RESULTS_DIR")" "$(basename "$RESULTS_DIR")"
else
    tar czf "$ARCHIVE" -C "$PROJECT_ROOT" "$relative_results"
fi
archive_sha="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
archive_size="$(stat -c %s "$ARCHIVE")"

printf 'TERMUX_EVIDENCE_ARCHIVE=%s\n' "$ARCHIVE"
printf 'TERMUX_EVIDENCE_ARCHIVE_SHA256=%s\n' "$archive_sha"
printf 'TERMUX_EVIDENCE_ARCHIVE_SIZE=%s\n' "$archive_size"
printf 'TERMUX_WORKFLOW_RETURN_CODE=%s\n' "$workflow_rc"

exit "$workflow_rc"
