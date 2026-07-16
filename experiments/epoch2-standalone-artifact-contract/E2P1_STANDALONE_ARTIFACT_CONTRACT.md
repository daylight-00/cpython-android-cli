# E2-P1 Standalone Artifact Contract Implementation

> **Status:** FROZEN — repository verification complete

## Inputs

- Epoch 1 final predecessor commit `e1de252740a96c40f3d587269136235a2c84ea16`, tree `66c976f3fc182496d2843771b46faaf98fc267da`.
- Epoch 2 Phase 0 commit `a34e5fdc6224e66aa7ed335e921780fbadd728dc`, tree `7543e0a8ff86a3bee1fcda33fc86b11692c90b92`.
- Stage 3-C manifest, archive, ownership, and transaction contracts.
- Stage 3-D/E managed-Python consumer and lifecycle evidence.
- Stage 3-F release-snapshot, acquisition, and content-addressed cache authority.

## Machine contract

```text
schemas/                         JSON Schema draft 2020-12 documents
fixtures/valid/                  deterministic unselectable release fixture
verify-e2p1-...py                independent semantic and archive verifier
test-verify-e2p1-...py           mutation-based expected-negative regression suite
run-e2p1-...sh                   bounded repository verification entry point
e2p1-authority.json              exact contract-file identities and frozen decision
```

The fixture contains a deterministic `pax-tar+zstd` archive with a `python/` root and four placeholder regular files. It is intentionally not a Python runtime. Its qualification sidecar and release index both prevent selection.

## Verification classes

The verifier checks:

- schema identity and strict top-level versioning;
- canonical JSON bytes;
- target, ABI, API, Bionic, wheel-tag, flavor, profile, and consumer-mapping separation;
- archive hash, root, member order, normalized headers, safe types, modes, and regular-file bytes;
- payload class and ownership rules;
- provenance, qualification, license, release-index, and checksum consistency;
- exact authority file identities;
- absence of Termux application-private paths from binary identity.

The negative suite mutates target identity, wheel tags, Termux binding, payload classes, manifest safety and ordering, qualification, release digests, sidecar hashes, checksums, archive bytes, and license identity. Every mutation must fail closed at its named boundary.

## Claim boundary

This implementation freezes contract design and repository-local verification only. E2-P2 must build a real product through stable façade commands. E2-P3 must qualify an extracted real artifact on emulator and Termux where target evidence is required.
