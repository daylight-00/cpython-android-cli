# Stage 3-C Phase 5 Gate 4C: Transition Coordinator Implementation

> **Status:** IMPLEMENTED — repository verification 69/69 PASS; Gate 4D target evidence pending
> **Products:** CPython 3.14.5 ↔ CPython 3.14.6
> **Target topology:** preserve the currently installed runtime/addon set
> **Frozen design:** Gate 4B, 66 scenarios

## Implementation question

> Can the frozen Gate 4B whole-product contract be represented by a dedicated coordinator without modifying the frozen Phase 4 engine, changing registry schema 1, or claiming target behavior before Termux evidence exists?

Gate 4C answers that repository implementation question. It does not accept an upgrade or downgrade execution.

## Files

```text
gate4c-transition-authorities.json
transition_coordinator.py
verify-gate4c-transition-implementation.py
run-gate4c-transition-implementation.sh
gate4c-transition-implementation-authority.json
```

## Authority inputs

The tracked authority specification binds both frozen products by exact product-lock, manifest, archive, artifact ID, size, SHA-256, owned-path count, and source commit.

At execution time an authority map supplies relative filesystem locations for those exact files. The coordinator rejects any product lock, manifest, or archive whose size or SHA-256 differs from the tracked specification.

The map is data, not a substitute authority. It cannot introduce a third product or modify a frozen identity.

## Dedicated operations

```text
transition
  replace one exact frozen product with the other

guard-install
  reject ordinary artifact installation when the requested product
  differs from the exact active product
```

Ordinary same-product installation remains owned by the frozen lifecycle engine. Cross-product artifact-by-artifact installation is not treated as a transition.

## Exact-source preflight

Before creating a transaction, the coordinator requires:

```text
one exact runtime-base authority
one exact and internally consistent product artifact tuple
runtime-base present in every accepted topology
registry schema 1 and the frozen registry kind
registered owned paths exactly matching their type, mode, size,
SHA-256 or symlink target
no existing transaction requiring recovery
no unowned collision at a target-owned path
```

A modified, missing, or wrong-type source-owned path rejects before mutation. Non-colliding unowned descendants are not registered and remain untouched.

## Transition plan

The plan is computed over the 2,958-path union frozen by Gate 4B:

```text
exact shared path     noop
changed shared path   replace
source-only path      remove
target-only path      create
```

The installed artifact topology is preserved exactly. Runtime-only remains runtime-only; each selected addon remains selected; transition cannot expand or contract the topology.

## Archive staging safety

Target archives may use the frozen `.tar.gz` or `.tar.zst` formats. Before any selected leaf is staged, the coordinator rejects:

```text
absolute or parent-escaping member names
duplicate member names
hard links
devices, FIFOs, sockets, and other special members
missing selected members
member/manifest type mismatch
symlink-target mismatch
staged payload identity mismatch
```

Only regular files, directories, and symbolic links are accepted archive member types.

## Transaction and recovery

The coordinator imports the frozen common and durability helpers without modifying the Phase 4 engine sources. It uses:

```text
existing exclusive installation lock
one schema-2 transition journal
PREPARED -> APPLYING -> COMMITTED
frozen replace/remove/create mutation vocabulary
schema-1 target registry written atomically
existing recovery engine for rollback or commit finalization
```

Crash-injection return codes remain:

```text
PREPARED       rc 90
late APPLYING  rc 93
COMMITTED      rc 92
```

PREPARED and APPLYING recover to the exact source and retain the frozen rollback tombstone behavior. COMMITTED recovery finalizes the exact target and cleans the transaction. Second recovery remains idempotent under the frozen engine rules.

`--fast-success` exists only for non-crash repository verification and cannot be combined with crash injection. Gate 4D target evidence must use durable checkpoints.

## Repository verification

Run:

```sh
bash experiments/stage3c-gate4-transition/run-gate4c-transition-implementation.sh
```

The verifier uses isolated synthetic frozen-product fixtures, including `.tar.gz` and `.tar.zst`, and checks:

```text
frozen engine blob identities
tracked production authority identities
both transition directions
runtime-only and fully composed topology
exact target registry and payload
unowned descendant preservation
all exact-source rejection classes
target collision rejection
topology preservation
transaction-residue rejection
unknown and mixed-product rejection
same-product/cross-product install guard
target lock/manifest/archive corruption rejection
PREPARED, late APPLYING, and COMMITTED recovery
second-recovery idempotence
installation-lock exclusion
```

Result:

```text
69/69 PASS
```

## Gate sequence

```text
Gate 4A  second-product authority                 FROZEN
Gate 4B  transition contract design               DESIGN FROZEN
Gate 4C  transition coordinator implementation    IMPLEMENTED — 69/69
Gate 4D  bidirectional Termux target validation   READY — not started
Gate 4E  independent transition freeze            pending
```

## Claim boundary

Gate 4C proves that the repository contains an implementation conforming to the frozen design under isolated synthetic transaction tests while preserving the frozen engine sources and registry schema.

It does not prove CPython 3.14.5 → 3.14.6 or 3.14.6 → 3.14.5 target behavior, native closure, HTTPS, timezone, subprocess, venv, uv, relocation, target crash recovery, mixed-version compatibility, migration, or Gate 4 transition acceptance. Those claims require Gate 4D Termux evidence and Gate 4E independent freeze.
