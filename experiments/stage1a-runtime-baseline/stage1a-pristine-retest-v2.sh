#!/data/data/com.termux/files/usr/bin/bash
# Prepare a pristine Stage 1-A prefix and validate it without mutating the prefix.
#
# Difference from v1:
#   Python bytecode caches are redirected outside the extracted prefix via
#   PYTHONPYCACHEPREFIX. This preserves normal bytecode-cache behavior while
#   keeping the artifact tree immutable for before/after hashing.
#
# Defaults:
#   archive: ~/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz
#   work:    ~/tmp/260704/stage1a/pristine-v2

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

ARCHIVE="${ARCHIVE:-$HOME/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz}"
WORK_ROOT="${WORK_ROOT:-$HOME/tmp/260704/stage1a/pristine-v2}"
EXTRACT_ROOT="$WORK_ROOT/extracted"
RESULTS_DIR="$WORK_ROOT/results"
PYCACHE_ROOT="$WORK_ROOT/pycache"

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
mkdir -p "$EXTRACT_ROOT" "$RESULTS_DIR" "$PYCACHE_ROOT"

echo "== Archive =="
echo "$ARCHIVE"
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

hash_prefix() {
    local output="$1"

    (
        cd "$CPYTHON_PREFIX"
        find . -type f -print0 \
            | sort -z \
            | xargs -0 sha256sum
    ) > "$output"
}

echo "== SHA-256 before validation =="
hash_prefix "$WORK_ROOT/sha256-before.txt"

TERMUX_PREFIX="${TERMUX_PREFIX:-${PREFIX:-/data/data/com.termux/files/usr}}"

echo
echo "== Run Stage 1-A validation in clean environment =="
echo "Bytecode cache root: $PYCACHE_ROOT"
echo

env -i \
    HOME="$HOME" \
    PREFIX="$TERMUX_PREFIX" \
    TERMUX_PREFIX="$TERMUX_PREFIX" \
    PATH="$TERMUX_PREFIX/bin:/system/bin" \
    TMPDIR="$TERMUX_PREFIX/tmp" \
    TERM="${TERM:-xterm-256color}" \
    PYTHONPYCACHEPREFIX="$PYCACHE_ROOT" \
    CPYTHON_PREFIX="$CPYTHON_PREFIX" \
    RESULTS_DIR="$RESULTS_DIR" \
    "$VALIDATOR"

echo
echo "== SHA-256 after validation =="
hash_prefix "$WORK_ROOT/sha256-after.txt"

if cmp -s "$WORK_ROOT/sha256-before.txt" "$WORK_ROOT/sha256-after.txt"; then
    echo "Artifact integrity: PASS"
    echo "The extracted CPython prefix was not modified."
else
    echo "Artifact integrity: FAIL"
    diff -u "$WORK_ROOT/sha256-before.txt" "$WORK_ROOT/sha256-after.txt" || true
    exit 4
fi

echo
echo "== Bytecode cache summary =="
find "$PYCACHE_ROOT" -type f | wc -l | awk '{print "Generated pyc files outside prefix:", $1}'

echo
echo "Pristine retest complete."
echo "Prefix:  $CPYTHON_PREFIX"
echo "Results: $RESULTS_DIR"
echo "Pycache: $PYCACHE_ROOT"
