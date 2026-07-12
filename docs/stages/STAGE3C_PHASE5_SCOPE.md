# Stage 3-C Phase 5 Scope: Installed Runtime and Lifecycle Validation

> **Status:** ACTIVE — Gate 3B preservation boundaries
> **Primary target:** Termux on Android arm64

## Phase question

> Does the installed runtime remain exact, functional, relocatable, repairable, composable, and safely removable through the accepted transaction and recovery engine?

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
  81 ELF / 329 edges / 0 unresolved / 67 extension imports
```

The source-tree fingerprint is a manifest contract identity. The installed strict fingerprint contains `mtime_ns` and is only a same-tree mutation control.

## Authority order

```text
Gate 1    installed runtime baseline                               FROZEN
Gate 2    historical complete installed-root relocation           FROZEN
Gate 3A0  reinstall and repair diagnostic census                  FROZEN
Phase 4I  missing registered non-directory repair intervention    FROZEN
Gate 3A   corrected reinstall and repair product acceptance       FROZEN
Gate 2R   corrected-engine complete-root relocation regression    FROZEN
Gate 3B   owned/unowned preservation boundaries                   ACTIVE
Gate 3C   addon lifecycle and dependency enforcement              DEFERRED
Gate 3D   runtime uninstall and final ownership boundary          DEFERRED
Gate 4    upgrade and downgrade with second frozen product        DEFERRED
```

## Frozen Gate 1

```text
archive sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

verifier
  80/80 PASS
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_RESULT.md
```

## Frozen historical Gate 2

```text
archive sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

Gate 1 at A / B
  80/80 / 80/80

verifier
  46/46 PASS
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

checks
  17/17 + 31/31
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
```

## Frozen Phase 4I intervention

```text
archive sha256
  d497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a

result-index sha256
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6

checks
  39/39 + 51/51

crash boundaries
  12/12
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_RESULT.md
```

## Frozen Gate 3A product acceptance

```text
archive sha256
  16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142

result-index sha256
  a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128

checks
  29/29 repair + 80/80 Gate 1 + 69/69 acceptance
```

Accepted matrix: exact reinstall NOOP; six isolated repairs; six sequential repairs; registry and unaffected-owned identity exact; portable identity exact; zero transaction residue; full runtime contract PASS.

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_RESULT.md
```

## Frozen Gate 2R corrected-engine relocation

```text
archive sha256
  8e2c131567d78a4208e7c8eb02e783a479713f6d867a3e5cd98eae60aa5738a7

result-index sha256
  69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c

Gate 1 at A / B
  80/80 / 80/80

historical relocation verifier
  46/46

corrected-engine authority verifier
  15/15
```

Frozen relocation identity:

```text
same filesystem / inode preserved
  true / true

complete-root shape
  719 / 60 / 656 / 3

complete-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30

portable fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

strict same-tree fingerprint
  3d61c27a3943930e53ac30035a2c4b77932cfabd17e4994f6370a30408a034f3

stale location-A references
  0
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION_RESULT.md
```

## Active Gate 3B preservation boundaries

### Policy question

> How must the accepted transaction engine treat user-modified owned leaves and unowned sentinels during reinstall, repair, and later uninstall without silently inventing ownership policy?

### Required census

```text
modified owned regular leaf
modified owned symlink
unowned sentinel file
unowned sentinel directory
```

### Required separation

Gate 3B must distinguish:

```text
install/reinstall ownership enforcement
repair behavior for registered mismatches
uninstall behavior for modified owned paths
preservation of unowned paths
registry and transaction-state transitions
```

No preservation or deletion rule may be assumed merely because a path exists under the installed prefix. The authority must be derived from the frozen manifest, registry, planner, operation executor, and recovery semantics.

### Required evidence

At minimum, the active investigation must capture:

```text
pre-operation path type/content/mode/target
planner action classification
touched and untouched path sets
journal mutation kinds
registry before and after
transaction residue
post-operation path identity
unaffected-path identity
runtime validity when the runtime is expected to remain installed
```

The first pass may be diagnostic. Product acceptance requires a separate target run after any policy intervention.

### Termux execution policy

All target-only workflows must provide one wrapper that verifies accepted input TGZ identities, performs fresh extraction, executes the workflow, records status and result indices, and packages a TGZ on PASS or FAIL. Log capture must be synchronous before packaging.

## Deferred Gate 3C

```text
runtime-base
→ development-addon
→ test-addon
→ dependency-order rejection
→ addon removals
→ runtime-base revalidation
```

## Deferred Gate 3D

```text
runtime-base-only state
approved unowned sentinels
owned payload removal
unowned preservation
registry transition
transaction residue check
empty-state verification
```

## Deferred Gate 4

Upgrade and downgrade remain deferred until a second complete frozen product identity exists. Synthetic version labels are not accepted.

## Non-reopening rule

Gate 3B may investigate preservation semantics around the accepted engine but must not silently broaden journal schema, registry schema, manifest/archive identity, addon dependency policy, or upgrade/downgrade policy. A policy-changing intervention requires an explicit authority decision.
