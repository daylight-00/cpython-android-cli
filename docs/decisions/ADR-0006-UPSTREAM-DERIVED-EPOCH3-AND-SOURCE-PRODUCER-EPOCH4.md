# ADR-0006: Upstream-derived Epoch 3 and source-producing Epoch 4

- **Status:** Accepted
- **Date:** 2026-07-19
- **Supersedes:** the prospective repository-promotion and source-producer sequence in ADR-0003 and the former E2-P4 through E2-P7 roadmap

## Context

External research reviewed the official CPython Android release model, BeeWare's dependency artifacts, Astral's `python-build-standalone` distribution model, Android API-level behavior, and the existing repository evidence.

The previous roadmap mixed three different responsibilities:

1. proving Android/Bionic adaptation questions;
2. constructing a clean standalone release repository;
3. owning a full source producer and dependency build graph.

That mixture made the source-producer decision appear to be an immediate prerequisite for a useful clean product. The project owner has chosen to trust the upstream production decisions first and defer full source ownership until the binary-derived product contract is stable.

## Decision

### Epoch 2 — upstream behavior and Android adaptation research

Epoch 2 uses the official Python.org Android product and the BeeWare dependency products selected by CPython as the primary control. It determines the minimum local adaptation required for an Android/Bionic standalone CLI and finishes bounded Android-specific evidence.

The official upstream API policy remains the control. Epoch 2 must additionally run a controlled API 36 comparison while holding source revisions, dependency versions, upstream patches, module surface, NDK identity, and linkage topology as constant as practical.

Required comparison classes are:

```text
A  exact official Python.org/BeeWare binary control
B  same CPython and launcher sources rebuilt for API 36,
   retaining the upstream BeeWare dependency binaries
C  same CPython and BeeWare dependency source revisions rebuilt for API 36
```

### Epoch 3 — clean upstream-derived release repository

Epoch 3 creates a new clean product repository. It consumes verified Python.org and BeeWare products, applies only enumerated standalone adaptation, and releases an Android/Bionic distribution whose artifact and metadata structure primarily follows Astral's standalone distribution.

Epoch 3 owns distribution assembly, launcher/adaptation, archive transformation, metadata, checksums, licenses, qualification, CI, release catalog, uv-facing consumption, and public maintenance of the project-owned delta. It does not own CPython or dependency source production.

### Epoch 4 — full Astral-like source producer

Epoch 4 remains in the research laboratory and builds the complete source-producing system: CPython, dependency recipes, NDK/toolchain materialization, extension configuration, linkage policy, optimization profiles, reproducibility, and source provenance.

Epoch 4 must reproduce the Epoch 3 consumer-facing product contract. Source-production details may differ; archive classes, target identity, runtime layout, module surface, wheel behavior, relocation, metadata semantics, and consumer behavior should not differ without a separate product-architecture decision.

## Structural reference

For both Epoch 3 and Epoch 4, Astral's standalone distribution is the primary structural reference, not merely a role analogy. Android-specific divergence must be explicit and justified.

Expected common surface includes:

```text
full
install_only
install_only_stripped
machine-readable Python and target metadata
release index and exact checksums
licenses and provenance
stable archive root and runtime paths
qualification and consumer contracts
```

Epoch 3 `full` retains upstream inputs, project overlays, mutation manifests, installed product, and audit material. Epoch 4 `full` additionally retains project-owned source-build products and intermediates.

## Repository boundary

`cpython-android-cli` remains the permanent research, evidence, rejected-alternative, and source-producer laboratory. The Epoch 3 release repository is initialized cleanly from an accepted product seed. It does not need to carry the laboratory's full history.

## E2-P3 disposition

The S22 Ultra primary qualification remains accepted. Emulator qualification remains waived and unclaimed. The prepared Note9 secondary qualification remains valid optional deferred evidence, but it is no longer a prerequisite for the recalibrated Epoch 2 research sequence or Epoch 3 design work. No dual-device or emulator claim is inferred.

## Consequences

- upstream production choices reduce near-term maintenance and security burden;
- Epoch 3 can deliver a clean Astral-structured Android distribution before source production is owned;
- Epoch 4 can compare source-produced output against a stable external contract;
- exact upstream control and API 36 variants become explicit Epoch 2 experiments;
- former installer-first, prerelease, promotion, and uv phases are retired as the canonical Epoch 2 sequence;
- historical contracts and evidence remain valid within their original claim boundaries.
