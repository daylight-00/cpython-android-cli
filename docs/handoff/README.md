# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE5_GATE3A_DIAGNOSTIC_HANDOFF_20260712.md
3. ../stages/STAGE3C_PHASE5_GATE3A_DIAGNOSTIC_SCOPE.md
4. ../stages/STAGE3C_PHASE5_SCOPE.md
5. STAGE3C_PHASE5_EVIDENCE_LEDGER.md
6. STAGE3C_EVIDENCE_LEDGER.md
7. ../../experiments/stage3c-installed-runtime-lifecycle/README.md

Frozen Gate 2 evidence:
8. ../evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
9. PHASE5_GATE3_HANDOFF_20260712.md

Historical Gate 2 context:
10. PHASE5_GATE2_CORRECTION_20260712.md
11. PHASE5_GATE2_HANDOFF_20260712.md
12. ../../experiments/stage3c-installed-runtime-relocation/README.md
```

## Current state

```text
Stage 3-C Phases 1–4
  FROZEN

Phase 5 Gate 1
  FROZEN 80/80

Phase 5 Gate 2
  FROZEN 46/46

Phase 5 Gate 3A0
  ACTIVE
  reinstall/repair diagnostic census

Phase 5 Gate 3A product acceptance
  BLOCKED pending diagnostic and intervention decision
```

## Expected diagnostic matrix

```text
exact reinstall                 NOOP
four in-place mismatch classes  supported repair
missing regular                 expected unsupported
missing symlink                 expected unsupported
```

A diagnostic PASS is not Gate 3A product acceptance.

## Authority rule

Uploaded Termux TGZ evidence closes the diagnostic census. Console markers or static source review alone do not.

If missing-leaf failure is confirmed, preserve evidence and make an explicit Phase 4 intervention decision before continuing lifecycle gates.
