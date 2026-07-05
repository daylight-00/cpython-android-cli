#!/usr/bin/env bash
# Capture provenance and ELF metadata for the Stage 1-A baseline.
#
# Run on the Linux workstation after:
#   source ~/tmp/260704/env.sh
#
# Output:
#   ~/tmp/260704/stage1a/results/host-snapshot-<timestamp>/

set -euo pipefail

: "${PROJECT_TODAY:?source env.sh first}"
: "${CPYTHON_BUILT_PREFIX:?source env.sh first}"
: "${CPYTHON_STAGE1A_PREV_PREFIX:?source env.sh first}"

RESULT_ROOT="${STAGE1A_RESULTS:-$PROJECT_TODAY/stage1a/results}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$RESULT_ROOT/host-snapshot-$STAMP"
mkdir -p "$OUT"

log() {
    printf '\n== %s ==\n' "$*"
}

capture_tree() {
    local prefix="$1"
    local name="$2"

    mkdir -p "$OUT/$name"

    {
        echo "prefix=$prefix"
        echo "captured_at=$(date -Is)"
        echo "uname=$(uname -a)"
    } > "$OUT/$name/context.txt"

    find "$prefix" -type f -o -type l \
        | LC_ALL=C sort \
        > "$OUT/$name/files.txt"

    (
        cd "$prefix"
        find . -type f -print0 \
            | LC_ALL=C sort -z \
            | xargs -0 sha256sum
    ) > "$OUT/$name/sha256.txt"

    find "$prefix" -type f \
        \( -name '*.so' -o -name '*.so.*' -o -path '*/bin/python*' \) \
        -print0 \
        | while IFS= read -r -d '' file; do
            rel="${file#"$prefix"/}"
            safe="${rel//\//__}"
            {
                echo "FILE: $file"
                file "$file" || true
                echo
                readelf -d "$file" 2>&1 || true
            } > "$OUT/$name/elf-$safe.txt"
        done
}

log "Capture built CPython prefix"
capture_tree "$CPYTHON_BUILT_PREFIX" "built-prefix"

log "Capture Stage 1-A launcher-enabled prefix"
capture_tree "$CPYTHON_STAGE1A_PREV_PREFIX" "stage1a-prefix"

log "Capture launcher dynamic section"
LAUNCHER="$CPYTHON_STAGE1A_PREV_PREFIX/bin/python$PYTHON_MM"
if [[ -e "$LAUNCHER" ]]; then
    {
        file "$LAUNCHER"
        echo
        readelf -d "$LAUNCHER"
    } > "$OUT/launcher-readelf.txt"
fi

log "Capture _ssl and its NEEDED/RUNPATH"
SSL_EXT="$(find "$CPYTHON_STAGE1A_PREV_PREFIX/lib/python$PYTHON_MM/lib-dynload" \
    -maxdepth 1 -type f -name '_ssl*.so' | head -n 1 || true)"

if [[ -n "$SSL_EXT" ]]; then
    {
        echo "SSL_EXT=$SSL_EXT"
        file "$SSL_EXT"
        echo
        readelf -d "$SSL_EXT"
    } > "$OUT/ssl-extension-readelf.txt"
fi

for lib in \
    "$CPYTHON_STAGE1A_PREV_PREFIX/lib/libssl_python.so" \
    "$CPYTHON_STAGE1A_PREV_PREFIX/lib/libcrypto_python.so"
do
    if [[ -f "$lib" ]]; then
        safe="$(basename "$lib")"
        {
            file "$lib"
            echo
            readelf -d "$lib"
        } > "$OUT/$safe.readelf.txt"
    fi
done

log "Summary"
echo "Snapshot: $OUT"
echo
echo "Key files:"
find "$OUT" -maxdepth 1 -type f -printf '  %f\n' | sort
