# Stage 3-C Phase 5 Scope: Installed Runtime and Lifecycle Validation

> **Status:** ACTIVE — Gate 3B preserve-and-report product acceptance
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
Gate 3B0  preservation-boundary diagnostic census                 FROZEN
Gate 3B   preserve-and-report product acceptance                  ACTIVE
Gate 3C   addon lifecycle and dependency enforcement              DEFERRED
Gate 3D   runtime uninstall and final ownership boundary          DEFERRED
Gate 4    upgrade and downgrade with second frozen product        DEFERRED
```

## Frozen prior gates

```text
Gate 1
  archive 06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea
  result-index 29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377
  80/80 PASS

historical Gate 2
  archive 8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e
  result-index a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d
  80/80 at A and B / 46/46 PASS

Gate 3A0
  archive 9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2
  result-index a7507ab60de402a636c8e2899706aec77844896254f28dd068c8683dcb3dce7b
  17/17 + 31/31

Phase 4I
  archive d497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a
  result-index 7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6
  39/39 + 51/51 / crash 12/12

Gate 3A
  archive 16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142
  result-index a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128
  29/29 + 80/80 + 69/69

Gate 2R
  archive 8e2c131567d78a4208e7c8eb02e783a479713f6d867a3e5cd98eae60aa5738a7
  result-index 69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c
  80/80 at A and B / 46/46 / 15/15
```

## Frozen Gate 3B0 preservation diagnostic

```text
archive sha256
  ed5cb08cc576e74cacac4077cf9c9d7f3164a34913197aae9ef10cc8c113801a

result-index sha256
  7a8e982a44118dac3f232b2fefb578d22bedc0c7d32a6267ab3cd55c5e8deb27

scenario checks
  16/16

independent verifier
  40/40

workflow / wrapper rc
  0 / 0
```

Frozen current-behavior census:

```text
registered mismatch + reinstall
  ENFORCED_REPAIR

unowned sentinel + reinstall
  PRESERVED_NOOP

modified registered leaf + uninstall
  PRESERVED_AND_DEREGISTERED

unowned sentinel + uninstall
  UNOWNED_PRESERVED
```

The frozen installation contract already specifies:

```text
registry.local_modification_uninstall_policy
  preserve-and-report

uninstall.modified_regular_or_symlink
  PRESERVE_AND_REPORT

uninstall.owned_directory
  REMOVE_ONLY_WHEN_EMPTY

uninstall.structural_parent
  PRESERVE_NAMESPACE

uninstall.unowned_descendant
  PRESERVE
```

The target census matches the contract exactly. No intervention is required.

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3B0_PRESERVATION_DIAGNOSTIC_RESULT.md
```

## Active Gate 3B preserve-and-report product acceptance

### Product question

> Does the accepted engine enforce registered ownership on reinstall while safely preserving and reporting modified or unowned residual paths through uninstall and crash recovery?

### Required happy-path matrix

```text
modified owned regular + reinstall
modified owned symlink + reinstall
unowned file + reinstall
unowned directory + reinstall
modified owned regular + uninstall
modified owned symlink + uninstall
unowned file + uninstall
unowned directory + uninstall
```

### Required uninstall acceptance

```text
preserved output exact and sorted
modified registered residual exact
unowned sentinel residual exact
registry 1 artifact / 714 rows → 0 / 0
all matching registered leaves removed
only contract-approved non-empty parent directories preserved
empty-registry verify PASS
transaction residue 0
```

Registry-owned identity and residual identity are separate evidence surfaces. Registered directory identity is type plus mode only; residual unowned directory content must be independently and recursively fingerprinted.

### Required crash-recovery matrix

For modified regular, modified symlink, unowned file, and unowned directory uninstall states, cover at least:

```text
crash after PREPARED
crash during APPLYING before registry commit
crash after COMMITTED before cleanup
```

Pre-commit recovery must restore the complete installed state and prior registry while retaining the original modification or sentinel. Committed recovery must retain the accepted residual state and empty registry. A second recovery must be idempotent.

### Reinstall regressions

```text
registered mismatch restored exactly
unowned sentinel preserved exactly
registry unchanged
registry-owned identity unchanged after repair
runtime verification clean
```

### Verification and evidence policy

Product acceptance requires a separate independently verified Termux TGZ. Scenario-level PASS and console markers are not authority.

Every target-only workflow must use one wrapper that verifies accepted input TGZ identities, performs fresh extraction, executes the workflow, captures logs synchronously, writes status and result indices, and packages a TGZ on PASS or FAIL.

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
approved residual sentinels
matching owned payload removal
preserved modified-path reporting
registry transition
transaction residue check
final empty-state verification
```

## Deferred Gate 4

Upgrade and downgrade remain deferred until a second complete frozen product identity exists. Synthetic version labels are not accepted.

## Non-reopening rule

Gate 3B may validate the frozen preserve-and-report policy and its recovery behavior. It must not silently broaden journal schema, registry schema, manifest/archive identity, addon dependency policy, or upgrade/downgrade policy. Any policy-changing intervention requires a separate authority decision.
