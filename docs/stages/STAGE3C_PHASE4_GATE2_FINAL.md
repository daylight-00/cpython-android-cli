# Stage 3-C Phase 4 Gate 2 Final: Installation Transaction Prototype

> **Status:** FROZEN
> **Primary target:** Termux on Android arm64

## Frozen input

```text
Phase 4 Gate 1 contract index
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3

runtime-base archive
  2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743

development-addon archive
  f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea

test-addon archive
  02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1
```

## Frozen transaction behavior

```text
fresh runtime-base creation          714
fresh development-addon creation     454
fresh test-addon creation           1788
composed exact ownership            2956

same-version runtime reinstall
  714 NOOP
  0 mutations

registered mismatch repair
  1 repair
  prior path backup
  atomic registry replacement

unowned required leaf
  reject before mutation

missing addon prerequisite
  reject before mutation

runtime uninstall with dependents
  reject before mutation
```

## Frozen rollback behavior

```text
install failure injection
  after 5 mutations
  ROLLED_BACK
  exact prior fingerprint restored

uninstall failure injection
  after 5 mutations
  ROLLED_BACK
  exact prior fingerprint restored
```

These are synchronous exception-handling rollback paths. Abrupt process termination recovery is not part of Gate 2.

## Frozen uninstall behavior

```text
matching registered leaves
  remove

locally modified registered leaves
  preserve and report

owned directories
  remove only when empty

structural parents
  preserve

unowned descendants
  preserve
```

## Frozen retained-directory behavior

After runtime uninstall preserved nonempty `lib` and `lib/python3.14`, runtime reinstall reused those two exact directory paths without registering or changing their unowned descendants.

## Validation ledger

```text
scenario runner       61/61 PASS
independent verifier  58/58 PASS
scenario logs          25/25 retained
input mutation              PASS
```

## Evidence

```text
docs/evidence/STAGE3C_PHASE4_TRANSACTION_PROTOTYPE_DESIGN.md
docs/evidence/STAGE3C_PHASE4_TRANSACTION_RESULT.md
```

Accepted result bundle:

```text
stage3c-phase4-installation-transaction-results-20260711-230729.tgz
sha256
  9ea7379263711c8501d674e78e25d29ccd1764db30497c5dc2414030d378c005

result-index sha256
  0041f1c3c73dc7a62291b6c3b244ac885d9bad6799d4115280febc20f61384da
```

## Non-reopening rule

Later work must not weaken:

```text
exact-path registry ownership
unowned leaf collision rejection
addon prerequisite enforcement
NOOP exact reinstall
backup-before-repair
reverse rollback
modified-path preservation
empty-only directory removal
structural and unowned descendant preservation
exact-directory reuse without descendant adoption
```

A change to these semantics reopens Gate 2 and requires complete 61-check scenario and 58-check independent verification.

## Deferred

```text
abrupt process-crash recovery
lock contention evidence
kernel or power-loss durability
parent-directory fsync
upgrade and downgrade
installed runtime behavior
```

## Final marker

```text
STAGE3C_PHASE4_GATE2=FROZEN
```
