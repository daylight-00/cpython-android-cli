# Recalibrated roadmap: Epoch 2 through Epoch 4

> **Canonical decisions:** ADR-0006 and ADR-0007
> **Date:** 2026-07-19
> **Detailed work and gates:** [`EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)

## Preserved history

E2-P0 through E2-P3 remain frozen or bounded historical authorities. Their artifacts, contracts, failures, corrections, and accepted target evidence are not rewritten.

The former prospective E2-P4 through E2-P7 sequence is retired. Installer conversion, prerelease automation, repository promotion, and uv integration are no longer the canonical remaining Epoch 2 phases.

## Current disposition

```text
S22 Ultra API 36 primary qualification    accepted
emulator qualification                     waived and unclaimed
dual-real-device AArch64 Termux evidence    accepted for same product bytes
Note9 API 29 secondary qualification       frozen pass — 35/35 + 19/19 + 41/41
dual-real-device closure                    not claimed
selectability/publication                   not claimed
```

## Governing evidence-to-product rule

Epoch 2 determines feasibility and boundaries. Epoch 3 independently selects the product.

```text
Epoch 2 evidence:
  pass / bounded-pass / fail / unavailable

Epoch 3 selection:
  adopt / adopt-with-redesign / exclude / defer-to-epoch4
```

A passed experiment is not automatic product inclusion. Base pip may pass and still be excluded. The same rule applies to CA/timezone bundling, SDK modes, multiprocessing, venv cases, uv integration, optional artifacts, and API-36-derived inputs.

## E2-R0 — Recalibration authority

**Goal:** adjudicate external research, freeze the upstream-first decision, preserve raw inputs, and define Epoch 2/3/4 boundaries.

**Acceptance:** exact raw archive bytes and hashes retained; ADR, charters, ownership, roadmap, current navigation, and machine verifier agree; negative fixtures reject source-producer migration into Epoch 3 and stale mandatory Note9/emulator claims.

## E2-R1 — Exact official upstream control and Astral prototype

**Goal:** consume the exact Python.org Android package and inherited BeeWare dependencies without local CPython production, freeze the no-mutation control, and prove truthful Astral full/install-only/stripped and `PYTHON.json` semantics.

**Detailed work:** UT-0 exact upstream control and UT-1 Astral artifact prototype.

**Outputs:** upstream input manifest, package/ELF/extension/sysconfig inventories, truthful artifact prototype, unavailable-build-fact policy, mutation baseline, and direct-adaptation stop/go decision.

## E2-R2 — Loader, relocation, launcher, getpath, and SDK

**Goal:** replace research bootstrap workarounds with a clean standalone mechanism and prove portable development metadata.

**Detailed work:** UT-2 and UT-3.

**Outputs:** per-object RUNPATH evidence, launcher/getpath decision, relocation and symlink matrix, normalized sysconfig, real Android native-extension wheel, and SDK-mode decision inputs.

## E2-R3 — Android data and feature evidence

**Goal:** establish host-neutral data and writable-state policies and produce bounded capability matrices.

**Detailed work:** UT-4 and UT-5.

**Outputs:** CA/timezone candidates, writable-state contract, subprocess and venv support boundaries, pip and uv evidence, multiprocessing classification, and Epoch 3 feature-selection inputs.

## E2-R4 — Platform and update portability

**Goal:** prove critical Android platform boundaries and adaptation maintainability.

**Detailed work:** UT-6 and UT-7.

**Outputs:** minimum-floor evidence, 16 KiB page-size results, context-differential evidence, one patch-update rehearsal, Python 3.15 preview, and version-specific delta census.

## E2-R5 — Controlled API-36 source-equivalent comparison

**Goal:** isolate compile-time Android API behavior while reusing upstream-published sources, patches, recipes, topology, and toolchain decisions as practical.

```text
A  exact Python.org/BeeWare binary control
B  same-source CPython/launcher API 36, official BeeWare binaries
C  same-source and same-recipe CPython/BeeWare API 36 rebuild
```

API 36 is mandatory Epoch 2 research. It is not automatic Epoch 3 input or release-floor selection.

## E2-R6 — Evidence export and Epoch 3 product seed

**Goal:** resolve E2-G1 through E2-G8 and export a bounded, producer-independent decision set plus one accepted upstream-derived product seed.

**Outputs:** supported and withheld target matrix, exact local delta, mandatory invariants, selectable-item evidence, archive/metadata contract, upstream acquisition rules, qualification contract, unresolved risks, selection candidates, clean-repository seed, and Epoch 4 deferred producer questions.

## Epoch 3 — Clean release repository

Initialize only after E3-I1 through E3-I4 pass. Build an upstream-derived Astral-structured distribution from pinned upstream products plus selected project-owned adaptation.

Epoch 3 completion requires E3-G1 through E3-G10. The clean product ships only capabilities authorized by the selection register.

## Epoch 4 — Full source producer

In the laboratory, reproduce the selected Epoch 3 contract from CPython and dependency sources using an Astral-like producer and artifact architecture. Source-production details may differ; consumer-visible changes require a separate product-architecture decision.
