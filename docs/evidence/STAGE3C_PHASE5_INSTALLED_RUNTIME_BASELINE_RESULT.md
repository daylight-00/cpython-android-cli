# Stage 3-C Phase 5 Gate 1: Installed Runtime Baseline Result

> **Status:** FROZEN PASS
> **Target:** Termux on Android arm64
> **Workflow:** `experiments/stage3c-installed-runtime-baseline/run-installed-runtime-baseline.sh`

## Executive result

The corrected authoritative Gate 1 run passed every component and all 80 independent checks.

```text
STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE=PASS
verifier                                  80/80 PASS
workflow return codes                     all 0
```

The first failed attempt remains preserved in:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_FAILURE.md
```

That failure is not rewritten or discarded. The corrected run used the accepted frozen Phase 4 input and the corrected portable installed-payload identity.

## Authoritative archive identity

```text
sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

members
  377

regular files / directories
  348 / 29

unsafe, link, or special archive entries
  0
```

The archive was independently inspected before acceptance.

## Result-index identity

```text
result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

indexed hash, size, and mode mismatches
  0
```

The nested frozen Phase 4 input result-index was independently rechecked against all 294 declared files.

## Accepted frozen input

```text
Phase 4 result-index sha256
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce

Phase 4 indexed files
  294 / 294 exact

Phase 4 input before / after
  exact
```

Gate 1 therefore consumed the accepted frozen Phase 4 evidence rather than a later mutable result directory.

## Installation and registry result

```text
install result                    PASS
created payload rows              714
registry mutation count           715
engine verify                     PASS
registry artifacts                  1
registry owned paths              714
manifest owned rows               714
manifest-to-registry mapping      exact
```

## Installed payload identity

Portable installed identity:

```text
kind
  stage3c-installed-payload-portable-v1

fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

entries
  714

regular / directory / symlink / special
  654 / 57 / 3 / 0
```

Observed strict same-tree mutation identity:

```text
strict installed fingerprint before / after
  a70d5e5ac6bcd491df4a836cda1f86cf4239f7d0b879e6c51f92d35a79473fec

installed prefix mutation
  none

pycache paths
  0

special paths
  0
```

The strict fingerprint is evidence for this same-tree validation run. It is not a portable cross-installation identity.

## Runtime result

```text
Python                         3.14.6
platform                       android
machine                        aarch64
SOABI                          cpython-314-aarch64-linux-android
MULTIARCH                      aarch64-linux-android
sys.executable                 installed prefix/bin/python
sys.prefix/base_prefix         installed prefix
sysconfig paths                inside installed prefix
HTTPS                          status 200
subprocess identity            installed prefix
```

## uv result

```text
uv venv                        PASS
venv base_prefix               installed prefix
uv run --with anyio            PASS
uv run base_prefix             installed prefix
```

Generated venvs and redirected bytecode caches were removed before final fingerprinting.

## Native closure result

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
checks
  80

passed
  80

failed
  0
```

The verifier independently checked frozen Phase 4 authority, manifest and registry equality, portable payload identity, strict before/after immutability, runtime identity, HTTPS, smoke markers, uv behavior, closure, system SONAME loading, extension imports, canonical JSON, and mutation controls.

## Gate 1 claim boundary

This PASS proves that `runtime-base` remains exact, functional, and natively closed on its original installed path after installation through the frozen Phase 4 transaction engine.

It does not prove:

```text
installed-root relocation
same-version reinstall or repair
addon lifecycle
exact uninstall preservation
upgrade
downgrade
cross-filesystem relocation
physical power-loss persistence
```

## Next authority

```text
Stage 3-C Phase 5 Gate 1
  FROZEN

Stage 3-C Phase 5 Gate 2
  ACTIVE

workflow
  experiments/stage3c-installed-runtime-relocation/run-installed-runtime-relocation.sh
```
