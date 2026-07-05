#!/data/data/com.termux/files/usr/bin/bash
# Prepare a pristine Stage 1-A prefix from the original pre-patchelf tarball
# and run the validation matrix without touching the currently installed prefix.
#
# Defaults:
#   archive: ~/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz
#   work:    ~/tmp/260704/stage1a/pristine
#
# Requires stage1a-validate-v3.sh in the same directory.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

ARCHIVE="${ARCHIVE:-$HOME/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz}"
WORK_ROOT="${WORK_ROOT:-$HOME/tmp/260704/stage1a/pristine}"
EXTRACT_ROOT="$WORK_ROOT/extracted"
RESULTS_DIR="$WORK_ROOT/results"

VALIDATOR="${VALIDATOR:-$SCRIPT_DIR/stage1a-validate-v3.sh}"

[[ -f "$ARCHIVE" ]] || {
    echo "ERROR: archive not found: $ARCHIVE" >&2
    exit 2
}

[[ -x "$VALIDATOR" ]] || {
    echo "ERROR: validator not executable: $VALIDATOR" >&2
    exit 2
}

rm -rf "$WORK_ROOT"
mkdir -p "$EXTRACT_ROOT" "$RESULTS_DIR"

echo "== Archive =="
echo "$ARCHIVE"
echo

echo "== Archive top entries =="
tar -tzf "$ARCHIVE" | head -40 || true
echo

tar -xzf "$ARCHIVE" -C "$EXTRACT_ROOT"

detect_prefix() {
    local root="$1"

    for candidate in \
        "$root/prefix" \
        "$root/python" \
        "$root/python/prefix"
    do
        if [[ -x "$candidate/bin/python" || -x "$candidate/bin/python3" || -x "$candidate/bin/python3.14" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done

    local python_bin
    python_bin="$(
        find "$root" -type f -path '*/bin/python3.14' -perm -u+x 2>/dev/null \
        | head -n 1
    )"

    if [[ -n "$python_bin" ]]; then
        dirname "$(dirname "$python_bin")"
        return 0
    fi

    return 1
}

CPYTHON_PREFIX="$(detect_prefix "$EXTRACT_ROOT")" || {
    echo "ERROR: could not locate extracted CPython prefix" >&2
    exit 3
}

export CPYTHON_PREFIX

echo "== Pristine prefix =="
echo "$CPYTHON_PREFIX"
echo

READELF="$(command -v readelf || command -v llvm-readelf || true)"
if [[ -n "$READELF" ]]; then
    echo "== Extension dynamic metadata BEFORE validation =="
    for pattern in '_ssl*.so' '_hashlib*.so' '_sqlite3*.so'; do
        file="$(find "$CPYTHON_PREFIX/lib/python3.14/lib-dynload" -maxdepth 1 -type f -name "$pattern" | head -n 1 || true)"
        if [[ -n "$file" ]]; then
            echo
            echo "--- $file"
            "$READELF" -d "$file" | grep -E 'NEEDED|RPATH|RUNPATH|SONAME' || true
        fi
    done
else
    echo "INFO: readelf not available; skipping ELF metadata inspection"
fi

echo
echo "== SHA-256 before validation =="
(
    cd "$CPYTHON_PREFIX"
    find . -type f -print0 | sort -z | xargs -0 sha256sum
) > "$WORK_ROOT/sha256-before.txt"

TERMUX_PREFIX="${TERMUX_PREFIX:-${PREFIX:-/data/data/com.termux/files/usr}}"

echo
echo "== Run Stage 1-A v3 validation in a clean environment =="

env -i \
    HOME="$HOME" \
    PREFIX="$TERMUX_PREFIX" \
    TERMUX_PREFIX="$TERMUX_PREFIX" \
    PATH="$TERMUX_PREFIX/bin:/system/bin" \
    TMPDIR="$TERMUX_PREFIX/tmp" \
    TERM="${TERM:-xterm-256color}" \
    CPYTHON_PREFIX="$CPYTHON_PREFIX" \
    RESULTS_DIR="$RESULTS_DIR" \
    "$VALIDATOR"

echo
echo "== SHA-256 after validation =="
(
    cd "$CPYTHON_PREFIX"
    find . -type f -print0 | sort -z | xargs -0 sha256sum
) > "$WORK_ROOT/sha256-after.txt"

if cmp -s "$WORK_ROOT/sha256-before.txt" "$WORK_ROOT/sha256-after.txt"; then
    echo "Artifact integrity: PASS (validation did not modify prefix files)"
else
    echo "Artifact integrity: FAIL (prefix files changed during validation)"
    diff -u "$WORK_ROOT/sha256-before.txt" "$WORK_ROOT/sha256-after.txt" || true
    exit 4
fi

echo
echo "Pristine retest complete."
echo "Prefix:  $CPYTHON_PREFIX"
echo "Results: $RESULTS_DIR"
