# Stage 3-C Phase 4 Gate 4 Final: Durability Primitive and Ordering Protocol

> **Status:** FROZEN
> **Primary target:** Termux on Android arm64

## Frozen input

```text
Gate 3 result-index sha256
  f5ba124ebb9752b45d60f027474a399adf61fc5db033c1165a79664cbfc743bd
```

## Frozen capability boundary

```text
regular-file fsync      PASS
directory fsync         PASS
O_DIRECTORY             available
same-filesystem layout  PASS
```

## Frozen atomic replacement

```text
OPEN_TEMP
WRITE_TEMP
FSYNC_FILE
REPLACE
FSYNC_DIR(target parent)
```

The temporary file must be created in the target directory with exclusive creation semantics. The target replacement is not complete for this contract until the target parent directory has been synced.

## Frozen directory creation

```text
MKDIR
FSYNC_DIR(new directory)
FSYNC_DIR(parent directory)
```

## Frozen cross-directory move

```text
MOVE
FSYNC_DIR(source parent)
FSYNC_DIR(destination parent)
```

When both parents are identical, one parent sync is sufficient. The frozen target trace used distinct parents and observed both syncs.

## Frozen removal

```text
UNLINK
FSYNC_DIR(parent)

RMDIR
FSYNC_DIR(parent)
```

## Frozen transaction ordering

```text
journal-prepared
payload
journal-applying
registry
journal-committed
backup-cleanup
```

Each journal, payload, and registry replacement must satisfy the complete five-event atomic-replacement sequence.

Backup cleanup must not begin before the COMMITTED journal replacement and its target-parent directory sync have completed.

## Frozen negative controls

```text
missing target-parent fsync
  rejected

registry before payload
  rejected
```

## Validation ledger

```text
scenario runner       64/64 PASS
independent verifier  53/53 PASS
positive traces         7/7 canonical
transaction events     27
negative controls        2
input mutation           PASS
```

## Evidence

```text
docs/evidence/STAGE3C_PHASE4_DURABILITY_PROTOCOL_DESIGN.md
docs/evidence/STAGE3C_PHASE4_DURABILITY_RESULT.md
```

Accepted result bundle:

```text
stage3c-phase4-installation-durability-results-20260712-011157.tgz
sha256
  94567ed50f030f3ab1844d81533a2e67eb22e83accabb0753a8501c84fd2ecda

result-index sha256
  3cb7e83eb6dc6c186a36da512ed41cbba4566abfc4bd4f5f71766ea1fcf075c4
```

## Non-reopening rule

Later work must not weaken:

```text
file fsync before replace
target-parent directory fsync after replace
new-directory and parent sync after mkdir
source-parent and destination-parent sync after cross-directory move
parent sync after unlink or rmdir
PREPARED before payload
payload before registry
registry before COMMITTED
COMMITTED before backup cleanup
negative-control rejection
```

A change to this ordering reopens Gate 4 and requires the complete `64/64 + 53/53` evidence chain.

## Deferred

```text
integration into every Gate 3 recovery-engine mutation path
actual sudden-power-loss testing
kernel panic or storage-controller failure
interruption inside one filesystem primitive
adversarial external mutation
upgrade and downgrade
installed runtime behavior
```

## Final marker

```text
STAGE3C_PHASE4_GATE4=FROZEN
```
