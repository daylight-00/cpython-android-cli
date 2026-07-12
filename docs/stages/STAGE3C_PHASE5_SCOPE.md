# Stage 3-C Phase 5 Scope: Installed Runtime and Lifecycle Validation

> **Status:** ACTIVE — Gate 2 installed-root relocation
> **Input:** frozen Stage 3-C Phases 1–4 and frozen Phase 5 Gate 1
> **Primary target:** Termux on Android arm64

## Phase question

> Does the frozen runtime remain exact, functional, natively closed, relocatable, and safely removable after installation through the frozen transaction engine rather than direct assembly?

## Frozen inputs

```text
runtime-base manifest entries
  714

runtime-base source-tree fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

runtime-base native closure
  81 ELF
  329 DT_NEEDED edges
  0 unresolved
  67/67 extension imports

Phase 4 integrated durability result-index
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce
```

## Design order

```text
Gate 1  install runtime-base and validate exact installed behavior      FROZEN
Gate 2  relocate the complete installed root and revalidate            ACTIVE
Gate 3  validate same-version lifecycle and exact uninstall            DEFERRED
Gate 4  validate upgrade and downgrade with a second frozen version    DEFERRED
```

## Frozen Gate 1 — installed runtime baseline

Gate 1 installed `runtime-base` through the frozen Phase 4 engine into a fresh installation root and validated the newly installed prefix.

Authoritative evidence:

```text
corrected archive sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

verifier
  80/80 PASS

workflow return codes
  all 0
```

Accepted-input checks:

```text
Phase 4 root result-index sha256
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce

Phase 4 indexed files
  294/294 exact

Phase 4 input before/after
  exact
```

Installed-state checks:

```text
install result                    PASS
created payload rows              714
registry mutation count           715
engine verify                     PASS
registry artifacts                  1
registry owned paths              714
manifest-to-registry mapping      exact
portable installed payload        exact
strict installed before/after     unchanged
installed prefix mutation         none
```

Portable installed-payload identity:

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

Runtime checks:

```text
Python version                3.14.6
platform                      android
SOABI                         cpython-314-aarch64-linux-android
MULTIARCH                     aarch64-linux-android
sys.executable                installed prefix/bin/python
sys.prefix/base_prefix        installed prefix
sysconfig paths               inside installed prefix
HTTPS                         status 200
subprocess identity           installed prefix
uv venv                       PASS
uv run with anyio             PASS
```

Native closure checks:

```text
symlinks                        3
ELF objects                    81
DT_NEEDED edges               329
RUNTIME_INTERNAL edges         80
ANDROID_SYSTEM edges          249
unresolved edges                0
inspection errors               0
system SONAME dlopen          5/5
extension imports            67/67
```

Gate 1 evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_RESULT.md
```

The first Gate 1 failure remains preserved in:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_FAILURE.md
```

Gate 1 claim boundary:

A PASS proves exact installed runtime-base registry and portable payload identity, strict validation-time immutability, and runtime behavior on the original installation path. It does not prove relocation or later lifecycle operations.

## Active Gate 2 — complete installed-root relocation

Gate 2 must relocate the complete installation root rather than only the runtime payload:

```text
installation/
├── prefix/
└── .cpython-android-cli/
    └── registry.json
```

The active implementation is:

```text
experiments/stage3c-installed-runtime-relocation/
├── README.md
├── run-installed-runtime-relocation.sh
└── verify-installed-runtime-relocation.py
```

### Gate 2 execution order

```text
1. rerun frozen Gate 1 at location A
2. require Gate 1 verifier 80/80
3. fingerprint installation root, prefix, portable payload, and registry
4. move installation/ to location B on the same filesystem
5. require source/destination device equality and inode preservation
6. verify registry through the frozen engine at location B
7. rerun runtime, HTTPS, smoke, uv, closure, and extension probes
8. rerun the complete Gate 1 80-check verifier against location B
9. reject stale location-A references
10. run the independent Gate 2 verifier
```

### Required move checks

```text
location A installation root        absent after move
location B installation root        present
location B Python                   executable
same filesystem                     true
installation-root inode preserved   true
full installation-root fingerprint  exact
runtime strict fingerprint          exact
portable payload fingerprint        f860caf... exact
registry before/after               exact
engine verify at B                  PASS
```

### Required stale-prefix checks

```text
location-A byte strings in moved regular files   0
location-A strings in moved symlink targets      0
location-A strings in B runtime probe JSON       0
location-A installation root                     absent
```

### Required location-B runtime checks

```text
Gate 1 revalidation             80/80 PASS
Python                          3.14.6
platform                        android
SOABI                           cpython-314-aarch64-linux-android
MULTIARCH                       aarch64-linux-android
sys.executable                  location B prefix/bin/python
sys.prefix/base_prefix          location B prefix
sysconfig paths                 inside location B prefix
HTTPS                           status 200
subprocess identity             location B prefix
uv venv                         PASS
uv run with anyio               PASS
ELF objects                     81
DT_NEEDED edges                329
unresolved edges                 0
system SONAME dlopen           5/5
extension imports             67/67
```

### Gate 2 independent verifier

```text
46 checks
```

It independently validates the frozen Gate 1 prerequisite, complete-root move state, same-filesystem inode preservation, full-root fidelity, strict and portable prefix fidelity, exact registry preservation, engine verification at B, stale-prefix absence, canonical machine evidence, and the relocated 80-check runtime result.

### Gate 2 claim boundary

A PASS proves same-filesystem rename-style relocation of the complete installation root and full destination runtime revalidation.

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

## Deferred Gate 3 — same-version lifecycle and uninstall

Gate 3 remains closed until Gate 2 is frozen from authoritative Termux evidence.

```text
exact reinstall NOOP
registered corruption repair
modified owned leaf preservation
unowned sentinel preservation
addon composition and removal
runtime dependency enforcement
exact registry transitions
final uninstall ownership boundary
```

## Deferred Gate 4 — explicit second-version lifecycle

Upgrade and downgrade are deferred until a second complete frozen product identity exists. Synthetic version labels are not sufficient evidence.

Required future inputs:

```text
second source identity
second manifest set
second deterministic archive set
second installation contract
explicit compatibility policy
```

## Non-reopening rule

Phase 5 consumes frozen Phase 1–4 identities. It must not modify source archives, manifests, registry semantics, transaction semantics, recovery behavior, or durability helpers while claiming installed-runtime validation.

The portable installed-payload fingerprint is a Phase 5 cross-form identity. It does not replace or rewrite the frozen Phase 1 source-tree fingerprint.

Gate 2 may orchestrate existing frozen installation and validation tools. It must not silently create a new installer, rewrite the registry, or broaden the relocation claim beyond the evidence.

## Results layout

```text
Gate 1
  results/termux/stage3c-phase5-installed-runtime-baseline/
  work/termux/stage3c-phase5-installed-runtime-baseline/

Gate 2
  results/termux/stage3c-phase5-installed-runtime-relocation/
  work/termux/stage3c-phase5-installed-runtime-relocation/
```
