# Stage 3-C Phase 5 Gate 2: Installed Runtime Relocation

> **Status:** FROZEN PASS
> **Prerequisite:** frozen Phase 5 Gate 1 PASS
> **Input:** frozen Stage 3-C Phase 4 integrated durability evidence

## Gate result

```text
STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION=PASS
location A Gate 1 prerequisite        80/80 PASS
location B Gate 1 revalidation        80/80 PASS
Gate 2 verifier                       46/46 PASS
workflow return codes                 all 0
```

Final evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
```

The first target failure remains preserved in:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_FAILURE.md
```

## Frozen archive identity

```text
stage3c-phase5-installed-runtime-relocation-root-shape-corrected-results-20260712-163535.tgz

sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

size
  24,212,336 bytes

members
  434

regular files / directories
  401 / 33

unsafe, link, or special entries
  0
```

Result-index:

```text
sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

indexed files
  393 / 393 exact
```

## Design boundary

The workflow did not introduce a second installer or a new generic relocation engine.

It performed:

```text
frozen Phase 4 input
  → existing Gate 1 installer and 80-check baseline at location A
  → complete installation/ root mv on one filesystem
  → engine verify and complete 80-check revalidation at location B
  → independent Gate 2 move and stale-prefix verifier
```

The moved object was the complete installation root:

```text
installation/
├── prefix/                              714 payload entries
└── .cpython-android-cli/
    ├── lock
    ├── registry.json
    └── transactions/
```

Moving only `prefix/` while leaving ownership or recovery state behind is not accepted evidence.

## Frozen complete-root identity

All three checkpoints matched exactly:

```text
location A before move
location B immediately after move
location B after all probes
```

Shape:

```text
entries          719
directories       60
regular files    656
symlinks            3
special             0
```

Fingerprint:

```text
aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30
```

## Frozen payload identities

Portable identity:

```text
fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

entries
  714 / 714 / 714

regular / directory / symlink / special
  654 / 57 / 3 / 0
```

Strict same-tree identity:

```text
fingerprint
  691b4886792a4f6bb63da1ad0f82d2cdac4d42848d04de934d0cfc0e0548a2a0

entries
  714 / 714 / 714

pycache paths
  0

special paths
  0
```

## Relocation checks

```text
complete installation-root move            PASS
source and destination filesystem device   equal
installation-root inode                    preserved
location A installation root               absent
location B installation root               present
location B Python                           executable
registry before / after                     byte exact
engine verify at location B                 PASS
stale location-A paths in moved tree        0
stale location-A paths in B probes          0
```

## Location-B runtime result

```text
Python                         3.14.6
platform                       android
machine                        aarch64
SOABI                          cpython-314-aarch64-linux-android
MULTIARCH                      aarch64-linux-android
sys.executable                 location B prefix/bin/python
sys.prefix/base_prefix         location B prefix
sysconfig paths                inside location B prefix
HTTPS                          status 200
subprocess identity            location B prefix
uv venv                        PASS
uv run --with anyio            PASS
```

## Location-B native closure

```text
symlinks                         3
ELF objects                     81
DT_NEEDED edges                329
RUNTIME_INTERNAL edges          80
ANDROID_SYSTEM edges           249
unresolved edges                 0
inspection errors                0
system SONAME dlopen           5/5
extension imports             67/67
```

## Independent verifier

```text
46/46 PASS
```

It validates the frozen Gate 1 prerequisite, complete-root move state, same-filesystem inode preservation, exact complete-root shape and fingerprint, strict and portable payload identities, registry equality, destination engine verification, stale-prefix absence, canonical machine evidence, and the relocated 80-check runtime result.

## Claim boundary

This PASS proves same-filesystem rename-style relocation of the complete installed root, including ownership and recovery state, and full runtime revalidation at the destination.

It does not prove:

```text
cross-filesystem copy relocation
archive transport or extraction at the destination
same-version reinstall or corruption repair
modified owned-leaf preservation
unowned sentinel preservation
addon lifecycle
exact uninstall preservation
upgrade
downgrade
physical power-loss persistence
```

## Next boundary

```text
Stage 3-C Phase 5 Gate 3
  same-version lifecycle and exact uninstall semantics
```
