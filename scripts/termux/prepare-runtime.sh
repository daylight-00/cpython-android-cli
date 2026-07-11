#!/data/data/com.termux/files/usr/bin/bash
# Assemble a fresh Stage 2-C runtime from the pristine runtime archive
# plus the canonical launcher artifact already present under out/.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/../lib/project-env.sh"

CPYTHON_RUNTIME_ARCHIVE="${CPYTHON_RUNTIME_ARCHIVE:-$CPYTHON_PACKAGE_ARCHIVE}"
CPYTHON_RUNTIME_CHECKSUMS="${CPYTHON_RUNTIME_CHECKSUMS:-$CPYTHON_PACKAGE_DIR/SHA256SUMS}"

SOURCE_LAUNCHER="$OUT_BIN/python3.14"
RUNTIME_ROOT="${RUNTIME_ROOT_OVERRIDE:-$TERMUX_WORK_ROOT/runtime}"
RUNTIME_PREFIX="$RUNTIME_ROOT/prefix"

[[ -f "$CPYTHON_RUNTIME_ARCHIVE" ]] || {
    echo "ERROR: runtime archive not found: $CPYTHON_RUNTIME_ARCHIVE" >&2
    exit 2
}

[[ -f "$CPYTHON_RUNTIME_CHECKSUMS" ]] || {
    echo "ERROR: runtime checksum manifest not found: $CPYTHON_RUNTIME_CHECKSUMS" >&2
    exit 2
}

(
    cd "$(dirname "$CPYTHON_RUNTIME_ARCHIVE")"
    sha256sum -c "$(basename "$CPYTHON_RUNTIME_CHECKSUMS")"
)

[[ -f "$SOURCE_LAUNCHER" ]] || {
    echo "ERROR: launcher artifact not found: $SOURCE_LAUNCHER" >&2
    echo "Sync out/$TARGET_ID/$BUILD_PROFILE from the workstation first." >&2
    exit 2
}

rm -rf "$RUNTIME_ROOT"
mkdir -p "$RUNTIME_ROOT"

tar -xzf "$CPYTHON_RUNTIME_ARCHIVE" -C "$RUNTIME_ROOT"

[[ -d "$RUNTIME_PREFIX/lib/python$PYTHON_MM" ]] || {
    echo "ERROR: extracted Python stdlib not found under: $RUNTIME_PREFIX" >&2
    exit 3
}

[[ -f "$RUNTIME_PREFIX/lib/libpython$PYTHON_MM.so" ]] || {
    echo "ERROR: extracted libpython not found under: $RUNTIME_PREFIX" >&2
    exit 3
}

mkdir -p "$RUNTIME_PREFIX/bin"

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
