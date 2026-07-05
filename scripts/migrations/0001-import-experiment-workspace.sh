#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" ]]; then
    echo "ERROR: not inside a Git repository" >&2
    exit 2
fi

cd "$ROOT"

[[ -d 260703 ]] || { echo "ERROR: expected ./260703" >&2; exit 2; }
[[ -d 260704 ]] || { echo "ERROR: expected ./260704" >&2; exit 2; }

mkdir -p docs/stages config/legacy legacy/duplicates experiments

move_if_exists() {
    local src="$1"
    local dst="$2"

    if [[ -e "$src" || -L "$src" ]]; then
        if [[ -e "$dst" || -L "$dst" ]]; then
            echo "ERROR: destination already exists: $dst" >&2
            exit 3
        fi
        mkdir -p "$(dirname "$dst")"
        mv "$src" "$dst"
        echo "MOVE  $src -> $dst"
    fi
}

move_if_exists "260704/CPYTHON_ANDROID_UV_PROJECT_CONTEXT.md" "docs/PROJECT_CONTEXT.md"
move_if_exists "260704/STAGE1A_BASELINE.md" "docs/stages/STAGE1A_BASELINE.md"
move_if_exists "260704/STAGE1A_BASELINE-1.md" "legacy/duplicates/STAGE1A_BASELINE-1.md"
move_if_exists "260704/STAGE1B_PYCONFIG_FREEZE.md" "docs/stages/STAGE1B_PYCONFIG.md"

move_if_exists "260704/env.sh" "config/legacy/env.sh"
move_if_exists "260704/env-260704.sh" "config/legacy/env-260704.sh"

move_if_exists "260703" "experiments/bootstrap-android-build"
move_if_exists "260704/stage1a" "experiments/stage1a-runtime-baseline"
move_if_exists "260704/stage1b" "experiments/stage1b-pyconfig"
move_if_exists "260704/stage2" "experiments/stage2a-bootstrap-strategies"
move_if_exists "260704/stage2b" "experiments/stage2b-conditional-reexec"

for link in     experiments/stage2a-bootstrap-strategies/python-pyconfig-auto     experiments/stage2a-bootstrap-strategies/python-s2-linker-update     experiments/stage2a-bootstrap-strategies/python-s2-reexec     experiments/stage2a-bootstrap-strategies/python-s2-setenv     experiments/stage2b-conditional-reexec/python-s2-r2
do
    if [[ -L "$link" ]]; then
        echo "REMOVE SYMLINK  $link -> $(readlink "$link")"
        rm "$link"
    fi
done

rmdir 260704 2>/dev/null || true

echo
echo "Phase 1 layout migration complete."
echo
find . -maxdepth 2 -mindepth 1 ! -path './.git*' | sort
