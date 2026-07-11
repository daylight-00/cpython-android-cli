# Stage 3-C Phase 4 Gate 3 Final: Abrupt Recovery and Lock Contention

> **Status:** FROZEN
> **Primary target:** Termux on Android arm64

## Frozen input

```text
Gate 2 result index
  0041f1c3c73dc7a62291b6c3b244ac885d9bad6799d4115280febc20f61384da

Gate 1 contract index
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3
```

## Frozen corrected isolation

```text
scenario seed regular files
  independent metadata-preserving copies

scenario seed symlinks
  preserved as symlinks

shared regular-file inode between seed and scenario root
  forbidden

hardlink seed cloning
  forbidden
```

The original hardlink failure remains preserved and does not count as a Gate 3 PASS.

## Frozen journal model

```text
schema version
  2

journal kind
  cpython-android-cli-crash-recoverable-transaction

states
  PREPARED
  APPLYING
  COMMITTED
  ROLLING_BACK
  ROLLED_BACK

mutation checkpoint
  INTENT before filesystem primitive
  APPLIED after filesystem primitive
```

## Frozen recovery behavior

```text
PREPARED
  rollback with zero restored mutations

APPLYING with INTENT only
  rollback without assuming the mutation happened

APPLYING with APPLIED mutations
  reverse in reverse order

payload and registry APPLIED before COMMITTED
  restore prior payload and prior registry

COMMITTED before cleanup
  finalize cleanup without rollback

ROLLED_BACK
  repeated recovery is a no-op
```

## Frozen crash matrix

```text
exit 90  PREPARED
exit 93  first durable INTENT before mutation
exit 91  five APPLIED install mutations
exit 91  five APPLIED uninstall mutations
exit 91  repaired payload and registry APPLIED before COMMITTED
exit 92  COMMITTED before cleanup
```

## Frozen lock behavior

```text
holder
  exclusive flock

nonblocking contender
  installation lock busy
  no mutation

post-release operation
  succeeds normally
```

## Validation ledger

```text
scenario runner       55/55 PASS
independent verifier  82/82 PASS
scenario logs          40/40 canonical
registry snapshots       5
observed path snapshots  5
snapshot mismatches       0
input mutation            PASS
```

## Evidence

```text
docs/evidence/STAGE3C_PHASE4_RECOVERY_LOCK_DESIGN.md
docs/evidence/STAGE3C_PHASE4_RECOVERY_SEED_CLONE_FAILURE.md
docs/evidence/STAGE3C_PHASE4_RECOVERY_RESULT.md
```

Accepted result bundle:

```text
stage3c-phase4-installation-recovery-independent-seed-copy-corrected-results-20260712-004138.tgz
sha256
  3c164f54e4f205ba8ba889274656375ce2c0cf137f65c6ccf6fb2cafab889bd6

result-index sha256
  f5ba124ebb9752b45d60f027474a399adf61fc5db033c1165a79664cbfc743bd
```

## Non-reopening rule

Later work must not weaken:

```text
independent scenario-root copies
durable INTENT before mutation
APPLIED only after mutation
prior-registry backup before first payload mutation
reverse rollback ordering
COMMITTED cleanup without rollback
ROLLED_BACK idempotence
exclusive installation lock
nonblocking contender rejection without mutation
```

A change to these semantics reopens Gate 3 and requires the complete 55-check scenario and 82-check independent verifier.

## Deferred

```text
regular-file and directory fsync protocol
parent-directory fsync after namespace changes
kernel or sudden-power-loss durability
crash inside one filesystem primitive
adversarial external mutation and lock fairness
upgrade and downgrade
installed runtime behavior
```

## Final marker

```text
STAGE3C_PHASE4_GATE3=FROZEN
```
