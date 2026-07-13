# Stage 3-C Phase 5 Scope: Installed Runtime and Lifecycle Validation

> **Status:** ACTIVE — Gate 3D final uninstall and ownership boundary design
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
Gate 3B   preserve-and-report product acceptance                  FROZEN
Gate 3C   addon lifecycle and dependency enforcement              FROZEN
Gate 3D   runtime uninstall and final ownership boundary          ACTIVE — DESIGN PENDING
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

## Frozen Gate 3B preserve-and-report product acceptance

```text
archive
  stage3c-phase5-gate3b-preservation-acceptance-results-20260713-024946.tgz

archive sha256
  0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b

root result-index sha256
  f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9

archive safety
  323 members / 290 regular / 33 directories / 0 unsafe / 0 links / 0 special

root indexed files
  289/289 exact

scenario / independent checks
  29/29 / 62/62 PASS

happy topology
  reinstall 4/4 / uninstall 4/4

crash recovery
  12/12

workflow
  scenario runner 0 / independent verifier 0 / workflow 0 / wrapper 0
```

Accepted crash boundaries:

```text
PREPARED       rc 90
late APPLYING  rc 93
COMMITTED      rc 92
```

Pre-commit recovery restores the prior registry and installed state while preserving the original modified leaf or unowned sentinel. Modified-owned states intentionally verify with exactly the modified registered leaf as `bad_paths` and rc 44; unowned-sentinel states verify cleanly with rc 0. Committed states retain the accepted residual, have an empty registry, and verify with rc 0.

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3B_PRESERVATION_ACCEPTANCE_RESULT.md
```

## Frozen Gate 3C addon lifecycle and dependency enforcement

```text
archive
  stage3c-phase5-gate3c-addon-lifecycle-results-20260713T033412Z.tar.zst

archive sha256
  43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a

root result-index sha256
  fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c

checks
  design 73/73
  target 50/50
  verifier 103/103
  external audit 27/27
```

Gate 3C freezes exact runtime-base prerequisites for both addons, no inter-addon dependency, both install/removal orders, dependency-invalid rejection without mutation, addon preservation and recovery, and complete runtime regression after addon removal.

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3C_ADDON_LIFECYCLE_ACCEPTANCE_RESULT.md
```

## Active Gate 3D final uninstall and ownership boundary

Gate 3D integrates the frozen Gate 3B runtime-base preserve-and-report behavior with the frozen Gate 3C composed-product lifecycle. It must begin from explicit composed/runtime-plus-addon/runtime-only states, reject runtime-base removal while addons remain, remove addons through accepted orders, and then audit final runtime-base removal.

Required final distinctions:

```text
registry empty
matching owned payload absent
approved modified-owned residual preserved and reported
unowned sentinel preserved and unchanged
required non-empty ancestors retained
transaction cleanup or accepted rollback tombstone
```

The immediate task is repository-side matrix and verifier design only. No target Gate 3D claim is authorized.

## Deferred Gate 4

Upgrade and downgrade remain deferred until a second complete frozen product identity exists. Synthetic version labels are not accepted.

## Non-reopening rule

Gate 3D must consume Gate 3B and Gate 3C as frozen authorities. It must not reopen preserve-and-report behavior, addon dependency policy, journal schema, registry schema, or manifest/archive identity. Any policy-changing intervention requires a separate authority decision.
