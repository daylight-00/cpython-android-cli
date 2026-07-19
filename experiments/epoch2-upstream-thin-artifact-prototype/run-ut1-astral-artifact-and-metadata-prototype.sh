#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
ROOT="${1:?repository root required}"
ARCHIVE="${2:?official archive required}"
SIGSTORE="${3:?sigstore bundle required}"
WORK="${4:?work directory required}"
ARTIFACTS="${5:?artifact directory required}"
PRE_HEAD="${6:?predecessor head required}"
PRE_TREE="${7:?predecessor tree required}"
OUT="experiments/epoch2-upstream-thin-artifact-prototype"
STRIP_TOOL="${STRIP_TOOL:-$(command -v llvm-strip || command -v strip)}"
python3 -B "$ROOT/$OUT/generate_artifact_prototype.py" --root "$ROOT" --archive "$ARCHIVE" --sigstore "$SIGSTORE" --work-dir "$WORK" --artifact-dir "$ARTIFACTS" --output-dir "$OUT" --strip-tool "$STRIP_TOOL"
python3 -B "$ROOT/$OUT/audit_artifact_prototype.py" --root "$ROOT" --output-dir "$OUT" --artifact-dir "$ARTIFACTS"
python3 -B "$ROOT/$OUT/finalize_artifact_prototype.py" --root "$ROOT" --output-dir "$OUT" --predecessor-head "$PRE_HEAD" --predecessor-tree "$PRE_TREE"
python3 -B "$ROOT/$OUT/verify_artifact_prototype.py" --root "$ROOT" --artifact-dir "$ARTIFACTS"
python3 -B "$ROOT/$OUT/test_verify_artifact_prototype.py" --root "$ROOT"
