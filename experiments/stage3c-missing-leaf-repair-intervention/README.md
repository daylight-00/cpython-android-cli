# Stage 3-C Phase 4I: Missing Registered Leaf Repair Intervention

> **Status:** FROZEN PASS
> **Target:** Termux on Android arm64
> **Product acceptance:** not claimed by this workflow

## Frozen result

```text
PHASE4I_EXACT_REINSTALL_NOOP=PASS
PHASE4I_IN_PLACE_REPAIR_REGRESSION=4/4 PASS
PHASE4I_MISSING_LEAF_REPAIR=2/2 PASS
PHASE4I_CRASH_RECOVERY=12/12 PASS
PHASE4I_INTERVENTION_VERIFICATION=51/51 PASS
PHASE4I_GATE3A_PRODUCT_ACCEPTANCE=NOT_CLAIMED
STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION=PASS
```

Accepted archive:

```text
stage3c-phase4-missing-leaf-repair-intervention-results-20260712-180237.tgz
sha256
  d497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a
size
  23,980,515 bytes
members
  580
```

Result identity:

```text
root result-index sha256
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6
indexed files
  523/523 exact
scenario checks
  39/39
independent verifier
  51/51
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_RESULT.md
```

## Frozen correction

The accepted correction changes only an absent registered non-directory repair:

```text
existing mismatch
  replaced intent
  backup current path
  publish frozen member

missing registered leaf
  created intent
  skip nonexistent backup move
  publish frozen member
```

Files:

```text
experiments/stage3c-installation-recovery/
├── recovery_operations_missing_leaf.py
└── recovery_engine_missing_leaf.py
```

No journal schema, registry schema, manifest, archive, ownership, uninstall, or addon policy changed.

## Accepted success matrix

```text
exact-noop                  PASS
regular-bytes               PASS
regular-mode                PASS
regular-wrong-type          PASS
symlink-target              PASS
missing-regular             PASS
missing-symlink             PASS
```

All repair scenarios produced:

```text
pre-verify one bad path
noop 713 / repair 1
mutation count 2
post-verify PASS
registry unchanged
portable payload exact
transaction residue 0
final leaf exact
```

## Accepted crash matrix

Both missing leaf types passed at:

```text
prepared
intent-1
mutation-1
intent-2
mutation-2
committed
```

Pre-commit recovery restored the original missing state and prior registry. Committed recovery preserved the repaired leaf and cleaned the transaction.

## Verification

```text
independent roots            19/19 inode-separated
scenario runner checks       39/39
independent verifier checks  51/51
generated JSON canonical     157/157
raw process cross-check      exact
```

## Next boundary

```text
Phase 5 Gate 3A product acceptance
```

The next workflow must exercise all six repair classes and then run the complete installed-runtime behavior contract with the corrected engine.

Handoff:

```text
docs/handoff/PHASE5_GATE3A_PRODUCT_ACCEPTANCE_HANDOFF_20260712.md
```

## Claim boundary

This intervention PASS proves the correction and recovery matrix only. Post-repair runtime, HTTPS, uv, native closure, extension imports, and Gate 2 relocation regression remain open.
