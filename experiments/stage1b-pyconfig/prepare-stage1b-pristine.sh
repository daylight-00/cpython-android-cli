#!/data/data/com.termux/files/usr/bin/bash
# Prepare a pristine Stage 1-B comparison prefix on Termux.
#
# Expected inputs:
#   ARCHIVE:
#     ~/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz
#
#   AUTO_LAUNCHER:
#     ./python-pyconfig-auto
#
#   HOME_LAUNCHER:
#     ./python-pyconfig-home
#
# Output:
#   ~/tmp/260704/stage1b/pristine-test/prefix
#
# This creates a fresh comparison tree and adds only the B0/B1 launchers.
# The original tarball is never modified.

set -euo pipefail

ARCHIVE="${ARCHIVE:-$HOME/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz}"
WORK_ROOT="${WORK_ROOT:-$HOME/tmp/260704/stage1b/pristine-test}"

AUTO_LAUNCHER="${AUTO_LAUNCHER:-$PWD/python-pyconfig-auto}"
HOME_LAUNCHER="${HOME_LAUNCHER:-$PWD/python-pyconfig-home}"

[[ -f "$ARCHIVE" ]] || {
    echo "ERROR: archive not found: $ARCHIVE" >&2
    exit 2
}

[[ -f "$AUTO_LAUNCHER" ]] || {
    echo "ERROR: B0 launcher not found: $AUTO_LAUNCHER" >&2
    exit 2
}

[[ -f "$HOME_LAUNCHER" ]] || {
    echo "ERROR: B1 launcher not found: $HOME_LAUNCHER" >&2
    exit 2
}

rm -rf "$WORK_ROOT"
mkdir -p "$WORK_ROOT"

echo "== Extract pristine Stage 1-A artifact =="
tar -xzf "$ARCHIVE" -C "$WORK_ROOT"

detect_prefix() {
    local root="$1"

    for candidate in \
        "$root/prefix" \
        "$root/python/prefix" \
        "$root/extracted/prefix"
    do
        if [[ -x "$candidate/bin/python" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done

    local python_bin
    python_bin="$(
        find "$root" \
            -type f \
            -path '*/bin/python' \
            -perm -u+x \
            2>/dev/null \
        | head -n 1
    )"

    if [[ -n "$python_bin" ]]; then
        dirname "$(dirname "$python_bin")"
        return 0
    fi

    return 1
}

CPYTHON_PREFIX="$(detect_prefix "$WORK_ROOT")" || {
    echo "ERROR: could not detect extracted CPython prefix" >&2
    exit 3
}

echo "Prefix:"
echo "  $CPYTHON_PREFIX"
echo

echo "== Baseline launcher =="
file "$CPYTHON_PREFIX/bin/python"

echo
echo "== Install Stage 1-B launchers =="
install -m 0755 \
    "$AUTO_LAUNCHER" \
    "$CPYTHON_PREFIX/bin/python-pyconfig-auto"

install -m 0755 \
    "$HOME_LAUNCHER" \
    "$CPYTHON_PREFIX/bin/python-pyconfig-home"

sha256sum \
    "$CPYTHON_PREFIX/bin/python" \
    "$CPYTHON_PREFIX/bin/python-pyconfig-auto" \
    "$CPYTHON_PREFIX/bin/python-pyconfig-home"

cat > "$WORK_ROOT/STAGE1B_TEST_PREFIX.env" <<EOF
export CPYTHON_PREFIX="$CPYTHON_PREFIX"
export BASE_BIN="$CPYTHON_PREFIX/bin/python"
export AUTO_BIN="$CPYTHON_PREFIX/bin/python-pyconfig-auto"
export HOME_BIN="$CPYTHON_PREFIX/bin/python-pyconfig-home"
EOF

echo
echo "Prepared Stage 1-B comparison prefix."
echo
echo "Environment file:"
echo "  $WORK_ROOT/STAGE1B_TEST_PREFIX.env"
echo
echo "Next:"
echo "  source \"$WORK_ROOT/STAGE1B_TEST_PREFIX.env\""
echo "  ./stage1b-compare.sh"
