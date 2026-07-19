#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${HW_T_BUNDLE_OUT_DIR:-$HOME/Downloads}"
REPOSITORY_RC=99
BUNDLE_RC=99
VERIFY_RC=99
SHA_RC=99
ACTION=failed
FAILURE_REASON=unknown
HEAD_OID=unknown
TREE_OID=unknown
BUNDLE_PATH=unknown
SIDECAR_PATH=unknown
finish(){
  printf '%s\n' '===== final status ====='
  printf 'REPOSITORY_RC=%s\nBUNDLE_RC=%s\nVERIFY_RC=%s\nSHA_RC=%s\n' "$REPOSITORY_RC" "$BUNDLE_RC" "$VERIFY_RC" "$SHA_RC"
  printf 'ACTION=%s\nFAILURE_REASON=%s\nHEAD=%s\nTREE=%s\nBUNDLE=%s\nSIDECAR=%s\n' "$ACTION" "$FAILURE_REASON" "$HEAD_OID" "$TREE_OID" "$BUNDLE_PATH" "$SIDECAR_PATH"
}
trap finish EXIT
cd "$ROOT" || { REPOSITORY_RC=1; FAILURE_REASON=repository-unavailable; exit 1; }
branch="$(git branch --show-current 2>/dev/null)" || { REPOSITORY_RC=1; FAILURE_REASON=git-state-unavailable; exit 1; }
HEAD_OID="$(git rev-parse HEAD 2>/dev/null)" || { REPOSITORY_RC=1; FAILURE_REASON=head-unavailable; exit 1; }
TREE_OID="$(git rev-parse HEAD^{tree} 2>/dev/null)" || { REPOSITORY_RC=1; FAILURE_REASON=tree-unavailable; exit 1; }
[[ "$branch" == main ]] || { REPOSITORY_RC=1; FAILURE_REASON=not-main; exit 1; }
[[ -z "$(git status --porcelain)" ]] || { REPOSITORY_RC=1; FAILURE_REASON=worktree-not-clean; exit 1; }
remote_main="$(git rev-parse origin/main 2>/dev/null)" || { REPOSITORY_RC=1; FAILURE_REASON=origin-main-unavailable; exit 1; }
[[ "$remote_main" == "$HEAD_OID" ]] || { REPOSITORY_RC=1; FAILURE_REASON=main-not-equal-origin-main; exit 1; }
REPOSITORY_RC=0
mkdir -p "$OUT_DIR" || { BUNDLE_RC=1; FAILURE_REASON=output-directory-failed; exit 1; }
name="cpython-android-cli-${HEAD_OID}.bundle"
BUNDLE_PATH="$OUT_DIR/$name"
SIDECAR_PATH="$BUNDLE_PATH.sha256"
rm -f "$BUNDLE_PATH" "$SIDECAR_PATH"
git bundle create "$BUNDLE_PATH" main
BUNDLE_RC=$?
[[ "$BUNDLE_RC" == 0 ]] || { FAILURE_REASON=bundle-create-failed; exit 1; }
git bundle verify "$BUNDLE_PATH" >/dev/null
VERIFY_RC=$?
[[ "$VERIFY_RC" == 0 ]] || { FAILURE_REASON=bundle-verify-failed; exit 1; }
(
  cd "$OUT_DIR" && sha256sum "$name" >"$name.sha256"
)
SHA_RC=$?
[[ "$SHA_RC" == 0 ]] || { FAILURE_REASON=sidecar-create-failed; exit 1; }
ACTION=bundle-created-verified
FAILURE_REASON=none
