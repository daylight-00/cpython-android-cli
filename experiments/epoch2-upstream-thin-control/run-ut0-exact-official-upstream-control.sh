#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARCHIVE="${1:?usage: $0 ARCHIVE [SIGSTORE] PRE_HEAD PRE_TREE}"
SIGSTORE="${2:-}"
PRE_HEAD="${3:?missing predecessor head}"
PRE_TREE="${4:?missing predecessor tree}"
OUT="$ROOT/experiments/epoch2-upstream-thin-control"
EXPECTED_SHA256="38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5"
PACKAGE_URL="https://www.python.org/ftp/python/3.14.6/python-3.14.6-aarch64-linux-android.tar.gz"
RELEASE_URL="https://www.python.org/downloads/release/python-3146/"
SOURCE_URL="https://www.python.org/ftp/python/3.14.6/Python-3.14.6.tar.xz"
SOURCE_SHA256="143b1dddefaec3bd2e21e3b839b34a2b7fb9842272883c576420d605e9f30c63"

rm -f "$OUT"/{README.md,gate-contract.json,upstream-input-manifest.json,package-and-file-hashes.json,elf-and-extension-inventory.json,dependency-provider-map.json,sysconfig-census.json,package-layout-map.json,provenance-map.json,producer-delta.json,independent-audit.json,upstream-control-authority.json,evidence-freeze.md}

args=(--root "$ROOT" --archive "$ARCHIVE" --expected-sha256 "$EXPECTED_SHA256" --package-url "$PACKAGE_URL" --release-page-url "$RELEASE_URL" --source-url "$SOURCE_URL" --source-sha256 "$SOURCE_SHA256" --predecessor-head "$PRE_HEAD" --predecessor-tree "$PRE_TREE")
if [[ -n "$SIGSTORE" ]]; then args+=(--sigstore "$SIGSTORE"); fi
python3 "$OUT/freeze_upstream_control.py" "${args[@]}"
python3 "$OUT/audit_upstream_control.py" --root "$ROOT" --archive "$ARCHIVE"
python3 "$OUT/finalize_upstream_control.py" --root "$ROOT" --predecessor-head "$PRE_HEAD" --predecessor-tree "$PRE_TREE"
python3 "$OUT/verify_upstream_control.py" --root "$ROOT" --archive "$ARCHIVE"
python3 "$OUT/test_verify_upstream_control.py"
