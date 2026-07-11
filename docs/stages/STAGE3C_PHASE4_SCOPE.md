# Stage 3-C Phase 4 Scope: Installation Transactions

> **Status:** ACTIVE — Gates 1–3 frozen, Gate 4 durability protocol active
> **Input:** frozen Phase 3 archives and frozen Phase 4 Gates 1–3
> **Primary target:** Termux on Android arm64

## Phase question

> Can exact installed ownership and lifecycle semantics remain recoverable after abrupt process termination, exclude concurrent mutation, and obey explicit filesystem durability ordering?

## Frozen Gate 1 — contract

```text
contract derivation       54/54 PASS
independent verifier      59/59 PASS
input mutation                  PASS
contract index
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3
```

Authoritative boundary:

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

Authoritative boundary:

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

Frozen isolation:

```text
scenario seed regular files
  independent copies

scenario seed symlinks
  preserved as symlinks

shared regular-file inode
  forbidden
```

Frozen crash boundaries:

```text
exit 90  PREPARED
exit 93  durable INTENT before mutation
exit 91  five APPLIED install mutations
exit 91  five APPLIED uninstall mutations
exit 91  payload and registry APPLIED before COMMITTED
exit 92  COMMITTED before cleanup
```

Frozen recovery direction:

```text
PREPARED / INTENT / APPLYING / registry pre-commit
  reverse to prior state

COMMITTED
  finalize cleanup without rollback

ROLLED_BACK
  repeated recovery is a no-op
```

Frozen lock direction:

```text
holder
  exclusive flock

nonblocking contender
  installation lock busy
  no mutation

post-release operation
  succeeds
```

Authoritative boundary:

```text
docs/stages/STAGE3C_PHASE4_GATE3_FINAL.md
docs/evidence/STAGE3C_PHASE4_RECOVERY_LOCK_DESIGN.md
docs/evidence/STAGE3C_PHASE4_RECOVERY_SEED_CLONE_FAILURE.md
docs/evidence/STAGE3C_PHASE4_RECOVERY_RESULT.md
```

## Active Gate 4 — durability primitive and ordering protocol

Run:

```sh
bash experiments/stage3c-installation-durability/run-installation-durability.sh
```

All mutable files remain below:

```text
work/termux/stage3c-phase4-installation-durability/
```

### Capability requirements

```text
regular-file fsync
directory fsync
O_DIRECTORY support
same-filesystem work layout
```

### Atomic replacement

```text
OPEN_TEMP
WRITE_TEMP
FSYNC_FILE
REPLACE
FSYNC_DIR(target parent)
```

### Namespace mutation

```text
mkdir
  MKDIR
  FSYNC_DIR(new directory)
  FSYNC_DIR(parent)

move across directories
  MOVE
  FSYNC_DIR(source parent)
  FSYNC_DIR(destination parent)

unlink / rmdir
  mutation
  FSYNC_DIR(parent)
```

### Transaction ordering

```text
journal-prepared
payload
journal-applying
registry
journal-committed
backup-cleanup
```

Every journal, payload, and registry replacement must use the complete atomic-replacement sequence.

### Negative controls

```text
missing target-parent fsync
registry declared before payload
```

Both invalid traces must be rejected.

### Validation

```text
scenario runner       64 checks
independent verifier  53 checks
positive traces         7
transaction events     27
input mutation        PASS required
```

Expected final marker:

```text
STAGE3C_PHASE4_INSTALLATION_DURABILITY=PASS
```

Detailed design:

```text
docs/evidence/STAGE3C_PHASE4_DURABILITY_PROTOCOL_DESIGN.md
experiments/stage3c-installation-durability/README.md
```

## Deferred Gate 5 and later

```text
integration of durability helpers into every Gate 3 transaction path
kernel or sudden-power-loss durability
crash inside one non-atomic filesystem primitive
adversarial external mutation and lock fairness
explicit second-version upgrade and downgrade
installed runtime smoke and native closure
uv venv and uv run from installed prefix
whole-prefix installed relocation
```

## Claim boundary

A Gate 4 PASS proves successful tested `fsync` operations and declared ordering on the target filesystem. It does not prove persistence after actual sudden power loss, kernel panic, controller failure, or interruption inside one filesystem primitive. It also does not yet prove complete recovery-engine integration.
