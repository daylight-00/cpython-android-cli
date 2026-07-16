# Stage 3-F Scope: Publication and Acquisition Boundaries

> **Status:** ACTIVE — Gates 1 and 2 frozen; Gate 3 active next
> **Input:** frozen Stage 3-E Gate 5 exact-key, local, project-owned managed-Python distribution
> **Primary target:** Termux on Android arm64, beginning at Gate 4 after local implementation gates
> **Canonical branch:** `agent/stage3f-publication-acquisition`

## Stage question

How can the two frozen exact HW-T Android CPython products be published and acquired without conflating immutable product identity, catalog metadata, mutable endpoint state, transport bytes, cache state, and installation authority?

## Gate sequence

```text
Gate 1  publication/acquisition authority design        FROZEN
Gate 2  immutable publication snapshot contract         FROZEN — 18/18
Gate 3  loopback transport and acquisition implementation ACTIVE NEXT
Gate 4  Termux target network-acquisition validation     pending
Gate 5  independent publication/acquisition freeze       pending
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

## Gate 2 frozen result

Gate 2 defines a canonical two-row snapshot and deterministic verifier. Exact artifact identities are traced to the accepted Stage 3-E dual-version result archive `3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2`.

```text
3.14.5  size 9761522   sha256 18832bb7982a679fcee067e2d33e106dac84307687b63803be105714596d422f
3.14.6  size 11789074  sha256 9575edef24d84b2fce32c55093ab01cb8b2b1a41b521d2011653fae87b5bcb64
snapshot body sha256   a00027a81956ef175bf537eff3a92286e26c1120fa536d0a8ad6a096a1760f8c
canonical file sha256  c942b9863e33c2edf7d628780bfeef0957b427fb12259ba49e708cb4858c52bc
verification           18/18 PASS
```

Required success, expected-negative, and incomplete fixture classes all pass. The model checks candidate observations but performs no transport, cache write, or installation.

## Gate 3 selected scope

Gate 3 implements a loopback-only publisher and acquisition engine around the frozen snapshot. The minimum matrix should cover:

```text
valid snapshot and complete artifact
stale or malformed snapshot
unknown snapshot digest
complete response with wrong artifact bytes
truncated response
wrong content length
redirect or public-origin attempt rejected by policy
existing verified cache preserved after failure
isolated candidate promoted only after independent size/hash verification
repeat acquisition is exact cache no-op
```

Gate 3 may use repository-local synthetic fixture artifacts. It does not need or permit the real CPython archives, uv, CPython execution, or Stage 3-E installation.

## Protected frozen inputs

```text
Stage 3-E freeze commit/tree
  6419e107e4aa8400ebd3d98f3583999075b8b935
  e16edd99bfadf2135d0b632ddef4d292c0d80ea6

Stage 3-F Gate 1 commit/tree
  39e5c6d56a45495a4f23b73b6fa0704ba28fbc74
  7a0c476e60280c23dd8edd2627b25b42e3fa1429

Stage 3-E Gate 5 authority blob
  651789e14f899b852f8fb8b4cbeceeaca318b19a
```

## Explicitly not proved

```text
public network availability or performance
DNS, TLS, certificate pinning, origin authenticity, or signatures
production redirects or mirrors
automatic acquisition through uv
resumable or concurrent downloads
cache eviction or garbage collection
uv default managed root
system-wide links or shell integration
upgrade/downgrade or migration
crash/concurrency/power-loss durability
third-product compatibility
upstream uv Android support
```

## Authoritative files through Gate 2

```text
docs/PROJECT_CONTEXT_STAGE3F.md
docs/stages/STAGE3F_SCOPE.md
experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md
experiments/stage3f-publication-acquisition/gate1-authority.json
experiments/stage3f-publication-acquisition/GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT.md
experiments/stage3f-publication-acquisition/publication_snapshot.py
experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json
experiments/stage3f-publication-acquisition/gate2-publication-snapshot-authority.json
experiments/stage3f-publication-acquisition/verify-gate2-publication-snapshot.py
docs/evidence/STAGE3F_GATE1_REPOSITORY_TRANSACTION_RESULT.md
docs/evidence/STAGE3F_GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_RESULT.md
```
