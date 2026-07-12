# Stage 3-C Phase 5 Gate 2: Installed Runtime Relocation Result

> **Status:** FROZEN PASS
> **Target:** Termux on Android arm64
> **Workflow:** `experiments/stage3c-installed-runtime-relocation/run-installed-runtime-relocation.sh`

## Executive result

```text
STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION=PASS
Gate 1 prerequisite at location A       80/80 PASS
Gate 1 revalidation at location B       80/80 PASS
Gate 2 verifier                         46/46 PASS
workflow return codes                   all 0
```

The first failed attempt remains preserved in:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_FAILURE.md
```

## Authoritative archive identity

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

unsafe, link, or special archive entries
  0
```

The archive was independently inspected before extraction.

## Result-index identities

```text
Gate 2 root result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

Gate 2 root indexed files
  393 / 393 exact

Gate 1 prerequisite result-index sha256
  bd6f579e4724932aacf756e561787d71daed4bae5897c10f8546a81c0d71a8e3

Gate 1 prerequisite indexed files
  341 / 341 exact

accepted Phase 4 result-index sha256
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce

accepted Phase 4 indexed files
  294 / 294 exact

hash, size, mode, missing, duplicate, and index-coverage mismatches
  0
```

All nested Phase 4 transaction, recovery, durability, and integration indices also matched their declared files.

## Relocation state

```text
complete installation-root move          PASS
source and target filesystem device      equal
installation-root inode                   preserved
location A root after move                absent
location B root after move                present
location B Python                         executable
```

The workflow therefore exercised a same-filesystem rename-style move of the complete installation root.

## Complete installation-root identity

All three checkpoints were exact:

```text
location A before move
location B immediately after move
location B after all probes
```

Observed shape:

```text
entries          719
directories       60
regular files    656
symlinks            3
special             0
```

Observed fingerprint:

```text
aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30
```

The complete root includes the 714-entry payload plus the prefix root, durable lock, ownership registry, installation state directory, and recovery transaction root.

## Payload identities

Portable installed-payload identity:

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

Both identities remained exact across the move and all destination probes.

## Registry and manifest result

```text
manifest owned rows             714
registry rows at location A     714
registry rows at location B     714
manifest-to-registry mapping    exact
registry A-to-B JSON            byte exact
engine verify at location B     PASS
engine bad paths                0
```

Frozen runtime-base artifact identities remained unchanged:

```text
artifact ID
  cpython-android-cli-3.14.6-android24-aarch64-runtime-base

archive sha256
  2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743

manifest sha256
  ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a
```

## Destination runtime result

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
```

## Destination uv result

```text
uv venv                        PASS
venv base_prefix               location B prefix
uv run --with anyio            PASS
uv run base_prefix             location B prefix
```

## Destination native closure

```text
payload rows                    714
symlinks                          3
ELF objects                      81
DT_NEEDED edges                 329
RUNTIME_INTERNAL edges           80
ANDROID_SYSTEM edges            249
unresolved edges                  0
inspection errors                 0
system SONAME dlopen            5/5
extension imports              67/67
```

The closure TSV files independently contained 329 classified dependency rows, zero unresolved rows, and zero inspection-error rows.

## Stale-location check

```text
location A root absent                 PASS
location-A matches in regular files       0
location-A matches in symlinks             0
location-A matches in probe outputs        0
```

## Independent verifier

```text
checks
  46

passed
  46

failed
  0
```

The verifier checked the location-A Gate 1 prerequisite, accepted Phase 4 identity, move state, complete-root shape and fingerprint, strict and portable payload identities, registry equality, destination engine verification, stale-location absence, canonical machine JSON, and complete location-B Gate 1 revalidation.

## Gate 2 claim boundary

This PASS proves same-filesystem rename-style relocation of the complete installation root, including ownership and recovery state, followed by exact destination runtime, HTTPS, uv, native-closure, and extension-import revalidation.

It does not prove:

```text
cross-filesystem copy relocation
archive transport or extraction at a destination
same-version reinstall or corruption repair
modified owned-leaf preservation
unowned sentinel preservation
addon composition and removal
exact uninstall preservation
upgrade
downgrade
physical power-loss persistence
```

## Next authority

```text
Stage 3-C Phase 5 Gate 2
  FROZEN

Stage 3-C Phase 5 Gate 3
  next active boundary
  same-version lifecycle and uninstall semantics
```
