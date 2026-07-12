#!/data/data/com.termux/files/usr/bin/bash
# One-command Termux runner for Gate 2R; always packages PASS or FAIL evidence.

set -uo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

GATE3A_ARCHIVE="${GATE3A_ARCHIVE:-$HOME/Downloads/stage3c-phase5-gate3a-reinstall-repair-acceptance-results-20260712-191758.tgz}"
GATE3A_SHA256="16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142"
GATE3A_EXTRACT="${GATE3A_EXTRACT:-${PREFIX:-/data/data/com.termux/files/usr}/tmp/stage3c-phase5-gate3a-accepted}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase5-gate2r-corrected-engine-relocation}"
WORK_DIR="${WORK_DIR:-$WORK_ROOT/termux/stage3c-phase5-gate2r-corrected-engine-relocation}"
ARCHIVE="${ARCHIVE:-$HOME/Downloads/stage3c-phase5-gate2r-corrected-engine-relocation-results-$(date +%Y%m%d-%H%M%S).tgz}"
RUNNER="$SCRIPT_DIR/run-gate2r-corrected-engine-relocation.sh"
TOOL_PYTHON="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}/bin/python"
TMP_LOG="${PREFIX:-/data/data/com.termux/files/usr}/tmp/stage3c-phase5-gate2r-wrapper-$$.log"

rm -f "$TMP_LOG"
workflow_rc=125
gate3a_results=""

{
    echo "== Gate 2R one-command Termux wrapper =="
    echo "repository: $PROJECT_ROOT"
    echo "gate3a archive: $GATE3A_ARCHIVE"
    echo "results: $RESULTS_DIR"
    echo "work: $WORK_DIR"

    if [[ ! -x "$TOOL_PYTHON" ]]; then
        echo "ERROR: canonical tool Python missing: $TOOL_PYTHON" >&2
        workflow_rc=2
    elif [[ ! -f "$GATE3A_ARCHIVE" ]]; then
        echo "ERROR: accepted Gate 3A archive missing: $GATE3A_ARCHIVE" >&2
        workflow_rc=2
    elif ! printf '%s  %s\n' "$GATE3A_SHA256" "$GATE3A_ARCHIVE" | sha256sum -c -; then
        workflow_rc=2
    else
        rm -rf "$GATE3A_EXTRACT"
        mkdir -p "$GATE3A_EXTRACT"
        if ! tar xzf "$GATE3A_ARCHIVE" -C "$GATE3A_EXTRACT"; then
            workflow_rc=2
        else
            gate3a_results="$(find "$GATE3A_EXTRACT" -type d -path '*/results/termux/stage3c-phase5-gate3a-reinstall-repair-acceptance' -print -quit)"
            if [[ -z "$gate3a_results" ]]; then
                echo "ERROR: Gate 3A result root not found after extraction" >&2
                workflow_rc=2
            else
                GATE3A_RESULTS="$gate3a_results" RESULTS_DIR="$RESULTS_DIR" WORK_DIR="$WORK_DIR" bash "$RUNNER"
                workflow_rc=$?
            fi
        fi
    fi
} > >(tee "$TMP_LOG") 2>&1

mkdir -p "$RESULTS_DIR"
cp -f "$TMP_LOG" "$RESULTS_DIR/termux-wrapper.log"

if [[ -x "$TOOL_PYTHON" ]]; then
    "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR/termux-wrapper-status.json" "$GATE3A_ARCHIVE" "$gate3a_results" "$ARCHIVE" "$workflow_rc" <<'PY'
import json,sys
from pathlib import Path
out=Path(sys.argv[1]); rc=int(sys.argv[5])
result={'schema_version':1,'pass':rc==0,'gate3a_archive':sys.argv[2],'gate3a_results':sys.argv[3],'evidence_archive':sys.argv[4],'workflow_returncode':rc}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2,sort_keys=True))
PY

    rm -f "$RESULTS_DIR/result-index.json"
    "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR" "$RESULTS_DIR/result-index.json" <<'PY'
import hashlib,json,os,stat,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve(); files=[]
for path in sorted(root.rglob('*'),key=lambda p:p.relative_to(root).as_posix()):
    if path==output or path.is_dir() or path.name=='result-index.log': continue
    rel=path.relative_to(root).as_posix(); st=path.lstat(); mode=f'{stat.S_IMODE(st.st_mode):04o}'
    if path.is_symlink(): files.append({'path':rel,'type':'symlink','mode':mode,'target':os.readlink(path)})
    elif path.is_file():
        h=hashlib.sha256()
        with path.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
        files.append({'path':rel,'type':'regular','mode':mode,'size':st.st_size,'sha256':h.hexdigest()})
    else: raise SystemExit(f'unsupported result entry: {path}')
result={'schema_version':1,'index_kind':'stage3c-phase5-gate2r-corrected-engine-relocation-result-index','file_count':len(files),'files':files}
output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2,sort_keys=True))
PY
else
    printf '{"schema_version":1,"pass":false,"workflow_returncode":%s,"error":"canonical tool Python missing"}\n' "$workflow_rc" > "$RESULTS_DIR/termux-wrapper-status.json"
fi

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
