# Project Context: Stage 3-F Publication and Acquisition Boundaries

> **Status:** Stage 3-F frozen through Gate 5 independent publication/acquisition freeze
> **Active boundary:** none — a new stage is required for broader work
> **Canonical branch:** `agent/stage3f-publication-acquisition`
> **Stage input:** `6419e107e4aa8400ebd3d98f3583999075b8b935`, tree `e16edd99bfadf2135d0b632ddef4d292c0d80ea6`
> **Final pre-freeze input:** `1e7797218473463bc85f6413c49080301eda2ad7`, tree `a3a1cb90f12b20ab47203b4f6b47d8a9694b0e04`

## Final gate state

```text
Gate 1  publication/acquisition authority design        FROZEN
Gate 2  immutable publication snapshot contract         FROZEN — 18/18, explicit retention correction
Gate 3  loopback transport/acquisition implementation   FROZEN — 31/31
Gate 4  Termux target acquisition validation             FROZEN — retained bytes, 16/16 + 31/31
Gate 5  independent publication/acquisition freeze       FROZEN
```

## Frozen authority

Product identity is exact bytes, byte size, SHA-256, provenance, and platform identity. Catalog rows bind exact keys to immutable products. A publication snapshot is canonical immutable metadata with a separate digest. Endpoint locators are pointers only. Transport bytes remain untrusted candidates until exact size, SHA-256, and snapshot binding pass. Verified cache objects are content-addressed. Installation remains a separate Stage 3-E authority.

## Correction lineage

Gate 2 freezes canonicalization behavior, but its original concrete archive bytes were not retained. Gate 4 v1 failed closed at derivation and preserved result `2a076288652f1c342da49eccbe4507291df05d1d596b5c6f1d5646610b5990be`. The original snapshot remains historical and unselectable.

Gate 4A retained exact archive bytes and established the selectable snapshot:

```text
3.14.5  9761545   2edec6cfaf20a44b2458567856c1d505e6942d0e43da0e8ba2a36761ebc05be2
3.14.6  11788907  f0c449f7bc5b5bd740f4776f43bec4418645d5f33da220fa523409b6aa0af208
snapshot body    dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233
snapshot file    419a9d4303fd6b3d7686400c7a275117ae6fe3421c93c30ff356529fc483b9e3
```

Both payloads pass 714/714 strict fidelity. Result `6cba95839a5dc05a7d4261467f1b7693e9d232fd44abe21ca4712e09b8e1977b` passes a 16/16 target matrix and 31/31 independent audit, with exact bytes retained in its self-indexed evidence.

## Gate 5 freeze

The repository record at `1e7797218473463bc85f6413c49080301eda2ad7` / `a3a1cb90f12b20ab47203b4f6b47d8a9694b0e04` was independently audited through result `daaf64255fce6d9c1ef2f5eb5e57d8dcc85472a4be48e56c47f21b94dee891f8`: 49 safe members, 46/46 self-index, project control 91/91, canonical authorship, exact remote readback, and clean post-state. Gate 5 freezes this complete lineage. No gate remains active.

## Deferred boundary

Public hosting, DNS/TLS/origin authentication, signatures, production redirects and mirrors, uv automatic acquisition, resumable transfer, cache eviction, installation, default-root adoption, global links, upgrades, recovery, concurrency, durability, third products, and upstream uv Android support require a new stage.

## Current reading path

```text
README.md
  -> docs/PROJECT_CONTEXT_STAGE3F.md
  -> docs/stages/STAGE3F_SCOPE.md
  -> experiments/stage3f-publication-acquisition/gate2-retention-correction-authority.json
  -> experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json
  -> experiments/stage3f-publication-acquisition/gate4-retained-artifact-acquisition-authority.json
  -> experiments/stage3f-publication-acquisition/GATE5_INDEPENDENT_PUBLICATION_ACQUISITION_FREEZE.md
  -> experiments/stage3f-publication-acquisition/gate5-independent-publication-acquisition-freeze.json
  -> docs/evidence/STAGE3F_GATE5_INDEPENDENT_FREEZE.md
  -> docs/evidence/STAGE3F_FINAL_SUMMARY.md
  -> docs/handoff/2026-07-16-stage3f-independent-freeze.md
```
