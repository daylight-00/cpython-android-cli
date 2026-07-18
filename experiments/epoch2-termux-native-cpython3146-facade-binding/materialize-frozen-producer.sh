#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
# shellcheck disable=SC1091
source "$PROJECT_ROOT/scripts/lib/project-env.sh"

exec python3 "$PROJECT_ROOT/components/standalone/lib/materialize_frozen_producer.py" \
  --root "$PROJECT_ROOT" \
  --binding "$PROJECT_ROOT/components/standalone/contracts/termux-native-cpython3146-producer-binding-v1.json"
