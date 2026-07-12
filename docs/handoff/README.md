# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE5_GATE2_HANDOFF_20260712.md
3. STAGE3C_EVIDENCE_LEDGER.md
4. ../stages/STAGE3C_SCOPE.md
5. ../stages/STAGE3C_PHASE5_SCOPE.md
6. ../../experiments/stage3c-installed-runtime-relocation/README.md

Historical Gate 1 correction context:
7. PHASE5_GATE1_CORRECTION_20260712.md
8. SESSION_HANDOFF_20260712.md
9. ../../experiments/stage3c-installed-runtime-baseline/README.md
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

next authoritative action
  run installed-runtime whole-root relocation on Termux
  upload the complete Gate 2 TGZ
```

## Authority rule

The repository records the design and frozen identities. Uploaded Termux TGZ evidence closes target gates.

Do not infer a PASS from local validation, final console markers alone, or the absence of visible errors.
