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

RESULTS_ROOT="$PROJECT_ROOT/results"
TERMUX_RESULTS_ROOT="$RESULTS_ROOT/termux/stage2c"

DIST_ROOT="$PROJECT_ROOT/dist/$TARGET_ID/$BUILD_PROFILE"

export \
    PROJECT_ROOT \
    TARGET_ID \
    BUILD_PROFILE \
    OUT_ROOT \
    OUT_BIN \
    OUT_META \
    WORK_ROOT \
    TERMUX_WORK_ROOT \
    RESULTS_ROOT \
    TERMUX_RESULTS_ROOT \
    DIST_ROOT
