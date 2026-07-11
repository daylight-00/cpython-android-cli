# Stage 3-C Phase 4 Recovery and Lock Design

> **Status:** IMPLEMENTED — target evidence pending
> **Input:** frozen Phase 4 Gate 2 result

## Purpose

Extend the isolated transaction prototype from synchronous rollback to explicit recovery after abrupt process termination, and prove that a concurrent nonblocking contender cannot mutate while the installation lock is held.

## Journal schema v2

```text
journal kind
  cpython-android-cli-crash-recoverable-transaction

states
  PREPARED
  APPLYING
  COMMITTED
  ROLLING_BACK
  ROLLED_BACK

mutation record states
  INTENT
  APPLIED
```

Every recoverable mutation records a durable `INTENT` before the filesystem primitive and records `APPLIED` after the primitive completes.

## Recoverable mutation kinds

```text
created
replaced
chmod
removed
removed-dir
registry
```

The prior registry bytes are copied into the transaction backup before the first payload mutation.

## Recovery direction

```text
PREPARED
  rollback with zero payload mutations

APPLYING with INTENT
  apply idempotent inverse only when the mutation became observable

APPLYING with APPLIED
  reverse mutations in reverse order

registry APPLIED before COMMITTED
  restore prior registry and prior payload

COMMITTED
  finalize transaction cleanup without rollback

ROLLED_BACK
  recovery is an idempotent no-op
```

Recovery runs under the same exclusive installation lock as install and uninstall.

## Crash injection

The scenario harness launches the engine as a separate process and uses immediate process termination at these durable boundaries:

```text
after PREPARED

after first durable INTENT and before its filesystem mutation

after five durable APPLIED install mutations

after five durable APPLIED uninstall mutations

after a repaired payload and registry are both APPLIED but before COMMITTED

after COMMITTED but before transaction cleanup
```

This is not ordinary exception injection. The process exits without executing Python cleanup or rollback handlers.

## Lock contention

A holder process acquires the exact installation lock and publishes a ready marker. While the lock remains held, a second process attempts a nonblocking development-addon install.

Required result:

```text
contender
  installation lock busy
  no mutation

post-release install
  create 454
  registry 1168
```

## Scenario matrix

```text
PREPARED crash rollback
INTENT-window crash rollback
APPLYING install rollback after 5
APPLYING uninstall rollback after 5
registry-applied pre-commit rollback
normal repair after recovered prior corruption
COMMITTED cleanup finalization
ROLLED_BACK recovery idempotence
nonblocking lock contender rejection
post-release install success
```

## Validation

```text
scenario runner       55 checks
independent verifier  82 checks
retained logs          40
final registry snapshots
  5 registry files
  5 independently observed path files
```

## Claim boundary

A PASS proves only the tested process-termination boundaries and flock contention path in isolated roots. It does not prove kernel or power-loss durability, parent-directory fsync, a crash inside a single non-atomic filesystem primitive, adversarial external mutation, fairness, upgrade or downgrade, or installed runtime behavior.
