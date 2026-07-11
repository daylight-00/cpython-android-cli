# Stage 3-C Phase 4 Gate 5A Final: Recovery Durability Integration Inventory

> **Status:** FROZEN
> **Primary target:** Termux on Android arm64

## Frozen input

```text
Gate 4 result-index sha256
  3cb7e83eb6dc6c186a36da512ed41cbba4566abfc4bd4f5f71766ea1fcf075c4
```

## Frozen source identities

```text
recovery_common.py
  1ba78274c8c56a1b2b6cbd525fb341719a2ce4a7

recovery_operations.py
  119571e8ad8a5663d20beff0ab82c85c14dfc4eb

recovery_engine.py
  9a3f1898c7420198ff33d2b067a6fa2a6ac8618d
```

## Frozen inventory boundary

```text
all detected rows       81
production rows          67
lifecycle categories     11
operation families       17
UNKNOWN categories        0
anchor duplicates         0
```

## Frozen production groups

```text
install-production       25
uninstall-production     14
rollback-production      11
transaction-metadata     10
transaction-backup        3
rollback-cleanup          2
recovery-cleanup          2
```

## Frozen checkpoint classification

```text
add_intent
  transaction-metadata
  journal-helper
  inherit durable atomic journal replacement

mark_applied
  transaction-metadata
  journal-helper
  inherit durable atomic journal replacement
```

The original classification failure remains preserved and does not count as a Gate 5A PASS.

## Frozen integration obligations

```text
namespace replace
  fsync affected source and destination parents

symlink publication
  fsync containing directory

metadata change
  fsync affected file or directory

unlink / rmdir
  fsync parent

regular copy
  fsync completed file before publication

tree removal
  fsync surviving parent

atomic write
  target-parent directory fsync after replace

journal persistence
  durable atomic replacement

prior-registry backup
  durable creation before first payload mutation

mkdir
  fsync new directory and parent
```

## Required Gate 5B replay

```text
Gate 3 recovery scenarios       55/55
Gate 3 independent verifier     82/82
Gate 4 durability scenarios     64/64
Gate 4 independent verifier     53/53
```

Inventory PASS alone cannot claim integrated durability.

## Validation ledger

```text
inventory scenario       32/32 PASS
independent verifier     29/29 PASS
input mutation                 PASS
```

## Evidence

```text
docs/evidence/STAGE3C_PHASE4_DURABILITY_INTEGRATION_INVENTORY_DESIGN.md
docs/evidence/STAGE3C_PHASE4_DURABILITY_INVENTORY_CLASSIFICATION_FAILURE.md
docs/evidence/STAGE3C_PHASE4_DURABILITY_INVENTORY_RESULT.md
```

Accepted result bundle:

```text
stage3c-phase4-recovery-durability-inventory-checkpoint-classification-corrected-results-20260712-020339.tgz
sha256
  c263814a506b7eb145a5fde891bb55ca1eedbb8b992096769f3505be31ce1d62

result-index sha256
  ac11225ae6b45ac45f1e378ecf7bba9cd074a1f779009318e001d5694d89ead8
```

## Non-reopening rule

Later work must not silently remove a frozen inventory row, weaken an obligation, change a production row to non-production, reintroduce an `UNKNOWN` category, or omit either checkpoint row.

Any source change necessarily creates new source blob identities. Gate 5B must prove that every frozen production obligation was resolved or explicitly superseded and must replay both frozen behavior chains.

## Claim boundary

Gate 5A proves source-bound inventory completeness only. It does not prove integrated durability, actual sudden-power-loss persistence, or installed runtime behavior.

## Final marker

```text
STAGE3C_PHASE4_GATE5A=FROZEN
```
