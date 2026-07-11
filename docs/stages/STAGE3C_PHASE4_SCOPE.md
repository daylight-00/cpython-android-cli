# Stage 3-C Phase 4 Scope: Installation Transactions

> **Status:** ACTIVE — Gates 1–2 frozen, Gate 3 recovery and lock validation active
> **Input:** frozen Phase 3 archives and frozen Phase 4 Gates 1–2
> **Primary target:** Termux on Android arm64

## Phase question

> Can exact installed ownership and lifecycle semantics remain recoverable after abrupt process termination while excluding concurrent mutation?

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

Frozen Gate 2 behavior:

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

## Active Gate 3 — abrupt recovery and lock contention

Run:

```sh
bash experiments/stage3c-installation-recovery/run-installation-recovery.sh
```

All mutable roots remain below:

```text
work/termux/stage3c-phase4-installation-recovery/
```

The canonical promoted prefix, isolated runtime-base source, live Termux prefix, and copied Gate 2 input are not transaction targets.

### Journal model

```text
schema version       2
states
  PREPARED
  APPLYING
  COMMITTED
  ROLLING_BACK
  ROLLED_BACK

mutation checkpoint
  INTENT before filesystem primitive
  APPLIED after filesystem primitive
```

### Process-termination matrix

```text
exit 90  after PREPARED
exit 93  after durable INTENT, before filesystem mutation
exit 91  after five APPLIED install mutations
exit 91  after five APPLIED uninstall mutations
exit 91  after repaired payload and registry APPLIED, before COMMITTED
exit 92  after COMMITTED, before cleanup
```

Recovery requirements:

```text
PREPARED / INTENT / APPLYING / registry pre-commit
  reverse to exact prior state

COMMITTED
  finalize cleanup without rollback

ROLLED_BACK
  idempotent recovery no-op
```

### Lock contention

```text
holder process
  acquires exclusive flock and publishes ready marker

nonblocking contender
  installation lock busy
  no mutation

post-release install
  development-addon create 454
  registry 1168
```

### Validation

```text
scenario runner       55 checks
independent verifier  82 checks
retained logs          40
final registry snapshots
  5 registry JSON
  5 observed-path JSON
input mutation        PASS required
```

Expected final marker:

```text
STAGE3C_PHASE4_INSTALLATION_RECOVERY=PASS
```

## Deferred Gate 4 and later

```text
kernel or power-loss durability
parent-directory fsync policy
crash inside one non-atomic filesystem primitive
adversarial external mutation and lock fairness
explicit second-version upgrade and downgrade
installed runtime smoke and native closure
uv venv and uv run from installed prefix
whole-prefix installed relocation
```

## Claim boundary

A Gate 3 PASS proves only the tested abrupt process-exit boundaries and flock contender path in isolated roots. It does not prove power-loss durability, filesystem-primitive atomicity, upgrade/downgrade, or installed runtime behavior.
