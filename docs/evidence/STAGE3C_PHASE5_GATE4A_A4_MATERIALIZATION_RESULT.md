# Stage 3-C Phase 5 Gate 4A A4 Materialization Result

> **Status:** A4 FROZEN PASS
> **Product:** CPython 3.14.5 / android24 / aarch64
> **Next boundary:** A5 standalone Termux validation

## Decision

The A4 three-artifact candidate is accepted as exact materialization authority.

The original result archive is immutable:

```text
archive
  20260714-gate4a-a4-three-artifact-materialization-results-20260714T080755Z.tar.zst

size
  17,542,978 bytes

sha256
  7a2b15403f216fcd391e6ee3ef46e678a5ae9f1b010180c26d7785042b86e571

materializer
  25/25 PASS

archived verifier
  26/27 FAIL
  failed check: archive_payload_matches_manifests
```

The archived failure is retained. It was adjudicated rather than erased or replaced.

## Independent adjudication

A read-only static adjudicator recomputed the exact outer result index, artifact archive safety, every manifest payload path, type, mode, size, digest and symlink target, embedded authority files, reconstruction, repository non-mutation, original NDK non-mutation, and the one-byte linker overlay boundary.

```text
adjudication result
  20260714-gate4a-a4-static-adjudication-v1-results-20260714T103910Z.tar.zst

size
  2,180 bytes

sha256
  c4dcef52b86d181badd0775b11c2bc2d3f7b29b142c81e33811a02fc927632ce

checks
  26/26 PASS

result index
  12/12 exact
```

The exact original verifier also reproduced as 27/27 PASS against the same archived artifact bytes in a reconstructed environment. The evidence therefore classifies the original single failure as an isolated verifier false negative, not a payload or manifest defect.

## Frozen artifact identities

```text
runtime-base
  archive sha256   d01e142dae90cdca8681c6674999acc197d05bb1bec9a75468fe9b8cf4fff52d
  archive size     9,803,730
  manifest sha256  2e5efbc9fe765c1b7a4d1bc7375a74d27bcf6d1a56557e3be11cffb9f451e815
  owned paths      714

development-addon
  archive sha256   623d776bd9a987aac0417c360746b4917d666a5829a522ef43574b66493387e0
  archive size     870,030
  manifest sha256  30a840feb2922684604d87b206617243a4ddce2fdff10053c720a52bae5fc671
  owned paths      447
  structural refs  2

test-addon
  archive sha256   7d397ab12cf1d70b2922754b8121936ae56270c45c7929f69656984cd6a0eb1d
  archive size     6,264,999
  manifest sha256  1d6f2c2fd48fa258f9fd982c84732118a012b977a50399395913d13e72c63877
  owned paths      1,785
  structural refs  2
```

The 2,946 owned paths are disjoint. Reconstructing the three artifacts reproduces the selected complete replay prefix under the accepted exclusion policy.

## Claim boundary

A4 accepts artifact bytes, manifests, product lock, manifest index, registry template, ownership partition and reconstruction identity.

A4 does not accept standalone target behavior, second-product freeze, upgrade, downgrade, mixed-version compatibility, migration, or transition recovery. A5 must validate the artifacts independently on Termux. Only A6 may freeze the complete second-product authority.
