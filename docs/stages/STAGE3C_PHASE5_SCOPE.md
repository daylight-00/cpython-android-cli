# Stage 3-C Phase 5 Scope: Installed Runtime and Lifecycle Validation

> **Status:** ACTIVE — Gate 3 same-version lifecycle and exact uninstall semantics
> **Input:** frozen Stage 3-C Phases 1–4 and frozen Phase 5 Gates 1–2
> **Primary target:** Termux on Android arm64

## Phase question

> Does the frozen runtime remain exact, functional, natively closed, relocatable, repairable, composable, and safely removable after installation through the frozen transaction engine rather than direct assembly?

## Frozen product identities

```text
runtime-base manifest entries
  714

runtime-base source-tree fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

portable installed-payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

runtime-base archive sha256
  2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743

runtime-base manifest sha256
  ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a

native closure
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
Gate 2  relocate the complete installed root and revalidate            FROZEN
Gate 3  validate same-version lifecycle and exact uninstall            ACTIVE
Gate 4  validate upgrade and downgrade with a second frozen version    DEFERRED
```

## Frozen Gate 1 — installed runtime baseline

Authoritative identity:

```text
archive sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

verifier
  80/80 PASS

workflow return codes
  all 0
```

Frozen result:

```text
install create actions              714
registry mutation count             715
registry artifacts                    1
registry owned paths                714
manifest-to-registry mapping        exact
portable installed payload          exact
strict validation-time mutation     none
HTTPS                               200
uv venv / uv run                    PASS
native closure                      81/329/0
system SONAME dlopen                5/5
extension imports                  67/67
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_RESULT.md
```

Gate 1 proves original-path installed identity and behavior. It does not independently prove relocation or later lifecycle operations.

## Frozen Gate 2 — complete installed-root relocation

Authoritative identity:

```text
archive sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

location A Gate 1 prerequisite
  80/80 PASS

location B Gate 1 revalidation
  80/80 PASS

Gate 2 verifier
  46/46 PASS

workflow return codes
  all 0
```

Complete installation-root identity:

```text
entries          719
directories       60
regular files    656
symlinks            3
special             0

fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30
```

Frozen result:

```text
same-filesystem whole-root move       PASS
installation-root inode preserved     PASS
location A root absent                PASS
location B root present               PASS
registry A-to-B                       byte exact
portable payload identity             exact
strict payload identity               exact
complete-root identity                exact
stale location-A references           0
engine verify at location B           PASS
HTTPS                                 200
uv venv / uv run                      PASS
native closure                        81/329/0
system SONAME dlopen                  5/5
extension imports                    67/67
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
```

Gate 2 proves same-filesystem rename-style relocation of the complete installed root and destination revalidation. It does not prove cross-filesystem relocation or lifecycle mutations after the move.

## Active Gate 3 — same-version lifecycle and exact uninstall

Gate 3 must consume the frozen installer, manifests, archives, registry semantics, transaction behavior, recovery behavior, and durability helpers without modifying them.

Gate 3 is divided into ordered subgates so each claim remains narrow and independently inspectable.

```text
Gate 3A  same-version reinstall NOOP and registered corruption repair
Gate 3B  modified owned-leaf and unowned-sentinel preservation
Gate 3C  addon composition, dependency enforcement, and addon removal
Gate 3D  runtime uninstall and exact final ownership boundary
```

A later subgate must not run until the previous subgate is frozen from authoritative Termux evidence.

### Gate 3A — reinstall and repair

Required scenarios:

```text
fresh runtime-base install
exact same-version reinstall
registered regular-file corruption
registered symlink corruption
registered mode corruption
registered missing leaf
registered missing owned directory where safe to reconstruct
```

Required same-version reinstall result:

```text
operation                    install runtime-base
result                       PASS
noop                         true
payload mutation count       0
registry mutation count      0
registry JSON                byte unchanged
portable payload identity    unchanged
strict payload identity      unchanged
runtime verification         PASS
```

Required corruption-repair result:

```text
only registered corrupted paths repaired
unaffected registered paths unchanged
registry returns to exact manifest mapping
portable payload identity restored
engine verify PASS
runtime, HTTPS, uv, and native closure PASS
```

Synthetic corruption must be applied only after a frozen clean baseline fingerprint is captured. Every intentional mutation must be recorded in machine-readable evidence.

### Gate 3B — preservation boundaries

Required preservation scenarios:

```text
modified owned regular leaf before reinstall
modified owned symlink before reinstall
unowned sentinel file inside an owned directory
unowned sentinel directory under a shared structural namespace
```

The gate must distinguish policy rather than assume it:

```text
registered corruption
  engine may repair to the frozen manifest identity

user-modified owned content
  preservation or replacement must match the frozen transaction contract

unowned content
  must not be claimed or silently removed
```

Expected outcomes must be derived from the frozen Phase 4 transaction contract and existing scenario evidence before target execution. Gate 3 must not redefine policy to make the test pass.

### Gate 3C — addon lifecycle and dependencies

Required order:

```text
install runtime-base
install development-addon
verify combined registry and payload
install test-addon where dependencies permit
verify combined registry and payload
attempt forbidden dependency-order removals
remove test-addon
remove development-addon
revalidate runtime-base
```

Required properties:

```text
owned-path overlap                         0
shared structural namespace preserved     exact
registry artifact transitions             exact
registry owned-path transitions           exact
runtime dependency enforcement            exact
addon removal preserves runtime-base       exact
runtime, HTTPS, uv, and closure after addon removal PASS
```

### Gate 3D — runtime uninstall and final boundary

Required final sequence:

```text
start from exact runtime-base-only state
place approved unowned sentinels
uninstall runtime-base through frozen engine
verify registry transition
verify owned payload removal
verify preservation of unowned sentinels
verify shared structural cleanup policy
verify no transaction residue
```

Required final state:

```text
runtime-base registry artifact         absent
runtime-base owned registry rows       0
registered owned payload paths         absent
unowned sentinel paths                 preserved
active transaction directories         0
engine verification                    PASS for empty installation state
```

Whether empty state directories, lock files, registry files, or structural directories remain must be judged against the frozen Phase 4 contract. Gate 3 may not invent an aesthetic cleanup rule.

## Gate 3 claim boundary

A complete Gate 3 PASS will prove same-version reinstall, repair, preservation, addon lifecycle, dependency enforcement, and exact uninstall behavior for the currently frozen product set.

It will not prove:

```text
upgrade or downgrade
compatibility with a second product identity
cross-filesystem relocation
physical power-loss persistence
storage-controller or kernel-level failure behavior
```

## Deferred Gate 4 — explicit second-version lifecycle

Upgrade and downgrade remain deferred until a second complete frozen product identity exists.

Synthetic version labels are not acceptable evidence.

Required future inputs:

```text
second source identity
second manifest set
second deterministic archive set
second installation contract
explicit compatibility policy
```

## Non-reopening rule

Phase 5 consumes frozen Phase 1–4 identities. It must not modify source archives, manifests, registry semantics, transaction semantics, recovery behavior, or durability helpers while claiming installed lifecycle validation.

Gate 3 may orchestrate existing frozen tools and introduce independent scenario runners and verifiers. It must not silently rewrite policy or broaden a claim beyond the target evidence.

## Results layout

```text
Gate 1
  results/termux/stage3c-phase5-installed-runtime-baseline/
  work/termux/stage3c-phase5-installed-runtime-baseline/

Gate 2
  results/termux/stage3c-phase5-installed-runtime-relocation/
  work/termux/stage3c-phase5-installed-runtime-relocation/

Gate 3
  results/termux/stage3c-phase5-installed-runtime-lifecycle/
  work/termux/stage3c-phase5-installed-runtime-lifecycle/
```
