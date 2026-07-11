# Stage 3-C Phase 4 Durability Protocol Design

> **Status:** IMPLEMENTED — target evidence pending
> **Input:** frozen Phase 4 Gate 3 recovery result

## Purpose

Define and execute the filesystem write-ordering obligations that must hold before later transaction code can claim a durability protocol.

This gate deliberately does not claim that an Android device survives kernel panic, sudden power loss, controller failure, or a crash inside one non-atomic filesystem primitive. It proves that required `fsync` calls and namespace ordering execute successfully on the target filesystem and that an independent verifier rejects missing or reordered obligations.

## Accepted Gate 3 input

```text
scenario runner       55/55 PASS
independent verifier  82/82 PASS
result-index
  f5ba124ebb9752b45d60f027474a399adf61fc5db033c1165a79664cbfc743bd
```

## Primitive contract

### Atomic replacement

```text
OPEN_TEMP
WRITE_TEMP
FSYNC_FILE
REPLACE
FSYNC_DIR(target parent)
```

The temporary file is created in the target directory with `O_EXCL`, receives all bytes, is file-synced, and is renamed over the target. The target parent directory is then synced so the namespace replacement has an explicit persistence boundary.

### Directory creation

```text
MKDIR
FSYNC_DIR(new directory)
FSYNC_DIR(parent directory)
```

### Move between directories

```text
MOVE
FSYNC_DIR(source parent)
FSYNC_DIR(destination parent)
```

The current prototype uses different source and destination parents so both parent sync obligations are independently observable.

### Removal

```text
UNLINK or RMDIR
FSYNC_DIR(parent directory)
```

## Transaction-order prototype

```text
journal PREPARED atomic replacement
payload atomic replacement
journal APPLYING/APPLIED atomic replacement
registry atomic replacement
journal COMMITTED atomic replacement
backup cleanup unlink + parent fsync
```

Each atomic replacement contains its own file sync and target-parent directory sync.

The required high-level order is:

```text
journal-prepared
payload
journal-applying
registry
journal-committed
backup-cleanup
```

## Capability probes

The target must successfully execute:

```text
regular-file fsync
directory fsync
O_DIRECTORY directory open
same-filesystem work layout
```

## Positive traces

```text
trace-atomic-create.json
trace-atomic-replace.json
trace-mkdir.json
trace-move.json
trace-unlink.json
trace-rmdir.json
trace-transaction.json
```

Each trace has contiguous sequence numbers and canonical JSON serialization.

## Negative controls

Two deliberately invalid trace documents prove that the audit logic is not pass-only:

```text
negative-missing-parent-fsync.json
  removes the final target-parent FSYNC_DIR

negative-transaction-order.json
  declares registry before payload
```

Both must be rejected by the scenario audit and independently identified by the verifier.

## Validation

```text
scenario runner       64 checks
independent verifier  53 checks
positive traces        7
transaction events    27
input mutation        PASS required
```

## Isolation

All mutable files remain below:

```text
work/termux/stage3c-phase4-installation-durability/
```

The copied Gate 3 evidence tree is read-only input and is fingerprinted before and after execution.

## Claim boundary

A PASS proves that the target filesystem accepted the tested regular-file and directory `fsync` operations and that the tested primitive and transaction traces obey the declared ordering. It does not prove persistence after actual power loss, kernel panic, storage-controller failure, write-cache loss, or interruption inside a single filesystem primitive. It also does not yet prove that the full Gate 3 transaction engine uses these helpers on every path.
