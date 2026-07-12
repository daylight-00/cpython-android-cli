#!/data/data/com.termux/files/usr/bin/bash
# Run the existing Gate 3B Termux workflow unchanged, then upload its TGZ with rclone.

set -uo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
RUNNER="$SCRIPT_DIR/run-gate3b-preservation-acceptance-termux.sh"
RCLONE_REMOTE="${RCLONE_REMOTE:-drive}"
RCLONE_DEST="${RCLONE_DEST:-ChatGPT-Handoff/inbox/daylight-00/cpython-android-cli/stage3c-phase5-gate3b-preservation-acceptance}"
TMP_LOG="${PREFIX:-/data/data/com.termux/files/usr}/tmp/stage3c-phase5-gate3b-drive-wrapper-$$.log"

rm -f "$TMP_LOG"

set +e
bash "$RUNNER" "$@" 2>&1 | tee "$TMP_LOG"
pipeline_rc=("${PIPESTATUS[@]}")
set -u

workflow_rc="${pipeline_rc[0]}"
tee_rc="${pipeline_rc[1]}"

if [[ "$tee_rc" -ne 0 ]]; then
    printf 'TERMUX_EVIDENCE_RCLONE_UPLOAD=FAIL rc=%s reason=tee\n' "$tee_rc" >&2
    rm -f "$TMP_LOG"
    if [[ "$workflow_rc" -ne 0 ]]; then
        exit "$workflow_rc"
    fi
    exit "$tee_rc"
fi

archive="$(sed -n 's/^TERMUX_EVIDENCE_ARCHIVE=//p' "$TMP_LOG" | tail -n 1)"
expected_sha="$(sed -n 's/^TERMUX_EVIDENCE_ARCHIVE_SHA256=//p' "$TMP_LOG" | tail -n 1)"
expected_size="$(sed -n 's/^TERMUX_EVIDENCE_ARCHIVE_SIZE=//p' "$TMP_LOG" | tail -n 1)"

if [[ -z "$archive" || ! -f "$archive" ]]; then
    echo 'TERMUX_EVIDENCE_RCLONE_UPLOAD=FAIL rc=2 reason=archive-missing' >&2
    rm -f "$TMP_LOG"
    if [[ "$workflow_rc" -ne 0 ]]; then
        exit "$workflow_rc"
    fi
    exit 2
fi

actual_sha="$(sha256sum "$archive" | awk '{print $1}')"
actual_size="$(stat -c %s "$archive")"
if [[ -z "$expected_sha" || "$actual_sha" != "$expected_sha" || -z "$expected_size" || "$actual_size" != "$expected_size" ]]; then
    echo 'TERMUX_EVIDENCE_RCLONE_UPLOAD=FAIL rc=3 reason=local-evidence-mismatch' >&2
    rm -f "$TMP_LOG"
    if [[ "$workflow_rc" -ne 0 ]]; then
        exit "$workflow_rc"
    fi
    exit 3
fi

if ! command -v rclone >/dev/null 2>&1; then
    echo 'TERMUX_EVIDENCE_RCLONE_UPLOAD=FAIL rc=127 reason=rclone-not-found' >&2
    rm -f "$TMP_LOG"
    if [[ "$workflow_rc" -ne 0 ]]; then
        exit "$workflow_rc"
    fi
    exit 127
fi

remote_archive="${RCLONE_REMOTE}:${RCLONE_DEST}/$(basename "$archive")"
set +e
rclone copyto "$archive" "$remote_archive"
rclone_rc=$?
set -u

if [[ "$rclone_rc" -eq 0 ]]; then
    printf 'TERMUX_EVIDENCE_RCLONE_UPLOAD=PASS\n'
    printf 'TERMUX_EVIDENCE_DRIVE_PATH=%s\n' "$remote_archive"
else
    printf 'TERMUX_EVIDENCE_RCLONE_UPLOAD=FAIL rc=%s\n' "$rclone_rc" >&2
fi

rm -f "$TMP_LOG"

if [[ "$workflow_rc" -ne 0 ]]; then
    exit "$workflow_rc"
fi
exit "$rclone_rc"
