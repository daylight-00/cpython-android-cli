# Stage 3-C Phase 5 Gate 2: Installed Runtime Relocation

> **Status:** ACTIVE — authoritative Termux result pending
> **Prerequisite:** frozen Phase 5 Gate 1 PASS
> **Input:** frozen Stage 3-C Phase 4 integrated durability evidence

## Gate question

> Does a runtime installed through the frozen Phase 4 engine remain exact, registered, functional, natively closed, and free of stale source-location references after the complete installation root is moved to a second location?

## Design boundary

This workflow does not introduce a second installer or a new generic relocation engine.

It performs:

```text
frozen Phase 4 input
  → existing Gate 1 installer and 80-check baseline at location A
  → complete installation/ root mv on one filesystem
  → engine verify and complete 80-check revalidation at location B
  → independent Gate 2 move and stale-prefix verifier
```

The moved object is the complete installation root:

```text
installation/
├── prefix/
└── .cpython-android-cli/
    └── registry.json
```

Moving only `prefix/` while leaving the ownership registry behind is not accepted evidence for this gate.

## Accepted Gate 1 authority

```text
Gate 1 archive sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

Gate 1 result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

Gate 1 verifier
  80/80 PASS
```

The Gate 2 workflow reruns the frozen Gate 1 workflow as an in-process prerequisite. It does not trust console markers alone.

## Required relocation checks

```text
location A Gate 1 prerequisite             80/80 PASS
complete installation-root move            PASS
source and destination filesystem device   equal
installation-root inode                    preserved
location A installation root               absent
location B Python                           executable
full installation-root fingerprint         exact
runtime-base strict fingerprint             exact
portable payload fingerprint               exact
registry before / after                     exact
engine verify at location B                 PASS
stale location-A paths in moved tree        0
stale location-A paths in B probes          0
```

The same-filesystem and inode-preservation checks prove that this gate exercised a rename-style whole-root move rather than an implicit cross-filesystem copy.

## Required location-B revalidation

The existing Gate 1 80-check verifier is rerun against the location-B prefix and registry.

```text
Python                         3.14.6
platform                       android
SOABI                          cpython-314-aarch64-linux-android
MULTIARCH                      aarch64-linux-android
sys.executable                 location B prefix/bin/python
sys.prefix/base_prefix         location B prefix
sysconfig paths                inside location B prefix
HTTPS                          status 200
subprocess identity            location B prefix
uv venv                        PASS
uv run --with anyio            PASS
ELF objects                    81
DT_NEEDED edges               329
unresolved edges                0
system SONAME dlopen          5/5
extension imports            67/67
```

## Run

Use a fresh extraction of the accepted Phase 4 archive:

```sh
cd "$HOME/projects/cpython-android-cli"

git pull --ff-only

git log -3 --oneline

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

## Expected markers

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

## Evidence layout

```text
results/termux/stage3c-phase5-installed-runtime-relocation/
├── baseline/
├── relocated/
├── a-installation-root.json
├── b-installation-root-after-move.json
├── b-installation-root-after-probes.json
├── a-installed-strict.json
├── b-installed-strict-before.json
├── b-installed-strict-after.json
├── a-installed-portable.json
├── b-installed-portable-before.json
├── b-installed-portable-after.json
├── a-registry.json
├── b-registry.json
├── relocation-state.json
├── stale-prefix-scan.json
├── relocated-baseline-verification.json
├── verification.json
├── workflow-status.json
└── result-index.json
```

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase5-installed-runtime-relocation"
ARCHIVE="$HOME/Downloads/stage3c-phase5-installed-runtime-relocation-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

Upload the TGZ rather than pasting only the final markers.

## Claim boundary

A PASS proves same-filesystem rename-style relocation of the complete installed root, including the ownership registry, and full runtime revalidation at the destination.

It does not prove:

```text
cross-filesystem copy relocation
archive transport or extraction at the destination
same-version reinstall or corruption repair
addon lifecycle
exact uninstall preservation
upgrade
downgrade
physical power-loss persistence
```
