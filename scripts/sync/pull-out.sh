#!/data/data/com.termux/files/usr/bin/bash
# Pull the canonical generated artifact tree from the build workstation.
#
# This is the counterpart to push-out.sh for network topologies where the
# runtime host can initiate outbound SSH but cannot accept inbound SSH.
#
# Dry run:
#   DRY_RUN=1 bash scripts/sync/pull-out.sh

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../lib/project-env.sh"

: "${ARTIFACT_SOURCE_REMOTE:?set ARTIFACT_SOURCE_REMOTE in .local/env}"
: "${ARTIFACT_SOURCE_PROJECT_ROOT:?set ARTIFACT_SOURCE_PROJECT_ROOT in .local/env}"

source_dir="$ARTIFACT_SOURCE_PROJECT_ROOT/out/$TARGET_ID/$BUILD_PROFILE"

mkdir -p "$OUT_ROOT"

args=(
    -a
    -v
    --itemize-changes
)

if [[ "${DRY_RUN:-0}" == "1" ]]; then
    args+=(--dry-run)
fi

if [[ "${DELETE_LOCAL:-0}" == "1" ]]; then
    args+=(--delete)
fi

echo "Source:"
echo "  $ARTIFACT_SOURCE_REMOTE:$source_dir/"
echo "Destination:"
echo "  $OUT_ROOT/"
echo

rsync \
    "${args[@]}" \
    "$ARTIFACT_SOURCE_REMOTE:$source_dir/" \
    "$OUT_ROOT/"
