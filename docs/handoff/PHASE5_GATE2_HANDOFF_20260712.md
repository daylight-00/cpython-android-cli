# Stage 3-C Phase 5 Gate 2 Handoff — 2026-07-12

> **Repository:** `daylight-00/cpython-android-cli`
> **Target:** Termux on Android arm64
> **Current gate:** Stage 3-C Phase 5 Gate 2
> **Authority:** frozen repository contracts plus accepted uploaded TGZ evidence
> **Correction authority:** `PHASE5_GATE2_CORRECTION_20260712.md`

## Executive state

```text
Stage 3-C Phases 1–4
  FROZEN

Stage 3-C Phase 5 Gate 1
  FROZEN PASS
  80/80

Stage 3-C Phase 5 Gate 2
  ACTIVE
  corrected authoritative Termux rerun pending
```

Gate 1 final evidence is recorded in:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_RESULT.md
```

The first Gate 2 target failure is preserved in:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_FAILURE.md
```

The first run passed every relocation and destination-runtime component but exposed an incorrect `717` complete-root count in the Gate 2 verifier. The corrected shape is `719` entries.

## Gate 1 frozen identity

```text
corrected archive sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

portable installed-payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

manifest / registry owned rows
  714 / 714 exact

native closure
  81 ELF
  329 edges
  0 unresolved

extension imports
  67/67
```

## Gate 2 question

> Does the installed runtime remain exact, registered, functional, natively closed, and free of stale source-location references after the complete installation root is moved to a second location?

## Mandatory design boundary

The workflow must move:

```text
installation/
├── prefix/                              714 payload entries
└── .cpython-android-cli/
    ├── lock
    ├── registry.json
    └── transactions/
```

Expected complete-root shape:

```text
entries          719
directories       60
regular files    656
symlinks            3
special             0
```

The workflow must not claim success by:

```text
moving only prefix/
reassembling a new prefix at location B
synthesizing or rewriting the registry
omitting the lock or transactions root
using the Stage 3-B promoted prefix as the runtime under test
skipping the Gate 1 80-check prerequisite
accepting console markers without machine evidence
```

Gate 2 is intentionally limited to a same-filesystem rename-style move. Cross-filesystem copy relocation remains outside the claim.

## Current implementation

```text
experiments/stage3c-installed-runtime-relocation/
├── README.md
├── run-installed-runtime-relocation.sh
└── verify-installed-runtime-relocation.py
```

The runner:

```text
1. reruns Gate 1 at location A
2. requires Gate 1 80/80 PASS
3. fingerprints the prefix, complete installation root, and registry
4. moves installation/ to location B on the same filesystem
5. requires device equality and inode preservation
6. verifies the registry through the frozen engine at B
7. reruns runtime, HTTPS, smoke, uv, closure, and extension probes
8. reruns the complete Gate 1 80-check verifier against B
9. scans the moved tree and B probe outputs for location-A references
10. runs a corrected 46-check Gate 2 verifier
```

## Corrected rerun

Use a fresh extraction of the accepted Phase 4 TGZ.

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

## Expected final markers

```text
INSTALLED_RUNTIME_RELOCATION_GATE1_PREREQUISITE=80/80 PASS
INSTALLED_RUNTIME_RELOCATION_WHOLE_ROOT_MOVE=PASS
INSTALLED_RUNTIME_RELOCATION_REGISTRY=714/714 PASS
INSTALLED_RUNTIME_RELOCATION_PORTABLE_FIDELITY=PASS
INSTALLED_RUNTIME_RELOCATION_STRICT_MUTATION_CHECK=PASS
INSTALLED_RUNTIME_RELOCATION_STALE_PREFIX=0 PASS
INSTALLED_RUNTIME_RELOCATION_SMOKE=PASS
INSTALLED_RUNTIME_RELOCATION_HTTPS=200 PASS
INSTALLED_RUNTIME_RELOCATION_UV_VENV=PASS
INSTALLED_RUNTIME_RELOCATION_UV_RUN=PASS
INSTALLED_RUNTIME_RELOCATION_NATIVE_CLOSURE=81/329/0 PASS
INSTALLED_RUNTIME_RELOCATION_EXTENSION_IMPORTS=67/67 PASS
INSTALLED_RUNTIME_RELOCATION_REVALIDATION=80/80 PASS
STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION=PASS
```

## Upload command

```sh
RESULTS="$PWD/results/termux/stage3c-phase5-installed-runtime-relocation"
ARCHIVE="$HOME/Downloads/stage3c-phase5-installed-runtime-relocation-root-shape-corrected-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Required independent inspection

After upload, independently verify:

```text
archive SHA-256 and safe members
result-index hash, size, and mode integrity
workflow return codes
baseline Gate 1 verifier 80/80
relocated Gate 1 verifier 80/80
Gate 2 verifier 46/46
complete-root shape 719/60/656/3
same device and preserved installation-root inode
location A absent and location B present
installation-root fingerprint exact across move and probes
strict runtime fingerprint exact across move and probes
portable fingerprint exact at f860caf...
registry JSON exact before and after
engine verify at location B
stale location-A tree matches 0
stale location-A probe matches 0
HTTPS 200
uv venv and uv run identities at B
81 ELF / 329 edges / 0 unresolved
5/5 system SONAME dlopen
67/67 extension imports
absence of pycache and special paths
canonical generated JSON
```

If Gate 2 fails, preserve the TGZ before changing the implementation.

## Gate 2 claim boundary

A PASS proves same-filesystem whole-installation-root relocation and destination revalidation.

It does not prove:

```text
cross-filesystem copy relocation
same-version reinstall or corruption repair
addon composition and removal
exact uninstall preservation
upgrade
downgrade
physical power-loss persistence
```

Gate 3 lifecycle work must not begin until Gate 2 is frozen from authoritative Termux evidence.
