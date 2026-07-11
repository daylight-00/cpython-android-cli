# Stage 3-C Phase 4 Final: Installation Registry, Transactions, Recovery, and Durability

> **Status:** FROZEN
> **Primary target:** Termux on Android arm64

## Phase result

Stage 3-C Phase 4 defines and validates the installation ownership registry, isolated lifecycle transactions, abrupt-process recovery, exclusive mutation lock, filesystem durability protocol, production mutation inventory, and integrated durability replay.

## Frozen Gate 1 — installation contract

```text
contract derivation       54/54 PASS
independent verifier      59/59 PASS
registered ownership       2956 paths
structural references         4 non-owning rows
contract index
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3
```

## Frozen Gate 2 — isolated transaction execution

```text
scenario runner       61/61 PASS
independent verifier  58/58 PASS
scenario logs          25/25
result-index
  0041f1c3c73dc7a62291b6c3b244ac885d9bad6799d4115280febc20f61384da
```

Frozen behaviors include fresh composition, prerequisites, exact reinstall NOOP, same-owner repair, collision rejection, install and uninstall rollback, modified-path preservation, unowned sentinel preservation, and retained-directory non-adoption.

## Frozen Gate 3 — abrupt recovery and lock exclusion

```text
scenario runner       55/55 PASS
independent verifier  82/82 PASS
scenario logs          40/40 canonical
snapshot pairs           5
result-index
  f5ba124ebb9752b45d60f027474a399adf61fc5db033c1165a79664cbfc743bd
```

Frozen recovery states:

```text
PREPARED / INTENT / APPLYING / registry pre-commit
  rollback

COMMITTED
  finalize cleanup

ROLLED_BACK
  repeated recovery NOOP

exclusive flock
  nonblocking contender rejection
```

## Frozen Gate 4 — durability protocol

```text
scenario runner       64/64 PASS
independent verifier  53/53 PASS
positive traces         7/7
negative controls        2
result-index
  3cb7e83eb6dc6c186a36da512ed41cbba4566abfc4bd4f5f71766ea1fcf075c4
```

Frozen ordering:

```text
file fsync before replace
target-parent fsync after replace
new-directory and parent fsync
source and destination parent fsync after move
parent fsync after unlink or rmdir
PREPARED before payload
payload before registry
registry before COMMITTED
COMMITTED before cleanup
```

## Frozen Gate 5A — production mutation inventory

```text
inventory scenario       32/32 PASS
independent verifier     29/29 PASS
all rows                     81
production rows              67
UNKNOWN                       0
result-index
  ac11225ae6b45ac45f1e378ecf7bba9cd074a1f779009318e001d5694d89ead8
```

Frozen source blobs:

```text
recovery_common.py
  1ba78274c8c56a1b2b6cbd525fb341719a2ce4a7
recovery_operations.py
  119571e8ad8a5663d20beff0ab82c85c14dfc4eb
recovery_engine.py
  9a3f1898c7420198ff33d2b067a6fa2a6ac8618d
```

## Frozen Gate 5B — integrated durability

```text
source integration             29/29 PASS
recovery replay                55/55 PASS
recovery verifier              82/82 PASS
durability replay              64/64 PASS
durability verifier            53/53 PASS
focused exercises              20/20 PASS
trace verifier                 29/29 PASS
overall verifier               36/36 PASS
result-index
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce
```

Accepted result archive:

```text
stage3c-phase4-integrated-durability-results-20260712-082135.tgz
sha256
  76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187
```

Integrated source blobs:

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

## Frozen installation semantics

```text
ownership authority
  exact registry rows derived from OWNED_PAYLOAD

structural namespace
  non-owning directory references

state root
  outside installed prefix

unowned leaf collision
  reject before mutation

same-version exact match
  NOOP

same-owner mismatch
  durable backup then repair

other-artifact owner
  reject

modified uninstall leaf
  preserve and report

owned directory
  remove only when empty

journal checkpoints
  PREPARED, APPLYING, INTENT, APPLIED, COMMITTED

pre-commit failure
  rollback exact prior registered state

post-commit interruption
  finalize cleanup without rollback

concurrent writer
  exclusive flock
```

## Frozen integrated durability semantics

```text
journal and registry
  durable atomic replacement

prior registry backup
  durable creation before payload mutation

regular payload publication
  temporary copy, file fsync, replace, parent fsync

symlink publication
  temporary symlink, replace, parent fsync

backup and restore move
  source and destination parent fsync

directory create
  directory and parent fsync

chmod repair
  affected object fsync

unlink and rmdir
  surviving parent fsync

transaction cleanup
  content first, journal last, transaction directory last

unjournaled preparation
  discard transaction-local state only
```

## Non-reopening rule

Later work must not silently alter registry ownership, structural non-ownership, collision policy, repair policy, uninstall preservation, journal states, recovery direction, lock semantics, durability ordering, Gate 5A obligations, or integrated source identities.

Any intentional change reopens Phase 4 and requires the complete Gate 1–5B evidence chain.

## Deferred physical failure boundary

The following are not claimed:

```text
actual sudden-power-loss persistence
kernel panic persistence
storage-controller or write-cache failure
interruption inside one filesystem primitive
filesystem or hardware behavior beyond successful target calls
```

These physical-failure claims are not required to begin installed-product validation.

## Evidence

```text
docs/stages/STAGE3C_PHASE4_GATE1_FINAL.md
docs/stages/STAGE3C_PHASE4_GATE2_FINAL.md
docs/stages/STAGE3C_PHASE4_GATE3_FINAL.md
docs/stages/STAGE3C_PHASE4_GATE4_FINAL.md
docs/stages/STAGE3C_PHASE4_GATE5A_FINAL.md
docs/evidence/STAGE3C_PHASE4_INTEGRATED_DURABILITY_RESULT.md
```

## Final marker

```text
STAGE3C_PHASE4=FROZEN
```
