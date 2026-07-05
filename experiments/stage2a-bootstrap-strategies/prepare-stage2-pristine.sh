#!/data/data/com.termux/files/usr/bin/bash
# Prepare a fresh Stage 2 comparison prefix on Termux.
#
# Run this from a directory containing:
#   python-pyconfig-auto
#   python-s2-setenv
#   python-s2-linker-update
#   python-s2-reexec

set -euo pipefail

ARCHIVE="${ARCHIVE:-$HOME/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz}"
WORK_ROOT="${WORK_ROOT:-$HOME/tmp/260704/stage2/pristine-test}"

B0_BIN="${B0_BIN:-$PWD/python-pyconfig-auto}"
SETENV_BIN="${SETENV_BIN:-$PWD/python-s2-setenv}"
UPDATE_BIN="${UPDATE_BIN:-$PWD/python-s2-linker-update}"
REEXEC_BIN="${REEXEC_BIN:-$PWD/python-s2-reexec}"

for f in "$ARCHIVE" "$B0_BIN" "$SETENV_BIN" "$UPDATE_BIN" "$REEXEC_BIN"; do
    [[ -f "$f" ]] || {
        echo "ERROR: required file not found: $f" >&2
        exit 2
    }
done

rm -rf "$WORK_ROOT"
mkdir -p "$WORK_ROOT"

tar -xzf "$ARCHIVE" -C "$WORK_ROOT"

CPYTHON_PREFIX="$WORK_ROOT/prefix"

[[ -x "$CPYTHON_PREFIX/bin/python" ]] || {
    echo "ERROR: expected prefix/bin/python not found" >&2
    exit 3
}

install -m 0755 "$B0_BIN" \
    "$CPYTHON_PREFIX/bin/python-pyconfig-auto"

install -m 0755 "$SETENV_BIN" \
    "$CPYTHON_PREFIX/bin/python-s2-setenv"

install -m 0755 "$UPDATE_BIN" \
    "$CPYTHON_PREFIX/bin/python-s2-linker-update"

install -m 0755 "$REEXEC_BIN" \
    "$CPYTHON_PREFIX/bin/python-s2-reexec"

cat > "$WORK_ROOT/STAGE2_TEST_PREFIX.env" <<EOF
export CPYTHON_PREFIX="$CPYTHON_PREFIX"
export B0_BIN="$CPYTHON_PREFIX/bin/python-pyconfig-auto"
export S2_SETENV_BIN="$CPYTHON_PREFIX/bin/python-s2-setenv"
export S2_UPDATE_BIN="$CPYTHON_PREFIX/bin/python-s2-linker-update"
export S2_REEXEC_BIN="$CPYTHON_PREFIX/bin/python-s2-reexec"
EOF

echo "Prepared Stage 2 comparison prefix:"
echo "  $CPYTHON_PREFIX"
echo
sha256sum \
    "$CPYTHON_PREFIX/bin/python-pyconfig-auto" \
    "$CPYTHON_PREFIX/bin/python-s2-setenv" \
    "$CPYTHON_PREFIX/bin/python-s2-linker-update" \
    "$CPYTHON_PREFIX/bin/python-s2-reexec"
echo
echo "Next:"
echo "  source \"$WORK_ROOT/STAGE2_TEST_PREFIX.env\""
echo "  ./stage2-compare.sh"
