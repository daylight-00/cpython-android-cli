#!/data/data/com.termux/files/usr/bin/bash
# Inspect ELF dependency metadata for Stage 1-A native modules.
#
# Run on Termux. Requires readelf (binutils package) or llvm-readelf.

set -euo pipefail

CPYTHON_PREFIX="${CPYTHON_PREFIX:-$HOME/opt/cpython-3.14/prefix}"
CPYTHON_MM="${CPYTHON_MM:-3.14}"
LIBDYN="$CPYTHON_PREFIX/lib/python$CPYTHON_MM/lib-dynload"

READELF="${READELF:-}"
if [[ -z "$READELF" ]]; then
    if command -v readelf >/dev/null 2>&1; then
        READELF="$(command -v readelf)"
    elif command -v llvm-readelf >/dev/null 2>&1; then
        READELF="$(command -v llvm-readelf)"
    else
        echo "ERROR: install binutils or provide READELF=/path/to/readelf" >&2
        exit 2
    fi
fi

inspect_one() {
    local file="$1"

    echo
    echo "================================================================"
    echo "FILE: $file"
    echo "================================================================"

    "$READELF" -d "$file" \
        | grep -E 'NEEDED|RPATH|RUNPATH|SONAME' \
        || true
}

find_one() {
    local pattern="$1"
    find "$LIBDYN" -maxdepth 1 -type f -name "$pattern" | head -n 1
}

SSL_EXT="$(find_one '_ssl*.so')"
HASH_EXT="$(find_one '_hashlib*.so')"
SQLITE_EXT="$(find_one '_sqlite3*.so')"

[[ -n "$SSL_EXT" ]] && inspect_one "$SSL_EXT"
[[ -n "$HASH_EXT" ]] && inspect_one "$HASH_EXT"
[[ -n "$SQLITE_EXT" ]] && inspect_one "$SQLITE_EXT"

for lib in \
    "$CPYTHON_PREFIX/lib/libssl_python.so" \
    "$CPYTHON_PREFIX/lib/libcrypto_python.so" \
    "$CPYTHON_PREFIX/lib/libsqlite3_python.so"
do
    [[ -f "$lib" ]] && inspect_one "$lib"
done

echo
echo "================================================================"
echo "Loader test without LD_LIBRARY_PATH"
echo "================================================================"

env \
    -u PYTHONHOME \
    -u PYTHONPATH \
    -u LD_LIBRARY_PATH \
    "$CPYTHON_PREFIX/bin/python" - <<'PY'
for name in ["_ssl", "_hashlib", "_sqlite3"]:
    try:
        module = __import__(name)
        print(name, "OK", getattr(module, "__file__", None))
    except Exception as exc:
        print(name, "FAIL", repr(exc))
PY
