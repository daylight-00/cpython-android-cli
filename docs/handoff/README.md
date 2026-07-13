# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE5_GATE3C_ADDON_LIFECYCLE_HANDOFF_20260713.md
3. ../../experiments/stage3c-installed-runtime-lifecycle/GATE3C_ADDON_LIFECYCLE_DESIGN.md
4. ../evidence/STAGE3C_PHASE5_GATE3C_ADDON_LIFECYCLE_DESIGN_RESULT.md
5. ../evidence/STAGE3C_PHASE5_GATE3C_TARGET_IMPLEMENTATION_RESULT.md
6. ../stages/STAGE3C_PHASE5_SCOPE.md
7. STAGE3C_PHASE5_EVIDENCE_LEDGER.md
8. ../evidence/STAGE3C_PHASE5_GATE3B_PRESERVATION_ACCEPTANCE_RESULT.md
9. ../../experiments/stage3c-installed-runtime-lifecycle/GATE3B_PRESERVATION_ACCEPTANCE.md
10. PHASE5_GATE3B_PRODUCT_ACCEPTANCE_HANDOFF_20260712.md
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
Gate 3C target implementation                       READY
Gate 3C target lifecycle/dependency enforcement      ACTIVE
Gate 3D final uninstall                              DEFERRED
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

## Active Gate 3C boundary

```text
development-addon -> runtime-base only
test-addon -> runtime-base only
no inter-addon dependency
both install and addon-removal orders
50-scenario target matrix
registry and ownership separation
12 addon crash-recovery scenarios
rollback audit tombstone / committed cleanup distinction
runtime-base exactness and behavior after addon removal
```

Gate 3C does not claim final runtime-base uninstall, upgrade, or downgrade.

## Evidence and transport rule

Only a complete independently inspected target archive can close a target gate. New archives use `.tar.zst`; historical `.tgz` evidence remains immutable. Console PASS markers alone are insufficient.
