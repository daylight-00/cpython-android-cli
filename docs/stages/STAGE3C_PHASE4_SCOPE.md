# Stage 3-C Phase 4 Scope: Installation Transactions

> **Status:** ACTIVE — Gates 1–5A frozen, Gate 5B integrated durability active
> **Input:** frozen Phase 3 archives and frozen Phase 4 Gates 1–5A
> **Primary target:** Termux on Android arm64

## Phase question

> Can exact installed ownership and lifecycle semantics remain recoverable after abrupt process termination, exclude concurrent mutation, and obey an explicit filesystem durability protocol on every production mutation path?

## Frozen Gate 1 — contract

```text
contract derivation       54/54 PASS
independent verifier      59/59 PASS
input mutation                  PASS
contract index
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3
```

```text
docs/stages/STAGE3C_PHASE4_GATE1_FINAL.md
docs/evidence/STAGE3C_PHASE4_INSTALLATION_CONTRACT_RESULT.md
```

Frozen rules include exact-path ownership, non-owning structural parents, unowned leaf rejection, exact reinstall no-op, backup-before-repair, modified-path preservation, empty-only directory removal, and rollback obligation before commit.

## Frozen Gate 2 — isolated transaction execution

```text
scenario runner       61/61 PASS
independent verifier  58/58 PASS
scenario logs          25/25 retained
input mutation              PASS

accepted TGZ
  stage3c-phase4-installation-transaction-results-20260711-230729.tgz

TGZ sha256
  9ea7379263711c8501d674e78e25d29ccd1764db30497c5dc2414030d378c005

result-index sha256
  0041f1c3c73dc7a62291b6c3b244ac885d9bad6799d4115280febc20f61384da
```

Frozen behavior:

```text
fresh runtime/addon composition       2956 paths
runtime dependency enforcement        PASS
exact runtime reinstall               714 NOOP / 0 mutations
single registered corruption repair   PASS
unowned collision rejection           no mutation
addon prerequisite rejection          no mutation
install rollback after 5 mutations    exact prior state
uninstall rollback after 5 mutations  exact prior state
modified leaf preservation            PASS
unowned sentinel preservation         PASS
retained directory reuse              no descendant adoption
```

```text
docs/stages/STAGE3C_PHASE4_GATE2_FINAL.md
docs/evidence/STAGE3C_PHASE4_TRANSACTION_RESULT.md
```

## Frozen Gate 3 — abrupt recovery and lock contention

```text
scenario runner       55/55 PASS
independent verifier  82/82 PASS
scenario logs          40/40 canonical
registry snapshots       5
observed path snapshots  5
input mutation            PASS

accepted TGZ
  stage3c-phase4-installation-recovery-independent-seed-copy-corrected-results-20260712-004138.tgz

TGZ sha256
  3c164f54e4f205ba8ba889274656375ce2c0cf137f65c6ccf6fb2cafab889bd6

result-index sha256
  f5ba124ebb9752b45d60f027474a399adf61fc5db033c1165a79664cbfc743bd
```

Frozen isolation and crash boundaries:

```text
independent scenario-root regular files
shared regular-file inode forbidden
exit 90  PREPARED
exit 93  durable INTENT before mutation
exit 91  five APPLIED install mutations
exit 91  five APPLIED uninstall mutations
exit 91  payload and registry APPLIED before COMMITTED
exit 92  COMMITTED before cleanup
```

Frozen recovery and lock direction:

```text
PREPARED / INTENT / APPLYING / registry pre-commit
  reverse to prior state

COMMITTED
  finalize cleanup without rollback

ROLLED_BACK
  repeated recovery is a no-op

exclusive flock
  nonblocking contender rejected without mutation
```

```text
docs/stages/STAGE3C_PHASE4_GATE3_FINAL.md
docs/evidence/STAGE3C_PHASE4_RECOVERY_LOCK_DESIGN.md
docs/evidence/STAGE3C_PHASE4_RECOVERY_SEED_CLONE_FAILURE.md
docs/evidence/STAGE3C_PHASE4_RECOVERY_RESULT.md
```

## Frozen Gate 4 — durability primitive and ordering protocol

```text
scenario runner       64/64 PASS
independent verifier  53/53 PASS
positive traces         7/7 canonical
transaction events     27
negative controls        2
input mutation            PASS

accepted TGZ
  stage3c-phase4-installation-durability-results-20260712-011157.tgz

TGZ sha256
  94567ed50f030f3ab1844d81533a2e67eb22e83accabb0753a8501c84fd2ecda

result-index sha256
  3cb7e83eb6dc6c186a36da512ed41cbba4566abfc4bd4f5f71766ea1fcf075c4
```

Frozen protocol:

```text
atomic replacement
  OPEN_TEMP
  WRITE_TEMP
  FSYNC_FILE
  REPLACE
  FSYNC_DIR(target parent)

mkdir
  MKDIR
  FSYNC_DIR(new directory)
  FSYNC_DIR(parent)

cross-directory move
  MOVE
  FSYNC_DIR(source parent)
  FSYNC_DIR(destination parent)

unlink / rmdir
  mutation
  FSYNC_DIR(parent)

transaction order
  journal-prepared
  payload
  journal-applying
  registry
  journal-committed
  backup-cleanup
```

```text
docs/stages/STAGE3C_PHASE4_GATE4_FINAL.md
docs/evidence/STAGE3C_PHASE4_DURABILITY_PROTOCOL_DESIGN.md
docs/evidence/STAGE3C_PHASE4_DURABILITY_RESULT.md
```

## Frozen Gate 5A — recovery durability integration inventory

```text
inventory scenario       32/32 PASS
independent verifier     29/29 PASS
input mutation                 PASS

accepted TGZ
  stage3c-phase4-recovery-durability-inventory-checkpoint-classification-corrected-results-20260712-020339.tgz

TGZ sha256
  c263814a506b7eb145a5fde891bb55ca1eedbb8b992096769f3505be31ce1d62

result-index sha256
  ac11225ae6b45ac45f1e378ecf7bba9cd074a1f779009318e001d5694d89ead8
```

Frozen source inventory:

```text
recovery_common.py
  1ba78274c8c56a1b2b6cbd525fb341719a2ce4a7
recovery_operations.py
  119571e8ad8a5663d20beff0ab82c85c14dfc4eb
recovery_engine.py
  9a3f1898c7420198ff33d2b067a6fa2a6ac8618d

all detected rows       81
production rows          67
lifecycle categories     11
operation families       17
UNKNOWN categories        0
```

Frozen checkpoint classification:

```text
add_intent    transaction-metadata
mark_applied  transaction-metadata
```

Required integration replay:

```text
Gate 3 recovery scenarios       55/55
Gate 3 independent verifier     82/82
Gate 4 durability scenarios     64/64
Gate 4 independent verifier     53/53
```

```text
docs/stages/STAGE3C_PHASE4_GATE5A_FINAL.md
docs/evidence/STAGE3C_PHASE4_DURABILITY_INTEGRATION_INVENTORY_DESIGN.md
docs/evidence/STAGE3C_PHASE4_DURABILITY_INVENTORY_CLASSIFICATION_FAILURE.md
docs/evidence/STAGE3C_PHASE4_DURABILITY_INVENTORY_RESULT.md
```

## Active Gate 5B — integrated durability and complete replay

Run:

```sh
bash experiments/stage3c-installation-durability-integration/run-integrated-durability.sh
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

Production integration:

```text
journal and registry
  durable atomic replacement

prior registry backup
  durable copy before payload mutation

payload files and symlinks
  fsynced temporary publication and parent sync

payload and backup moves
  source/destination parent sync

directory create and repair
  directory and parent sync

unlink, rmdir, and tree cleanup
  surviving parent sync

transaction cleanup
  content first
  journal last
  transaction directory last

unjournaled transaction preparation
  DISCARDED_PREPARE
```

Validation matrix:

```text
source integration verifier     29/29
Gate 3 recovery replay           55/55
Gate 3 recovery verifier         82/82
Gate 4 durability replay         64/64
Gate 4 durability verifier       53/53
focused integrated exercises     20/20
integrated trace verifier        29/29
overall independent verifier     36/36
input mutation                   PASS
```

Expected final marker:

```text
STAGE3C_PHASE4_INTEGRATED_DURABILITY=PASS
```

Detailed design:

```text
docs/evidence/STAGE3C_PHASE4_INTEGRATED_DURABILITY_DESIGN.md
experiments/stage3c-installation-durability-integration/INTEGRATED_DURABILITY.md
```

## Deferred later gates

```text
actual sudden-power-loss durability
kernel panic or storage-controller failure
crash inside one non-atomic filesystem primitive
adversarial external mutation and lock fairness
explicit second-version upgrade and downgrade
installed runtime smoke and native closure
uv venv and uv run from installed prefix
whole-prefix installed relocation
```

## Claim boundary

A Gate 5B PASS proves integrated source mapping, complete frozen behavioral replay, complete frozen durability replay, and ordered sync traces for exercised production paths. It does not prove persistence after actual sudden power loss, kernel panic, storage-controller failure, write-cache loss, or interruption inside one filesystem primitive.
