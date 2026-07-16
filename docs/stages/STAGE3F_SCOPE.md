# Stage 3-F Scope: Publication and Acquisition Boundaries

> **Status:** ACTIVE — Gate 1 authority design frozen; Gate 2 active next
> **Input:** frozen Stage 3-E Gate 5 exact-key, local, project-owned managed-Python distribution
> **Primary target:** Termux on Android arm64, beginning only after local contract gates
> **Canonical branch:** `agent/stage3f-publication-acquisition`

## Stage question

How can the two frozen exact HW-T Android CPython products be published and acquired without conflating immutable product identity, catalog metadata, mutable endpoint state, transport bytes, cache state, and installation authority?

## Gate sequence

```text
Gate 1  publication/acquisition authority design        FROZEN
Gate 2  immutable publication snapshot contract         ACTIVE NEXT
Gate 3  loopback transport and acquisition implementation pending
Gate 4  Termux target network-acquisition validation     pending
Gate 5  independent publication/acquisition freeze       pending
```

## Gate 1 decision

The stage separates eight authorities:

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

SHA-256 and exact byte size bind an artifact identity. A URL, redirect, server, filename, cache path, or catalog ordering does not. A publication snapshot is canonical immutable metadata with its own digest. A mutable endpoint may only select among immutable snapshots and is not accepted as a product-identity authority.

An acquisition must fail closed:

```text
receive into untrusted candidate
  -> verify exact expected size
  -> verify exact expected SHA-256
  -> verify catalog/snapshot binding
  -> promote to verified content-addressed cache
  -> only then permit a later installation operation
```

No failed, partial, stale, or mismatched candidate may replace a verified cache object or mutate the Stage 3-E managed root.

## Gate 2 selected scope

Gate 2 creates a repository-local canonical snapshot schema and deterministic verifier for the exact 3.14.5 and 3.14.6 keys. Required fixture classes:

```text
success
  complete canonical two-row snapshot with exact frozen identities

expected negative
  duplicate/redefined key, digest mismatch, size mismatch, or locator-only identity

incomplete
  missing artifact identity, missing row, or missing snapshot digest input
```

Gate 2 is class L because it proves local canonicalization and verification behavior. It uses no network endpoint, uv command, Android target, product execution, or managed-root mutation.

## Protected frozen inputs

```text
Stage 3-E freeze commit/tree
  6419e107e4aa8400ebd3d98f3583999075b8b935
  e16edd99bfadf2135d0b632ddef4d292c0d80ea6

Stage 3-E Gate 5 authority blob
  651789e14f899b852f8fb8b4cbeceeaca318b19a

exact keys
  cpython-3.14.5-linux-aarch64-none
  cpython-3.14.6-linux-aarch64-none
```

The exact artifact identities used by Gate 2 must be traced to existing frozen product authorities. Gate 2 may not synthesize or replace product bytes.

## Explicitly not proved by Stage 3-F Gate 1

```text
network availability or performance
DNS, TLS, certificate pinning, or origin authenticity
signature or key-distribution policy
redirect and mirror policy
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

## Authoritative Gate 1 files

```text
docs/PROJECT_CONTEXT_STAGE3F.md
docs/stages/STAGE3F_SCOPE.md
experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md
experiments/stage3f-publication-acquisition/gate1-authority.json
docs/evidence/STAGE3F_GATE1_AUTHORITY_DESIGN_RESULT.md
```
