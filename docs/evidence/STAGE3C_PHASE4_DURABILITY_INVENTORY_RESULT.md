# Stage 3-C Phase 4 Recovery Durability Inventory Result

> **Status:** PASS — Gate 5A mutation inventory closed
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase4-recovery-durability-inventory-checkpoint-classification-corrected-results-20260712-020339.tgz`

## Result archive identity

```text
sha256
  c263814a506b7eb145a5fde891bb55ca1eedbb8b992096769f3505be31ce1d62

size
  22,944,114 bytes

members
  188

regular files
  170

directories
  18

symlinks / hardlinks / special entries
  0 / 0 / 0

unsafe member names
  0
```

## Machine result

```text
inventory scenario       32/32 PASS
independent verifier     29/29 PASS
workflow return codes     all 0
failed checks                 []
```

```text
STAGE3C_PHASE4_DURABILITY_INTEGRATION_INVENTORY=PASS
STAGE3C_PHASE4_RECOVERY_DURABILITY_INVENTORY=PASS
```

## Result index

```text
sha256
  ac11225ae6b45ac45f1e378ecf7bba9cd074a1f779009318e001d5694d89ead8

indexed files
  165

independent hash, size, and mode mismatches
  0
```

## Accepted Gate 4 identity

```text
Gate 4 result-index sha256
  3cb7e83eb6dc6c186a36da512ed41cbba4566abfc4bd4f5f71766ea1fcf075c4
```

The embedded Gate 4 result retained its frozen `64/64 + 53/53` PASS and all-zero workflow return codes.

## Frozen recovery source identities

```text
recovery_common.py
  1ba78274c8c56a1b2b6cbd525fb341719a2ce4a7

recovery_operations.py
  119571e8ad8a5663d20beff0ab82c85c14dfc4eb

recovery_engine.py
  9a3f1898c7420198ff33d2b067a6fa2a6ac8618d
```

These are Git blob identities and matched exactly on the Termux target.

## Inventory totals

```text
all detected rows
  81

production rows
  67

lifecycle categories
  11

operation families
  17

UNKNOWN categories
  0

anchor duplicates
  0
```

## Lifecycle categories

```text
install-production       25
uninstall-production     14
rollback-production      11
transaction-metadata     10
transaction-backup        3
rollback-cleanup          2
recovery-cleanup          2
transient-staging         8
lock-state                2
lock-probe                2
tool-output               2
```

Production-only total:

```text
25 + 14 + 11 + 10 + 3 + 2 + 2
  = 67
```

## Operation families

```text
mkdir                       24
journal-helper              13
metadata-change             11
namespace-replace            7
atomic-write-helper          4
tree-remove                  4
direct-write                 3
path-open-write              2
registry-backup-helper       2
regular-copy                 2
symlink-create               2
unlink                       2
file-or-directory-fsync      1
os-open-create               1
rmdir                        1
stream-flush                 1
stream-write                 1
```

## Corrected durable checkpoint classification

The preserved first attempt correctly rejected two unclassified journal checkpoint calls. The corrected target result includes both as production `transaction-metadata`:

```text
recovery_common.py:add_intent
  line 261
  operation journal-helper
  persist_journal(transaction, journal)
  obligation: inherit durable atomic journal replacement

recovery_common.py:mark_applied
  line 269
  operation journal-helper
  persist_journal(transaction, journal)
  obligation: inherit durable atomic journal replacement
```

Both rows are present in `mutation-inventory.json` and in the production `integration-plan.json`.

Preserved failure record:

```text
docs/evidence/STAGE3C_PHASE4_DURABILITY_INVENTORY_CLASSIFICATION_FAILURE.md
```

## Integration plan

```text
production rows
  67

groups
  install-production       25
  uninstall-production     14
  rollback-production      11
  transaction-metadata     10
  transaction-backup        3
  rollback-cleanup          2
  recovery-cleanup          2
```

Required Gate 5B replay:

```text
Gate 3 recovery scenarios       55/55
Gate 3 independent verifier     82/82
Gate 4 durability scenarios     64/64
Gate 4 independent verifier     53/53
```

## Canonical generated evidence

```text
mutation-inventory.json
  sha256 91d8194c163ebabac27130f3039b1ef1a488c9d70745ad2e77980a38f2f188de

integration-plan.json
  sha256 61bd86c0583be24cf6b732d99e5e33dbb86ff267ca2840f4cc80814b6a0e530e

scenario.json
  sha256 6a823047ae94119a3d26fbee472939cde5f256ca39e3e729eef0fe1f7b0a980f

verification.json
  sha256 243396d46d06fd3b79dbd44357c67482333e31e5911974f9a6c9985d33427de8
```

The generated Gate 5A inventory, plan, scenario, verification, and workflow JSON files are canonical sorted JSON. One inherited Phase 2 product-lock input retains its older serialization and is outside the Gate 5A generated-output claim.

## Input mutation

```text
input entries before/after
  173 / 173

input fingerprint before/after
  bbb95feb9aa861fd5f84bb845be1be4ce2f2745f8ba3434b0e5e5452b6d745c1

mutation check
  PASS
```

## Closed claims

This result proves that every call detected by the declared scanner families in the exact frozen Gate 3 source blobs has a unique source anchor, lifecycle category, production-path classification, and explicit integration obligation. It also proves that no detected call remained `UNKNOWN` after the checkpoint correction.

## Claim boundary

This result does not prove that durability helpers have been integrated into the recovery engine. It does not replay install, uninstall, rollback, recovery, journal, registry, or cleanup behavior with an integrated implementation. Gate 5B must apply the plan and replay the frozen Gate 3 and Gate 4 chains.
