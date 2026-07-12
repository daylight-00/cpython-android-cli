#!/data/data/com.termux/files/usr/bin/bash
# Gate 2R: run the frozen relocation workflow with the accepted corrected engine.
set -euo pipefail
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"
GATE3A_RESULTS="${GATE3A_RESULTS:-$RESULTS_ROOT/termux/stage3c-phase5-gate3a-reinstall-repair-acceptance}"
CANONICAL_PREFIX="${CANONICAL_PREFIX:-$WORK_ROOT/termux/stage3b-promoted-runtime/prefix}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3c-phase5-gate2r-corrected-engine-relocation}"
WORK_DIR="${WORK_DIR:-$WORK_ROOT/termux/stage3c-phase5-gate2r-corrected-engine-relocation}"
TOOL_PYTHON="$CANONICAL_PREFIX/bin/python"
FROZEN_BASELINE="$PROJECT_ROOT/experiments/stage3c-installed-runtime-baseline/run-installed-runtime-baseline.sh"
FROZEN_RELOCATION="$PROJECT_ROOT/experiments/stage3c-installed-runtime-relocation/run-installed-runtime-relocation.sh"
ENGINE="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_engine_missing_leaf.py"
OPS="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_operations_missing_leaf.py"
VERIFIER="$SCRIPT_DIR/verify-gate2r-corrected-engine-relocation.py"
PATCH_DIR="$WORK_DIR/patched-tools"
PATCHED_BASELINE="$PATCH_DIR/run-installed-runtime-baseline.sh"
PATCHED_RELOCATION="$PATCH_DIR/run-installed-runtime-relocation.sh"
PHASE4_RESULTS="$GATE3A_RESULTS/input/phase4"
for f in "$GATE3A_RESULTS/result-index.json" "$GATE3A_RESULTS/verification.json" "$GATE3A_RESULTS/workflow-status.json" "$PHASE4_RESULTS/result-index.json" "$FROZEN_BASELINE" "$FROZEN_RELOCATION" "$ENGINE" "$OPS" "$VERIFIER"; do [[ -f "$f" ]] || { echo "ERROR: missing $f" >&2; exit 2; }; done
rm -rf "$RESULTS_DIR" "$WORK_DIR"; mkdir -p "$RESULTS_DIR/input/gate3a" "$PATCH_DIR"; cp -a "$GATE3A_RESULTS"/. "$RESULTS_DIR/input/gate3a"/
"$TOOL_PYTHON" -I -B -S - "$FROZEN_BASELINE" "$FROZEN_RELOCATION" "$PATCHED_BASELINE" "$PATCHED_RELOCATION" "$RESULTS_DIR/patch-authority.json" <<'PY'
import json,sys
from pathlib import Path
base=Path(sys.argv[1]).read_text(); rel=Path(sys.argv[2]).read_text()
old_engine='ENGINE="$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_engine.py"'
new_engine='ENGINE="${ENGINE_OVERRIDE:-$PROJECT_ROOT/experiments/stage3c-installation-recovery/recovery_engine.py}"'
old_baseline='BASELINE_RUNNER="$PROJECT_ROOT/experiments/stage3c-installed-runtime-baseline/run-installed-runtime-baseline.sh"'
new_baseline='BASELINE_RUNNER="${BASELINE_RUNNER_OVERRIDE:-$PROJECT_ROOT/experiments/stage3c-installed-runtime-baseline/run-installed-runtime-baseline.sh}"'
forward='WORK_DIR="$BASELINE_WORK" \\\nbash "$BASELINE_RUNNER" \\'
forward_new='WORK_DIR="$BASELINE_WORK" \\\nENGINE_OVERRIDE="$ENGINE" \\\nbash "$BASELINE_RUNNER" \\'
counts={'baseline_engine_override_count':base.count(old_engine),'relocation_engine_override_count':rel.count(old_engine),'relocation_baseline_override_count':rel.count(old_baseline),'relocation_engine_forward_count':rel.count(forward)}
base=base.replace(old_engine,new_engine); rel=rel.replace(old_engine,new_engine).replace(old_baseline,new_baseline).replace(forward,forward_new)
Path(sys.argv[3]).write_text(base); Path(sys.argv[4]).write_text(rel)
r={'schema_version':1,**counts}; r['pass']=all(v==1 for v in counts.values()); Path(sys.argv[5]).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r['pass'] else 97)
PY
chmod +x "$PATCHED_BASELINE" "$PATCHED_RELOCATION"
"$TOOL_PYTHON" -I -B -S - "$ENGINE" "$OPS" "$RESULTS_DIR/engine-authority.json" <<'PY'
import hashlib,json,sys
from pathlib import Path
e=Path(sys.argv[1]).resolve(); o=Path(sys.argv[2]).resolve(); r={'schema_version':1,'engine_path':str(e),'operations_path':str(o),'engine_sha256':hashlib.sha256(e.read_bytes()).hexdigest(),'operations_sha256':hashlib.sha256(o.read_bytes()).hexdigest()}; r['pass']=r['engine_sha256']=='33b55d94714fb96f401caefe0e72d6587da955a9d0c201f4eb18dfc5193eb87a' and r['operations_sha256']=='61d20c68c7c5234a00328104914b83adc69859acca9791f3b14d9ff969e24021'; Path(sys.argv[3]).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r['pass'] else 98)
PY
set +e
PHASE4_RESULTS="$PHASE4_RESULTS" CANONICAL_PREFIX="$CANONICAL_PREFIX" RESULTS_DIR="$RESULTS_DIR" WORK_DIR="$WORK_DIR/relocation" ENGINE_OVERRIDE="$ENGINE" BASELINE_RUNNER_OVERRIDE="$PATCHED_BASELINE" bash "$PATCHED_RELOCATION" > "$RESULTS_DIR/historical-relocation.log" 2>&1
historical_rc=$?
set -e
cat "$RESULTS_DIR/historical-relocation.log"
cp -a "$RESULTS_DIR/verification.json" "$RESULTS_DIR/historical-relocation-verification.json" 2>/dev/null || true
cp -a "$RESULTS_DIR/workflow-status.json" "$RESULTS_DIR/historical-workflow-status.json" 2>/dev/null || true
final_rc=125
if [[ $historical_rc -eq 0 ]]; then
  set +e; "$TOOL_PYTHON" -I -B -S "$VERIFIER" --results-dir "$RESULTS_DIR" --output "$RESULTS_DIR/verification.json" > "$RESULTS_DIR/gate2r-verifier.log" 2>&1; final_rc=$?; set -e
else
  "$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR/verification.json" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'schema_version':1,'pass':False,'blocked':True,'check_count':0,'checks':{},'failed_checks':['historical_relocation_blocked']},indent=2,sort_keys=True)+'\n')
PY
fi
cat "$RESULTS_DIR/gate2r-verifier.log" 2>/dev/null || cat "$RESULTS_DIR/verification.json"
"$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR/workflow-status.json" "$historical_rc" "$final_rc" <<'PY'
import json,sys
from pathlib import Path
rc={'historical_relocation':int(sys.argv[2]),'gate2r_verification':int(sys.argv[3])}; r={'schema_version':1,'pass':all(v==0 for v in rc.values()),'returncodes':rc}; Path(sys.argv[1]).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,indent=2,sort_keys=True))
PY
"$TOOL_PYTHON" -I -B -S - "$RESULTS_DIR" "$RESULTS_DIR/result-index.json" <<'PY'
import hashlib,json,os,stat,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); rows=[]
for p in sorted(root.rglob('*'),key=lambda x:x.relative_to(root).as_posix()):
 if p==out or p.is_dir() or p.name=='result-index.log': continue
 rel=p.relative_to(root).as_posix(); s=p.lstat(); mode=f'{stat.S_IMODE(s.st_mode):04o}'
 if p.is_symlink(): rows.append({'path':rel,'type':'symlink','mode':mode,'target':os.readlink(p)})
 elif p.is_file():
  h=hashlib.sha256(p.read_bytes()).hexdigest(); rows.append({'path':rel,'type':'regular','mode':mode,'size':s.st_size,'sha256':h})
 else: raise SystemExit(99)
r={'schema_version':1,'index_kind':'stage3c-phase5-gate2r-corrected-engine-relocation-result-index','file_count':len(rows),'files':rows}; out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,indent=2,sort_keys=True))
PY
if [[ $historical_rc -ne 0 ]]; then echo "STAGE3C_PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION=FAIL rc=$historical_rc"; exit "$historical_rc"; fi
if [[ $final_rc -ne 0 ]]; then echo "STAGE3C_PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION=FAIL rc=$final_rc"; exit "$final_rc"; fi
echo "GATE2R_HISTORICAL_RELOCATION=46/46 PASS"
echo "GATE2R_CORRECTED_ENGINE_AUTHORITY=PASS"
echo "GATE2R_VERIFICATION=15/15 PASS"
echo "STAGE3C_PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION=PASS"
