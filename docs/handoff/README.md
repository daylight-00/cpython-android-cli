# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE5_GATE2_CORRECTION_20260712.md
3. PHASE5_GATE2_HANDOFF_20260712.md
4. STAGE3C_EVIDENCE_LEDGER.md
5. ../stages/STAGE3C_SCOPE.md
6. ../stages/STAGE3C_PHASE5_SCOPE.md
7. ../../experiments/stage3c-installed-runtime-relocation/README.md

Historical Gate 1 context:
8. PHASE5_GATE1_CORRECTION_20260712.md
9. SESSION_HANDOFF_20260712.md
10. ../../experiments/stage3c-installed-runtime-baseline/README.md
```

## Current state

```text
Stage 3-C Phases 1–4
  FROZEN

Stage 3-C Phase 5 Gate 1
  FROZEN PASS
  verifier 80/80

first Gate 1 target result
  preserved FAIL 78/80

Stage 3-C Phase 5 Gate 2
  ACTIVE
  corrected authoritative rerun pending

first Gate 2 target result
  preserved FAIL 45/46
  incorrect complete-root count only

next authoritative action
  rerun installed-runtime whole-root relocation on Termux
  expected complete-root shape 719/60/656/3
  upload the corrected Gate 2 TGZ
```

## Authority rule

The repository records the design and frozen identities. Uploaded Termux TGZ evidence closes target gates.

Do not infer a PASS from local validation, final console markers alone, or the absence of visible errors.
