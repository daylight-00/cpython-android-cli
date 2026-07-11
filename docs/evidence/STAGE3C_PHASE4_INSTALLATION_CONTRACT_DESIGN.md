# Stage 3-C Phase 4 Installation Contract Design

> **Status:** IMPLEMENTED — target evidence pending

## Purpose

Freeze installed ownership and lifecycle policy before implementing target mutation.

## Registry model

```text
registry kind
  cpython-android-cli-installed-ownership-registry

registered records
  OWNED_PAYLOAD only

owned paths
  2956

structural references
  4
```

Each registered path records its artifact owner, entry type, mode, and type-specific identity. Regular files retain size and SHA-256. Symlinks retain their target. Directories retain mode only.

`STRUCTURAL_PARENT` is represented separately and never becomes exclusive ownership.

## State layout

```text
<installation-root>/
  prefix/
  .cpython-android-cli/
    registry.json
    lock
    transactions/
```

The registry and transaction state are outside the installed payload prefix.

## Collision model

```text
absent owned payload path
  create the manifest entry type

existing unowned regular file or symlink
  conflict

existing compatible owned-directory path
  reuse and register exact directory ownership
  preserve every descendant ownership boundary

existing compatible structural directory
  create or reuse without ownership

required directory occupied by non-directory
  conflict

same-version exact registered match
  no-op

same-artifact registered mismatch
  replacement requires backup

other-artifact owner
  conflict
```

Exact directory ownership is ownership of the directory path only. It does not adopt or overwrite existing descendants. This permits a later install to reuse a directory retained because it contains an unowned sentinel.

Unowned regular files and symlinks are never silently adopted.

## Uninstall model

```text
matching registered leaf
  remove exact path

locally modified registered leaf
  preserve and report

owned directory
  remove only when empty

structural parent
  preserve namespace

unowned descendant
  preserve
```

## Transaction ordering

The model defines twelve install steps and ten uninstall steps. Preflight and lock acquisition precede mutation. A prepared journal and backup plan precede the first mutation. Registry replacement occurs only after payload changes. A failure after the first mutation and before durable commit requires rollback.

States:

```text
PREPARED
APPLYING
COMMITTED
ROLLING_BACK
ROLLED_BACK
FAILED
```

## Outputs

```text
installed-owned-paths.tsv
structural-paths.tsv
collision-policy.tsv
operation-order.tsv
contract-summary.tsv
registry-template.json
installation-contract.json
contract-index.json
```

## Verification

```text
deriver       54 checks
verifier      59 checks
```

The verifier independently reconstructs every owned row, structural row, summary, registry record, policy row, operation-order row, and generated-file hash from frozen Phase 3 evidence.

## Claim boundary

A PASS proves deterministic policy representation only. Filesystem changes, rollback execution, recovery, concurrency, upgrade, downgrade, and runtime validation remain unproved.
