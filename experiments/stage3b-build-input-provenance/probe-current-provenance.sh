#!/usr/bin/env bash
# Stage 3-B Phase 1 read-only producer provenance reconstruction.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

: "${ANDROID_CC:?set ANDROID_CC in .local/env}"
: "${CPYTHON_DEV_PREFIX:?set CPYTHON_DEV_PREFIX in .local/env}"

OUTPUT_DIR="${OUTPUT_DIR:-$RESULTS_ROOT/workstation/stage3b-build-input-provenance}"
CPYTHON_SRC_ARG="${CPYTHON_SRC:-}"
RUNTIME_ARCHIVE_ARG="${CPYTHON_RUNTIME_ARCHIVE:-}"

mkdir -p "$OUTPUT_DIR"

args=(
    --project-root "$PROJECT_ROOT"
    --output-dir "$OUTPUT_DIR"
    --android-cc "$ANDROID_CC"
    --cpython-dev-prefix "$CPYTHON_DEV_PREFIX"
)

if [[ -n "$CPYTHON_SRC_ARG" ]]; then
    args+=(--cpython-src "$CPYTHON_SRC_ARG")
fi

if [[ -n "$RUNTIME_ARCHIVE_ARG" ]]; then
    args+=(--runtime-archive "$RUNTIME_ARCHIVE_ARG")
fi

python3 \
    "$SCRIPT_DIR/probe-current-provenance.py" \
    "${args[@]}"

printf '\n'
printf 'Build inputs:  %s\n' "$OUTPUT_DIR/current-build-inputs.json"
printf 'Toolchain:     %s\n' "$OUTPUT_DIR/current-toolchain-identity.json"
printf 'Dependencies:  %s\n' "$OUTPUT_DIR/current-dependency-provenance.tsv"
printf 'Command map:   %s\n' "$OUTPUT_DIR/current-build-command-map.md"
printf 'Evidence files:%s\n' " $OUTPUT_DIR/current-build-evidence-files.tsv"
printf 'Summary:       %s\n' "$OUTPUT_DIR/provenance-summary.json"
printf '\n'
echo "STAGE3B_PROVENANCE_RECONSTRUCTION=COMPLETE"
