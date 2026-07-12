#!/data/data/com.termux/files/usr/bin/bash
# One-command Termux runner: verify inputs, execute Gate 3A, and always package evidence.

set -uo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

PHASE4_ARCHIVE="${PHASE4_ARCHIVE:-$HOME/Downloads/stage3c-phase4-integrated-durability-results-20260712-082135.tgz}"
PHASE4I_ARCHIVE="${PHASE4I_ARCHIVE:-$HOME/Downloads/stage3c-phase4-missing-leaf-repair-intervention-results-20260712-180237.tgz}"
PHASE4_EXTRACT="${PHASE4_EXTRACT:-${PREFIX:-/data/data/com.termux/files/usr}/tmp/stage3c-phase4-integrated-durability-accepted}"
PHASE4I_EXTRACT="${PHASE4I_EXTRACT:-${PREFIX:-/data/data/com.termux/files/usr}/tmp/stage3c-phase4-missing-leaf-repair-intervention-accepted}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase5-gate3a-reinstall-repair-acceptance}"
ARCHIVE="${ARCHIVE:-$HOME/Downloads/stage3c-phase5-gate3a-reinstall-repair-acceptance-results-$(date +%Y%m%d-%H%M%S).tgz}"
RUNNER="$SCRIPT_DIR/run-gate3a-product-acceptance.sh"
TOOL_PYTHON="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}/bin/python"
TMP_LOG="${PREFIX:-/data/data/com.termux/files/usr}/tmp/stage3c-phase5-gate3a-termux-wrapper-$$.log"
RC_FILE="${PREFIX:-/data/data/com.termux/files/usr}/tmp/stage3c-phase5-gate3a-termux-wrapper-$$.rc"

EXPECTED_PHASE4_ARCHIVE_SHA256="76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187"
EXPECTED_PHASE4I_ARCHIVE_SHA256="d497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a"

run_workflow() {
    local phase4_results phase4i_results rc

    [[ -x "$TOOL_PYTHON" ]] || { echo "ERROR: canonical tool Python missing: $TOOL_PYTHON" >&2; return 2; }
    [[ -f "$PHASE4_ARCHIVE" ]] || { echo "ERROR: Phase 4 archive missing: $PHASE4_ARCHIVE" >&2; return 2; }
    [[ -f "$PHASE4I_ARCHIVE" ]] || { echo "ERROR: Phase 4I archive missing: $PHASE4I_ARCHIVE" >&2; return 2; }
    [[ -f "$RUNNER" ]] || { echo "ERROR: Gate 3A runner missing: $RUNNER" >&2; return 2; }

    printf '%s  %s\n' "$EXPECTED_PHASE4_ARCHIVE_SHA256" "$PHASE4_ARCHIVE" | sha256sum -c - || return $?
    printf '%s  %s\n' "$EXPECTED_PHASE4I_ARCHIVE_SHA256" "$PHASE4I_ARCHIVE" | sha256sum -c - || return $?

    rm -rf "$PHASE4_EXTRACT" "$PHASE4I_EXTRACT"
    mkdir -p "$PHASE4_EXTRACT" "$PHASE4I_EXTRACT"
    tar xzf "$PHASE4_ARCHIVE" -C "$PHASE4_EXTRACT" || return $?
    tar xzf "$PHASE4I_ARCHIVE" -C "$PHASE4I_EXTRACT" || return $?

    phase4_results="$(find "$PHASE4_EXTRACT" -type d -path '*/results/termux/stage3c-phase4-integrated-durability' -print -quit)"
    phase4i_results="$(find "$PHASE4I_EXTRACT" -type d -path '*/results/termux/stage3c-phase4-missing-leaf-repair-intervention' -print -quit)"
    [[ -n "$phase4_results" ]] || { echo "ERROR: Phase 4 results directory not found" >&2; return 3; }
    [[ -n "$phase4i_results" ]] || { echo "ERROR: Phase 4I results directory not found" >&2; return 3; }

    PHASE4_RESULTS="$phase4_results" \
    PHASE4I_RESULTS="$phase4i_results" \
    RESULTS_DIR="$RESULTS_DIR" \
        bash "$RUNNER"
    rc=$?
    return "$rc"
}

write_wrapper_status() {
    local workflow_rc="$1"
    mkdir -p "$RESULTS_DIR"
    cp -f "$TMP_LOG" "$RESULTS_DIR/termux-wrapper.log"
    "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR/termux-wrapper-status.json" "$workflow_rc" "$PHASE4_ARCHIVE" "$PHASE4I_ARCHIVE" "$ARCHIVE" <<'PY'
import json, sys
from pathlib import Path
out=Path(sys.argv[1])
rc=int(sys.argv[2])
result={
    "schema_version":1,
    "pass":rc==0,
    "workflow_returncode":rc,
    "phase4_archive":sys.argv[3],
    "phase4i_archive":sys.argv[4],
    "evidence_archive":sys.argv[5],
}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
}

rewrite_result_index() {
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

rm -f "$TMP_LOG" "$RC_FILE"
mkdir -p "$(dirname "$ARCHIVE")"

{
    run_workflow
    printf '%s\n' "$?" > "$RC_FILE"
} 2>&1 | tee "$TMP_LOG"

workflow_rc="$(cat "$RC_FILE")"
write_wrapper_status "$workflow_rc"
rewrite_result_index > "$RESULTS_DIR/result-index.log" 2>&1

package_rc=0
tar czf "$ARCHIVE" -C "$PROJECT_ROOT" "results/termux/stage3c-phase5-gate3a-reinstall-repair-acceptance" || package_rc=$?

if [[ $package_rc -eq 0 ]]; then
    archive_sha256="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
    archive_size="$(stat -c '%s' "$ARCHIVE")"
    echo "TERMUX_EVIDENCE_ARCHIVE=$ARCHIVE"
    echo "TERMUX_EVIDENCE_ARCHIVE_SHA256=$archive_sha256"
    echo "TERMUX_EVIDENCE_ARCHIVE_SIZE=$archive_size"
else
    echo "ERROR: evidence archive creation failed: $ARCHIVE" >&2
fi

echo "TERMUX_WORKFLOW_RETURN_CODE=$workflow_rc"
rm -f "$TMP_LOG" "$RC_FILE"

if [[ $package_rc -ne 0 ]]; then
    exit "$package_rc"
fi
exit "$workflow_rc"
