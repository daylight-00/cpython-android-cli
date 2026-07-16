# Stage 3-F Gate 1: Publication and Acquisition Authority Design

> **Status:** DESIGN FROZEN
> **Class:** R — repository-only authority design
> **Selected next gate:** deterministic immutable-publication snapshot contract and fixture census

## Why Stage 3-F is separate

Stage 3-E accepted exact local catalog rows and a project-owned persistent managed root, but it kept acquisition offline through local artifact paths. Publication adds mutable naming, endpoint freshness, transport failure, cache state, and origin-trust questions that cannot be inferred from local-file installation success.

Gate 1 therefore opens a new stage without changing any accepted product or installation behavior.

## Frozen input

```text
Stage 3-E Gate 5 freeze commit
  6419e107e4aa8400ebd3d98f3583999075b8b935

Stage 3-E Gate 5 freeze tree
  e16edd99bfadf2135d0b632ddef4d292c0d80ea6

Stage 3-E Gate 5 authority blob
  651789e14f899b852f8fb8b4cbeceeaca318b19a

resolved main at onboarding
  b5a2ca39d1250122312355dd3dbc6165b9409786

exact managed keys
  cpython-3.14.5-linux-aarch64-none
  cpython-3.14.6-linux-aarch64-none
```

The Stage 3-E exact-key and project-owned-root contracts remain unchanged and independent.

## Authority separation

### Product authority

One immutable product is identified by exact bytes, exact size, SHA-256, platform identity, and frozen provenance. Product identity does not come from a URL, filename, HTTP header, server, or cache location.

### Catalog-row authority

One exact catalog key binds to one immutable product identity. A key cannot be silently redefined. A row may contain one or more locators, but all locators must resolve to the same expected bytes.

### Publication-snapshot authority

A publication snapshot is a canonical immutable ordered representation of a complete row set. Its digest identifies metadata bytes, not artifact bytes. A new snapshot may add rows or change locator policy only under an explicit later contract; it may not redefine an existing exact key.

### Endpoint authority

An endpoint is a discovery or transport locator. A mutable endpoint may identify the current immutable snapshot. The endpoint response is untrusted until canonical schema and digest validation succeeds.

### Transport authority

Transport records received bytes, length, status, redirects, timing, and failures. Transport success alone does not establish artifact identity or origin authenticity.

### Acquisition authority

An acquisition writes only to an untrusted candidate. Exact expected size and SHA-256 are checked before promotion. A failed or incomplete candidate is preserved or deleted according to later policy but cannot replace verified state.

### Cache authority

A verified cache object is content-addressed by artifact SHA-256. Locator-keyed or filename-keyed cache entries are not authoritative. Cache freshness and endpoint freshness are independent from product identity.

### Installation authority

Installation remains the frozen Stage 3-E explicit project-owned persistent root. Stage 3-F acquisition may eventually supply verified bytes to that boundary, but Gate 1 does not invoke or change installation.

## Trust distinctions

```text
SHA-256 equality
  proves byte identity against an already trusted expected digest

publication snapshot validation
  proves metadata consistency against an expected snapshot contract

TLS or endpoint reachability
  does not by itself prove product identity

origin authenticity or signatures
  separate, not accepted by Gate 1

availability and freshness
  operational properties, not identity
```

## Fail-closed invariants

```text
existing exact key cannot map to different bytes
locator alone cannot define product identity
unverified candidate cannot enter verified cache
failed acquisition cannot mutate installed roots
stale or malformed snapshot cannot replace accepted snapshot state
partial response cannot be interpreted as complete artifact
metadata digest and artifact digest remain distinct
```

## Selected Gate 2

Gate 2 implements a deterministic repository-local publication-snapshot schema and verifier. It must:

```text
resolve exact frozen artifact identities from tracked authorities
emit canonical JSON for the two exact rows
derive one publication-snapshot SHA-256
reject duplicate or redefined exact keys
reject missing size or SHA-256
reject a locator used as identity
model candidate size/hash verification before promotion
exercise success, expected-negative, and incomplete fixtures
prove deterministic output across repeated runs
```

Gate 2 must not open sockets, invoke uv, execute CPython products, touch the canonical products, use the real uv managed directory, or modify the Stage 3-E persistent root.

## Gate sequence

```text
Gate 1  FROZEN_AUTHORITY_DESIGN
Gate 2  ACTIVE_NEXT_IMMUTABLE_PUBLICATION_SNAPSHOT_CONTRACT
Gate 3  PENDING_LOOPBACK_TRANSPORT_ACQUISITION_IMPLEMENTATION
Gate 4  PENDING_TERMUX_NETWORK_ACQUISITION_VALIDATION
Gate 5  PENDING_INDEPENDENT_PUBLICATION_ACQUISITION_FREEZE
```

## Not proved

Gate 1 proves no network behavior, endpoint availability, TLS/origin trust, signature model, redirect/mirror policy, uv automatic download behavior, target compatibility, cache durability, installation behavior, global exposure, upgrades, recovery, concurrency, third-product support, or upstream uv Android support.
