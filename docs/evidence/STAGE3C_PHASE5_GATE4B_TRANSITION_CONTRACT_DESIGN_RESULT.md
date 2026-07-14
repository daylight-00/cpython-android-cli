# Stage 3-C Phase 5 Gate 4B Transition Contract Design Result

> **Status:** DESIGN FROZEN
> **Products:** CPython 3.14.5 ↔ CPython 3.14.6
> **Verifier:** 106/106 PASS
> **Next gate:** Gate 4C transition coordinator implementation

## Decision

Gate 4B freezes a dedicated whole-product transition contract. Cross-product replacement must not be performed by invoking the frozen same-product installer artifact by artifact.

The design consumes both frozen product authorities and keeps the existing artifact bytes, manifests, ownership rules, registry schema, recovery mutation vocabulary, durability helpers, and exclusive installation lock unchanged.

## Exact inventory

```text
union owned paths       2958
shared paths            2944
byte-identical shared    216
replacement required    2728
3.14.6-only                12
3.14.5-only                 2
owner transfers              0
```

```text
inventory file sha256
  c06855780ca4df3c14cc765aec3e61a0a7d0ace4a156d03bf697243bab090993

classification sha256
  1daad3ef9c99eba060852962231e12e6361877709f15e0cb2f18952574f4310b
```

The inventory proves that a direct cross-product install would be incomplete: source-only paths could remain on disk after registry replacement, addons from the source product could coexist with the target runtime, and independent artifact transactions would not provide product-level rollback.

## Frozen policy

```text
operation                  dedicated whole-product transition
source                     exact recognized frozen product
artifact topology          preserved
modified owned path        reject before mutation
unowned descendant         preserve unless target-owned collision
target-owned collision     reject before mutation
shared exact               noop
shared changed             transactional replace
source-only                transactional remove
target-only                transactional create
registry                   exact target tuple, schema version 1
active product             derived from exact runtime artifact identity
journal                    recovery-compatible PREPARED/APPLYING/COMMITTED
lock                       frozen exclusive installation lock
```

The active product lock is verified against the selected authority input. No separate mutable product-lock file is installed.

## Scenario authority

```text
preflight     14
happy path     8
collision     12
recovery      24
locking        2
audit          6
total          66
```

```text
matrix sha256
  7e30fe98996781c86ea719d9fd8512f054a8dfeae5e1328e17264595d6abb55a

repository verifier
  106/106 PASS

verifier output sha256
  74e0c4b723e22f3e09d6586e0d194e72cc5e41b1c3e29f802fd82614601a7956
```

The eight happy paths cover both directions over runtime-only, runtime-plus-development, runtime-plus-test, and complete-product topologies. The 24 recovery scenarios cover both directions, all four topologies, and PREPARED, late APPLYING, and COMMITTED boundaries.

## Non-reopening boundary

Gate 4C may add a transition coordinator, but it may not silently edit the frozen Phase 4 engine files, registry schema, artifact manifests, archive bytes, or same-product lifecycle policy. A contract change requires a separate authority decision.

## Claim boundary

This result proves design consistency only. It does not prove a transition implementation, upgrade, downgrade, mixed-version runtime behavior, migration, or target recovery behavior.

Gate 4C must implement the exact design before any Termux transition execution begins.
