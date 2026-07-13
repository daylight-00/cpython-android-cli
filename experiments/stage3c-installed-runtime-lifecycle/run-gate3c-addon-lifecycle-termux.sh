#!/data/data/com.termux/files/usr/bin/bash
# One-command Termux runner for Gate 3C addon lifecycle/dependency target evidence.
# Packages PASS or FAIL evidence as .tar.zst and preserves real process return codes.

set -uo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

GATE3B_ARCHIVE="${GATE3B_ARCHIVE:-$HOME/.cache/hw-t/authorities/stage3c-phase5-gate3b-preservation-acceptance-results-20260713-024946.tgz}"
GATE3B_SHA256='0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b'
GATE3B_INDEX_SHA256='f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9'
GATE3B_EXTRACT="${GATE3B_EXTRACT:-${PREFIX:-/data/data/com.termux/files/usr}/tmp/stage3c-phase5-gate3b-authority-gate3c}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase5-gate3c-addon-lifecycle}"
WORK_DIR="${WORK_DIR:-$WORK_ROOT/termux/stage3c-phase5-gate3c-addon-lifecycle}"
STAMP="${STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
ARCHIVE="${ARCHIVE:-$HOME/Downloads/stage3c-phase5-gate3c-addon-lifecycle-results-${STAMP}.tar.zst}"
META_PYTHON="${META_PYTHON:-${PREFIX:-/data/data/com.termux/files/usr}/bin/python}"
RUNNER="$SCRIPT_DIR/run-gate3c-addon-lifecycle.py"
VERIFIER="$SCRIPT_DIR/verify-gate3c-addon-lifecycle.py"
MATRIX="$SCRIPT_DIR/gate3c-addon-lifecycle-matrix.json"
ENGINE="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_engine_missing_leaf.py"
OPERATIONS="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_operations_missing_leaf.py"
LOCAL_SCRIPT_RUNNER="$PROJECT_ROOT/experiments/stage3c-artifact-manifest/run-isolated-local-script.py"
TMP_LOG="${PREFIX:-/data/data/com.termux/files/usr}/tmp/stage3c-phase5-gate3c-wrapper-$$.log"

runner_rc=125
verifier_rc=125
workflow_rc=125
observed_gate3b_sha=''
gate3b_results=''
contract_results=''

rm -f "$TMP_LOG" "${TMP_LOG}.runner" "${TMP_LOG}.verifier"
rm -rf "$RESULTS_DIR" "$WORK_DIR"
mkdir -p "$RESULTS_DIR" "$WORK_DIR" "$(dirname "$ARCHIVE")"

{
    echo '== Gate 3C addon lifecycle/dependency target wrapper =='
    echo "repository: $PROJECT_ROOT"
    echo "Gate 3B authority: $GATE3B_ARCHIVE"
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
    for file in "$META_PYTHON" "$GATE3B_ARCHIVE" "$RUNNER" "$VERIFIER" "$MATRIX" "$ENGINE" "$OPERATIONS" "$LOCAL_SCRIPT_RUNNER"; do
        if [[ ! -f "$file" ]]; then
            echo "ERROR: required file missing: $file" >&2
            missing=1
        fi
    done

    if [[ $missing -ne 0 ]]; then
        workflow_rc=2
    else
        observed_gate3b_sha="$(sha256sum "$GATE3B_ARCHIVE" | awk '{print $1}')"
        if [[ "$observed_gate3b_sha" != "$GATE3B_SHA256" ]]; then
            echo 'ERROR: Gate 3B archive SHA-256 mismatch' >&2
            echo "expected: $GATE3B_SHA256" >&2
            echo "observed: $observed_gate3b_sha" >&2
            workflow_rc=2
        else
            set +e
            "$META_PYTHON" -I -B -S - "$GATE3B_ARCHIVE" "$RESULTS_DIR/archive-safety.json" <<'PY'
import json,sys,tarfile
from pathlib import Path,PurePosixPath
archive=Path(sys.argv[1]); output=Path(sys.argv[2])
counts={'regular':0,'directory':0,'link':0,'special':0,'unsafe':0}
with tarfile.open(archive,'r:gz') as tf:
    members=tf.getmembers()
    for member in members:
        path=PurePosixPath(member.name)
        if path.is_absolute() or '..' in path.parts:
            counts['unsafe']+=1
        if member.isfile(): counts['regular']+=1
        elif member.isdir(): counts['directory']+=1
        elif member.issym() or member.islnk(): counts['link']+=1
        else: counts['special']+=1
result={'schema_version':1,'archive':str(archive),'member_count':len(members),'counts':counts,'pass':counts['unsafe']==0 and counts['link']==0 and counts['special']==0}
output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
raise SystemExit(0 if result['pass'] else 2)
PY
            safety_rc=$?
            set +e
            if [[ $safety_rc -ne 0 ]]; then
                workflow_rc=$safety_rc
            else
                rm -rf "$GATE3B_EXTRACT"
                mkdir -p "$GATE3B_EXTRACT"
                if ! tar xzf "$GATE3B_ARCHIVE" -C "$GATE3B_EXTRACT"; then
                    echo 'ERROR: Gate 3B authority extraction failed' >&2
                    workflow_rc=2
                else
                    gate3b_results="$(find "$GATE3B_EXTRACT" -type d -path '*/results/termux/stage3c-phase5-gate3b-preservation-acceptance' -print -quit)"
                    if [[ -z "$gate3b_results" ]]; then
                        echo 'ERROR: Gate 3B result root not found after extraction' >&2
                        workflow_rc=2
                    else
                        contract_results="$gate3b_results/input/contract"
                        observed_index="$(sha256sum "$gate3b_results/result-index.json" | awk '{print $1}')"
                        if [[ "$observed_index" != "$GATE3B_INDEX_SHA256" ]]; then
                            echo 'ERROR: Gate 3B root result-index identity mismatch' >&2
                            workflow_rc=2
                        else
                            set +e
                            "$META_PYTHON" -I -B -S "$RUNNER" \
                                --gate3b-results "$gate3b_results" \
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
value={'schema_version':1,'pass':False,'blocked':True,'check_count':0,'checks':{},'failed_checks':['target_scenario_runner_blocked']}
Path(sys.argv[1]).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
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
    fi

    "$META_PYTHON" -I -B -S - "$RESULTS_DIR/workflow-status.json" "$runner_rc" "$verifier_rc" "$workflow_rc" <<'PY'
import json,sys
from pathlib import Path
runner=int(sys.argv[2]); verifier=int(sys.argv[3]); workflow=int(sys.argv[4])
value={'schema_version':1,'pass':workflow==0 and runner==0 and verifier==0,'returncodes':{'target_scenario_runner':runner,'independent_verifier':verifier},'workflow_returncode':workflow,'claim_boundary':'Target Gate 3C evidence generated; acceptance remains pending independent archive inspection. Gate 3D final uninstall, upgrade, and downgrade remain unclaimed.'}
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
        echo "GATE3C_ADDON_LIFECYCLE_SCENARIOS=${scenario_count}/50 PASS"
        echo "GATE3C_ADDON_LIFECYCLE_INDEPENDENT_VERIFICATION=${verifier_count}/${verifier_count} PASS"
        echo 'STAGE3C_PHASE5_GATE3C_ADDON_LIFECYCLE=PASS'
    else
        echo "STAGE3C_PHASE5_GATE3C_ADDON_LIFECYCLE=FAIL rc=$workflow_rc"
    fi
} > "$TMP_LOG" 2>&1

cp -f "$TMP_LOG" "$RESULTS_DIR/termux-wrapper.log"
cat "$TMP_LOG"
rm -f "${TMP_LOG}.runner" "${TMP_LOG}.verifier"

"$META_PYTHON" -I -B -S - \
    "$RESULTS_DIR/termux-wrapper-status.json" "$GATE3B_ARCHIVE" "$GATE3B_SHA256" "$observed_gate3b_sha" \
    "$gate3b_results" "$ARCHIVE" "$runner_rc" "$verifier_rc" "$workflow_rc" <<'PY'
import json,sys
from pathlib import Path
runner=int(sys.argv[7]); verifier=int(sys.argv[8]); workflow=int(sys.argv[9])
value={'schema_version':1,'pass':workflow==0,'gate3b_archive':sys.argv[2],'gate3b_expected_sha256':sys.argv[3],'gate3b_observed_sha256':sys.argv[4],'gate3b_sha256_pass':bool(sys.argv[4]) and sys.argv[3]==sys.argv[4],'gate3b_results':sys.argv[5],'evidence_archive':sys.argv[6],'target_scenario_runner_returncode':runner,'independent_verifier_returncode':verifier,'workflow_returncode':workflow,'target_gate3c_executed':runner not in (125,),'gate3c_accepted':False,'claim_boundary':'Archive production does not itself close Gate 3C; independent external archive inspection is required.'}
Path(sys.argv[1]).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
print(json.dumps(value,indent=2,sort_keys=True))
PY

rm -f "$RESULTS_DIR/result-index.json"
"$META_PYTHON" -I -B -S - "$RESULTS_DIR" "$RESULTS_DIR/result-index.json" <<'PY'
import hashlib,json,os,stat,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve(); files=[]
for path in sorted(root.rglob('*'),key=lambda p:p.relative_to(root).as_posix()):
    if path==output or path.is_dir(): continue
    rel=path.relative_to(root).as_posix(); st=path.lstat(); mode=f'{stat.S_IMODE(st.st_mode):04o}'
    if path.is_symlink(): files.append({'path':rel,'type':'symlink','mode':mode,'target':os.readlink(path)})
    elif path.is_file():
        h=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''): h.update(block)
        files.append({'path':rel,'type':'regular','mode':mode,'size':st.st_size,'sha256':h.hexdigest()})
    else: raise SystemExit(f'unsupported result entry: {path}')
value={'schema_version':1,'index_kind':'stage3c-phase5-gate3c-addon-lifecycle-result-index','file_count':len(files),'files':files}
output.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
print(json.dumps({'file_count':len(files)},indent=2,sort_keys=True))
PY

case "$ARCHIVE" in
    *.tar.zst) ;;
    *) echo "ERROR: generated archive is not .tar.zst: $ARCHIVE" >&2; exit 44 ;;
esac

relative_results="${RESULTS_DIR#$PROJECT_ROOT/}"
if [[ "$relative_results" == "$RESULTS_DIR" ]]; then
    if tar --help 2>/dev/null | grep -q -- '--zstd'; then
        tar --zstd -cf "$ARCHIVE" -C "$(dirname "$RESULTS_DIR")" "$(basename "$RESULTS_DIR")"
    else
        tar -cf - -C "$(dirname "$RESULTS_DIR")" "$(basename "$RESULTS_DIR")" | zstd -T0 -19 -o "$ARCHIVE"
    fi
else
    if tar --help 2>/dev/null | grep -q -- '--zstd'; then
        tar --zstd -cf "$ARCHIVE" -C "$PROJECT_ROOT" "$relative_results"
    else
        tar -cf - -C "$PROJECT_ROOT" "$relative_results" | zstd -T0 -19 -o "$ARCHIVE"
    fi
fi
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"

printf 'TERMUX_EVIDENCE_ARCHIVE=%s\n' "$ARCHIVE"
printf 'TERMUX_EVIDENCE_ARCHIVE_SHA256=%s\n' "$(awk '{print $1}' "$ARCHIVE.sha256")"
printf 'TERMUX_EVIDENCE_ARCHIVE_SIZE=%s\n' "$(stat -c %s "$ARCHIVE")"
printf 'TERMUX_WORKFLOW_RETURN_CODE=%s\n' "$workflow_rc"
exit "$workflow_rc"
