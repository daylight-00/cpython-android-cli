# Epoch 2 Roadmap

> **Recalibrated:** 2026-07-19 by ADR-0006 and ADR-0007
> **Detailed sequence:** [`EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md`](EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md)
> **Work items and gates:** [`EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)

## Historical authorities

E2-P0 through E2-P3 remain preserved in their original contracts, evidence, experiments, and handoffs.

```text
E2-P0  documentation and component boundaries          frozen
E2-P1  standalone artifact contract                     frozen
E2-P2  façade and Termux-native producer authority      frozen
E2-P3  primary S22 Ultra/API 36 qualification           frozen
        secondary Note9/API 29 qualification            frozen
        dual-real-device AArch64 Termux compatibility   accepted
        emulator                                        waived, not claimed
```

The Note9/API 29/Exynos run passed the unchanged 35-check matrix and is separately frozen. Together with the S22 Ultra/API 36 result, E2-P3 accepts bounded dual-real-device AArch64 Termux compatibility for the exact same product bytes. The emulator and original real-plus-emulator contract remain unqualified, and this historical closure does not change the recalibrated research sequence.

## Retired prospective phases

The former E2-P4 installer conversion, E2-P5 prerelease automation, E2-P6 repository promotion, and E2-P7 uv integration sequence is superseded. Those topics may reappear as selected Epoch 3 product responsibilities but are not canonical Epoch 2 phase authorities.

## Active sequence

```text
E2-R0  recalibration authority and raw research intake
E2-R1  UT-0 exact upstream control + UT-1 Astral artifact prototype
E2-R2  UT-2 loader/relocation/launcher/getpath + UT-3 sysconfig/SDK
E2-R3  UT-4 Android data policy + UT-5 capability matrices
E2-R4  UT-6 platform portability + UT-7 update portability
E2-R5  API A/B/C: official control and same-source API-36 comparisons
E2-R6  E2-G1..G8 closure, evidence export, Epoch 3 product seed
```

## Evidence-to-product boundary

```text
Epoch 2 evidence disposition
  pass / bounded-pass / fail / unavailable
        ↓
Epoch 3 selection disposition
  adopt / adopt-with-redesign / exclude / defer-to-epoch4
```

Experiment success does not require product inclusion. In particular, passing pip, CA, timezone, multiprocessing, SDK, uv, venv, optional artifact, or API-36 experiments remain decision inputs.

## Governing rule

```text
exact upstream control
  -> bounded Android experiments
  -> explicit evidence dispositions
  -> mandatory invariants + selectable decision inputs
  -> E2-G8 producer-independent export
  -> Epoch 3 selection register
  -> clean Epoch 3 release repository
  -> Epoch 4 source-producer substitution
```
