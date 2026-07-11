# Stage 3-C Phase 5 Scope: Installed Runtime and Lifecycle Validation

> **Status:** ACTIVE — Gate 1 installed runtime baseline
> **Input:** frozen Stage 3-C Phases 1–4
> **Primary target:** Termux on Android arm64

## Phase question

> Does the frozen runtime remain exact, functional, natively closed, relocatable, and safely removable after installation through the frozen transaction engine rather than direct assembly?

## Frozen inputs

```text
runtime-base manifest entries
  714

runtime-base fingerprint
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
Gate 1  install runtime-base and validate exact installed behavior
Gate 2  relocate the complete installed prefix and revalidate
Gate 3  validate same-version lifecycle and exact uninstall preservation
Gate 4  validate explicit upgrade and downgrade only when a second frozen version exists
```

## Active Gate 1 — installed runtime baseline

The frozen integrated engine installs `runtime-base` into a fresh installation root. Validation then runs from the installed prefix, not from the Stage 3-B promoted tree or Phase 1 isolated assembly.

Required installed-state checks:

```text
install result                PASS
created payload rows          714
registry mutation count       715
engine verify                 PASS
registry artifacts              1
registry owned paths          714
manifest-to-registry mapping  exact
installed tree fingerprint    exact
installed prefix mutation     none
```

Required runtime checks:

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
```

Required uv checks:

```text
uv venv                       PASS
venv base_prefix              installed prefix
uv run with anyio             PASS
uv run interpreter identity   installed prefix
```

Required native closure checks:

```text
symlinks                        3
ELF objects                    81
DT_NEEDED edges               329
RUNTIME_INTERNAL edges         80
ANDROID_SYSTEM edges          249
unresolved edges                0
inspection errors               0
system SONAME dlopen           5/5
extension imports             67/67
```

## Gate 1 claim boundary

A PASS proves exact installed runtime-base identity and behavior on the original installation path after installation through the frozen Phase 4 engine. It does not prove relocation, upgrade, downgrade, uninstall exactness, or preservation under later lifecycle operations.

## Deferred Gate 2 — installed-prefix relocation

Move the complete installation root or installed prefix to a second location and revalidate:

```text
portable tree fidelity
registry consistency
runtime identity
native closure
HTTPS
uv venv
uv run
stale source-prefix absence
```

## Deferred Gate 3 — same-version lifecycle and uninstall

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

Phase 5 consumes frozen Phase 1–4 identities. It must not modify source archives, manifests, registry semantics, transaction semantics, recovery behavior, or durability helpers while claiming only installed-runtime validation.

## Results layout

```text
results/termux/stage3c-phase5-installed-runtime-baseline/
work/termux/stage3c-phase5-installed-runtime-baseline/
```
