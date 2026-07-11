#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-B Phase 4.3: assemble promoted runtime without touching frozen Stage 2-C.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

CANDIDATE_ROOT="$WORK_ROOT/termux/stage3b-promoted-runtime"

RUNTIME_ROOT_OVERRIDE="$CANDIDATE_ROOT" \
bash "$PROJECT_ROOT/scripts/termux/prepare-runtime.sh"

PREFIX_ROOT="$CANDIDATE_ROOT/prefix"
LAUNCHER="$PREFIX_ROOT/bin/python3.14"

[[ -x "$LAUNCHER" ]] || {
    echo "ERROR: promoted launcher missing after assembly: $LAUNCHER" >&2
    exit 3
}
[[ "$(readlink "$PREFIX_ROOT/bin/python3")" == "python3.14" ]] || {
    echo "ERROR: python3 symlink contract mismatch" >&2
    exit 3
}
[[ "$(readlink "$PREFIX_ROOT/bin/python")" == "python3" ]] || {
    echo "ERROR: python symlink contract mismatch" >&2
    exit 3
}

printf '\nCandidate runtime: %s\n' "$PREFIX_ROOT"
printf 'Launcher SHA-256: '
sha256sum "$LAUNCHER"
echo
echo "STAGE3B_PROMOTED_RUNTIME_ASSEMBLY=PASS"
