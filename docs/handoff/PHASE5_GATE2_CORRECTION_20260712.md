# Stage 3-C Phase 5 Gate 2 Correction Handoff — 2026-07-12

> **Status:** corrected authoritative Termux rerun pending
> **Preserved failure:** `docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_FAILURE.md`

## First target result

```text
STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION=FAIL rc=65
Gate 2 verifier                         45/46 PASS
```

The failed check was:

```text
installation_root_entry_count_717
```

Every relocation, registry, runtime, HTTPS, uv, native-closure, extension-import, stale-prefix, and destination Gate 1 revalidation check passed.

## Root cause

The complete installation root contains 719 entries, not 717:

```text
prefix/                                  1 directory
prefix payload                          714 entries
.cpython-android-cli/                    1 directory
.cpython-android-cli/lock                1 regular file
.cpython-android-cli/registry.json       1 regular file
.cpython-android-cli/transactions/       1 directory
```

The durable lock and empty transaction root are intentional frozen Phase 4 installation state.

Correct complete-root shape:

```text
entry_count       719
directory_count    60
regular_count     656
symlink_count       3
special paths       0
```

## Correction

The Gate 2 verifier still contains exactly 46 checks. The single incorrect `717` check is replaced by an exact complete-root shape check at all three checkpoints:

```text
location A before move
location B immediately after move
location B after all probes
```

No installer, relocation, registry, recovery, durability, runtime, or claim-boundary semantics changed.

## Corrected rerun

```sh
cd "$HOME/projects/cpython-android-cli"

git fetch origin agent/phase5-gate2-installed-relocation
git switch --detach origin/agent/phase5-gate2-installed-relocation

git log -1 --oneline

PHASE4_ARCHIVE="$HOME/Downloads/stage3c-phase4-integrated-durability-results-20260712-082135.tgz"
PHASE4_EXTRACT="$PREFIX/tmp/stage3c-phase4-integrated-durability-accepted"

printf '%s  %s\n' \
  '76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187' \
  "$PHASE4_ARCHIVE" | sha256sum -c -

rm -rf "$PHASE4_EXTRACT"
mkdir -p "$PHASE4_EXTRACT"
tar xzf "$PHASE4_ARCHIVE" -C "$PHASE4_EXTRACT"

PHASE4_RESULTS="$(find "$PHASE4_EXTRACT" \
  -type d \
  -path '*/results/termux/stage3c-phase4-integrated-durability' \
  -print -quit)"

test -n "$PHASE4_RESULTS"

PHASE4_RESULTS="$PHASE4_RESULTS" \
  bash experiments/stage3c-installed-runtime-relocation/run-installed-runtime-relocation.sh
```

## Expected result

```text
Gate 1 prerequisite                  80/80 PASS
location B revalidation              80/80 PASS
Gate 2 verifier                      46/46 PASS
installation-root shape             719/60/656/3 PASS
STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION=PASS
```

Upload a new TGZ. Preserve the first failed archive unchanged.
