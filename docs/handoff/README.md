# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. ../../README.md
2. ../PROJECT_CONTEXT_STAGE3C.md
3. COLLABORATION_PROTOCOL.md
4. ../GITHUB_COLLABORATION_WORKFLOW.md
5. PHASE5_GATE4_UPGRADE_DOWNGRADE_HANDOFF_20260713.md
6. ../../experiments/stage3c-gate4-second-product-authority/GATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN.md
7. ../../experiments/stage3c-gate4-second-product-authority/gate4a-second-product-authority-input.json
8. ../../experiments/stage3c-gate4-second-product-authority/gate4a-second-product-authority-matrix.json
9. ../evidence/STAGE3C_PHASE5_GATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN_RESULT.md
10. ../stages/STAGE3C_PHASE5_SCOPE.md
11. STAGE3C_PHASE5_EVIDENCE_LEDGER.md
12. ../evidence/STAGE3C_PHASE5_GATE3D_FINAL_UNINSTALL_ACCEPTANCE_RESULT.md
13. PHASE5_GATE3D_FINAL_UNINSTALL_HANDOFF_20260713.md
14. ../../experiments/stage3c-installed-runtime-lifecycle/gate3d-final-uninstall-acceptance.json
15. ../evidence/STAGE3C_PHASE5_GATE3D_EXTERNAL_AUDIT.json
16. ../evidence/STAGE3C_PHASE5_GATE3D_TARGET_IMPLEMENTATION_RESULT.md
17. ../../experiments/stage3c-installed-runtime-lifecycle/GATE3D_FINAL_UNINSTALL_DESIGN.md
18. ../evidence/STAGE3C_PHASE5_GATE3C_ADDON_LIFECYCLE_ACCEPTANCE_RESULT.md
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
Gate 3D final uninstall design                       FROZEN 108/108, 44 scenarios
Gate 3D final uninstall target                       FROZEN 44/44 + 138/138 + 37/37
Gate 4 upgrade/downgrade                             ACTIVE — second product authority/design pending
Gate 4A authority acquisition                          DESIGN FROZEN — 3.14.5 input capture pending
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

## Frozen Gate 3D identity

```text
archive sha256
  579b880495098e9a46b40e2d96c9555178d0ad8c725d40768e6b854227d66143

root result-index sha256
  5f9aa64cb4e0679a4784c9c3b8ebd6d8d91829704984672186dc9f9c0d96ed60

result-tree-safety sha256
  47b571d79990cf6c5f1157f7784a5acfa47478b04a7c6f55185d3c4f38ab8a00

scenario / verifier / external audit
  44/44 / 138/138 / 37/37 PASS
```

Gate 3D accepts complete addon teardown, final runtime-base uninstall, exact registry and owned-payload removal, approved residual preservation, recovery, lock exclusion, and final archive/index integrity.

## Active Gate 4 boundary

Gate 4A selected CPython 3.14.5 (`v3.14.5`, `5607950ef232dad16d75c0cf53101d9649d89115`) as the genuine second-product input. Exact source/producer/dependency/toolchain capture is next, followed by clean replay, three-artifact materialization, standalone Termux validation, and independent freeze.

No second-product artifact authority is frozen. No upgrade/downgrade matrix or target claim is frozen. A synthetic version label, edited copy of the first product, or official reference package used directly as project authority is not acceptable.

## Evidence and transport rule

Only a complete independently inspected target archive can close a target gate. New archives use `.tar.zst`; historical `.tgz` evidence remains immutable. Console PASS markers alone are insufficient.
