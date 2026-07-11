# Stage 3-C Phase 4 Integrated Durability Design

> **Status:** IMPLEMENTED — authoritative target evidence pending
> **Input:** frozen Phase 4 Gate 5A inventory

## Purpose

Apply the frozen Gate 4 durability protocol to every production mutation group identified by Gate 5A, then replay the complete Gate 3 recovery chain and Gate 4 durability chain without weakening either claim boundary.

## Frozen Gate 5A input

```text
result-index sha256
  ac11225ae6b45ac45f1e378ecf7bba9cd074a1f779009318e001d5694d89ead8

inventory rows
  81

production rows
  67

UNKNOWN
  0
```

## Integrated source identities

```text
recovery_common.py
  3183ba0861ef45e7a395201bec0085f3f69fb248

recovery_operations.py
  8a307065e00fd7a7332541f4911c5478945374ee

recovery_engine.py
  aebf5b9a33d163f7f8758f785ca621c94c0e478b

recovery_durability.py
  61bfb859f73acccb0dfcce1d2a630bfd1ffc2d3f
```

These are Git blob identities checked by the source-integration verifier.

## Durability helper boundary

```text
fsync_directory
fsync_path
durable_ensure_directory
durable_mkdir
durable_chmod
durable_atomic_write
durable_copy_file
durable_move
durable_publish_regular
durable_publish_symlink
durable_unlink
durable_rmdir
durable_tree_remove
durable_cleanup_transaction
durable_open_lock
```

### Atomic named-file publication

```text
create exclusive temporary in target parent
write all bytes
set final mode
fsync temporary file
replace target
fsync target parent
```

### Move

```text
replace source with destination
fsync source parent
fsync destination parent when distinct
```

### Directory creation

```text
mkdir
chmod final mode
fsync new directory
fsync parent
```

### Removal

```text
unlink or rmdir
fsync surviving parent
```

### Metadata repair

```text
chmod
fsync affected file or directory
```

## Integrated transaction ordering

Install and uninstall preserve the frozen recovery ordering:

```text
create transaction directory durably
prepare transient staging
create backup directory durably
create prior-registry backup durably
write PREPARED journal durably
write APPLYING journal durably
write INTENT journal durably
perform one durable mutation
write APPLIED journal durably
publish registry durably
write COMMITTED journal durably
remove transaction content
remove journal last
remove transaction directory
```

The journal remains present until all staging and backup content has been removed. A COMMITTED recovery therefore finalizes cleanup rather than rolling back.

## Pre-journal preparation failure

A crash or exception can occur after the transaction directory is created but before `journal.json` exists. Recovery now classifies such a directory as:

```text
UNJOURNALED_PREPARE
  → DISCARDED_PREPARE
```

Only transaction-local staging and backup state are removed. No registered payload rollback is attempted because no PREPARED journal was published.

## Production mapping

Gate 5A groups are resolved as follows:

```text
transaction-metadata
  durable atomic journal replacement

transaction-backup
  durable prior-registry copy

install-production
  durable mkdir, chmod, backup move, regular/symlink publication,
  registry replacement, and committed cleanup

uninstall-production
  durable backup move, directory removal, registry replacement,
  and committed cleanup

rollback-cleanup
  durable recursive removal

rollback-production
  durable registry restoration/removal, payload restoration,
  mode restoration, and directory recreation

recovery-cleanup
  durable COMMITTED cleanup and unjournaled prepare discard
```

## Source integration verifier

```text
29 checks
```

It verifies:

```text
Gate 5A 32/29 PASS and exact result index
frozen source identities
integrated source identities
81 frozen rows and 67 production rows
both checkpoint rows
no direct mutation primitives in inventoried production functions
required helper calls for every production function
complete durability helper function set
Gate 5A replay counts retained
```

## Behavioral replay

The integrated engine must pass the unchanged frozen Gate 3 tools:

```text
recovery scenarios       55/55
independent verifier     82/82
retained logs             40
snapshot pairs             5
```

## Focused integrated exercises

```text
20 checks
16 canonical logs
```

They cover:

```text
fresh runtime install and verification
directory mode repair
symlink repair
development-addon install
successful development-addon uninstall
unjournaled prepare discard
successful runtime uninstall
fresh runtime registry-applied pre-commit rollback
```

## Integrated trace verification

Optional JSONL tracing is enabled only by the gate workflow through:

```text
CPYTHON_ANDROID_CLI_DURABILITY_TRACE_DIR
```

Trace writing is outside the installation root and does not alter registry or payload state.

The 29-check trace verifier reconstructs:

```text
OPEN_TEMP → WRITE_TEMP/COPY_TEMP → FSYNC_FILE → REPLACE → FSYNC_DIR
SYMLINK_TEMP → REPLACE → FSYNC_DIR
MOVE → source/destination parent FSYNC_DIR
CHMOD → FSYNC_PATH
UNLINK/RMDIR → parent FSYNC_DIR
MKDIR → new-directory and parent FSYNC_DIR
```

Required observed labels include journal, registry, payload publication, backup moves, rollback, uninstall, and COMMITTED cleanup.

## Durability protocol replay

The unchanged frozen Gate 4 tools must also pass:

```text
durability scenarios       64/64
independent verifier       53/53
positive traces              7
negative controls             2
```

## Overall verifier

```text
36 checks
```

It combines source mapping, Gate 3 replay, Gate 4 replay, focused exercises, integrated traces, canonical evidence, and immutable Gate 5A input.

## Claim boundary

A PASS proves that the integrated source set resolves the frozen Gate 5A production inventory, preserves frozen Gate 3 behavior, preserves the Gate 4 protocol, and emits ordered `fsync` traces for exercised production paths. It does not prove persistence across actual sudden power loss, kernel panic, storage-controller failure, write-cache loss, or interruption inside one filesystem primitive.
