#!/usr/bin/env bash
set -euo pipefail
here="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/generate-gate2-publication-snapshot.py" --output "$here/gate2-publication-snapshot.generated.json"
cmp "$here/gate2-publication-snapshot.json" "$here/gate2-publication-snapshot.generated.json"
rm -f "$here/gate2-publication-snapshot.generated.json"
python3 -B "$here/verify-gate2-publication-snapshot.py"
