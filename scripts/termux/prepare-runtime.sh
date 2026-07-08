#!/data/data/com.termux/files/usr/bin/bash
# Assemble a fresh Stage 2-C runtime from the pristine runtime archive
# plus the canonical launcher artifact already present under out/.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../lib/project-env.sh"

CPYTHON_RUNTIME_ARCHIVE="${CPYTHON_RUNTIME_ARCHIVE:-$HOME/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz}"

SOURCE_LAUNCHER="$OUT_BIN/python3.14"
RUNTIME_ROOT="$TERMUX_WORK_ROOT/runtime"
RUNTIME_PREFIX="$RUNTIME_ROOT/prefix"

[[ -f "$CPYTHON_RUNTIME_ARCHIVE" ]] || {
    echo "ERROR: runtime archive not found: $CPYTHON_RUNTIME_ARCHIVE" >&2
    exit 2
}

[[ -f "$SOURCE_LAUNCHER" ]] || {
    echo "ERROR: launcher artifact not found: $SOURCE_LAUNCHER" >&2
    echo "Sync out/$TARGET_ID/$BUILD_PROFILE from the workstation first." >&2
    exit 2
}

rm -rf "$RUNTIME_ROOT"
mkdir -p "$RUNTIME_ROOT"

tar -xzf "$CPYTHON_RUNTIME_ARCHIVE" -C "$RUNTIME_ROOT"

[[ -d "$RUNTIME_PREFIX/bin" ]] || {
    echo "ERROR: extracted prefix/bin not found" >&2
    exit 3
}

install -m 0755 "$SOURCE_LAUNCHER" "$RUNTIME_PREFIX/bin/python3.14"

ln -sfn python3.14 "$RUNTIME_PREFIX/bin/python3"
ln -sfn python3 "$RUNTIME_PREFIX/bin/python"

cat > "$RUNTIME_ROOT/runtime.env" <<EOF
export CPYTHON_PREFIX="$RUNTIME_PREFIX"
export PYTHON_BIN="$RUNTIME_PREFIX/bin/python"
EOF

echo "Prepared Stage 2-C runtime:"
echo "  $RUNTIME_PREFIX"
echo
echo "Launcher artifact:"
echo "  $SOURCE_LAUNCHER"
echo
echo "Next:"
echo "  source \"$RUNTIME_ROOT/runtime.env\""
echo "  \"$RUNTIME_PREFIX/bin/python\" -V"
