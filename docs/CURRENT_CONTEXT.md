# Current Project Context

> **Current epoch:** Epoch 2 — upstream-thin research program
> **Current gate:** detailed plan authority frozen
> **Next bounded gate:** E2-R1 / UT-0 exact official upstream control
> **Frozen predecessor:** Epoch 1 through Stage 3-F

## Current decisions

```text
Epoch 2
  Python.org Android product is the primary CPython control.
  BeeWare products selected by CPython are the dependency control.
  Direct adaptation and bounded Android experiments continue.
  Same-source and same-recipe API 36 comparison is mandatory.
  Experiment success does not automatically select an Epoch 3 feature.

Epoch 3
  Create a clean upstream-derived release repository.
  Product artifacts and metadata primarily follow Astral standalone structure.
  Select every optional capability through an explicit selection register.
  Full CPython/dependency source production is not owned.

Epoch 4
  Build the full Astral-like Android source producer in this laboratory.
  Preserve the selected Epoch 3 consumer-facing product contract.
```

Authorities:

1. [`decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md`](decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md)
2. [`decisions/ADR-0007-EPOCH2-EVIDENCE-AND-EPOCH3-SELECTION-GATES.md`](decisions/ADR-0007-EPOCH2-EVIDENCE-AND-EPOCH3-SELECTION-GATES.md)
3. [`roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)

## Evidence-to-product boundary

```text
Epoch 2 evidence
  pass / bounded-pass / fail / unavailable
        ↓
Epoch 3 selection
  adopt / adopt-with-redesign / exclude / defer-to-epoch4
```

A passing pip experiment may still lead to an Epoch 3 product without base pip. The same applies to CA and timezone payloads, multiprocessing, SDK modes, uv integration, venv cases, optional artifacts, and API-36-derived inputs.

## Current E2-P3 disposition

```text
S22 Ultra / API 36 / qcom
  qualification       35/35
  result verifier     19/19
  independent review  38/38
  status              accepted and frozen

Android Emulator
  status              infrastructure-infeasible, waived, unclaimed

Galaxy Note9 / API 29 / Exynos 9810
  qualification       35/35
  result verifier     19/19
  independent review  41/41
  status              accepted and frozen

dual-device claim     accepted — AArch64 Termux compatibility
selectability         false
publication           not authorized
```

The Note9 profile is frozen together with the primary S22 Ultra profile as bounded dual-real-device AArch64 Termux compatibility evidence. The emulator remains unqualified and the original real-plus-emulator contract remains unsatisfied. This historical closure does not alter the upstream-thin research program or select any Epoch 3 feature.

## Active Epoch 2 sequence

```text
E2-R0  recalibration and detailed-plan authority
E2-R1  UT-0 exact upstream control + UT-1 Astral prototype
E2-R2  UT-2 loader/relocation/launcher/getpath + UT-3 sysconfig/SDK
E2-R3  UT-4 data policy + UT-5 capability matrices
E2-R4  UT-6 platform portability + UT-7 update portability
E2-R5  API A/B/C same-source and same-recipe API-36 comparison
E2-R6  E2-G1..G8 closure, evidence export, Epoch 3 product seed
```

## API comparison contract

```text
A  exact official Python.org/BeeWare binary control

B  same upstream CPython and launcher source revisions and patches,
   compiled for API 36 with official BeeWare binaries retained

C  same upstream CPython and BeeWare dependency source revisions,
   patches, recipes, topology, and toolchain identity as practical,
   compiled for API 36
```

The compile API is the intended changed variable. API-36 results are Epoch 2 evidence and are not automatic Epoch 3 inputs.

## Epoch 3 gate model

Initialization requires:

```text
E3-I1  accepted evidence export
E3-I2  complete selection register
E3-I3  clean repository boundary
E3-I4  contract freeze
```

Completion requires E3-G1 through E3-G10 in the detailed plan, including reproducible upstream acquisition, bounded transformation, clean runtime architecture, Astral artifacts, selected feature surface, platform qualification, host neutrality, update operations, consumer readiness, and the Epoch 4 substitution boundary.

## Repository roles

```text
cpython-android-cli
  permanent research/evidence/source-producer laboratory

Epoch 3 clean repository
  selected upstream-derived distribution, releases, CI, catalog, consumers

Epoch 4 work in this repository
  project-owned CPython and dependency source producer
```

## Immediate reading path

1. [`decisions/ADR-0007-EPOCH2-EVIDENCE-AND-EPOCH3-SELECTION-GATES.md`](decisions/ADR-0007-EPOCH2-EVIDENCE-AND-EPOCH3-SELECTION-GATES.md)
2. [`roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)
3. [`decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md`](decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md)
4. [`roadmap/EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md`](roadmap/EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md)
5. [`epochs/EPOCH2_CHARTER.md`](epochs/EPOCH2_CHARTER.md)
6. [`epochs/EPOCH3_CHARTER.md`](epochs/EPOCH3_CHARTER.md)
7. [`references/UPSTREAM_THIN_PLAN_INTAKE_20260719.md`](references/UPSTREAM_THIN_PLAN_INTAKE_20260719.md)
8. [`references/raw/2026-07-19-upstream-thin-plan/`](references/raw/2026-07-19-upstream-thin-plan/)
9. [`evidence/E2_UPSTREAM_THIN_PLAN_AUTHORITY_FREEZE.md`](evidence/E2_UPSTREAM_THIN_PLAN_AUTHORITY_FREEZE.md)

## Next bounded gate

Execute only UT-0 under E2-R1: acquire and verify the exact official upstream package, freeze its no-mutation inventory, map the inherited BeeWare dependency identities, and compare it with the reconstructed-product baseline.

Do not select Epoch 3 features or begin Epoch 4 source-producer implementation. E2-P3 dual-real-device evidence is historical compatibility evidence, not an Epoch 3 product-selection decision.
