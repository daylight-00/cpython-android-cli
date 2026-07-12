# Phase 4 Missing-Leaf Repair Intervention Handoff — 2026-07-12

> **Status:** FROZEN PASS
> **Accepted target evidence:** complete Termux TGZ independently inspected
> **Next boundary:** Phase 5 Gate 3A product acceptance

## Frozen diagnostic ancestry

```text
Gate 3A0 archive sha256
  9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2

Gate 3A0 result-index sha256
  a7507ab60de402a636c8e2899706aec77844896254f28dd068c8683dcb3dce7b
```

## Frozen intervention identity

```text
archive
  stage3c-phase4-missing-leaf-repair-intervention-results-20260712-180237.tgz

archive sha256
  d497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a

result-index sha256
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6

scenario checks
  39/39

independent verifier
  51/51
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_RESULT.md
```

## Accepted implementation

```text
recovery_operations_missing_leaf.py
  absent registered non-directory only
  replaced intent → created intent
  skip corresponding nonexistent backup move
  existing mismatches retain replaced semantics

recovery_engine_missing_leaf.py
  injects accepted install operation into the frozen CLI engine
```

## Accepted target matrix

```text
exact reinstall NOOP                    PASS
four existing-path repair regressions   PASS
missing regular repair                  PASS
missing symlink repair                  PASS
regular crash boundaries 6/6            PASS
symlink crash boundaries 6/6            PASS
```

All nineteen roots were inode-separated. Pre-commit recovery restored the original missing state and prior registry. Committed recovery preserved the repaired leaf and cleaned the transaction.

## Claim boundary

The intervention itself is frozen. Gate 3A installed-runtime product acceptance remains open because post-repair Python behavior, HTTPS, uv, native closure, extension imports, and corrected-engine Gate 1-equivalent regression have not yet been accepted.

Successor handoff:

```text
docs/handoff/PHASE5_GATE3A_PRODUCT_ACCEPTANCE_HANDOFF_20260712.md
```
