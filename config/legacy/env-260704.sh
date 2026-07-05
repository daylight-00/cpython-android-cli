#!/usr/bin/env bash
# Host workstation environment for the CPython Android CLI + uv project.
#
# Project convention:
#   ~/tmp/YYMMDD/  = daily work area
#
# Current session:
#   260703 = previous day's build/prototype workspace
#   260704 = today's Stage 1-A work area
#
# Usage:
#   source ~/tmp/260704/env.sh
#   stage1a_env_check

# ---------------------------------------------------------------------------
# Daily workspace convention
# ---------------------------------------------------------------------------

export PROJECT_TMP="$HOME/tmp"

export PROJECT_PREV="$PROJECT_TMP/260703"
export PROJECT_TODAY="$PROJECT_TMP/260704"
export PROJECT_TOOLS="$PROJECT_TMP/tools"

# New files, logs, and experiments created today should go here.
export PROJECT_WORK="$PROJECT_TODAY"

# ---------------------------------------------------------------------------
# Android SDK / NDK
# ---------------------------------------------------------------------------

export ANDROID_HOME="$PROJECT_TOOLS/Android"
export ANDROID_SDK_ROOT="$ANDROID_HOME"

# Prefer an SDK-managed NDK under ~/tmp/tools/Android/ndk/<version>.
if [[ -z "${ANDROID_NDK_HOME:-}" && -d "$ANDROID_HOME/ndk" ]]; then
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

# Fallback to the separately unpacked NDK tree.
if [[ -z "${ANDROID_NDK_HOME:-}" && -d "$PROJECT_TOOLS/ndk" ]]; then
    export ANDROID_NDK_HOME="$PROJECT_TOOLS/ndk"
fi

export NDK="${ANDROID_NDK_HOME:-}"

if [[ -n "$NDK" ]]; then
    export ANDROID_TOOLCHAIN="$NDK/toolchains/llvm/prebuilt/linux-x86_64"
fi

# ---------------------------------------------------------------------------
# Target configuration
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Source and upstream artifact inputs
# ---------------------------------------------------------------------------

# CPython source checkout used for Android builds.
export CPYTHON_SRC="$PROJECT_TOOLS/cpython-$PYTHON_VERSION"

# Upstream Python.org Android archive kept in tools/.
export CPYTHON_ANDROID_ARCHIVE="$PROJECT_TOOLS/python-$PYTHON_VERSION-$ANDROID_TARGET.tar.gz"

# ---------------------------------------------------------------------------
# Previous day's build outputs and prototype artifacts
# ---------------------------------------------------------------------------

# IMPORTANT:
# This is a BUILT Python tree from the previous day's work.
# It is not merely the unpacked Python.org archive.
export CPYTHON_BUILT_ROOT="$PROJECT_PREV/python-$PYTHON_VERSION-$ANDROID_TARGET"
export CPYTHON_BUILT_PREFIX="$CPYTHON_BUILT_ROOT/prefix"

# Previous Stage 1-A CLI-adaptation workspace.
# This is where the launcher-enabled prefix was prepared.
export CPYTHON_STAGE1A_PREV_ROOT="$PROJECT_PREV/android-python-work"
export CPYTHON_STAGE1A_PREV_PREFIX="$CPYTHON_STAGE1A_PREV_ROOT/prefix"

# Previous packaged artifact.
export CPYTHON_STAGE1A_PREV_TARBALL="$PROJECT_PREV/cpython-$PYTHON_MM-aarch64-linux-android-for-uv.tar.gz"

# ---------------------------------------------------------------------------
# Today's Stage 1-A workspace
# ---------------------------------------------------------------------------

# Today's work should be isolated from yesterday's build/prototype tree.
export STAGE1A_WORK="$PROJECT_TODAY/stage1a"
export STAGE1A_PREFIX="$STAGE1A_WORK/prefix"
export STAGE1A_RESULTS="$STAGE1A_WORK/results"
export STAGE1A_DIST="$STAGE1A_WORK/dist"

# Default runtime-under-test:
# start from yesterday's launcher-enabled Stage 1-A prefix.
# Override CPYTHON_PREFIX before sourcing if needed.
if [[ -z "${CPYTHON_PREFIX:-}" ]]; then
    export CPYTHON_PREFIX="$CPYTHON_STAGE1A_PREV_PREFIX"
fi

export CPYTHON_BIN="$CPYTHON_PREFIX/bin/python"
export CPYTHON_LIB="$CPYTHON_PREFIX/lib"
export CPYTHON_INCLUDE="$CPYTHON_PREFIX/include/python$PYTHON_MM"

# ---------------------------------------------------------------------------
# PATH helpers
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Sanity report
# ---------------------------------------------------------------------------

stage1a_env_check() {
    local failed=0

    _check_dir() {
        local name="$1"
        local path="$2"

        if [[ -d "$path" ]]; then
            printf '[OK]   %-34s %s\n' "$name" "$path"
        else
            printf '[MISS] %-34s %s\n' "$name" "$path"
            failed=1
        fi
    }

    _check_file() {
        local name="$1"
        local path="$2"

        if [[ -f "$path" ]]; then
            printf '[OK]   %-34s %s\n' "$name" "$path"
        else
            printf '[MISS] %-34s %s\n' "$name" "$path"
            failed=1
        fi
    }

    _check_exec() {
        local name="$1"
        local path="$2"

        if [[ -x "$path" ]]; then
            printf '[OK]   %-34s %s\n' "$name" "$path"
        else
            printf '[MISS] %-34s %s\n' "$name" "$path"
            failed=1
        fi
    }

    echo
    echo "CPython Android CLI project environment"
    echo "---------------------------------------"
    echo "Previous workspace: $PROJECT_PREV"
    echo "Today's workspace:  $PROJECT_TODAY"
    echo

    _check_dir  "ANDROID_HOME"              "$ANDROID_HOME"
    _check_dir  "ANDROID_NDK_HOME"          "${ANDROID_NDK_HOME:-}"
    _check_exec "ANDROID_CC"                "${ANDROID_CC:-}"

    _check_dir  "CPYTHON_SRC"               "$CPYTHON_SRC"
    _check_file "CPYTHON_ANDROID_ARCHIVE"   "$CPYTHON_ANDROID_ARCHIVE"

    _check_dir  "CPYTHON_BUILT_PREFIX"      "$CPYTHON_BUILT_PREFIX"
    _check_dir  "STAGE1A_PREV_PREFIX"       "$CPYTHON_STAGE1A_PREV_PREFIX"
    _check_file "STAGE1A_PREV_TARBALL"      "$CPYTHON_STAGE1A_PREV_TARBALL"

    if [[ -d "$STAGE1A_WORK" ]]; then
        printf '[OK]   %-34s %s\n' "STAGE1A_WORK" "$STAGE1A_WORK"
    else
        printf '[INFO] %-34s %s\n' "STAGE1A_WORK (not created yet)" "$STAGE1A_WORK"
    fi

    if [[ -x "$CPYTHON_BIN" ]]; then
        printf '[OK]   %-34s %s\n' "CPYTHON_BIN under test" "$CPYTHON_BIN"
    else
        printf '[MISS] %-34s %s\n' "CPYTHON_BIN under test" "$CPYTHON_BIN"
        failed=1
    fi

    echo
    echo "Target: ${ANDROID_TARGET}${ANDROID_API}"
    echo "ABI:    $ANDROID_ABI"
    echo "Python: $PYTHON_VERSION"
    echo
    echo "Runtime-under-test prefix:"
    echo "  $CPYTHON_PREFIX"
    echo

    return "$failed"
}

stage1a_prepare_today() {
    mkdir -p \
        "$STAGE1A_WORK" \
        "$STAGE1A_RESULTS" \
        "$STAGE1A_DIST"

    printf 'Prepared today workspace:\n'
    printf '  %s\n' "$STAGE1A_WORK"
}

printf 'Loaded host project environment for 260704.\n'
printf 'Run: stage1a_env_check\n'
printf 'Optional: stage1a_prepare_today\n'
