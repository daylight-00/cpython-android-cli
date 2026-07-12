# Stage 3-C Phase 5 Scope: Installed Runtime and Lifecycle Validation

> **Status:** ACTIVE — missing registered leaf repair intervention
> **Input:** frozen Stage 3-C product identities, Gates 1–2, and frozen Gate 3A0 diagnostic evidence
> **Primary target:** Termux on Android arm64

## Phase question

> Does the installed runtime remain exact, functional, relocatable, repairable, composable, and safely removable through the transaction and recovery engine?

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
```

## Authority order

```text
Gate 1    installed runtime baseline                               FROZEN
Gate 2    complete installed-root relocation                      FROZEN
Gate 3A0  reinstall and repair diagnostic census                  FROZEN
Phase 4I  missing registered non-directory repair intervention    ACTIVE
Gate 3A   accepted same-version reinstall and repair              BLOCKED
Gate 3B   owned/unowned preservation boundaries                   DEFERRED
Gate 3C   addon lifecycle and dependency enforcement              DEFERRED
Gate 3D   runtime uninstall and final ownership boundary          DEFERRED
Gate 4    upgrade and downgrade with second frozen product        DEFERRED
```

`Gate 3A0` is diagnostic authority. Its PASS classifies existing behavior and does not establish product acceptance.

## Frozen Gate 1

```text
archive sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

verifier
  80/80 PASS

install / registry
  714 creates
  715 mutations
  1 artifact
  714 owned rows

runtime
  Python 3.14.6
  Android aarch64
  HTTPS 200
  uv PASS
  native closure 81/329/0
  system SONAME 5/5
  extension imports 67/67
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_RESULT.md
```

## Frozen Gate 2

```text
archive sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

location A Gate 1
  80/80 PASS

location B Gate 1
  80/80 PASS

Gate 2 verifier
  46/46 PASS

complete-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30

complete-root shape
  719 entries
  60 directories
  656 regular files
  3 symlinks
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
```

## Frozen Gate 3A0 diagnostic

```text
archive sha256
  9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2

result-index sha256
  a7507ab60de402a636c8e2899706aec77844896254f28dd068c8683dcb3dce7b

scenario checks
  17/17 PASS

independent verifier
  31/31 PASS

Phase 4 copied input
  324/324 exact
```

Frozen classification:

```text
exact same-version reinstall            supported NOOP
regular byte mismatch                   supported repair
regular mode mismatch                   supported repair
symlink target mismatch                 supported repair
registered regular wrong type           supported repair
registered regular absent               unsupported
registered symlink absent               unsupported
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
```

## Active Phase 4I intervention

### Confirmed defect

For an absent registered regular or symlink leaf, the frozen engine executes:

```text
planner
  repair

journal intent
  replaced

execution
  durable_move(absent source, backup)
  os.replace(absent source, backup)
  FileNotFoundError

recovery
  APPLYING → ROLLED_BACK
  restored_count 0
  retained ROLLED_BACK transaction

final state
  registry row retained
  leaf absent
  verify still fails
```

### Authorized correction

```text
registered path exists and differs
  keep replaced mutation
  backup current path
  publish frozen member

registered path is absent
  use created mutation
  do not backup a nonexistent source
  publish frozen member
```

The existing `created` rollback path must be reused. No new journal schema or recovery operation is authorized.

Decision:

```text
docs/handoff/PHASE5_GATE3A_INTERVENTION_DECISION_20260712.md
```

### Required success scenarios

```text
missing registered regular repair
missing registered symlink repair
exact same-version NOOP regression
four in-place repair regressions
```

Successful missing-leaf repair must produce:

```text
install PASS
one repair action or explicitly named missing-repair action
exact manifest path identity
registry identity exact
portable payload identity restored
engine verify PASS
no transaction residue
```

### Required crash/recovery scenarios

At minimum:

```text
prepared before intent
created intent recorded before publish
published leaf before registry mutation
registry mutation before commit
committed before cleanup
```

Expected recovery:

```text
pre-commit crash
  restore original missing state
  restore prior registry

post-commit crash
  preserve repaired leaf
  preserve committed registry
```

### Non-authorized changes

```text
manifest or archive identity
registry schema
artifact identity
ownership policy
uninstall preservation policy
addon dependency policy
new generic repair subsystem
```

## Mandatory revalidation order

```text
1. static and synthetic intervention validation
2. authoritative Termux intervention scenarios
3. Gate 3A product acceptance
4. Gate 1 regression if accepted engine input identity changes
5. Gate 2 regression if accepted engine input identity changes
6. Gate 3B may then open
```

Prior target evidence may be reused only where the accepted input identity and exercised code path are proven unaffected.

## Deferred Gate 3A product acceptance

Gate 3A product acceptance must prove:

```text
exact reinstall NOOP
all supported in-place repair classes
missing regular repair
missing symlink repair
post-repair runtime behavior
HTTPS
uv
native closure
extension imports
no transaction residue
```

## Deferred Gate 3B preservation

```text
modified owned regular leaf
modified owned symlink
unowned sentinel file
unowned sentinel directory
policy derived from the transaction contract
```

## Deferred Gate 3C addons

```text
runtime-base
→ development-addon
→ test-addon
→ dependency-order rejection
→ addon removals
→ runtime-base revalidation
```

## Deferred Gate 3D uninstall

```text
runtime-base-only state
approved unowned sentinels
frozen-engine uninstall
owned payload removal
unowned preservation
registry transition
transaction residue check
empty-state verification
```

## Deferred Gate 4

Upgrade and downgrade remain deferred until a second complete frozen product identity exists. Synthetic version labels are not accepted.

## Non-reopening rule

The active intervention may change only the registered missing non-directory repair execution path and directly required scenario/verifier code.

Any broader change requires a new authority decision.

## Results layout

```text
Gate 3A0 diagnostic
  results/termux/stage3c-phase5-gate3a-reinstall-repair-diagnostic/

Phase 4I intervention
  results/termux/stage3c-phase4-missing-leaf-repair-intervention/

Gate 3A product acceptance
  results/termux/stage3c-phase5-gate3a-reinstall-repair-acceptance/
```
