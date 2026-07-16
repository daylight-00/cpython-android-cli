#!/usr/bin/env bash
set -euo pipefail

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../.." && pwd)
RESULTS=${E2P1_RESULTS_DIR:-"$ROOT/results/epoch2/e2p1-standalone-artifact-contract"}
mkdir -p "$RESULTS"

export PYTHONDONTWRITEBYTECODE=1

VERIFY_RC=99
TEST_RC=99
DIFF_RC=99

set +e
python3 "$HERE/verify-e2p1-standalone-artifact-contract.py" --root "$ROOT" --output "$RESULTS/verification.json" >"$RESULTS/verification.stdout" 2>"$RESULTS/verification.stderr"
VERIFY_RC=$?
python3 "$HERE/test-verify-e2p1-standalone-artifact-contract.py" --root "$ROOT" --output "$RESULTS/test-verification.json" >"$RESULTS/test-verification.stdout" 2>"$RESULTS/test-verification.stderr"
TEST_RC=$?
git -C "$ROOT" diff --check >"$RESULTS/git-diff-check.stdout" 2>"$RESULTS/git-diff-check.stderr"
DIFF_RC=$?
set -e

python3 - "$RESULTS" "$VERIFY_RC" "$TEST_RC" "$DIFF_RC" <<'PY'
import json
import sys
from pathlib import Path
out = Path(sys.argv[1])
verify_rc, test_rc, diff_rc = map(int, sys.argv[2:])
status = {
    "schema_version": 1,
    "workflow": "epoch2-p1-standalone-artifact-contract",
    "returncodes": {"verification": verify_rc, "negative_tests": test_rc, "git_diff_check": diff_rc},
    "pass": verify_rc == test_rc == diff_rc == 0,
    "claim_boundary": "Repository contract verification only; no real runtime or target claim.",
}
(out / "workflow-status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(status, indent=2, sort_keys=True))
PY

printf 'E2P1_VERIFY_RC=%s\n' "$VERIFY_RC"
printf 'E2P1_TEST_RC=%s\n' "$TEST_RC"
printf 'E2P1_DIFF_RC=%s\n' "$DIFF_RC"
printf 'E2P1_RESULTS=%s\n' "$RESULTS"

if (( VERIFY_RC != 0 || TEST_RC != 0 || DIFF_RC != 0 )); then
    exit 1
fi
printf 'E2P1_STANDALONE_ARTIFACT_CONTRACT=PASS\n'
