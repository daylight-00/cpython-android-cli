# Stage 3-C Phase 4 Scope: Installation Transactions

> **Status:** FROZEN — Gates 1–5B complete
> **Input:** frozen Phase 3 archives
> **Primary target:** Termux on Android arm64

## Phase question

> Can exact installed ownership and lifecycle semantics remain recoverable after abrupt process termination, exclude concurrent mutation, and obey an explicit filesystem durability protocol on every production mutation path?

## Frozen Gate 1 — installation contract

```text
contract derivation       54/54 PASS
independent verifier      59/59 PASS
contract index
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3
```

Frozen ownership:

```text
registered OWNED_PAYLOAD paths   2956
non-owning structural rows          4
state root                         outside prefix
```

## Frozen Gate 2 — isolated lifecycle transactions

```text
scenario runner       61/61 PASS
independent verifier  58/58 PASS
scenario logs          25/25
result-index
  0041f1c3c73dc7a62291b6c3b244ac885d9bad6799d4115280febc20f61384da
```

Frozen behaviors:

```text
fresh runtime/addon composition       2956 paths
exact runtime reinstall               714 NOOP / 0 mutations
same-owner repair                     PASS
collision and prerequisite rejection no mutation
install and uninstall rollback        exact prior state
modified leaf preservation            PASS
unowned sentinel preservation         PASS
retained directory reuse              no descendant adoption
```

## Frozen Gate 3 — abrupt recovery and lock exclusion

```text
scenario runner       55/55 PASS
independent verifier  82/82 PASS
scenario logs          40/40 canonical
snapshot pairs           5
result-index
  f5ba124ebb9752b45d60f027474a399adf61fc5db033c1165a79664cbfc743bd
```

Frozen states:

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
all detected rows            81
production rows               67
UNKNOWN                        0
result-index
  ac11225ae6b45ac45f1e378ecf7bba9cd074a1f779009318e001d5694d89ead8
```

Frozen source identities:

```text
recovery_common.py
  1ba78274c8c56a1b2b6cbd525fb341719a2ce4a7
recovery_operations.py
  119571e8ad8a5663d20beff0ab82c85c14dfc4eb
recovery_engine.py
  9a3f1898c7420198ff33d2b067a6fa2a6ac8618d
```

## Frozen Gate 5B — integrated durability and complete replay

```text
source integration             29/29 PASS
Gate 3 recovery replay          55/55 PASS
Gate 3 recovery verifier        82/82 PASS
Gate 4 durability replay        64/64 PASS
Gate 4 durability verifier      53/53 PASS
focused exercises               20/20 PASS
integrated trace verifier       29/29 PASS
overall verifier                36/36 PASS
result-index
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce
```

Accepted TGZ:

```text
stage3c-phase4-integrated-durability-results-20260712-082135.tgz
sha256
  76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187
```

Integrated source identities:

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

Observed integrated traces:

```text
files                  25
events             42,941
ordering violations     0
```

## Frozen production semantics

```text
journal and registry
  durable atomic replacement

prior-registry backup
  durable creation before payload mutation

regular and symlink publication
  temporary publication and parent sync

backup and restore move
  source and destination parent sync

directory create and repair
  object and parent sync

unlink, rmdir, and cleanup
  surviving parent sync

transaction cleanup
  content first, journal last, transaction directory last

unjournaled preparation
  discard transaction-local state only
```

## Physical failure boundary

Phase 4 does not claim:

```text
actual sudden-power-loss persistence
kernel panic persistence
storage-controller or write-cache failure
interruption inside one filesystem primitive
```

Those claims are not required for installed-product validation.

## Non-reopening rule

Later work must not silently change ownership, structural non-ownership, collision policy, repair policy, uninstall preservation, journal states, recovery direction, lock semantics, durability ordering, production obligations, or integrated source identities.

Any intentional change reopens Phase 4 and its complete Gate 1–5B evidence chain.

## Final evidence

```text
docs/stages/STAGE3C_PHASE4_FINAL.md
docs/evidence/STAGE3C_PHASE4_INTEGRATED_DURABILITY_RESULT.md
```

## Final marker

```text
STAGE3C_PHASE4=FROZEN
```
