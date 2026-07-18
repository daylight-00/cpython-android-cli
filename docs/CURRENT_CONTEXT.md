# Current Project Context

> **Current epoch:** Epoch 2 — recalibrated upstream-control research
> **Current gate:** E2-R0 recalibration authority
> **Next bounded gate:** E2-R1 exact official upstream control and direct adaptation
> **Frozen predecessor:** Epoch 1 through Stage 3-F

## Current decision

```text
Epoch 2
  Python.org Android product is the primary CPython control.
  BeeWare products selected by CPython are the dependency control.
  Direct standalone adaptation and bounded Android research continue.
  A controlled API 36 comparison is mandatory.

Epoch 3
  Create a clean upstream-derived release repository.
  Product artifacts and metadata primarily follow Astral standalone structure.
  Full CPython/dependency source production is not owned.

Epoch 4
  Build the full Astral-like Android source producer in this laboratory.
  Preserve the Epoch 3 consumer-facing product contract.
```

Authority: [`decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md`](decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md).

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
  package             prepared
  execution           deferred
  roadmap role        optional additional evidence

dual-device claim     not made
selectability         false
publication           not authorized
```

The Note9 package may be executed later against its exact frozen repository binding. It no longer blocks the recalibrated Epoch 2 sequence or Epoch 3 planning.

## Active Epoch 2 research sequence

```text
E2-R0  recalibration authority and raw research intake
E2-R1  exact official upstream control and direct adaptation
E2-R2  patch-update rehearsal and Python 3.15 preview
E2-R3  official control / CPython API 36 / complete API 36 comparison
E2-R4  minimum floor, 16 KiB pages, native SDK/wheel, host boundaries,
       cross-context probes, licenses, and uv consumer contract
E2-R5  evidence export and clean Epoch 3 product seed
```

## API comparison contract

```text
A  exact official Python.org/BeeWare binary control
B  same CPython and launcher sources compiled for API 36,
   upstream BeeWare binaries retained
C  same CPython and BeeWare dependency source revisions compiled for API 36
```

The API number is the intended changed variable. Source revisions, dependency versions, upstream patches, module surface, NDK identity, linkage topology, and build options remain fixed as practical.

## Repository roles

```text
cpython-android-cli
  permanent research/evidence/source-producer laboratory

Epoch 3 clean repository
  upstream-derived distribution, releases, CI, catalog, and consumers

Epoch 4 work in this repository
  project-owned CPython and dependency source producer
```

## Immediate reading path

1. [`decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md`](decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md)
2. [`roadmap/EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md`](roadmap/EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md)
3. [`epochs/EPOCH2_CHARTER.md`](epochs/EPOCH2_CHARTER.md)
4. [`epochs/EPOCH3_CHARTER.md`](epochs/EPOCH3_CHARTER.md)
5. [`epochs/EPOCH4_CHARTER.md`](epochs/EPOCH4_CHARTER.md)
6. [`references/EXTERNAL_RESEARCH_ARCHIVE_INTAKE_20260719.md`](references/EXTERNAL_RESEARCH_ARCHIVE_INTAKE_20260719.md)
7. [`references/raw/2026-07-19-epoch2-epoch4-recalibration/`](references/raw/2026-07-19-epoch2-epoch4-recalibration/)
8. [`evidence/E2_RECALIBRATION_AUTHORITY_FREEZE.md`](evidence/E2_RECALIBRATION_AUTHORITY_FREEZE.md)

## Next bounded gate

Design and execute only E2-R1. Acquire and verify the exact official upstream package, adapt it through the thinnest standalone path, enumerate every mutation, and compare the result with the frozen reconstructed-product baseline. Do not begin Epoch 4 source-producer implementation and do not relabel deferred Note9 evidence as accepted.
