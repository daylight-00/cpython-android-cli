# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION_HANDOFF_20260712.md
3. ../../experiments/stage3c-installed-runtime-relocation/GATE2R_CORRECTED_ENGINE_RELOCATION.md
4. ../evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_RESULT.md
5. ../stages/STAGE3C_PHASE5_SCOPE.md
6. STAGE3C_PHASE5_EVIDENCE_LEDGER.md

Historical Gate 3A authority:
7. ../../experiments/stage3c-installed-runtime-lifecycle/GATE3A_PRODUCT_ACCEPTANCE.md
8. PHASE5_GATE3A_PRODUCT_ACCEPTANCE_HANDOFF_20260712.md
9. ../evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_FAILURE_20260712.md
10. ../evidence/STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_RESULT.md
11. PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_HANDOFF_20260712.md
12. PHASE5_GATE3A_INTERVENTION_DECISION_20260712.md

Historical diagnostic authority:
13. ../evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
14. PHASE5_GATE3A_DIAGNOSTIC_HANDOFF_20260712.md

Historical Gate 2 evidence:
15. ../evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
16. PHASE5_GATE3_HANDOFF_20260712.md
```

## Current state

```text
Phase 5 Gate 1
  FROZEN 80/80

Phase 5 historical Gate 2
  FROZEN 46/46

Phase 5 Gate 3A0 diagnostic
  FROZEN 17/17 + 31/31

Phase 4I missing-leaf intervention
  FROZEN 39/39 + 51/51

Phase 5 Gate 3A product acceptance
  FROZEN 29/29 + 80/80 + 69/69

Phase 5 Gate 2R corrected-engine relocation
  ACTIVE
  authoritative Termux run pending
```

## Frozen Gate 3A identity

```text
archive sha256
  16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142

result-index sha256
  a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128
```

## Active Gate 2R target

```text
fresh corrected-engine install at A
Gate 1-equivalent 80/80 at A and B
historical relocation verifier 46/46
corrected-engine authority verifier 15/15
same-filesystem complete-root mv
root inode preserved
complete-root shape 719/60/656/3
registry and portable identity exact
strict and complete-root identity unchanged
zero stale A references
full destination runtime validation
```

## Termux execution policy

All target-only workflows must provide one wrapper script that performs accepted input verification, fresh extraction, execution, status/index capture, and TGZ packaging on PASS or FAIL. No separate `tar` command should be required.

## Authority rule

Only a complete independently inspected Termux TGZ can close Gate 2R. Console markers and scenario-level `pass` fields are insufficient.
