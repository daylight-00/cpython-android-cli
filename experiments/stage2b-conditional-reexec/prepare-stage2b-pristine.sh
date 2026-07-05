#!/data/data/com.termux/files/usr/bin/bash
# Prepare a fresh Stage 2-B test prefix on Termux.

set -euo pipefail

ARCHIVE="${ARCHIVE:-$HOME/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz}"
WORK_ROOT="${WORK_ROOT:-$HOME/tmp/260704/stage2b/pristine-test}"
R2_BIN="${R2_BIN:-$PWD/python-s2-r2}"

[[ -f "$ARCHIVE" ]] || {
    echo "ERROR: archive not found: $ARCHIVE" >&2
    exit 2
}

[[ -f "$R2_BIN" ]] || {
    echo "ERROR: R2 launcher not found: $R2_BIN" >&2
    exit 2
}

rm -rf "$WORK_ROOT"
mkdir -p "$WORK_ROOT"

tar -xzf "$ARCHIVE" -C "$WORK_ROOT"

CPYTHON_PREFIX="$WORK_ROOT/prefix"

[[ -x "$CPYTHON_PREFIX/bin/python" ]] || {
    echo "ERROR: expected prefix/bin/python not found" >&2
    exit 3
}

install -m 0755 \
    "$R2_BIN" \
    "$CPYTHON_PREFIX/bin/python-s2-r2"

cat > "$WORK_ROOT/STAGE2B_TEST_PREFIX.env" <<EOF
export CPYTHON_PREFIX="$CPYTHON_PREFIX"
export S2_R2_BIN="$CPYTHON_PREFIX/bin/python-s2-r2"
EOF

echo "Prepared Stage 2-B test prefix:"
echo "  $CPYTHON_PREFIX"
echo
sha256sum "$CPYTHON_PREFIX/bin/python-s2-r2"
echo
echo "Next:"
echo "  source \"$WORK_ROOT/STAGE2B_TEST_PREFIX.env\""
echo "  ./stage2b-validate.sh"
