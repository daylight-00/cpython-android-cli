# Handoff — Epoch 2 to Epoch 4 recalibration

## Repository input

```text
branch  main
HEAD    7e9210ce21b31ed2b2c9008d6c1b1dbe6daf6214
tree    a232ec4daab0a71ba8137750e2b30df60d39b83e
```

## Decision

Epoch 2 is an upstream-control and Android adaptation research phase. Epoch 3 is a clean upstream-derived Astral-structured release repository. Epoch 4 is the full Astral-like source producer and must reproduce the Epoch 3 consumer contract.

## P3 disposition

- S22 Ultra authority remains accepted.
- emulator remains waived and unclaimed.
- Note9 package remains valid, optional, and deferred.
- no dual-device claim exists.

## Reading order

1. `docs/decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md`
2. `docs/roadmap/EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md`
3. `docs/epochs/EPOCH2_CHARTER.md`
4. `docs/epochs/EPOCH3_CHARTER.md`
5. `docs/epochs/EPOCH4_CHARTER.md`
6. `docs/references/EXTERNAL_RESEARCH_ARCHIVE_INTAKE_20260719.md`
7. `docs/references/raw/2026-07-19-epoch2-epoch4-recalibration/`

## Next action

E2-R1 official upstream control and direct adaptation. Do not begin the Epoch 4 source producer and do not treat the deferred Note9 execution as the current blocker.
