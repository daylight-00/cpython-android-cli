# Stage 3-C Phase 4 Recovery Durability Integration Inventory

> **Status:** IMPLEMENTED — target evidence pending
> **Input:** frozen Phase 4 Gate 4 durability result

## Purpose

Before changing the frozen Gate 3 recovery engine, enumerate every detected filesystem mutation and `fsync` call in its exact source blobs. Each call site must be anchored to a module, function, line, column, operation class, lifecycle category, and explicit durability obligation.

This gate does not integrate helpers. It closes the completeness problem that must precede integration.

## Frozen source blobs

```text
recovery_common.py
  1ba78274c8c56a1b2b6cbd525fb341719a2ce4a7

recovery_operations.py
  119571e8ad8a5663d20beff0ab82c85c14dfc4eb

recovery_engine.py
  9a3f1898c7420198ff33d2b067a6fa2a6ac8618d
```

These are Git blob identities, not ordinary file-content SHA-256 values.

## Detected operation families

```text
atomic_write
persist_journal
save_prior_registry
os.replace
os.symlink
os.chmod
os.unlink
os.rmdir
os.open with mutating flags
os.fsync
shutil.copyfile
shutil.copyfileobj
shutil.rmtree
Path.mkdir
Path.open with write mode
Path.write_bytes
Path.write_text
Path.unlink
Path.rmdir
stream.write
stream.flush
```

## Lifecycle categories

```text
transaction-metadata
transaction-backup
install-production
uninstall-production
rollback-cleanup
rollback-production
recovery-cleanup
transient-staging
lock-state
lock-probe
tool-output
```

Every detected call must resolve to one category. `UNKNOWN` is a hard failure.

## Production integration obligations

```text
replace
  fsync source parent and destination parent

symlink publication
  fsync containing directory

chmod
  fsync affected file or directory

unlink / rmdir
  fsync parent

regular copy
  fsync completed file before publication

tree removal
  fsync surviving parent

atomic_write
  add target-parent directory fsync

journal persistence
  inherit durable atomic replacement

prior-registry backup
  durably create backup before first payload mutation

mkdir
  fsync new directory and parent
```

## Generated evidence

```text
mutation-inventory.json
  complete sorted call-site inventory

integration-plan.json
  production-only rows grouped by lifecycle category

scenario.json
  input, source identity, coverage, classification, and plan checks

verification.json
  independent source re-scan and output consistency checks
```

## Required replay after implementation

The actual integration gate must replay both frozen behavior chains:

```text
Gate 3 recovery scenarios       55/55
Gate 3 independent verifier     82/82
Gate 4 durability scenarios     64/64
Gate 4 independent verifier     53/53
```

Passing only the source inventory is insufficient to claim durable recovery-engine integration.

## Validation

```text
inventory scenario       32 checks
independent verifier     29 checks
source blobs              exact
unknown categories          0 required
input mutation            PASS required
```

## Claim boundary

A PASS proves that every detected mutation and sync call in the exact frozen recovery source blobs was inventoried and assigned an integration obligation. It does not prove that any helper was integrated or that any crash, rollback, recovery, or cleanup path has been replayed with an integrated implementation.
