#!/usr/bin/env bash
# Push only the canonical generated artifact tree to the Termux checkout.
#
# Source code should be synchronized with Git. This script is only for
# generated build output.
#
# Safe default:
#   no --delete unless DELETE_REMOTE=1 is explicitly set.
#
# Dry run:
#   DRY_RUN=1 ./scripts/sync/push-out.sh

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../lib/project-env.sh"

: "${SYNC_REMOTE:?set SYNC_REMOTE in .local/env}"
: "${SYNC_REMOTE_PROJECT_ROOT:?set SYNC_REMOTE_PROJECT_ROOT in .local/env}"

[[ -d "$OUT_ROOT" ]] || {
    echo "ERROR: local output tree not found: $OUT_ROOT" >&2
    exit 2
}

remote_dir="$SYNC_REMOTE_PROJECT_ROOT/out/$TARGET_ID/$BUILD_PROFILE"

args=(
    -a
    -v
    --itemize-changes
)

if [[ "${DRY_RUN:-0}" == "1" ]]; then
    args+=(--dry-run)
fi

if [[ "${DELETE_REMOTE:-0}" == "1" ]]; then
    args+=(--delete)
fi

echo "Source:"
echo "  $OUT_ROOT/"
echo "Destination:"
echo "  $SYNC_REMOTE:$remote_dir/"
echo

rsync \
    "${args[@]}" \
    "$OUT_ROOT/" \
    "$SYNC_REMOTE:$remote_dir/"
