# Stage 3-C Phase 5 Scope: Installed Runtime and Lifecycle Validation

> **Status:** ACTIVE — Gate 3A corrected reinstall and repair product acceptance
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
  81 ELF
  329 DT_NEEDED edges
  0 unresolved
  67/67 extension imports
```

The source-tree fingerprint is a manifest contract identity. It is not a fixed installed strict fingerprint. The installed strict fingerprint contains `mtime_ns` and is used only as a same-tree mutation control.

## Authority order

```text
Gate 1    installed runtime baseline                               FROZEN
Gate 2    complete installed-root relocation                      FROZEN
Gate 3A0  reinstall and repair diagnostic census                  FROZEN
Phase 4I  missing registered non-directory repair intervention    FROZEN
Gate 3A   corrected reinstall and repair product acceptance       ACTIVE
Gate 2R   corrected-engine relocation regression                  DEFERRED
Gate 3B   owned/unowned preservation boundaries                   DEFERRED
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
  17/17

independent verifier
  31/31
```

Diagnostic classification of the prior engine:

```text
exact reinstall                       supported NOOP
four existing-path repairs            supported
missing regular repair                unsupported
missing symlink repair                unsupported
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

scenario checks
  39/39

independent verifier
  51/51

success/regression roots
  7/7

crash boundaries
  12/12
```

Accepted correction:

```text
existing mismatch
  replaced mutation
  backup current path

missing registered non-directory
  created mutation
  skip nonexistent backup move
```

The correction adds no journal schema, registry schema, manifest, archive, ownership, uninstall, or addon policy.

Evidence:

```text
docs/evidence/STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_RESULT.md
```

## Active Gate 3A product acceptance

### Product question

> After every accepted same-version repair class, does the corrected installed runtime retain exact ownership identity and the complete Gate 1 behavior contract?

### Required classes

```text
exact same-version reinstall NOOP
regular byte repair
regular mode repair
registered regular wrong-type repair
symlink target repair
missing regular repair
missing symlink repair
```

### Scenario isolation

Use one fresh corrected-engine seed and independent roots for all six repairs.

Also use one sequential acceptance root:

```text
fresh install
→ exact reinstall NOOP
→ six corruption/repair cycles
→ complete runtime validation
```

All roots must be inode-separated from the seed.

### Per-repair requirements

```text
intentional mutation evidence
pre-repair verify exactly one bad path
install actions noop 713 / repair 1
mutation count 2
post-repair verify PASS
registry bytes unchanged
portable fingerprint f860caf... exact
strict output 714-entry shape/safety PASS
transaction residue 0
candidate exact to manifest and source archive
unaffected-path identity exact
```

No fixed strict fingerprint is required across independent roots. The strict output contains mtime and is not portable.

### Full corrected-runtime requirements

After all repairs, the sequential acceptance root must prove:

```text
Python 3.14.6
Android aarch64
SOABI cpython-314-aarch64-linux-android
MULTIARCH aarch64-linux-android
sys.prefix and base_prefix exact
sysconfig paths inside installed prefix
HTTPS 200
smoke-termux PASS
uv venv PASS
uv run anyio PASS
native closure 81 ELF / 329 edges / 0 unresolved
system SONAME dlopen 5/5
extension imports 67/67
engine verify PASS
registry 1 artifact / 714 owned rows
portable payload exact before and after probes
strict shape/safety PASS before and after probes
strict fingerprint unchanged across probes
no transaction residue
```

### Gate 1 regression

The accepted correction changes engine implementation identity. Therefore Gate 3A acceptance must include a complete Gate 1-equivalent corrected-engine regression. Prior Gate 1 evidence alone is insufficient.

The active workflow invokes the complete frozen 80-check Gate 1 verifier on the sequential repaired root.

### Gate 2 boundary

Corrected-engine relocation remains a separate Gate 2R regression unless the acceptance workflow explicitly relocates the complete root and repeats destination validation.

### Independent verification

```text
repair scenario checks
  29

Gate 1 regression checks
  80

Gate 3A acceptance checks
  69
```

The 69 checks are split into repair/evidence and runtime/identity modules. The verifier reopens raw engine outputs, mutation records, registry bytes, portable and strict controls, runtime probes, uv results, native closure outputs, and result-index coverage.

Scenario `pass` values and console markers are not authority.

Handoff:

```text
docs/handoff/PHASE5_GATE3A_PRODUCT_ACCEPTANCE_HANDOFF_20260712.md
```

## Deferred Gate 2R

```text
complete corrected-engine installation-root move
registry byte exact
portable identity exact
strict same-tree identity unchanged across destination probes
full destination runtime validation
zero stale source references
```

## Deferred Gate 3B

```text
modified owned regular leaf
modified owned symlink
unowned sentinel file
unowned sentinel directory
policy derived from the transaction contract
```

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

Gate 3A may add orchestration and independent verification around the accepted correction only.

It must not broaden:

```text
journal schema
registry schema
manifest or archive identity
ownership policy
uninstall policy
addon dependency policy
```

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
