# Project Context: Stage 3-F Publication and Acquisition Boundaries

> **Status:** Stage 3-F frozen through Gate 3 loopback transport/acquisition implementation
> **Active boundary:** Gate 4 Termux target loopback network-acquisition validation
> **Canonical branch:** `agent/stage3f-publication-acquisition`
> **Stage input:** `6419e107e4aa8400ebd3d98f3583999075b8b935`, tree `e16edd99bfadf2135d0b632ddef4d292c0d80ea6`
> **Gate 2 input:** `39e5c6d56a45495a4f23b73b6fa0704ba28fbc74`, tree `7a0c476e60280c23dd8edd2627b25b42e3fa1429`
> **Gate 3 input:** `82c21757e08b040fb7167c90e60fa48af323efb0`, tree `ba85ac5bf09bdfc2aac7482077535ac2942cbc38`
> **Resolved main at stage start:** `b5a2ca39d1250122312355dd3dbc6165b9409786`

## Frozen foundation

Stage 2, Stage 3-A, Stage 3-B, Stage 3-C through Gate 4E, Stage 3-D through Gate 6, and Stage 3-E through Gate 5 remain frozen. Stage 3-F does not mutate accepted CPython products, Stage 3-C ownership and transition authorities, the Stage 3-D exact-path system-Python contract, or the Stage 3-E project-owned persistent-root contract.

Stage 3-E proved a local, offline, exact-key managed-Python surface for CPython 3.14.5 and 3.14.6. Stage 3-F separates publication metadata, endpoint state, transport observations, candidate verification, verified caches, and installation authority.

## Gate state

```text
Gate 1  publication/acquisition authority design        FROZEN
Gate 2  immutable publication snapshot contract         FROZEN — 18/18 local verification
Gate 3  loopback transport/acquisition implementation   FROZEN — 31/31 local verification
Gate 4  Termux target network-acquisition validation     ACTIVE NEXT — loopback-only actual bytes
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

```text
snapshot body SHA-256  a00027a81956ef175bf537eff3a92286e26c1120fa536d0a8ad6a096a1760f8c
canonical file SHA-256 c942b9863e33c2edf7d628780bfeef0957b427fb12259ba49e708cb4858c52bc
canonical file size    2328
rows                   2
verification           18/18 PASS
```

Canonical JSON uses sorted keys, no insignificant whitespace, and one trailing LF. The snapshot body digest, complete envelope digest, and artifact digests remain separate identities.

## Gate 3 frozen implementation

Gate 3 implements one bounded loopback publisher and acquisition engine with synthetic fixture bytes:

```text
publisher          http://127.0.0.1:<ephemeral-port>
redirects          rejected
external hosts     rejected before socket
response length    required and exact
candidate          isolated and untrusted
promotion          exact size, SHA-256, and snapshot binding
cache              sha256/<prefix>/<digest>, exclusive no-replacement
repeat acquisition exact cache no-op without another request
verification       31/31 PASS
```

Failed, truncated, oversized, wrong-hash, wrong-size, redirect, missing-route, and mismatched-snapshot cases fail closed. Candidate residue is removed, existing verified objects remain unchanged, and a mismatched object at the target content-addressed path is never replaced.

The synthetic fixture bytes are implementation evidence only and are not CPython product identities.

## Selected Gate 4

Gate 4 moves the same acquisition policy to the authoritative Termux host using the actual frozen CPython 3.14.5 and 3.14.6 archive bytes. Transport remains loopback-only and cache state remains isolated.

Gate 4 must prove:

```text
exact Gate 2 snapshot fetch and validation
actual archive transfer through 127.0.0.1
independent observed size and SHA-256
content-addressed promotion for both artifacts
repeat cache no-op
truncated and corrupt transfer failure preservation
repository and all protected state unchanged
complete result archive and independent audit
```

It must not invoke uv, execute an unverified product, install into the Stage 3-E managed root, expose global links, or use a public endpoint.

## Deferred boundary

Public hosting, DNS/TLS/origin authenticity, signatures, production redirect and mirror policy, automatic uv acquisition, resumable transfer, cache eviction, default managed-root adoption, global exposure, installation, upgrades, crash recovery, concurrency, durability, third products, and upstream uv Android support remain unaccepted.

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
  -> docs/evidence/STAGE3F_GATE2_REPOSITORY_TRANSACTION_RESULT.md
  -> experiments/stage3f-publication-acquisition/GATE3_LOOPBACK_TRANSPORT_ACQUISITION_IMPLEMENTATION.md
  -> experiments/stage3f-publication-acquisition/gate3-loopback-acquisition-authority.json
  -> docs/evidence/STAGE3F_GATE3_LOOPBACK_TRANSPORT_ACQUISITION_RESULT.md
  -> docs/PROJECT_CONTEXT_STAGE3E.md
  -> docs/evidence/STAGE3E_FINAL_SUMMARY.md
  -> docs/session-operations/README.md
```

## Immediate next boundary

Prepare and run the bounded Gate 4 Termux target loopback acquisition matrix with actual frozen archive bytes. Stop before uv invocation, product execution, installation, public networking, or managed-root mutation.
