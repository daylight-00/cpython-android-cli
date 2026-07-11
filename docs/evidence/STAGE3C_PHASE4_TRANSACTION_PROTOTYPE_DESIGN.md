# Stage 3-C Phase 4 Transaction Prototype Design

> **Status:** IMPLEMENTED — target evidence pending
> **Input:** frozen Phase 4 Gate 1 contract

## Purpose

Execute the frozen contract in isolated installation roots without touching the canonical product, runtime-base source, or a live user prefix.

## Prototype state layout

```text
<installation-root>/
  prefix/
  .cpython-android-cli/
    registry.json
    lock
    transactions/<transaction-id>/
      journal.json
      staging/
      backup/
```

Registry, lock, and journal files are mode `0600`.

## Preflight

Before payload mutation the engine verifies:

```text
frozen archive SHA-256 and size
embedded manifest byte identity
addon prerequisite identity
complete exact-path ownership conflicts
unowned leaf collisions
compatible exact directory reuse
structural directory type and mode
absence of symlink parents
```

## Mutation model

```text
regular and symlink creation
  stage then atomic replace

registered mismatch repair
  move prior entry to transaction backup
  install staged replacement

owned directory creation
  shallow-to-deep

registry update
  canonical JSON temporary file + fsync + atomic replace
```

## Rollback model

Failure injection occurs after a selected payload or registry mutation count. Rollback reverses mutations in reverse order, restores backups and prior registry bytes, and leaves a `ROLLED_BACK` journal for evidence.

## Uninstall model

```text
matching registered regular or symlink
  move to backup then remove on commit

modified registered regular or symlink
  preserve and report

owned directory
  remove deepest-first only when empty

registry
  remove artifact and its exact path records atomically
```

## Scenario matrix

```text
fresh runtime-base install
fresh development-addon overlay
fresh test-addon overlay
runtime uninstall blocked while addons depend on it
exact 714-path runtime reinstall NOOP
single registered runtime corruption detection and repair
injected test-addon uninstall failure and rollback
unowned runtime leaf collision rejection with no mutation
addon prerequisite rejection with no mutation
injected development-addon install failure and rollback
modified test leaf preservation
unowned sentinel preservation
test-addon uninstall
development-addon uninstall
runtime-base uninstall with nonempty owned directories retained
runtime-base reinstall reusing two retained directories without adopting descendants
```

## Validation

```text
scenario runner       61 checks
independent verifier  58 checks
```

## Claim boundary

A PASS proves the tested isolated transaction execution paths. It does not prove process-crash recovery, concurrent lock contention, upgrade or downgrade, durable parent-directory fsync, or installed runtime behavior.
