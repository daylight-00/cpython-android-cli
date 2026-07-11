# Stage 3-C Phase 4 Scope: Installation Contract

> **Status:** ACTIVE — contract model only
> **Input:** frozen Phase 3 archives and Phase 2 manifests
> **Primary target:** Termux on Android arm64

## Question

How should installed ownership, shared namespace, collision handling, same-version reinstall, transaction ordering, recovery obligations, and uninstall behavior be represented before an installer mutates a target?

## Frozen archive input

```text
runtime-base
  2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743

development-addon
  f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea

test-addon
  02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1
```

Authoritative boundary:

```text
docs/stages/STAGE3C_PHASE3_FINAL.md
docs/evidence/STAGE3C_PHASE3_REPRODUCIBLE_ARCHIVE_RESULT.md
```

## Gate 1

```sh
bash experiments/stage3c-installation-contract/run-installation-contract.sh
```

This gate derives a deterministic model without changing an installation target.

```text
exact registered paths       2956
non-owning structural refs      4
shared namespace
  lib
  lib/python3.14
```

Only `OWNED_PAYLOAD` becomes registered ownership. Archive metadata is not installed into the payload prefix. `STRUCTURAL_PARENT` remains non-owning.

## State layout

```text
<installation-root>/
  prefix/
  .cpython-android-cli/
    registry.json
    lock
    transactions/
```

## Required policy

```text
existing unowned regular file or symlink
  conflict

existing compatible owned-directory path
  reuse and register exact directory ownership
  preserve all descendant ownership boundaries

existing compatible structural directory
  create or reuse without ownership

required directory path occupied by non-directory
  conflict

matching registered reinstall
  no-op

same-owner mismatch
  replace only with backup

other-artifact ownership
  conflict

modified path during uninstall
  preserve and report

owned directory
  remove only when empty

structural parent and unowned descendant
  preserve
```

Exact directory ownership never implies ownership of its descendants. This permits reinstall after an uninstall preserved a directory containing unowned sentinel content, without silently adopting that content.

A complete preflight, exclusive lock, same-filesystem staging, prior-state backup, prepared journal, atomic registry update, and rollback obligation are required before later mutation prototypes can pass.

## Validation

```text
contract derivation       54 checks
independent verifier      59 checks
input evidence mutation    PASS
```

Expected final marker:

```text
STAGE3C_PHASE4_INSTALLATION_CONTRACT=PASS
```

## Claim boundary

A PASS proves the model is deterministic and independently reproducible. It does not prove target mutation, rollback execution, crash recovery, concurrency, upgrade, downgrade, or installed runtime behavior.
