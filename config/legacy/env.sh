#!/usr/bin/env bash
# Host workstation environment for the CPython Android CLI + uv project.
#
# Usage:
#   source ~/tmp/260704/env.sh
#
# This is for build/packaging work on the Linux workstation.
# Keep it separate from the Termux Stage 1-A runtime environment.

export PROJECT_TMP="$HOME/tmp"
export PROJECT_DAY="$PROJECT_TMP/260704"
export PROJECT_WORK="$PROJECT_TMP/260703"
export PROJECT_TOOLS="$PROJECT_TMP/tools"

# Android SDK / NDK
export ANDROID_HOME="$PROJECT_TOOLS/Android"
export ANDROID_SDK_ROOT="$ANDROID_HOME"

if [[ -z "${ANDROID_NDK_HOME:-}" ]]; then
    if [[ -d "$ANDROID_HOME/ndk" ]]; then
        _ndk_candidate="$(
            find "$ANDROID_HOME/ndk" \
                -maxdepth 1 \
                -mindepth 1 \
                -type d \
                2>/dev/null \
            | sort -V \
            | tail -n 1
        )"
        if [[ -n "$_ndk_candidate" ]]; then
            export ANDROID_NDK_HOME="$_ndk_candidate"
        fi
    fi
fi

if [[ -z "${ANDROID_NDK_HOME:-}" && -d "$PROJECT_TOOLS/ndk" ]]; then
    export ANDROID_NDK_HOME="$PROJECT_TOOLS/ndk"
fi

export NDK="${ANDROID_NDK_HOME:-}"

if [[ -n "$NDK" ]]; then
    export ANDROID_TOOLCHAIN="$NDK/toolchains/llvm/prebuilt/linux-x86_64"
fi

# Target
export PYTHON_VERSION="3.14.6"
export PYTHON_MM="3.14"
export ANDROID_ARCH="aarch64"
export ANDROID_ABI="arm64-v8a"
export ANDROID_TARGET="aarch64-linux-android"
export ANDROID_API="24"

if [[ -n "${ANDROID_TOOLCHAIN:-}" ]]; then
    export ANDROID_CC="$ANDROID_TOOLCHAIN/bin/${ANDROID_TARGET}${ANDROID_API}-clang"
    export ANDROID_CXX="$ANDROID_TOOLCHAIN/bin/${ANDROID_TARGET}${ANDROID_API}-clang++"
    export ANDROID_STRIP="$ANDROID_TOOLCHAIN/bin/llvm-strip"
    export ANDROID_READELF="$ANDROID_TOOLCHAIN/bin/llvm-readelf"
fi

# CPython source and official Android artifact
export CPYTHON_SRC="$PROJECT_TOOLS/cpython-$PYTHON_VERSION"
export CPYTHON_ANDROID_ARCHIVE="$PROJECT_TOOLS/python-$PYTHON_VERSION-$ANDROID_TARGET.tar.gz"

export CPYTHON_ANDROID_OFFICIAL_DIR="$PROJECT_WORK/python-$PYTHON_VERSION-$ANDROID_TARGET"
export CPYTHON_ANDROID_OFFICIAL_PREFIX="$CPYTHON_ANDROID_OFFICIAL_DIR/prefix"

# Current experiment
export CPYTHON_WORK_ROOT="$PROJECT_WORK/android-python-work"
export CPYTHON_PREFIX="$CPYTHON_WORK_ROOT/prefix"
export CPYTHON_BIN="$CPYTHON_PREFIX/bin/python"
export CPYTHON_LIB="$CPYTHON_PREFIX/lib"
export CPYTHON_INCLUDE="$CPYTHON_PREFIX/include/python$PYTHON_MM"

export CPYTHON_STAGE1A_TARBALL="$PROJECT_WORK/cpython-$PYTHON_MM-aarch64-linux-android-for-uv.tar.gz"

_path_prepend() {
    local dir="$1"
    [[ -d "$dir" ]] || return 0
    case ":$PATH:" in
        *":$dir:"*) ;;
        *) PATH="$dir:$PATH" ;;
    esac
}

_path_prepend "$ANDROID_HOME/cmdline-tools/latest/bin"
_path_prepend "$ANDROID_HOME/platform-tools"

if [[ -n "${ANDROID_TOOLCHAIN:-}" ]]; then
    _path_prepend "$ANDROID_TOOLCHAIN/bin"
fi

export PATH
unset -f _path_prepend
unset _ndk_candidate 2>/dev/null || true

stage1a_env_check() {
    local failed=0

    _check_dir() {
        local name="$1"
        local path="$2"
        if [[ -d "$path" ]]; then
            printf '[OK]   %-32s %s\n' "$name" "$path"
        else
            printf '[MISS] %-32s %s\n' "$name" "$path"
            failed=1
        fi
    }

    _check_file() {
        local name="$1"
        local path="$2"
        if [[ -f "$path" ]]; then
            printf '[OK]   %-32s %s\n' "$name" "$path"
        else
            printf '[MISS] %-32s %s\n' "$name" "$path"
            failed=1
        fi
    }

    _check_exec() {
        local name="$1"
        local path="$2"
        if [[ -x "$path" ]]; then
            printf '[OK]   %-32s %s\n' "$name" "$path"
        else
            printf '[MISS] %-32s %s\n' "$name" "$path"
            failed=1
        fi
    }

    echo
    echo "CPython Android CLI project environment"
    echo "---------------------------------------"

    _check_dir  "ANDROID_HOME"            "$ANDROID_HOME"
    _check_dir  "ANDROID_NDK_HOME"        "${ANDROID_NDK_HOME:-}"
    _check_exec "ANDROID_CC"              "${ANDROID_CC:-}"
    _check_dir  "CPYTHON_SRC"             "$CPYTHON_SRC"
    _check_file "CPYTHON_ANDROID_ARCHIVE" "$CPYTHON_ANDROID_ARCHIVE"
    _check_dir  "OFFICIAL_PREFIX"         "$CPYTHON_ANDROID_OFFICIAL_PREFIX"
    _check_dir  "CPYTHON_PREFIX"          "$CPYTHON_PREFIX"

    if [[ -x "$CPYTHON_BIN" ]]; then
        printf '[OK]   %-32s %s\n' "CPYTHON_BIN" "$CPYTHON_BIN"
    else
        printf '[INFO] %-32s %s\n' "CPYTHON_BIN" "$CPYTHON_BIN"
    fi

    echo
    echo "Target: ${ANDROID_TARGET}${ANDROID_API}"
    echo "ABI:    $ANDROID_ABI"
    echo "Python: $PYTHON_VERSION"
    echo

    return "$failed"
}

printf 'Loaded host project environment.\n'
printf 'Run: stage1a_env_check\n'
