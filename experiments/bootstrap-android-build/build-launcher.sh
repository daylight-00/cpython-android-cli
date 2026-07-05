#!/usr/bin/env bash
set -euxo pipefail

PYMM=3.14
API=24
TARGET=aarch64-linux-android

: "${ANDROID_HOME:?ANDROID_HOME is not set}"
: "${PREFIX:?PREFIX is not set}"

if [ ! -d "$ANDROID_HOME/ndk" ]; then
  echo "NDK directory not found: $ANDROID_HOME/ndk" >&2
  exit 1
fi

if [ ! -d "$PREFIX/include/python${PYMM}" ]; then
  echo "Python include directory not found: $PREFIX/include/python${PYMM}" >&2
  exit 1
fi

NDK="$(find "$ANDROID_HOME/ndk" -maxdepth 1 -mindepth 1 -type d | sort -V | tail -1)"
TOOLCHAIN="$NDK/toolchains/llvm/prebuilt/linux-x86_64"
CC="$TOOLCHAIN/bin/${TARGET}${API}-clang"

if [ ! -x "$CC" ]; then
  echo "Android clang not found: $CC" >&2
  exit 1
fi

mkdir -p "$PREFIX/bin"

cat > python-launcher.c <<'SRC'
#include <Python.h>

int main(int argc, char **argv) {
    return Py_BytesMain(argc, argv);
}
SRC

"$CC" \
  -fPIE -pie \
  -I"$PREFIX/include/python${PYMM}" \
  python-launcher.c \
  -L"$PREFIX/lib" \
  -lpython${PYMM} -ldl -lm -llog \
  -Wl,-rpath,'$ORIGIN/../lib' \
  -o "$PREFIX/bin/python${PYMM}"

ln -sf "python${PYMM}" "$PREFIX/bin/python3"
ln -sf "python${PYMM}" "$PREFIX/bin/python"

file "$PREFIX/bin/python${PYMM}"
