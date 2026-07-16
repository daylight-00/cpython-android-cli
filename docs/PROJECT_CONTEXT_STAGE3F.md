# Project Context: Stage 3-F Publication and Acquisition Boundaries

> **Status:** Stage 3-F frozen through corrected Gate 4 retained-artifact acquisition
> **Active boundary:** Gate 5 independent publication/acquisition freeze
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
Gate 4  Termux target network-acquisition validation     FROZEN — retained actual bytes, 16/16 + 31/31
Gate 5  independent publication/acquisition freeze       ACTIVE NEXT
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

## Gate 2 historical snapshot and retention correction

Gate 2 remains frozen as a deterministic canonicalization and candidate-observation contract with 18/18 local verification. Its original concrete snapshot recorded transient archive identities but did not retain those exact bytes. Gate 4 v1 therefore failed closed at derivation; the historical snapshot is preserved but is no longer selectable for acquisition.

Gate 4A establishes the active retained snapshot from exact bytes preserved in the accepted target result:

```text
cpython-3.14.5-linux-aarch64-none
  size    9761545
  sha256  2edec6cfaf20a44b2458567856c1d505e6942d0e43da0e8ba2a36761ebc05be2

cpython-3.14.6-linux-aarch64-none
  size    11788907
  sha256  f0c449f7bc5b5bd740f4776f43bec4418645d5f33da220fa523409b6aa0af208

retained snapshot body SHA-256  dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233
retained snapshot file SHA-256  419a9d4303fd6b3d7686400c7a275117ae6fe3421c93c30ff356529fc483b9e3
retained snapshot file size    2997
```

This is an explicit authority repair after preserved failure evidence, not permission for mutable endpoint-driven exact-key redefinition.

## Gate 3 frozen implementation

Gate 3 freezes the 31/31 loopback publisher and fail-closed content-addressed acquisition engine using synthetic fixtures. Redirects and non-loopback hosts are rejected, candidate residue is removed, verified objects are not overwritten, and repeat acquisition is a no-request cache hit.

## Gate 4 frozen target result

Gate 4A executes the same policy on Termux with the retained actual archive bytes. The result archive `6cba95839a5dc05a7d4261467f1b7693e9d232fd44abe21ca4712e09b8e1977b` is safe with 62 members and 46/46 exact self-index entries. Its raw target matrix passes 16/16 and the independent verifier passes 31/31.

Both payloads pass 714/714 strict source fidelity. Complete transfers, independent size/hash observations, content-addressed promotion, repeat cache hits, truncated/corrupt rejection, peer preservation, candidate cleanup, and protected-state identity are accepted. The exact archive bytes remain retained inside the result evidence.

No uv command or product was executed, no archive was installed, no public or external endpoint was used, and the Stage 3-E managed root remained unchanged.

## Selected Gate 5

Gate 5 independently freezes the corrected authority lineage and accepted Gate 4 evidence. It is repository/audit work only and must stop before public publication, uv acquisition, execution, installation, origin authentication, recovery, concurrency, or durability.

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
  -> experiments/stage3f-publication-acquisition/gate2-retention-correction-authority.json
  -> experiments/stage3f-publication-acquisition/GATE4_TERMUX_RETAINED_ARTIFACT_ACQUISITION.md
  -> experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json
  -> experiments/stage3f-publication-acquisition/gate4-retained-artifact-acquisition-authority.json
  -> docs/evidence/STAGE3F_GATE4_V1_DERIVATION_FAILURE.md
  -> docs/evidence/STAGE3F_GATE4_RETAINED_ARTIFACT_ACQUISITION_RESULT.md
  -> docs/PROJECT_CONTEXT_STAGE3E.md
  -> docs/evidence/STAGE3E_FINAL_SUMMARY.md
  -> docs/session-operations/README.md
```

## Immediate next boundary

Run the independent Gate 5 Stage 3-F freeze over the corrected retention authority, Gate 4 target archive, repository transaction, and clean remote state. Stop before public publication, uv acquisition, product execution, installation, or managed-root mutation.
