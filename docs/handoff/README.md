# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE5_GATE3A_INTERVENTION_DECISION_20260712.md
3. ../evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
4. ../stages/STAGE3C_PHASE5_GATE3A_DIAGNOSTIC_SCOPE.md
5. ../stages/STAGE3C_PHASE5_SCOPE.md
6. STAGE3C_PHASE5_EVIDENCE_LEDGER.md
7. STAGE3C_EVIDENCE_LEDGER.md
8. ../../experiments/stage3c-installed-runtime-lifecycle/README.md

Historical Gate 3A diagnostic design:
9. PHASE5_GATE3A_DIAGNOSTIC_HANDOFF_20260712.md

Frozen Gate 2 evidence:
10. ../evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
11. PHASE5_GATE3_HANDOFF_20260712.md
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

Phase 5 Gate 3A product acceptance
  BLOCKED

active authority
  narrow Phase 4 registered missing-leaf repair intervention
```

## Frozen diagnostic identity

```text
archive sha256
  9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2

result-index sha256
  a7507ab60de402a636c8e2899706aec77844896254f28dd068c8683dcb3dce7b
```

## Confirmed defect

```text
registered missing regular or symlink
  planned as repair
  recorded as replaced
  durable_move(absent source, backup)
  FileNotFoundError
  retained ROLLED_BACK journal
  missing leaf remains absent
```

## Authorized correction

```text
existing mismatching path
  retain replaced mutation semantics

missing registered non-directory
  use created mutation semantics
  do not move a nonexistent source
```

The intervention must preserve all diagnostic failure evidence and remain separate from Gate 3A product acceptance.
