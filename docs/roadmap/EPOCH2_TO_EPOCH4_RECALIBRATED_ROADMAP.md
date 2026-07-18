# Recalibrated roadmap: Epoch 2 through Epoch 4

> **Canonical decision:** ADR-0006
> **Date:** 2026-07-19

## Preserved history

E2-P0 through E2-P3 remain frozen or bounded historical authorities. Their artifacts, contracts, failures, corrections, and accepted target evidence are not rewritten.

The former prospective E2-P4 through E2-P7 sequence is retired. Installer conversion, prerelease automation, repository promotion, and uv integration are no longer the canonical remaining Epoch 2 phases.

## Current disposition

```text
S22 Ultra API 36 primary qualification    accepted
emulator qualification                     waived and unclaimed
Note9 API 29 secondary qualification       prepared, optional, deferred
dual-real-device closure                    not claimed
selectability/publication                   not claimed
```

## E2-R0 — Recalibration authority

**Goal:** adjudicate external research, freeze the upstream-first decision, preserve raw inputs, and define Epoch 2/3/4 boundaries.

**Acceptance:** exact raw archive bytes and hashes retained; ADR, charters, ownership, roadmap, current navigation, and machine verifier agree; negative fixtures reject source-producer migration into Epoch 3 and stale mandatory Note9/emulator claims.

## E2-R1 — Official upstream control and direct adaptation

**Goal:** consume the exact Python.org Android package and inherited BeeWare dependencies without local CPython production, apply the minimum enumerated standalone delta, and run essential qualification.

**Outputs:** upstream input manifest, mutation manifest, adapted archive, comparison against the frozen reconstructed producer, target evidence, and stop/go decision for the thin upstream path.

## E2-R2 — Upstream update portability

**Goal:** rehearse one CPython patch update and produce a Python 3.15 delta preview.

**Outputs:** configuration-only versus code-change census, package-layout delta, extension/sysconfig/wheel delta, launcher compatibility, and upstream security/update responsibility map.

## E2-R3 — Android API comparison

**Goal:** isolate the effect of compile-time API policy.

```text
A  exact Python.org/BeeWare binary control
B  same CPython and launcher sources at API 36,
   upstream BeeWare binary dependencies retained
C  same CPython and BeeWare dependency source revisions at API 36
```

**Controls:** source revisions, dependency versions, upstream patches, module set, NDK identity, linkage topology, and build options remain constant as practical.

**Measurements:** runtime compatibility, ELF requirements, symbols, TLS behavior, subprocess and file APIs, size, startup, extension imports, wheel tags, provenance burden, and minimum runtime floor.

## E2-R4 — Product-boundary evidence

**Goal:** close remaining Android adaptation questions required by Epoch 3.

**Work:** minimum-floor qualification, 16 KiB page-size validation, native-extension SDK probe, wheel build/import, relocation matrix, host-data policy, Termux/ADB/root differential probes, license/source mapping, and uv consumer requirements.

## E2-R5 — Evidence export and Epoch 3 product seed

**Goal:** export a bounded, producer-independent decision set and one accepted upstream-derived product seed.

**Outputs:** supported target matrix, exact local delta, archive/metadata contract, upstream acquisition rules, qualification contract, unresolved risks, clean-repository seed, and Epoch 4 deferred producer questions.

## Epoch 3 — Clean release repository

Initialize and maintain the upstream-derived Astral-structured distribution. Build release artifacts from pinned upstream products plus the project-owned adaptation; do not own full source production.

## Epoch 4 — Full source producer

In the laboratory, reproduce the Epoch 3 contract from CPython and dependency sources using an Astral-like producer and artifact architecture.
