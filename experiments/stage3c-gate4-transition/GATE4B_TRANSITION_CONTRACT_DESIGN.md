# Stage 3-C Phase 5 Gate 4B: Cross-Version Transition Contract Design

> **Status:** DESIGN FROZEN — implemented by Gate 4C and target-accepted through Gate 4E
> **Products:** CPython 3.14.5 ↔ CPython 3.14.6
> **Target:** Termux on Android arm64, API 24, NDK 27.3.13750724
> **Scenario matrix:** 66 bidirectional scenarios

## Design question

> Can the two independently frozen three-artifact products transition in either direction without reopening their artifact, ownership, registry, durability, or same-product lifecycle contracts?

Gate 4B is a design gate. It freezes the transition policy and evidence matrix. It does not execute an upgrade or downgrade.

## Frozen inputs

```text
first product
  CPython 3.14.6
  source c63aec69bd59c55314c06c23f4c22c03de76fe45
  product lock 83f6b1fd3b610c22606f8dd4108a86cf2454e5997d0d0ada4124a209bfb091b7
  owned paths 2956

second product
  CPython 3.14.5
  source 5607950ef232dad16d75c0cf53101d9649d89115
  product lock e8c189d4a7386f1c522cc1479515b266fff60fdffedb3b7e842d9730ec21faeb
  owned paths 2946
```

Both products keep the same target, Android API, NDK, artifact names, and ownership model. Their archive, manifest, product-lock, native-closure, runtime-behavior, and provenance identities remain distinct.

## Exact cross-product inventory

The frozen manifests produce this union:

```text
union owned paths       2958
shared paths            2944
byte-identical shared    216
replacement required    2728
3.14.6-only                12
3.14.5-only                 2
cross-artifact transfers    0
```

Per artifact:

```text
runtime-base
  714 ↔ 714
  shared 713 = 60 exact + 653 replacement
  one path unique to each product

development-addon
  454 ↔ 447
  shared 446 = 11 exact + 435 replacement
  3.14.6-only 8; 3.14.5-only 1

test-addon
  1788 ↔ 1785
  shared 1785 = 145 exact + 1640 replacement
  3.14.6-only 3; 3.14.5-only 0
```

The exact one-sided paths and classification digests are frozen in `gate4b-cross-version-inventory.json`.

## Why ordinary install is not a transition

The frozen same-product installer identifies ownership by the artifact name. Directly installing the other product would therefore misclassify cross-version paths as repairs.

Static inspection and the exact manifest delta show four unacceptable effects:

1. Source-only paths would disappear from the registry but remain on disk.
2. Replacing `runtime-base` would not reject addons belonging to the other product.
3. Separate artifact commits would not provide product-level rollback.
4. The registry does not carry an independent mutable product-lock field.

Therefore ordinary `install` remains a same-product lifecycle operation. Cross-product change requires a dedicated whole-product `transition` operation.

## Non-reopening architecture

Gate 4B does not modify the frozen Phase 4 engine files, artifact manifests, archive bytes, or registry schema.

The future transition coordinator may import the frozen common and durability helpers, but it must create one recovery-compatible transaction over the complete selected artifact topology.

```text
exclusive installation lock
        |
        v
exact source authority and payload preflight
        |
        v
single transition journal
  state PREPARED
  operation transition
  frozen mutation vocabulary
        |
        v
union path plan
  exact shared     -> noop
  changed shared   -> transactional replace
  source-only      -> transactional remove
  target-only      -> transactional create
        |
        v
atomic registry replacement with exact target artifact tuple
        |
        v
COMMITTED -> cleanup
```

The existing registry remains schema version 1. The active product is derived from the exact `runtime-base` artifact ID and the frozen authority mapping. The target product lock is verified as an input; no separate mutable product-lock file is installed.

## Artifact topology

Transition preserves the installed artifact set:

```text
runtime-base
runtime-base + development-addon
runtime-base + test-addon
runtime-base + development-addon + test-addon
```

Artifact expansion or contraction is not part of transition. Existing same-product install and uninstall operations remain responsible for changing addon topology before or after a transition.

This separates two questions:

```text
Which product is active?       -> transition
Which addons are installed?    -> same-product lifecycle
```

## Source exactness and user data

Every registered source-owned path must match the source registry before mutation. Modified, missing, or wrong-type owned paths reject the transition before mutation.

This is intentionally stricter than uninstall preserve-and-report. Transition must not silently discard modified content, leave it mixed into the target product, or reinterpret it as target-owned data. The source installation remains unchanged so the user can resolve the conflict explicitly.

Unowned descendants remain unchanged unless they occupy a target-owned path. An unowned target-path collision rejects before mutation.

## Transaction plan counts

The full topology transition has one registry mutation plus:

```text
noop shared paths        216
replace shared paths    2728
remove source-only        2 or 12
create target-only       12 or 2
journaled mutations     2743
```

The journaled mutation total is symmetric in both directions. Supported topology totals are:

```text
runtime-only             656
runtime + development   1100
runtime + test          2299
complete product        2743
```

## Recovery

The transition journal uses the frozen mutation vocabulary and states.

```text
PREPARED or APPLYING
  first recovery   -> restore exact source, ROLLED_BACK
  second recovery  -> NOOP_ROLLED_BACK

COMMITTED
  first recovery   -> finalize exact target, remove transaction
  second recovery  -> zero transactions
```

Recovery must restore not merely runnable Python but the exact source registry, artifact tuple, owned payload identities, unowned sentinels, and artifact topology.

## Locking

The existing exclusive installation lock covers the entire transition. A second transition, install, uninstall, verify mutation, or recovery operation cannot enter while the transition owns the lock. Nonblocking contention rejects before mutation.

## Post-transition acceptance

Every successful direction and topology must prove:

```text
exact target registry and owned payload
no source-only stale paths
all target-only paths present
unowned sentinels unchanged
zero committed transaction residue
runtime and subprocess identity
native closure and extension imports
HTTPS and timezone integration
venv and uv explicit-interpreter workflows
whole-prefix relocation
installed addon behavior for the preserved topology
```

## Scenario matrix

The frozen matrix contains exactly 66 scenarios:

```text
preflight     14
happy path     8
collision     12
recovery      24
locking        2
audit          6
```

The eight happy paths cover both directions across all four artifact topologies. Recovery covers both directions, all four topologies, and PREPARED, late APPLYING, and COMMITTED boundaries.

## Gate sequence

```text
Gate 4A  second-product authority                 FROZEN
Gate 4B  transition contract design               DESIGN FROZEN
Gate 4C  transition coordinator implementation    IMPLEMENTED — 69/69
Gate 4D  bidirectional Termux target validation   ACCEPTED — 66/66
Gate 4E  independent transition freeze            FROZEN PASS
```

Gate 4C implements only this design and passes its repository verifier. A design change still requires a new authority decision rather than silent implementation drift.

## Evidence contract

Target execution must use one Termux wrapper and emit a PASS-or-FAIL `.tar.zst` containing raw stdout/stderr, real return codes, canonical JSON, before/after registries, complete owned and unowned inventories, transition journals, first and second recovery evidence, runtime probes, archive safety, a complete self-excluding result index, and an explicit claim boundary.

## Claim boundary

A Gate 4B design PASS proves that the exact two-product manifest delta, non-reopening transition policy, recovery model, and 66-scenario validation matrix are internally consistent.

It does not prove a transition implementation, upgrade, downgrade, mixed-version runtime behavior, migration, or target recovery behavior.
