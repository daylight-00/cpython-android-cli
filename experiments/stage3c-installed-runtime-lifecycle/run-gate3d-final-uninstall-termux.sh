#!/data/data/com.termux/files/usr/bin/bash
# One-command Termux runner for Gate 3D final uninstall/ownership evidence.
# Produces a .tar.zst archive on PASS or FAIL and preserves real return codes.

set -uo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

GATE3B_ARCHIVE="${GATE3B_ARCHIVE:-$HOME/.cache/hw-t/authorities/stage3c-phase5-gate3b-preservation-acceptance-results-20260713-024946.tgz}"
GATE3C_ARCHIVE="${GATE3C_ARCHIVE:-$HOME/.cache/hw-t/authorities/stage3c-phase5-gate3c-addon-lifecycle-results-20260713T033412Z.tar.zst}"
GATE3B_SHA256='0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b'
GATE3C_SHA256='43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a'
GATE3B_INDEX_SHA256='f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9'
GATE3C_INDEX_SHA256='fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c'
TMP_ROOT="${TMPDIR:-${PREFIX:-/data/data/com.termux/files/usr}/tmp}"
GATE3B_EXTRACT="${GATE3B_EXTRACT:-$TMP_ROOT/stage3c-phase5-gate3b-authority-gate3d}"
GATE3C_EXTRACT="${GATE3C_EXTRACT:-$TMP_ROOT/stage3c-phase5-gate3c-authority-gate3d}"
GATE3C_TAR="$TMP_ROOT/stage3c-phase5-gate3c-authority-gate3d-$$.tar"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase5-gate3d-final-uninstall}"
WORK_DIR="${WORK_DIR:-$WORK_ROOT/termux/stage3c-phase5-gate3d-final-uninstall}"
STAMP="${STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
ARCHIVE="${ARCHIVE:-$HOME/Downloads/stage3c-phase5-gate3d-final-uninstall-results-${STAMP}.tar.zst}"
META_PYTHON="${META_PYTHON:-${PREFIX:-/data/data/com.termux/files/usr}/bin/python}"
RUNNER="$SCRIPT_DIR/run-gate3d-final-uninstall.py"
VERIFIER="$SCRIPT_DIR/verify-gate3d-final-uninstall.py"
FINALIZER="$SCRIPT_DIR/finalize-gate3d-evidence.py"
MATRIX="$SCRIPT_DIR/gate3d-final-uninstall-matrix.json"
ENGINE="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_engine_missing_leaf.py"
OPERATIONS="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_operations_missing_leaf.py"
LOCAL_SCRIPT_RUNNER="$PROJECT_ROOT/experiments/stage3c-artifact-manifest/run-isolated-local-script.py"
TMP_LOG="$TMP_ROOT/stage3c-phase5-gate3d-wrapper-$$.log"

runner_rc=125
verifier_rc=125
tree_safety_rc=125
index_rc=125
workflow_rc=125
observed_gate3b_sha=''
observed_gate3c_sha=''
gate3b_results=''
gate3c_results=''
contract_results=''

mkdir -p "$TMP_ROOT"
rm -f "$TMP_LOG" "${TMP_LOG}.runner" "${TMP_LOG}.verifier" "${TMP_LOG}.index" "$GATE3C_TAR"
rm -rf "$RESULTS_DIR" "$WORK_DIR"
mkdir -p "$RESULTS_DIR" "$WORK_DIR" "$(dirname "$ARCHIVE")"

inspect_tar() {
    local tar_path="$1" output="$2" label="$3"
    "$META_PYTHON" -I -B -S - "$tar_path" "$output" "$label" <<'PY'
import json,sys,tarfile
from pathlib import Path,PurePosixPath
archive=Path(sys.argv[1]); output=Path(sys.argv[2]); label=sys.argv[3]
counts={'regular':0,'directory':0,'symlink':0,'hardlink':0,'special':0,'unsafe':0}
with tarfile.open(archive,'r:*') as tf:
    members=tf.getmembers()
    for member in members:
        path=PurePosixPath(member.name)
        if path.is_absolute() or '..' in path.parts: counts['unsafe']+=1
        if member.isfile(): counts['regular']+=1
        elif member.isdir(): counts['directory']+=1
        elif member.issym(): counts['symlink']+=1
        elif member.islnk(): counts['hardlink']+=1
        else: counts['special']+=1
result={'schema_version':1,'authority':label,'archive':str(archive),'member_count':len(members),'counts':counts,'pass':counts['unsafe']==0 and counts['symlink']==0 and counts['hardlink']==0 and counts['special']==0}
output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
raise SystemExit(0 if result['pass'] else 2)
PY
}

{
    echo '== Gate 3D final uninstall/ownership target wrapper =='
    echo "repository: $PROJECT_ROOT"
    echo "Gate 3B authority: $GATE3B_ARCHIVE"
    echo "Gate 3C authority: $GATE3C_ARCHIVE"
    echo "results: $RESULTS_DIR"
    echo "work: $WORK_DIR"
    echo "archive: $ARCHIVE"

    missing=0
    for command in sha256sum tar zstd find awk date stat; do
        if ! command -v "$command" >/dev/null 2>&1; then
            echo "ERROR: missing required command: $command" >&2
            missing=1
        fi
    done
    for file in "$META_PYTHON" "$GATE3B_ARCHIVE" "$GATE3C_ARCHIVE" "$RUNNER" "$VERIFIER" "$FINALIZER" "$MATRIX" "$ENGINE" "$OPERATIONS" "$LOCAL_SCRIPT_RUNNER"; do
        if [[ ! -f "$file" ]]; then
            echo "ERROR: required file missing: $file" >&2
            missing=1
        fi
    done

    if [[ $missing -ne 0 ]]; then
        workflow_rc=2
    else
        observed_gate3b_sha="$(sha256sum "$GATE3B_ARCHIVE" | awk '{print $1}')"
        observed_gate3c_sha="$(sha256sum "$GATE3C_ARCHIVE" | awk '{print $1}')"
        if [[ "$observed_gate3b_sha" != "$GATE3B_SHA256" || "$observed_gate3c_sha" != "$GATE3C_SHA256" ]]; then
            echo 'ERROR: authority archive SHA-256 mismatch' >&2
            echo "Gate3B expected=$GATE3B_SHA256 observed=$observed_gate3b_sha" >&2
            echo "Gate3C expected=$GATE3C_SHA256 observed=$observed_gate3c_sha" >&2
            workflow_rc=2
        else
            rm -rf "$GATE3B_EXTRACT" "$GATE3C_EXTRACT"
            mkdir -p "$GATE3B_EXTRACT" "$GATE3C_EXTRACT"
            set +e
            inspect_tar "$GATE3B_ARCHIVE" "$RESULTS_DIR/gate3b-archive-safety.json" gate3b
            gate3b_safety_rc=$?
            set +e
            if [[ $gate3b_safety_rc -ne 0 ]]; then
                workflow_rc=$gate3b_safety_rc
            elif ! tar xzf "$GATE3B_ARCHIVE" -C "$GATE3B_EXTRACT"; then
                workflow_rc=2
            elif ! zstd -dc "$GATE3C_ARCHIVE" > "$GATE3C_TAR"; then
                workflow_rc=2
            else
                set +e
                inspect_tar "$GATE3C_TAR" "$RESULTS_DIR/gate3c-archive-safety.json" gate3c
                gate3c_safety_rc=$?
                set +e
                if [[ $gate3c_safety_rc -ne 0 ]]; then
                    workflow_rc=$gate3c_safety_rc
                elif ! tar xf "$GATE3C_TAR" -C "$GATE3C_EXTRACT"; then
                    workflow_rc=2
                else
                    gate3b_results="$(find "$GATE3B_EXTRACT" -type d -path '*/results/termux/stage3c-phase5-gate3b-preservation-acceptance' -print -quit)"
                    gate3c_results="$(find "$GATE3C_EXTRACT" -type d -name target-results -print -quit)"
                    if [[ -z "$gate3b_results" || -z "$gate3c_results" ]]; then
                        echo 'ERROR: authority result root not found' >&2
                        workflow_rc=2
                    else
                        contract_results="$gate3b_results/input/contract"
                        observed_gate3b_index="$(sha256sum "$gate3b_results/result-index.json" | awk '{print $1}')"
                        observed_gate3c_index="$(sha256sum "$gate3c_results/result-index.json" | awk '{print $1}')"
                        if [[ "$observed_gate3b_index" != "$GATE3B_INDEX_SHA256" || "$observed_gate3c_index" != "$GATE3C_INDEX_SHA256" ]]; then
                            echo 'ERROR: authority result-index identity mismatch' >&2
                            workflow_rc=2
                        else
                            set +e
                            "$META_PYTHON" -I -B -S "$RUNNER" \
                                --gate3b-archive "$GATE3B_ARCHIVE" \
                                --gate3b-results "$gate3b_results" \
                                --gate3c-archive "$GATE3C_ARCHIVE" \
                                --gate3c-results "$gate3c_results" \
                                --contract-results "$contract_results" \
                                --matrix "$MATRIX" \
                                --engine "$ENGINE" \
                                --operations "$OPERATIONS" \
                                --local-script-runner "$LOCAL_SCRIPT_RUNNER" \
                                --work-root "$WORK_DIR" \
                                --output-dir "$RESULTS_DIR" \
                                --require-pass \
                                > "${TMP_LOG}.runner" 2>&1
                            runner_rc=$?
                            set +e
                            cat "${TMP_LOG}.runner"
                            if [[ $runner_rc -eq 0 ]]; then
                                set +e
                                "$META_PYTHON" -I -B -S "$VERIFIER" \
                                    --results-dir "$RESULTS_DIR" \
                                    --output "$RESULTS_DIR/verification.json" \
                                    > "${TMP_LOG}.verifier" 2>&1
                                verifier_rc=$?
                                set +e
                                cat "${TMP_LOG}.verifier"
                            else
                                "$META_PYTHON" -I -B -S - "$RESULTS_DIR/verification.json" <<'PY'
import json,sys
from pathlib import Path
value={'schema_version':1,'pass':False,'blocked':True,'check_count':0,'pass_count':0,'checks':{},'failed_checks':['target_scenario_runner_blocked']}
Path(sys.argv[1]).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
PY
                            fi
                            workflow_rc=0
                            if [[ $runner_rc -ne 0 ]]; then workflow_rc=$runner_rc
                            elif [[ $verifier_rc -ne 0 ]]; then workflow_rc=$verifier_rc
                            fi
                        fi
                    fi
                fi
            fi
        fi
    fi

    rm -f "$RESULTS_DIR/result-tree-safety.json" "$RESULTS_DIR/result-index.json"
    set +e
    "$META_PYTHON" -I -B -S "$FINALIZER" \
        --results-dir "$RESULTS_DIR" --phase audit \
        --safety-output "$RESULTS_DIR/result-tree-safety.json" \
        --index-output "$RESULTS_DIR/result-index.json"
    tree_safety_rc=$?
    set +e
    if [[ $workflow_rc -eq 0 && $tree_safety_rc -ne 0 ]]; then workflow_rc=$tree_safety_rc; fi

    "$META_PYTHON" -I -B -S - "$RESULTS_DIR/workflow-status.json" "$runner_rc" "$verifier_rc" "$tree_safety_rc" "$workflow_rc" <<'PY'
import json,sys
from pathlib import Path
runner,verifier,safety,workflow=map(int,sys.argv[2:])
value={'schema_version':1,'pass':workflow==0 and runner==0 and verifier==0 and safety==0,'returncodes':{'target_scenario_runner':runner,'independent_verifier':verifier,'result_tree_safety':safety},'workflow_returncode':workflow,'claim_boundary':'Target Gate 3D evidence generated; acceptance remains pending independent archive inspection. Upgrade and downgrade remain unclaimed.'}
Path(sys.argv[1]).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
print(json.dumps(value,indent=2,sort_keys=True))
PY

    if [[ $workflow_rc -eq 0 ]]; then
        scenario_count="$($META_PYTHON -I -B -S - "$RESULTS_DIR/scenario-summary.json" <<'PY'
import json,sys
print(json.load(open(sys.argv[1]))['pass_count'])
PY
)"
        verifier_count="$($META_PYTHON -I -B -S - "$RESULTS_DIR/verification.json" <<'PY'
import json,sys
print(json.load(open(sys.argv[1]))['check_count'])
PY
)"
        echo "GATE3D_FINAL_UNINSTALL_SCENARIOS=${scenario_count}/44 PASS"
        echo "GATE3D_FINAL_UNINSTALL_INDEPENDENT_VERIFICATION=${verifier_count}/${verifier_count} PASS"
        echo 'STAGE3C_PHASE5_GATE3D_FINAL_UNINSTALL=PASS'
    else
        echo "STAGE3C_PHASE5_GATE3D_FINAL_UNINSTALL=FAIL rc=$workflow_rc"
    fi
} > "$TMP_LOG" 2>&1

cp -f "$TMP_LOG" "$RESULTS_DIR/termux-wrapper.log"
cat "$TMP_LOG"
rm -f "${TMP_LOG}.runner" "${TMP_LOG}.verifier" "$GATE3C_TAR"

"$META_PYTHON" -I -B -S - \
    "$RESULTS_DIR/termux-wrapper-status.json" "$GATE3B_ARCHIVE" "$GATE3B_SHA256" "$observed_gate3b_sha" \
    "$GATE3C_ARCHIVE" "$GATE3C_SHA256" "$observed_gate3c_sha" "$gate3b_results" "$gate3c_results" "$ARCHIVE" \
    "$runner_rc" "$verifier_rc" "$tree_safety_rc" "$workflow_rc" <<'PY'
import json,sys
from pathlib import Path
runner=int(sys.argv[11]); verifier=int(sys.argv[12]); safety=int(sys.argv[13]); workflow=int(sys.argv[14])
value={'schema_version':1,'pass':workflow==0,'gate3b_archive':sys.argv[2],'gate3b_expected_sha256':sys.argv[3],'gate3b_observed_sha256':sys.argv[4],'gate3c_archive':sys.argv[5],'gate3c_expected_sha256':sys.argv[6],'gate3c_observed_sha256':sys.argv[7],'gate3b_results':sys.argv[8],'gate3c_results':sys.argv[9],'evidence_archive':sys.argv[10],'target_scenario_runner_returncode':runner,'independent_verifier_returncode':verifier,'result_tree_safety_returncode':safety,'workflow_returncode':workflow,'target_gate3d_executed':runner not in (125,),'gate3d_accepted':False,'claim_boundary':'Archive production does not itself close Gate 3D; independent external archive inspection is required. Upgrade and downgrade remain unclaimed.'}
Path(sys.argv[1]).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
print(json.dumps(value,indent=2,sort_keys=True))
PY

rm -f "$RESULTS_DIR/result-index.json"
set +e
"$META_PYTHON" -I -B -S "$FINALIZER" \
    --results-dir "$RESULTS_DIR" --phase index \
    --safety-output "$RESULTS_DIR/result-tree-safety.json" \
    --index-output "$RESULTS_DIR/result-index.json" \
    > "${TMP_LOG}.index" 2>&1
index_rc=$?
set +e
cat "${TMP_LOG}.index" | tee -a "$TMP_LOG"
rm -f "${TMP_LOG}.index"
if [[ $workflow_rc -eq 0 && $index_rc -ne 0 ]]; then workflow_rc=$index_rc; fi

"$META_PYTHON" -I -B -S - "$RESULTS_DIR/workflow-status.json" "$RESULTS_DIR/termux-wrapper-status.json" "$index_rc" "$workflow_rc" <<'PY'
import json,sys
from pathlib import Path
workflow_path=Path(sys.argv[1]); wrapper_path=Path(sys.argv[2]); index_rc=int(sys.argv[3]); workflow_rc=int(sys.argv[4])
workflow=json.loads(workflow_path.read_text()); workflow['returncodes']['result_index']=index_rc; workflow['workflow_returncode']=workflow_rc; workflow['pass']=workflow_rc==0 and all(value==0 for value in workflow['returncodes'].values()); workflow_path.write_text(json.dumps(workflow,indent=2,sort_keys=True)+'\n')
wrapper=json.loads(wrapper_path.read_text()); wrapper['result_index_returncode']=index_rc; wrapper['workflow_returncode']=workflow_rc; wrapper['pass']=workflow_rc==0; wrapper_path.write_text(json.dumps(wrapper,indent=2,sort_keys=True)+'\n')
PY

cp -f "$TMP_LOG" "$RESULTS_DIR/termux-wrapper.log"
# Re-audit the final tree after status/log files are stable, then regenerate the
# root index so both records describe exactly the bytes that will be archived.
rm -f "$RESULTS_DIR/result-index.json"
set +e
"$META_PYTHON" -I -B -S "$FINALIZER" \
    --results-dir "$RESULTS_DIR" --phase audit \
    --safety-output "$RESULTS_DIR/result-tree-safety.json" \
    --index-output "$RESULTS_DIR/result-index.json"
final_safety_rc=$?
set +e
if [[ $workflow_rc -eq 0 && $final_safety_rc -ne 0 ]]; then workflow_rc=$final_safety_rc; fi
if [[ $final_safety_rc -eq 0 ]]; then
    "$META_PYTHON" -I -B -S "$FINALIZER" \
        --results-dir "$RESULTS_DIR" --phase index \
        --safety-output "$RESULTS_DIR/result-tree-safety.json" \
        --index-output "$RESULTS_DIR/result-index.json"
    final_index_rc=$?
else
    final_index_rc=125
fi
if [[ $workflow_rc -eq 0 && $final_index_rc -ne 0 ]]; then workflow_rc=$final_index_rc; fi

# Persist final packaging return codes, then regenerate the index once more so
# its hashes cover the final status bytes.
"$META_PYTHON" -I -B -S - "$RESULTS_DIR/workflow-status.json" "$RESULTS_DIR/termux-wrapper-status.json" "$final_safety_rc" "$final_index_rc" "$workflow_rc" <<'PY'
import json,sys
from pathlib import Path
workflow_path=Path(sys.argv[1]); wrapper_path=Path(sys.argv[2])
final_safety_rc=int(sys.argv[3]); final_index_rc=int(sys.argv[4]); workflow_rc=int(sys.argv[5])
workflow=json.loads(workflow_path.read_text())
workflow['returncodes']['result_tree_safety']=final_safety_rc
workflow['returncodes']['result_index']=final_index_rc
workflow['workflow_returncode']=workflow_rc
workflow['pass']=workflow_rc==0 and all(value==0 for value in workflow['returncodes'].values())
workflow_path.write_text(json.dumps(workflow,indent=2,sort_keys=True)+'\n')
wrapper=json.loads(wrapper_path.read_text())
wrapper['result_tree_safety_returncode']=final_safety_rc
wrapper['result_index_returncode']=final_index_rc
wrapper['workflow_returncode']=workflow_rc
wrapper['pass']=workflow_rc==0
wrapper_path.write_text(json.dumps(wrapper,indent=2,sort_keys=True)+'\n')
PY
if [[ $final_safety_rc -eq 0 && $final_index_rc -eq 0 ]]; then
    rm -f "$RESULTS_DIR/result-index.json"
    "$META_PYTHON" -I -B -S "$FINALIZER" \
        --results-dir "$RESULTS_DIR" --phase index \
        --safety-output "$RESULTS_DIR/result-tree-safety.json" \
        --index-output "$RESULTS_DIR/result-index.json"
    archive_index_rc=$?
    if [[ $workflow_rc -eq 0 && $archive_index_rc -ne 0 ]]; then workflow_rc=$archive_index_rc; fi
else
    archive_index_rc=125
fi

case "$ARCHIVE" in *.tar.zst) ;; *) echo "ERROR: generated archive is not .tar.zst: $ARCHIVE" >&2; exit 44 ;; esac
if tar --help 2>/dev/null | grep -q -- '--zstd'; then
    tar --zstd -cf "$ARCHIVE" -C "$(dirname "$RESULTS_DIR")" "$(basename "$RESULTS_DIR")"
else
    tar -cf - -C "$(dirname "$RESULTS_DIR")" "$(basename "$RESULTS_DIR")" | zstd -T0 -19 -o "$ARCHIVE"
fi
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"

printf 'TERMUX_EVIDENCE_ARCHIVE=%s\n' "$ARCHIVE"
printf 'TERMUX_EVIDENCE_ARCHIVE_SHA256=%s\n' "$(awk '{print $1}' "$ARCHIVE.sha256")"
printf 'TERMUX_EVIDENCE_ARCHIVE_SIZE=%s\n' "$(stat -c %s "$ARCHIVE")"
printf 'TERMUX_WORKFLOW_RETURN_CODE=%s\n' "$workflow_rc"
exit "$workflow_rc"
