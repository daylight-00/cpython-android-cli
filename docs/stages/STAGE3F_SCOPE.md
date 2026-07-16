# Stage 3-F Scope: Publication and Acquisition Boundaries

> **Status:** ACTIVE — corrected Gate 4 frozen; Gate 5 active next
> **Input:** frozen Stage 3-E Gate 5 exact-key, local, project-owned managed-Python distribution
> **Primary target:** Termux on Android arm64; Gate 4 accepted
> **Canonical branch:** `agent/stage3f-publication-acquisition`

## Stage question

How can the two frozen exact HW-T Android CPython products be published and acquired without conflating immutable product identity, catalog metadata, mutable endpoint state, transport bytes, cache state, and installation authority?

## Gate sequence

```text
Gate 1  publication/acquisition authority design        FROZEN
Gate 2  immutable publication snapshot contract         FROZEN — 18/18
Gate 3  loopback transport/acquisition implementation   FROZEN — 31/31
Gate 4  Termux target network-acquisition validation     FROZEN — retained bytes, 16/16 + 31/31
Gate 5  independent publication/acquisition freeze       ACTIVE NEXT
```

## Frozen authority separation

```text
product identity
catalog row
publication snapshot
endpoint locator
transport observation
acquisition candidate
verified cache
installation root
```

SHA-256 and exact byte size bind an artifact identity. A URL, redirect, server, filename, cache path, or catalog ordering does not. A mutable endpoint may select an immutable snapshot but cannot redefine an exact product key.

## Gate 2 result and retention correction

Gate 2 freezes canonicalization and observation behavior with 18/18 local verification. Its original snapshot is retained as historical contract evidence but is unselectable for acquisition because the exact transient archive bytes were not retained.

The fail-closed Gate 4 v1 archive `2a076288652f1c342da49eccbe4507291df05d1d596b5c6f1d5646610b5990be` exposed that retention gap before target acquisition. Gate 4A then retained exact replacement archive bytes, verified strict 714/714 payload fidelity for each frozen runtime-base source, and produced the active corrected snapshot.

```text
3.14.5  size 9761545   sha256 2edec6cfaf20a44b2458567856c1d505e6942d0e43da0e8ba2a36761ebc05be2
3.14.6  size 11788907  sha256 f0c449f7bc5b5bd740f4776f43bec4418645d5f33da220fa523409b6aa0af208
snapshot body sha256   dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233
canonical file sha256  419a9d4303fd6b3d7686400c7a275117ae6fe3421c93c30ff356529fc483b9e3
```

Ordinary exact-key mutation remains forbidden. This is an explicit documented correction, and the historical snapshot cannot be selected by acquisition.

## Gate 3 frozen result

Gate 3 freezes a 31/31 loopback-only implementation with deterministic synthetic fixtures, strict response length, no redirects, pre-socket non-loopback rejection, isolated candidates, exact size/hash/snapshot binding, exclusive content-addressed promotion, repeat cache no-op, and failure preservation.

## Gate 4 frozen result

Gate 4 accepts result archive `6cba95839a5dc05a7d4261467f1b7693e9d232fd44abe21ca4712e09b8e1977b`:

```text
archive size          42968242
safe members          62
self-index            46/46
raw target matrix     16/16 PASS
independent verifier  31/31 PASS
```

The evidence retains the exact two archive objects and proves complete loopback transfer, independent transport observations, isolated promotion, repeat cache hit, corrupt/truncated failure preservation, candidate cleanup, and repository/protected-state identity. uv, products, installation, public endpoints, and external networking were not used.

## Gate 5 selected scope

Gate 5 independently audits and freezes the corrected authority lineage, retained snapshot, Gate 4 target archive, repository recording, and remote clean state. It makes no new target, public-network, uv, execution, installation, recovery, concurrency, or durability claim.

## Protected frozen inputs

```text
Stage 3-E freeze commit/tree
  6419e107e4aa8400ebd3d98f3583999075b8b935
  e16edd99bfadf2135d0b632ddef4d292c0d80ea6

Stage 3-F Gate 1 commit/tree
  39e5c6d56a45495a4f23b73b6fa0704ba28fbc74
  7a0c476e60280c23dd8edd2627b25b42e3fa1429

Stage 3-F Gate 2 commit/tree
  82c21757e08b040fb7167c90e60fa48af323efb0
  ba85ac5bf09bdfc2aac7482077535ac2942cbc38

Stage 3-E Gate 5 authority blob
  651789e14f899b852f8fb8b4cbeceeaca318b19a
```

## Explicitly not proved

```text
public network availability or performance
DNS, TLS, certificate pinning, origin authenticity, or signatures
production redirects or mirrors
automatic acquisition through uv
installation or product execution
resumable or concurrent downloads
cache eviction or garbage collection
uv default managed root
system-wide links or shell integration
upgrade/downgrade or migration
crash/concurrency/power-loss durability
third-product compatibility
upstream uv Android support
```

## Authoritative files through Gate 4

```text
docs/PROJECT_CONTEXT_STAGE3F.md
docs/stages/STAGE3F_SCOPE.md
experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md
experiments/stage3f-publication-acquisition/gate1-authority.json
experiments/stage3f-publication-acquisition/GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT.md
experiments/stage3f-publication-acquisition/publication_snapshot.py
experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json
experiments/stage3f-publication-acquisition/gate2-publication-snapshot-authority.json
experiments/stage3f-publication-acquisition/GATE3_LOOPBACK_TRANSPORT_ACQUISITION_IMPLEMENTATION.md
experiments/stage3f-publication-acquisition/loopback_acquisition.py
experiments/stage3f-publication-acquisition/verify-gate3-loopback-acquisition.py
experiments/stage3f-publication-acquisition/gate3-loopback-acquisition-authority.json
docs/evidence/STAGE3F_GATE2_REPOSITORY_TRANSACTION_RESULT.md
docs/evidence/STAGE3F_GATE3_LOOPBACK_TRANSPORT_ACQUISITION_RESULT.md
experiments/stage3f-publication-acquisition/gate2-retention-correction-authority.json
experiments/stage3f-publication-acquisition/GATE4_TERMUX_RETAINED_ARTIFACT_ACQUISITION.md
experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json
experiments/stage3f-publication-acquisition/gate4-retained-artifact-acquisition-authority.json
docs/evidence/STAGE3F_GATE4_V1_DERIVATION_FAILURE.md
docs/evidence/STAGE3F_GATE4_RETAINED_ARTIFACT_ACQUISITION_RESULT.md
```
