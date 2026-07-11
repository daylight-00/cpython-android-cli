# Stage 3-C Phase 4 Installation Durability Result

> **Status:** PASS — Gate 4 durability primitive and ordering protocol closed
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase4-installation-durability-results-20260712-011157.tgz`

## Result archive identity

```text
sha256
  94567ed50f030f3ab1844d81533a2e67eb22e83accabb0753a8501c84fd2ecda

size
  22,922,351 bytes

members
  174

regular files
  158

directories
  16

symlinks / hardlinks / special entries
  0 / 0 / 0

unsafe member names
  0
```

## Machine result

```text
durability scenarios       64/64 PASS
independent verifier       53/53 PASS
workflow return codes       all 0
failed checks                   []
```

```text
STAGE3C_PHASE4_DURABILITY_SCENARIOS=PASS
STAGE3C_PHASE4_INSTALLATION_DURABILITY=PASS
```

## Result index

```text
sha256
  3cb7e83eb6dc6c186a36da512ed41cbba4566abfc4bd4f5f71766ea1fcf075c4

indexed files
  154

independent hash, size, and mode mismatches
  0
```

## Accepted Gate 3 identity

```text
Gate 3 result-index sha256
  f5ba124ebb9752b45d60f027474a399adf61fc5db033c1165a79664cbfc743bd
```

The embedded Gate 3 result also retained its frozen `55/55 + 82/82` PASS and all-zero workflow return codes.

## Target capability result

```text
regular-file fsync
  PASS

directory fsync
  PASS

O_DIRECTORY available
  true

same-filesystem work layout
  true

regular-file mode
  0600

directory mode
  0700
```

## Frozen atomic replacement sequence

```text
OPEN_TEMP
WRITE_TEMP
FSYNC_FILE
REPLACE
FSYNC_DIR(target parent)
```

Both first creation and replacement produced the exact five-event sequence.

```text
atomic create events
  5

atomic replace events
  5

temporary files remaining
  0

final mode
  0600
```

## Frozen namespace sequences

Directory creation:

```text
MKDIR
FSYNC_DIR(new directory)
FSYNC_DIR(parent directory)
```

Cross-directory move:

```text
MOVE
FSYNC_DIR(source parent)
FSYNC_DIR(destination parent)
```

Removal:

```text
UNLINK
FSYNC_DIR(parent)

RMDIR
FSYNC_DIR(parent)
```

All parent paths in the retained traces matched the declared affected directories.

## Frozen transaction sequence

```text
journal-prepared
payload
journal-applying
registry
journal-committed
backup-cleanup
```

The transaction trace retained 27 contiguous events:

```text
journal PREPARED replacement     5 events
payload replacement              5 events
journal APPLYING replacement     5 events
registry replacement             5 events
journal COMMITTED replacement    5 events
backup unlink + parent fsync     2 events
```

Final prototype state:

```text
journal
  COMMITTED

registry
  owned: [payload]

payload bytes
  payload-v1\n

backup
  absent

atomic temporary files
  absent
```

## Negative controls

Missing target-parent fsync:

```text
OPEN_TEMP
WRITE_TEMP
FSYNC_FILE
REPLACE
```

The trace was rejected because the five-operation atomic sequence and final parent-directory sync were absent.

Invalid transaction ordering:

```text
journal-prepared  1
registry          2
payload           3
journal-applying  4
journal-committed 5
backup-cleanup    6
```

The trace was rejected because registry was declared before payload.

## Retained trace evidence

```text
positive traces
  7 / 7 canonical JSON

trace-atomic-create.json
trace-atomic-replace.json
trace-mkdir.json
trace-move.json
trace-rmdir.json
trace-transaction.json
trace-unlink.json

negative controls
  2
```

All retained scenario, verification, capability, contract, positive trace, negative-control, and workflow JSON files used canonical sorted JSON serialization.

## Input mutation

```text
input entries before/after
  150 / 150

input fingerprint before/after
  af7b64f51fb8d7f21d206dc3683507e9155aa117d77378c0d63125422887f3d6

regular files
  137

directories
  13

special paths
  0
```

## Closed claims

This result proves that the target filesystem accepted the tested regular-file and directory `fsync` calls and that the retained primitive and prototype transaction traces obey the declared operation ordering. The independent verifier reconstructed sequence, parent-path, final-state, canonical-serialization, negative-control, and immutable-input checks.

## Claim boundary

This result does not prove persistence after actual sudden power loss, kernel panic, storage-controller failure, write-cache loss, or interruption inside a single filesystem primitive. It also does not prove that every install, uninstall, rollback, recovery, registry, journal, and cleanup path in the Gate 3 recovery engine already uses these durability helpers. That integration is the next gate.
