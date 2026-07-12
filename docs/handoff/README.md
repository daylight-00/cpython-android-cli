# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE5_GATE3_HANDOFF_20260712.md
3. STAGE3C_PHASE5_EVIDENCE_LEDGER.md
4. STAGE3C_EVIDENCE_LEDGER.md
5. ../stages/STAGE3C_SCOPE.md
6. ../stages/STAGE3C_PHASE5_SCOPE.md
7. ../evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md

Historical Gate 2 context:
8. PHASE5_GATE2_CORRECTION_20260712.md
9. PHASE5_GATE2_HANDOFF_20260712.md
10. ../../experiments/stage3c-installed-runtime-relocation/README.md

Historical Gate 1 context:
11. PHASE5_GATE1_CORRECTION_20260712.md
12. SESSION_HANDOFF_20260712.md
13. ../../experiments/stage3c-installed-runtime-baseline/README.md
```

## Current state

```text
Stage 3-C Phases 1–4
  FROZEN

Stage 3-C Phase 5 Gate 1
  FROZEN PASS
  verifier 80/80

Stage 3-C Phase 5 Gate 2
  FROZEN PASS
  Gate 1 prerequisite at A 80/80
  Gate 1 revalidation at B 80/80
  Gate 2 verifier 46/46

preserved failures
  Gate 1 first target 78/80
  Gate 2 first target 45/46

Stage 3-C Phase 5 Gate 3A
  ACTIVE DESIGN BOUNDARY
  same-version reinstall NOOP and registered corruption repair
```

## Frozen Gate 2 identity

```text
archive sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

complete-root shape
  719 entries / 60 directories / 656 regular / 3 symlinks

complete-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30
```

## Authority rule

The repository records the design and frozen identities. Uploaded Termux TGZ evidence closes target gates.

Do not infer a PASS from local validation, final console markers alone, or the absence of visible errors.
