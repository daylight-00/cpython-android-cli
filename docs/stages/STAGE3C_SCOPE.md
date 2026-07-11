# Stage 3-C Scope: Distribution Archive and Installation Contract

> **Status:** ACTIVE — Phases 1–3 and Phase 4 Gates 1–2 frozen; Gate 3 active
> **Primary target:** Termux on Android arm64
> **Python baseline:** CPython 3.14.6

## Stage question

> What archive and installation contract allows downstream tools to inspect, verify, stage, install, repair, recover, remove, and relocate the runtime without project-specific knowledge or unsafe ownership assumptions?

## Design order

```text
freeze product semantics
freeze component ownership and manifests
freeze archive bytes and extraction safety
freeze installation state and transaction policy
execute and validate isolated lifecycle transactions
validate abrupt recovery and lock exclusion
validate upgrade/downgrade and installed runtime behavior
```

## Phase roadmap

```text
Phase 1  product roles and isolated component validation     FROZEN
Phase 2  ownership, shared namespace, and manifests          FROZEN
Phase 3  reproducible archive serialization                  FROZEN
Phase 4  installation registry and transactions              ACTIVE
Phase 5  installed runtime and lifecycle validation          DEFERRED
```

## Frozen Phase 1 boundary

```text
canonical entries          3155
canonical fingerprint      5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
runtime-base entries        714
runtime-base fingerprint    9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
native closure              81 ELF / 329 edges / unresolved 0
extension imports           67/67
relocation                  PASS
```

```text
docs/stages/STAGE3C_PHASE1_FINAL.md
```

## Frozen Phase 2 boundary

```text
runtime-base owned paths        714
development-addon owned paths   454
test-addon owned paths         1788
selected total                 2956
unsupported GUI excluded        199
exact owned overlap               0
```

Shared structural namespace:

```text
lib
lib/python3.14
```

Manifest identities:

```text
manifest index
  540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1
runtime-base
  ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a
development-addon
  9a01655d63044ab126fd71236ca2cb814221317ee9b6b44fd2417fa5535a8b2a
test-addon
  47d9f2e24e74b23e34ae6bfa95a0df22ec7cf9505e3e189dc3d6bdf2dc1c8b5f
```

```text
docs/stages/STAGE3C_PHASE2_FINAL.md
```

## Frozen Phase 3 boundary

```text
runtime-base archive
  2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743
development-addon archive
  f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea
test-addon archive
  02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1
```

```text
builder                    31/31 PASS
extraction preflight       28/28 PASS
archive verifier           76/76 PASS
safe staging extraction      3/3 PASS
```

Frozen serialization:

```text
POSIX pax tar + gzip level 9
mtime 0
uid/gid 0/0
empty owner names
exact deterministic member order
hardlinks and special entries forbidden
```

```text
docs/stages/STAGE3C_PHASE3_FINAL.md
docs/evidence/STAGE3C_PHASE3_REPRODUCIBLE_ARCHIVE_RESULT.md
```

## Phase 4 Gate 1 — frozen contract

```text
contract derivation       54/54 PASS
independent verifier      59/59 PASS
input mutation                  PASS
contract index
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3
```

```text
registered ownership      2956 exact OWNED_PAYLOAD paths
structural references        4 non-owning rows
state root                 outside prefix/
```

Frozen rules:

```text
unowned leaf collision              reject
compatible directory reuse          exact directory path only
same-version exact match            NOOP
same-owner mismatch                 backup then repair
other-artifact owner                reject
modified uninstall leaf             preserve and report
owned directory                     remove only when empty
structural and unowned descendants  preserve
PREPARED journal                    before first mutation
registry replacement                atomic after payload changes
pre-commit mutation failure         rollback required
```

```text
docs/stages/STAGE3C_PHASE4_GATE1_FINAL.md
docs/evidence/STAGE3C_PHASE4_INSTALLATION_CONTRACT_RESULT.md
```

## Phase 4 Gate 2 — frozen transaction execution

```text
scenario runner       61/61 PASS
independent verifier  58/58 PASS
scenario logs          25/25 retained
input mutation              PASS

accepted TGZ sha256
  9ea7379263711c8501d674e78e25d29ccd1764db30497c5dc2414030d378c005

result-index sha256
  0041f1c3c73dc7a62291b6c3b244ac885d9bad6799d4115280febc20f61384da
```

Frozen behavior:

```text
fresh runtime/addon composition       2956 paths
runtime dependency enforcement        PASS
exact runtime reinstall               714 NOOP / 0 mutations
registered corruption repair          PASS
unowned collision rejection           no mutation
addon prerequisite rejection          no mutation
install and uninstall rollback        exact prior fingerprints
modified-path preservation            PASS
unowned sentinel preservation         PASS
retained directory reuse              no descendant adoption
```

```text
docs/stages/STAGE3C_PHASE4_GATE2_FINAL.md
docs/evidence/STAGE3C_PHASE4_TRANSACTION_RESULT.md
```

## Phase 4 Gate 3 — active recovery and lock validation

Implementation:

```text
experiments/stage3c-installation-recovery/
```

Active matrix:

```text
PREPARED process exit and rollback
INTENT-window process exit and rollback
five-mutation install process exit and rollback
five-mutation uninstall process exit and rollback
registry-applied pre-commit process exit and rollback
COMMITTED pre-cleanup process exit and finalization
retained ROLLED_BACK recovery idempotence
nonblocking flock contender rejection
post-release addon install
```

Required validation:

```text
scenario runner       55/55
independent verifier  82/82
scenario logs          40/40
final snapshots         5 registry + 5 observed path sets
input mutation        PASS
```

Detailed scope:

```text
docs/stages/STAGE3C_PHASE4_SCOPE.md
```

## Deferred Phase 4 gates

```text
kernel or power-loss durability
parent-directory fsync policy
crash inside one non-atomic filesystem primitive
adversarial external mutation and lock fairness
explicit second-version upgrade and downgrade
```

## Phase 5

Phase 5 validates runtime behavior from installed prefixes:

```text
installed hash and registry verification
runtime smoke and native closure
uv venv and uv run
whole-prefix relocation
same-version lifecycle
upgrade and rollback lifecycle
uninstall exact ownership
unowned sentinel preservation
```

## Non-reopening rule

Later work must not silently change component ownership, structural non-ownership, artifact and manifest identities, archive bytes, extraction preflight, license ownership, addon prerequisites, Gate 1 policy, or frozen Gate 2 lifecycle behavior.

Any intentional change reopens the corresponding frozen phase or gate and its complete evidence chain.

## Evidence layout

Tracked:

```text
docs/stages/STAGE3C_*.md
docs/evidence/STAGE3C_*.md
experiments/stage3c-*/
```

Generated:

```text
results/termux/stage3c-*/
work/termux/stage3c-*/
```

Generated archives and bulk target evidence remain outside Git and are uploaded as stage-qualified TGZ bundles.

## Current action

Execute and independently verify the Phase 4 abrupt recovery and lock-contention matrix.
