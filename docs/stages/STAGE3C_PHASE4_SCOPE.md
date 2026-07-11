# Stage 3-C Phase 4 Scope: Installation Transactions

> **Status:** ACTIVE — Gate 1 frozen, Gate 2 transaction prototype active
> **Input:** frozen Phase 3 archives and frozen Phase 4 Gate 1 contract
> **Primary target:** Termux on Android arm64

## Phase question

> Can exact installed ownership, collision, reinstall, rollback, and uninstall semantics be executed in isolated installation roots without mutating source products or adopting unowned content?

## Frozen Gate 1

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

Frozen registry model:

```text
exact registered paths       2956
non-owning structural refs      4
shared namespace
  lib
  lib/python3.14
```

Frozen state layout:

```text
<installation-root>/
  prefix/
  .cpython-android-cli/
    registry.json
    lock
    transactions/
```

Frozen policy:

```text
unowned required leaf                    conflict before mutation
compatible exact owned-directory path    reuse exact directory only
compatible structural directory          reuse without ownership
same-version exact registered entry      NOOP
same-owner mismatch                      backup then repair
other-artifact owner                     conflict
modified uninstall leaf                  preserve and report
owned directory                          remove only when empty
structural parent and unowned descendant preserve
```

## Active Gate 2

Run:

```sh
bash experiments/stage3c-installation-transaction/run-installation-transaction.sh
```

All mutation is isolated below:

```text
work/termux/stage3c-phase4-installation-transaction/
```

The canonical promoted product, isolated runtime-base source, and live Termux prefix are not transaction targets.

### Scenario matrix

```text
fresh runtime-base install
fresh development-addon overlay
fresh test-addon overlay
runtime uninstall rejected while addons depend on it
exact 714-path runtime reinstall NOOP
single registered runtime corruption detection and repair
injected test-addon uninstall failure after five mutations
uninstall rollback to byte-identical pre-state
unowned runtime leaf collision rejection with no mutation
addon prerequisite rejection with no mutation
injected development-addon install failure after five mutations
install rollback to byte-identical pre-state
modified test leaf preservation
unowned sentinel preservation
test-addon uninstall
development-addon uninstall
runtime-base uninstall with nonempty exact directories retained
runtime-base reinstall reusing two directories without descendant adoption
```

### Validation

```text
scenario runner       61 checks
independent verifier  58 checks
input mutation        PASS required
```

Expected marker:

```text
STAGE3C_PHASE4_INSTALLATION_TRANSACTION=PASS
```

### Expected outputs

```text
results/termux/stage3c-phase4-installation-transaction/
  input/contract/
  01-*.json ... 25-*.json
  snapshots/
  scenario.json
  verification.json
  input-before.json
  input-after.json
  input-mutation-check.txt
  workflow-status.json
  result-index.json
```

## Deferred Gate 3 and later

```text
process-crash recovery from PREPARED/APPLYING states
concurrent lock contention and exclusion evidence
durable parent-directory fsync policy
explicit second-version upgrade and downgrade
installed runtime smoke and native closure
uv venv and uv run from installed prefix
whole-prefix installed relocation
```

## Claim boundary

A Gate 2 PASS proves only the explicitly tested isolated transaction paths. It does not prove crash recovery, concurrency, upgrade/downgrade, or installed runtime behavior.
