# Project Context: Stage 3-F Publication and Acquisition Boundaries

> **Status:** Stage 3-F Gate 1 publication/acquisition authority design frozen
> **Active boundary:** Gate 2 deterministic immutable-publication snapshot contract and fixture census
> **Canonical branch:** `agent/stage3f-publication-acquisition`
> **Stage input:** `6419e107e4aa8400ebd3d98f3583999075b8b935`, tree `e16edd99bfadf2135d0b632ddef4d292c0d80ea6`
> **Resolved main at stage start:** `b5a2ca39d1250122312355dd3dbc6165b9409786`

## Frozen foundation

Stage 2, Stage 3-A, Stage 3-B, Stage 3-C through Gate 4E, Stage 3-D through Gate 6, and Stage 3-E through Gate 5 remain frozen. Stage 3-F does not mutate the accepted CPython products, the Stage 3-C ownership and transition authorities, the Stage 3-D exact-path system-Python contract, or the Stage 3-E project-owned persistent-root contract.

Stage 3-E proved a local, offline, exact-key managed-Python surface for CPython 3.14.5 and 3.14.6. It deliberately did not prove how catalog metadata or artifact bytes are published, discovered, transported, cached, authenticated, or acquired from a network endpoint.

## Stage question

How should immutable HW-T product identities, catalog snapshots, endpoint locators, transport bytes, verified caches, and installation roots be separated so that publication and acquisition can be tested without allowing a mutable endpoint or partial download to redefine an accepted product?

## Gate state

```text
Gate 1  publication/acquisition authority design        FROZEN
Gate 2  immutable publication snapshot contract         ACTIVE NEXT — repository-local deterministic fixtures
Gate 3  loopback transport and acquisition implementation pending
Gate 4  Termux target network-acquisition validation     pending
Gate 5  independent publication/acquisition freeze       pending
```

## Gate 1 frozen authority model

```text
product authority
  frozen artifact bytes, exact size, and SHA-256

catalog-row authority
  exact immutable key bound to one product identity

publication-snapshot authority
  canonical immutable set of catalog rows with its own digest

endpoint authority
  a locator or mutable pointer; never product identity by itself

transport authority
  observed response bytes and transport metadata

acquisition authority
  candidate download verified by exact size and SHA-256 before promotion

cache authority
  verified content-addressed objects; unverified partials are non-authoritative

installation authority
  unchanged Stage 3-E explicit project-owned managed root
```

A mutable endpoint may point to a newer immutable publication snapshot, but a client must validate the snapshot and artifact identities before changing any trusted cache or installation state. Endpoint freshness, artifact identity, origin trust, and availability are separate claims.

## Selected Gate 2

Gate 2 is repository-local and deterministic. It will define one canonical publication-snapshot schema and a verifier with success, expected-negative, and incomplete fixtures for the two frozen exact keys:

```text
cpython-3.14.5-linux-aarch64-none
cpython-3.14.6-linux-aarch64-none
```

Gate 2 will bind exact frozen artifact identities, canonicalize the snapshot bytes, derive the snapshot SHA-256, enforce unique immutable keys, and model candidate acquisition verification. It will not open a socket, invoke uv, execute a target product, or modify a managed root.

## Non-reopening and deferred boundary

Gate 1 does not accept a public server, DNS, TLS origin authenticity, signatures, redirects, mirrors, automatic downloads, mutable catalog semantics, cache eviction, resumable transfer, uv default-root adoption, global executable exposure, upgrades, crash recovery, concurrent writers, power-loss durability, third products, or upstream uv Android support.

## Current reading path

```text
README.md
  -> docs/PROJECT_CONTEXT_STAGE3F.md
  -> docs/stages/STAGE3F_SCOPE.md
  -> experiments/stage3f-publication-acquisition/GATE1_AUTHORITY_DESIGN.md
  -> experiments/stage3f-publication-acquisition/gate1-authority.json
  -> docs/evidence/STAGE3F_GATE1_AUTHORITY_DESIGN_RESULT.md
  -> docs/PROJECT_CONTEXT_STAGE3E.md
  -> docs/evidence/STAGE3E_FINAL_SUMMARY.md
  -> docs/session-operations/README.md
```

## Immediate next boundary

Implement and verify the deterministic Gate 2 publication-snapshot contract and fixture census in the repository only. Stop before loopback networking, Termux execution, uv invocation, or managed-root mutation.
