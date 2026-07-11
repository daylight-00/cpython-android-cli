#!/data/data/com.termux/files/usr/bin/bash
# Stage 3-A non-mutating tzdata fallback probe using uv ephemeral dependency injection.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../../scripts/lib/project-env.sh"

RUNTIME_PREFIX="${RUNTIME_PREFIX:-$TERMUX_WORK_ROOT/runtime/prefix}"
PYTHON_BIN="${PYTHON_BIN:-$RUNTIME_PREFIX/bin/python}"
RESULTS_DIR="${RESULTS_DIR:-$RESULTS_ROOT/termux/stage3a-runtime-closure}"
UV_BIN="${UV_BIN:-$(command -v uv || true)}"

[[ -x "$PYTHON_BIN" ]] || {
    echo "ERROR: runtime Python not executable: $PYTHON_BIN" >&2
    exit 2
}

[[ -n "$UV_BIN" && -x "$UV_BIN" ]] || {
    echo "ERROR: uv not found" >&2
    exit 2
}

mkdir -p "$RESULTS_DIR"
OUTPUT_JSON="$RESULTS_DIR/zoneinfo-uv-tzdata-probe.json"

set +e
PYTHONDONTWRITEBYTECODE=1 \
PYTHONNOUSERSITE=1 \
PYTHONSAFEPATH=1 \
PYTHONTZPATH="" \
UV_PYTHON_DOWNLOADS=never \
"$UV_BIN" run \
    --no-project \
    --with tzdata \
    --python "$PYTHON_BIN" \
    "$SCRIPT_DIR/probe-zoneinfo-with-tzdata.py" \
    | tee "$OUTPUT_JSON"
probe_rc=${PIPESTATUS[0]}
set -e

printf '\n'
printf 'Result: %s\n' "$OUTPUT_JSON"
printf '\n'

if [[ $probe_rc -ne 0 ]]; then
    echo "ZONEINFO_UV_TZDATA_PROBE=FAIL rc=$probe_rc"
    exit "$probe_rc"
fi

echo "ZONEINFO_UV_TZDATA_PROBE=PASS"
