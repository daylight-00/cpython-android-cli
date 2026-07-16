#!/usr/bin/env bash
# Shared project path and configuration model.
# This file must be sourced.

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "ERROR: source scripts/lib/project-env.sh; do not execute it" >&2
    exit 2
fi

PROJECT_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.." &&
    pwd -P
)"

DEFAULTS_ENV="$PROJECT_ROOT/config/defaults.env"
LOCAL_ENV="$PROJECT_ROOT/.local/env"

[[ -f "$DEFAULTS_ENV" ]] || {
    echo "ERROR: missing project defaults: $DEFAULTS_ENV" >&2
    return 2
}

# shellcheck disable=SC1090
source "$DEFAULTS_ENV"

if [[ -f "$LOCAL_ENV" ]]; then
    # shellcheck disable=SC1090
    source "$LOCAL_ENV"
fi

TARGET_ID="${TARGET_ID:-aarch64-linux-android24}"
BUILD_PROFILE="${BUILD_PROFILE:-release}"

OUT_ROOT="$PROJECT_ROOT/out/$TARGET_ID/$BUILD_PROFILE"
OUT_BIN="$OUT_ROOT/bin"
OUT_META="$OUT_ROOT/metadata"

WORK_ROOT="$PROJECT_ROOT/work"
TERMUX_WORK_ROOT="$WORK_ROOT/termux/stage2c"

PROMOTED_CPYTHON_DEV_PREFIX="$WORK_ROOT/workstation/stage3b-promoted-cpython/prefix"
CPYTHON_PACKAGE_DIR="$OUT_ROOT/cpython"
CPYTHON_PACKAGE_ARCHIVE="$CPYTHON_PACKAGE_DIR/python-$PYTHON_VERSION-$TARGET_HOST.tar.gz"

RESULTS_ROOT="$PROJECT_ROOT/results"
TERMUX_RESULTS_ROOT="$RESULTS_ROOT/termux/stage2c"

DIST_ROOT="$PROJECT_ROOT/dist/$TARGET_ID/$BUILD_PROFILE"

# The stable facade execs Python after sourcing this file. Export every
# tracked default consumed by that Python boundary; shell-local assignments are
# otherwise lost even though they remain visible to shell-only callers.
export \
    PROJECT_ROOT \
    DEFAULTS_ENV \
    LOCAL_ENV \
    TARGET_ID \
    TARGET_HOST \
    ANDROID_API \
    PYTHON_VERSION \
    PYTHON_MM \
    BUILD_PROFILE \
    OUT_ROOT \
    OUT_BIN \
    OUT_META \
    WORK_ROOT \
    TERMUX_WORK_ROOT \
    PROMOTED_CPYTHON_DEV_PREFIX \
    CPYTHON_PACKAGE_DIR \
    CPYTHON_PACKAGE_ARCHIVE \
    RESULTS_ROOT \
    TERMUX_RESULTS_ROOT \
    DIST_ROOT

# Machine-local configuration intentionally uses ordinary assignments in
# .local/env. Mark the names consumed after an exec boundary for export without
# requiring every host configuration to repeat `export`.
export \
    PROJECT_ROLE \
    ANDROID_HOME \
    ANDROID_SDK_ROOT \
    ANDROID_NDK_HOME \
    ANDROID_NDK_ROOT \
    ANDROID_CC \
    ANDROID_CXX \
    ANDROID_AR \
    ANDROID_RANLIB \
    ANDROID_STRIP \
    DRIVER_PYTHON \
    CPYTHON_SOURCE_REPO \
    CPYTHON_SRC \
    CPYTHON_DEV_PREFIX_OVERRIDE \
    SYNC_REMOTE \
    SYNC_REMOTE_PROJECT_ROOT
