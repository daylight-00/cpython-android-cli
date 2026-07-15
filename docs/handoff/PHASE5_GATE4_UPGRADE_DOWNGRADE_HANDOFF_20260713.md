# Phase 5 Gate 4 Upgrade and Downgrade Handoff — initiated 2026-07-13

> **Status:** FROZEN — Gate 4E independent transition freeze complete
> **Frozen inputs:** CPython 3.14.6 and CPython 3.14.5 complete three-artifact authorities
> **Target:** Termux on Android arm64

## Gate question

> Can one complete frozen three-artifact product transition to and from the other while preserving dependency, ownership, residual, collision, transaction, recovery, and runtime-behavior boundaries?

## Frozen products

```text
first product
  CPython 3.14.6 / android24 / aarch64
  source commit c63aec69bd59c55314c06c23f4c22c03de76fe45
  product lock  83f6b1fd3b610c22606f8dd4108a86cf2454e5997d0d0ada4124a209bfb091b7

second product
  CPython 3.14.5 / android24 / aarch64
  source commit 5607950ef232dad16d75c0cf53101d9649d89115
  product lock  e8c189d4a7386f1c522cc1479515b266fff60fdffedb3b7e842d9730ec21faeb
```

Both products independently passed standalone Termux lifecycle validation. The second-product authority was frozen through Gate 4A A6; it is not a relabeled first-product copy or the official Android package used directly.

## Current gate map

```text
Gate 4A  second-product authority                 FROZEN PASS
Gate 4B  transition contract design               DESIGN FROZEN — 66 scenarios
Gate 4C  transition coordinator implementation    IMPLEMENTED — 69/69
Gate 4D  bidirectional Termux target validation   ACCEPTED — 66/66
Gate 4E  independent transition freeze            FROZEN PASS
```

## Frozen transition contract

The 2,958-path union contains:

```text
shared paths             2944
byte-exact shared         216
replacement required     2728
3.14.6-only                 12
3.14.5-only                  2
cross-artifact transfers     0
```

Gate 4B freezes:

```text
dedicated whole-product transition
same-product-only ordinary artifact install
exact source registry and payload preflight
preserve installed runtime/addon topology
preserve non-colliding unowned descendants
reject unowned target-owned collisions
noop / replace / remove / create plan
one schema-2 PREPARED/APPLYING/COMMITTED journal
schema-1 target registry replacement
frozen lock, durability, and recovery semantics
```

## Implemented coordinator

Gate 4C adds a dedicated coordinator and exact two-product authority specification while leaving the frozen Phase 4 recovery engine source blobs unchanged.

```text
repository verifier       69/69 PASS
registry schema            1
frozen engine changes      none
claim                      repository implementation only
```

The coordinator validates exact product locks, manifests, archives, artifact IDs, owned-path counts, sizes, and SHA-256 identities. It rejects modified source-owned content, mixed or unknown product tuples, topology expansion/contraction, authority corruption, transaction residue, and target collisions before mutation.

Target archives are staged only after rejecting unsafe or duplicate member names, hardlinks and special files, missing members, member-type mismatches, symlink-target mismatches, and staged-payload identity mismatches.

## Frozen Gate 4D and Gate 4E authority

Gate 4D preserves two target archives. The first complete run is an immutable FAIL record with 55 unaffected PASS scenarios and 11 classified harness false negatives. The second archive independently verifies the first archive, reruns H01–H08 with corrected probes, replays C11–C12 from raw state evidence, derives A04, and produces a final 66/66 adjudication.

```text
v1 archive sha256  ef24baca1f01d3e106825fb99e537d68ba0beffa9cd4e92577e43bd35421e77c
v1 self-index      1223/1223 exact
v2 archive sha256  98ab810732dd2eb35bff9180dcb8fa1ec872eb09103d58670edb481cc9e3e5b2
v2 self-index      529/529 exact
final scenarios    66/66 PASS
```

Accepted scope includes both directions, all four frozen topologies, exact-source preflight, collision and lock rejection, PREPARED/APPLYING rollback, COMMITTED finalization, second-recovery idempotence, exact target registry/payload, CLI, extensions, HTTPS/base runtime, timezone, venv, uv, and relocation. Third-product compatibility, registry-schema migration, arbitrary mixed-product repair, and consumer integration remain unaccepted.

## Operating contract

Repository changes are prepared as a Drive package. The user runs one rclone bootstrap command. The runner validates the local branch/HEAD/tree/clean state, applies the exact patch, runs all repository gates, commits with the configured local Git identity using `git commit -s`, pushes with local Git, uploads one `.tar.zst` result, and verifies remote readback.

GitHub connector/API operations are not part of this workflow.
