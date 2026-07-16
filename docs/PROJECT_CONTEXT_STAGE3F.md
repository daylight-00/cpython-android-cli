# Project Context: Stage 3-F Publication and Acquisition Boundaries

> **Status:** Stage 3-F frozen through Gate 2 immutable publication snapshot contract
> **Active boundary:** Gate 3 loopback transport and acquisition implementation
> **Canonical branch:** `agent/stage3f-publication-acquisition`
> **Stage input:** `6419e107e4aa8400ebd3d98f3583999075b8b935`, tree `e16edd99bfadf2135d0b632ddef4d292c0d80ea6`
> **Gate 2 input:** `39e5c6d56a45495a4f23b73b6fa0704ba28fbc74`, tree `7a0c476e60280c23dd8edd2627b25b42e3fa1429`
> **Resolved main at stage start:** `b5a2ca39d1250122312355dd3dbc6165b9409786`

## Frozen foundation

Stage 2, Stage 3-A, Stage 3-B, Stage 3-C through Gate 4E, Stage 3-D through Gate 6, and Stage 3-E through Gate 5 remain frozen. Stage 3-F does not mutate the accepted CPython products, the Stage 3-C ownership and transition authorities, the Stage 3-D exact-path system-Python contract, or the Stage 3-E project-owned persistent-root contract.

Stage 3-E proved a local, offline, exact-key managed-Python surface for CPython 3.14.5 and 3.14.6. Stage 3-F separates publication metadata, endpoint state, transport observations, candidate verification, verified caches, and installation authority.

## Gate state

```text
Gate 1  publication/acquisition authority design        FROZEN
Gate 2  immutable publication snapshot contract         FROZEN — 18/18 local verification
Gate 3  loopback transport and acquisition implementation ACTIVE NEXT
Gate 4  Termux target network-acquisition validation     pending
Gate 5  independent publication/acquisition freeze       pending
```

## Gate 1 frozen authority model

```text
product identity       exact bytes, size, SHA-256, provenance, platform
catalog row            exact key bound to one immutable product
publication snapshot   canonical immutable complete row set with its own digest
endpoint locator       mutable pointer, never product identity
transport observation  received bytes and transport metadata
acquisition candidate  untrusted until exact checks pass
verified cache         content-addressed by artifact SHA-256
installation root      unchanged Stage 3-E project-owned root
```

## Gate 2 frozen snapshot

The canonical snapshot binds the two accepted Stage 3-E runtime-only products:

```text
cpython-3.14.5-linux-aarch64-none
  size    9761522
  sha256  18832bb7982a679fcee067e2d33e106dac84307687b63803be105714596d422f

cpython-3.14.6-linux-aarch64-none
  size    11789074
  sha256  9575edef24d84b2fce32c55093ab01cb8b2b1a41b521d2011653fae87b5bcb64
```

Snapshot identities:

```text
snapshot body SHA-256  a00027a81956ef175bf537eff3a92286e26c1120fa536d0a8ad6a096a1760f8c
canonical file SHA-256 c942b9863e33c2edf7d628780bfeef0957b427fb12259ba49e708cb4858c52bc
canonical file size   2328
rows                  2
verification          18/18 PASS
```

Canonical JSON uses sorted keys, no insignificant whitespace, and one trailing LF. The body digest identifies metadata bytes and remains distinct from artifact digests and the complete envelope file digest.

The verifier rejects duplicate or redefined exact keys, digest mismatch, missing identity, locator-only identity, missing rows, and mismatched candidate size, hash, or snapshot binding. Repeated generation is byte-identical.

Gate 2 models candidate observations only. It writes no cache object and permits no installation.

## Selected Gate 3

Gate 3 may implement one deterministic loopback publisher and acquisition workflow against the frozen snapshot. It should separate endpoint response capture, snapshot validation, complete versus truncated artifact transfer, independent size/hash observation, snapshot binding, and isolated verified-cache promotion.

Gate 3 remains bounded to loopback and isolated paths. It must not use a public endpoint, invoke uv automatic acquisition, execute target products, or mutate the Stage 3-E managed root. Termux target network-acquisition validation remains Gate 4.

## Deferred boundary

Public hosting, DNS/TLS/origin authenticity, signatures, redirect and mirror policy, automatic uv acquisition, resumable transfer, cache eviction, default managed-root adoption, global exposure, upgrades, crash recovery, concurrency, durability, third products, and upstream uv Android support remain unaccepted.

## Current reading path

```text
README.md
  -> docs/PROJECT_CONTEXT_STAGE3F.md
  -> docs/stages/STAGE3F_SCOPE.md
  -> experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md
  -> experiments/stage3f-publication-acquisition/gate1-authority.json
  -> docs/evidence/STAGE3F_GATE1_REPOSITORY_TRANSACTION_RESULT.md
  -> experiments/stage3f-publication-acquisition/GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT.md
  -> experiments/stage3f-publication-acquisition/gate2-publication-snapshot.json
  -> experiments/stage3f-publication-acquisition/gate2-publication-snapshot-authority.json
  -> docs/evidence/STAGE3F_GATE2_IMMUTABLE_PUBLICATION_SNAPSHOT_RESULT.md
  -> docs/PROJECT_CONTEXT_STAGE3E.md
  -> docs/evidence/STAGE3E_FINAL_SUMMARY.md
  -> docs/session-operations/README.md
```

## Immediate next boundary

Design and implement the bounded Gate 3 loopback transport/acquisition workflow. Stop before public networking, uv integration, target product execution, or managed-root mutation.
