# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE5_GATE3D_FINAL_UNINSTALL_HANDOFF_20260713.md
3. ../evidence/STAGE3C_PHASE5_GATE3D_TARGET_IMPLEMENTATION_RESULT.md
4. ../../experiments/stage3c-installed-runtime-lifecycle/GATE3D_FINAL_UNINSTALL_DESIGN.md
5. ../../experiments/stage3c-installed-runtime-lifecycle/gate3d-final-uninstall-matrix.json
6. ../evidence/STAGE3C_PHASE5_GATE3C_ADDON_LIFECYCLE_ACCEPTANCE_RESULT.md
7. PHASE5_GATE3C_ADDON_LIFECYCLE_HANDOFF_20260713.md
8. ../../experiments/stage3c-installed-runtime-lifecycle/GATE3C_ADDON_LIFECYCLE_DESIGN.md
9. ../evidence/STAGE3C_PHASE5_GATE3C_ARCHIVE_INTEGRITY_CORRECTION.md
10. ../evidence/STAGE3C_PHASE5_GATE3C_TARGET_IMPLEMENTATION_RESULT.md
11. ../stages/STAGE3C_PHASE5_SCOPE.md
12. STAGE3C_PHASE5_EVIDENCE_LEDGER.md
13. ../evidence/STAGE3C_PHASE5_GATE3B_PRESERVATION_ACCEPTANCE_RESULT.md
```

## Current state

```text
Gate 1 installed runtime baseline                    FROZEN 80/80
historical Gate 2 relocation                         FROZEN 46/46
Gate 3A0 reinstall/repair diagnostic                 FROZEN 17/17 + 31/31
Phase 4I missing-leaf intervention                   FROZEN 39/39 + 51/51
Gate 3A reinstall/repair product acceptance          FROZEN 29/29 + 80/80 + 69/69
Gate 2R corrected-engine relocation                  FROZEN 80/80 + 46/46 + 15/15
Gate 3B0 preservation diagnostic                     FROZEN 16/16 + 40/40
Gate 3B preserve-and-report product acceptance       FROZEN 29/29 + 62/62
Gate 3C design                                       FROZEN 73/73, 50 scenarios
Gate 3C target implementation                       FROZEN 50/50 + 103/103
Gate 3C target lifecycle/dependency enforcement      FROZEN 27/27 external audit
Gate 3D final uninstall design                       DESIGN FROZEN — 108/108, 44 scenarios
Gate 3D target implementation                       READY — 44/44 local + 138/138 verifier; Termux pending
Gate 4 upgrade/downgrade                             DEFERRED
```

## Frozen Gate 3B identity

```text
archive sha256
  0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b

root result-index sha256
  f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9

happy reinstall / uninstall / crash
  4/4 / 4/4 / 12/12
```

Crash boundaries are PREPARED rc 90, late APPLYING rc 93, and COMMITTED rc 92. Modified-owned pre-commit states intentionally verify with exactly the modified leaf and rc 44; unowned pre-commit and committed states verify rc 0.

## Frozen Gate 3C identity

```text
archive sha256
  43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a

root result-index sha256
  fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c

scenario / verifier / external audit
  50/50 / 103/103 / 27/27 PASS
```

Gate 3C accepts both addon install and removal orders, exact runtime-base prerequisites, dependency rejection without mutation, addon preservation/recovery, and complete runtime revalidation after addon removal.

## Frozen Gate 3D design boundary

```text
consume frozen Gate 3B runtime-base uninstall semantics
consume frozen Gate 3C composed-product lifecycle
remove all addons before runtime-base
final registry / owned-payload / residual separation
modified-owned and unowned residual census
transaction recovery and second-recovery idempotence
no upgrade or downgrade claim

canonical design matrix: 44 scenarios
target runner/verifier implemented
local semantic validation: 44/44 + 138/138
authoritative Termux archive and external inspection still required
```

## Evidence and transport rule

Only a complete independently inspected target archive can close a target gate. New archives use `.tar.zst`; historical `.tgz` evidence remains immutable. Console PASS markers alone are insufficient.
