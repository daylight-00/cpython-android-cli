# Phase 5 Gate 4 Upgrade and Downgrade Handoff — initiated 2026-07-13

> **Status:** ACTIVE — Gate 4C implemented; Gate 4D bidirectional Termux validation ready
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
Gate 4D  bidirectional Termux target validation   READY — not started
Gate 4E  independent transition freeze            pending
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

## Immediate task: Gate 4D

Prepare one Termux wrapper that consumes both exact frozen product authorities and executes the 66-scenario matrix or an explicitly justified exact implementation mapping of it.

Required target evidence includes:

```text
both directions across all four artifact topologies
source and target product-lock/manifest/archive verification
before/after registry and complete owned-payload inventory
unowned descendant and collision evidence
PREPARED, late APPLYING, and COMMITTED recovery
first and second recovery results
lock exclusion
CLI and subprocess identity
native closure and extension imports
HTTPS trust and timezone boundaries
venv and uv explicit-interpreter workflow
whole-prefix relocation
complete raw stdout/stderr and real return codes
safe single-root .tar.zst and exact self-excluding result index
explicit claim boundary
```

No real upgrade, downgrade, post-transition runtime behavior, target recovery behavior, mixed-version compatibility, migration, or final transition authority is frozen yet.

## Authority records

```text
experiments/stage3c-gate4-second-product-authority/gate4a-a6-second-product-freeze-authority.json
experiments/stage3c-gate4-transition/GATE4B_TRANSITION_CONTRACT_DESIGN.md
experiments/stage3c-gate4-transition/gate4b-transition-design-authority.json
experiments/stage3c-gate4-transition/GATE4C_TRANSITION_COORDINATOR_IMPLEMENTATION.md
experiments/stage3c-gate4-transition/gate4c-transition-implementation-authority.json
docs/evidence/STAGE3C_PHASE5_GATE4C_TRANSITION_COORDINATOR_IMPLEMENTATION_RESULT.md
```

## Operating contract

Repository changes are prepared as a Drive package. The user runs one rclone bootstrap command. The runner validates the local branch/HEAD/tree/clean state, applies the exact patch, runs all repository gates, commits with the configured local Git identity using `git commit -s`, pushes with local Git, uploads one `.tar.zst` result, and verifies remote readback.

GitHub connector/API operations are not part of this workflow.
