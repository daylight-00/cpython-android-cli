# Stage 3-C Phase 5 Evidence Ledger

> **Purpose:** compact authoritative identity ledger for installed-runtime and lifecycle gates.
> **Authority:** accepted Termux TGZ evidence plus repository-frozen contracts.

## Gate 1 — installed runtime baseline

```text
status
  FROZEN PASS

archive sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

verifier
  80/80 PASS

portable fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978
```

Runtime: Python 3.14.6, Android aarch64, HTTPS 200, uv PASS, closure 81/329/0, system SONAME 5/5, extension imports 67/67.

## Gate 2 — historical complete-root relocation

```text
status
  FROZEN PASS

archive sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

Gate 1 at A / B
  80/80 / 80/80

verifier
  46/46 PASS
```

## Gate 3A0 — reinstall and repair diagnostic

```text
status
  FROZEN DIAGNOSTIC PASS

archive sha256
  9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2

result-index sha256
  a7507ab60de402a636c8e2899706aec77844896254f28dd068c8683dcb3dce7b

checks
  17/17 + 31/31
```

## Phase 4I — missing registered leaf intervention

```text
status
  FROZEN PASS

archive sha256
  d497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a

result-index sha256
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6

checks
  39/39 + 51/51

crash boundaries
  12/12
```

## Gate 3A — corrected reinstall and repair product acceptance

```text
status
  FROZEN PASS

archive sha256
  16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142

result-index sha256
  a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128

checks
  29/29 repair + 80/80 Gate 1 + 69/69 acceptance
```

## Gate 2R — corrected-engine complete-root relocation

```text
status
  FROZEN PASS

archive sha256
  8e2c131567d78a4208e7c8eb02e783a479713f6d867a3e5cd98eae60aa5738a7

result-index sha256
  69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c

Gate 1 at A / B
  80/80 / 80/80

historical relocation verifier
  46/46

corrected-engine verifier
  15/15

complete-root shape
  719 / 60 / 656 / 3

complete-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30
```

## Gate 3B0 — preservation-boundary diagnostic

```text
status
  FROZEN DIAGNOSTIC PASS

archive
  stage3c-phase5-gate3b0-preservation-diagnostic-results-20260712-211837.tgz

archive sha256
  ed5cb08cc576e74cacac4077cf9c9d7f3164a34913197aae9ef10cc8c113801a

archive size
  22,701,335 bytes

archive members
  131

result-index sha256
  7a8e982a44118dac3f232b2fefb578d22bedc0c7d32a6267ab3cd55c5e8deb27

indexed files
  110/110 exact

scenario checks
  16/16

independent verifier
  40/40
```

Frozen census:

```text
reinstall-owned-regular       ENFORCED_REPAIR
reinstall-owned-symlink       ENFORCED_REPAIR
reinstall-unowned-file        PRESERVED_NOOP
reinstall-unowned-directory   PRESERVED_NOOP
uninstall-owned-regular       PRESERVED_AND_DEREGISTERED
uninstall-owned-symlink       PRESERVED_AND_DEREGISTERED
uninstall-unowned-file        UNOWNED_PRESERVED
uninstall-unowned-directory   UNOWNED_PRESERVED
```

Contract decision:

```text
local modification uninstall policy
  preserve-and-report

modified regular or symlink
  PRESERVE_AND_REPORT

owned directory
  REMOVE_ONLY_WHEN_EMPTY

structural parent
  PRESERVE_NAMESPACE

unowned descendant
  PRESERVE
```

The Termux census matches the frozen contract. No intervention is required.

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3B0_PRESERVATION_DIAGNOSTIC_RESULT.md
```

## Gate 3B — preserve-and-report product acceptance

```text
status
  FROZEN PASS

archive
  stage3c-phase5-gate3b-preservation-acceptance-results-20260713-024946.tgz

archive sha256
  0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b

archive size
  24,857,211 bytes

archive members
  323

root result-index sha256
  f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9

root indexed files
  289/289 exact

scenario checks
  29/29 PASS

independent verifier
  62/62 PASS

happy / crash topology
  8/8 / 12/12

return codes
  scenario 0 / verifier 0 / workflow 0 / wrapper 0
```

Accepted boundaries are PREPARED rc 90, late APPLYING rc 93, and COMMITTED rc 92. Modified-owned pre-commit recovery intentionally returns verifier rc 44 with exactly the modified leaf; unowned pre-commit and committed states return rc 0.

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3B_PRESERVATION_ACCEPTANCE_RESULT.md
```

## Active boundary

```text
Gate 3C addon lifecycle and dependency enforcement
```

Frozen repository-side design:

```text
verification             73/73 PASS
matrix sha256            52c622450e9664c6738a75fbc947b809cf1f4766e61b04a68a1a8dcc24b6c14a
scenario matrix          50
preflight/composition    10/10
uninstall/recovery        9/12
locking/behavior          2/7
```

Required target proof:

```text
both addon install orders
both addon removal orders
exact runtime-base prerequisite identity
exact registry and ownership transitions
dependency-invalid operation rejection without mutation
addon repair, uninstall preservation, and recovery
shared-path and collision-policy enforcement
runtime-base identity and behavior after addon removal
no Gate 3D final-runtime-uninstall claim
```

Design evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3C_ADDON_LIFECYCLE_DESIGN_RESULT.md
docs/evidence/STAGE3C_PHASE5_GATE3C_TARGET_IMPLEMENTATION_RESULT.md
```


## Gate 3C target implementation

```text
status
  READY FOR TERMUX — target evidence pending

input authority
  Gate 3B archive 0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b
  Gate 3B result-index f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9

scenario topology
  50 total
  10 preflight / 10 composition / 9 uninstall
  12 recovery / 2 locking / 7 behavior

execution surfaces
  single Termux wrapper
  raw stdout and stderr plus real process return codes
  payload, registry, and transaction snapshots
  independent verifier
  root result-index
  PASS-or-FAIL .tar.zst archive

recovery retention
  PREPARED/APPLYING -> exact prior state + one ROLLED_BACK audit tombstone
  second rollback recovery -> NOOP_ROLLED_BACK
  COMMITTED -> exact new state + transaction cleanup
```

Implementation evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3C_TARGET_IMPLEMENTATION_RESULT.md
```

## Deferred boundaries

```text
Gate 3D runtime uninstall and final ownership boundary
Gate 4 upgrade and downgrade
```

## Evidence paths

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_RESULT.md
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
docs/evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
docs/evidence/STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_RESULT.md
docs/evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_RESULT.md
docs/evidence/STAGE3C_PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION_RESULT.md
docs/evidence/STAGE3C_PHASE5_GATE3B0_PRESERVATION_DIAGNOSTIC_RESULT.md
docs/evidence/STAGE3C_PHASE5_GATE3B_PRESERVATION_ACCEPTANCE_RESULT.md
docs/evidence/STAGE3C_PHASE5_GATE3C_ADDON_LIFECYCLE_DESIGN_RESULT.md
docs/evidence/STAGE3C_PHASE5_GATE3C_TARGET_IMPLEMENTATION_RESULT.md
```
