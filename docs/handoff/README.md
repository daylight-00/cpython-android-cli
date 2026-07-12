# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_HANDOFF_20260712.md
3. PHASE5_GATE3A_INTERVENTION_DECISION_20260712.md
4. ../evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
5. ../stages/STAGE3C_PHASE5_SCOPE.md
6. STAGE3C_PHASE5_EVIDENCE_LEDGER.md
7. ../../experiments/stage3c-missing-leaf-repair-intervention/README.md

Historical Gate 3A diagnostic design:
8. PHASE5_GATE3A_DIAGNOSTIC_HANDOFF_20260712.md
9. ../stages/STAGE3C_PHASE5_GATE3A_DIAGNOSTIC_SCOPE.md
10. ../../experiments/stage3c-installed-runtime-lifecycle/README.md

Frozen Gate 2 evidence:
11. ../evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
12. PHASE5_GATE3_HANDOFF_20260712.md
```

## Current state

```text
Stage 3-C Phases 1–4
  FROZEN except the explicitly authorized missing-leaf repair intervention

Phase 5 Gate 1
  FROZEN 80/80

Phase 5 Gate 2
  FROZEN 46/46

Phase 5 Gate 3A0 diagnostic
  FROZEN PASS
  scenario checks 17/17
  independent verifier 31/31

Phase 4I missing-leaf intervention
  ACTIVE
  authoritative Termux run pending

Phase 5 Gate 3A product acceptance
  BLOCKED
```

## Intervention target

```text
7 success/regression roots
12 crash-recovery roots
19 independent clones
39 scenario checks
51 independent verifier checks
```

Expected candidate behavior:

```text
missing registered regular
missing registered symlink
  created mutation
  no nonexistent backup move
  exact repair on success
  original missing state on pre-commit recovery
  repaired state on committed recovery
```

## Authority rule

Do not merge the corrective PR or call Gate 3A accepted from local validation. The complete Termux TGZ must be independently inspected first.
