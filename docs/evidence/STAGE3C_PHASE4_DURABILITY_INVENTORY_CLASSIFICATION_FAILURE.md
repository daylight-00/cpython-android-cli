# Stage 3-C Phase 4 Durability Inventory Classification Failure

> **Status:** FAIL preserved — corrected target rerun required
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase4-recovery-durability-inventory-results-20260712-014705.tgz`

## Result archive identity

```text
sha256
  eff7496fd6f9220d9b3a85a20298e8e3f95e4dd418c6a3b50695b1fc8329f235

size
  22,944,049 bytes

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

## Workflow result

```text
mutation_inventory          51
input_mutation               0
independent_verification   125

STAGE3C_PHASE4_RECOVERY_DURABILITY_INVENTORY=FAIL rc=51
```

The independent verifier was correctly blocked because the inventory scenario failed its `UNKNOWN=0` contract.

## Result index

```text
sha256
  5925eae91123ac462e109f933e089506b29b51c00a8c57c557c027df834f34ec

indexed files
  165

independent hash, size, and mode mismatches
  0
```

## Exact failed check

```text
unknown_categories_absent
  false

UNKNOWN rows
  2
```

All other 31 scenario checks passed.

## Exact unclassified call sites

```text
recovery_common.py
  function add_intent
  line 261
  persist_journal(transaction, journal)

recovery_common.py
  function mark_applied
  line 269
  persist_journal(transaction, journal)
```

Both calls are durable transaction checkpoint writes in the production recovery path:

```text
add_intent
  records mutation status INTENT before the filesystem primitive

mark_applied
  records mutation status APPLIED after the filesystem primitive
```

They therefore belong to the existing `transaction-metadata` category and must be included in the production integration plan.

## Observed inventory

```text
row count
  81

production rows before correction
  65

UNKNOWN rows
  2

expected production rows after correction
  67
```

The scanner detected the calls correctly. The defect was only that `CATEGORY_BY_FUNCTION` omitted the two checkpoint functions.

## Preserved successful boundaries

```text
Gate 4 scenario
  64/64 PASS

Gate 4 verifier
  53/53 PASS

Gate 4 workflow
  all return codes 0

Gate 4 result index
  exact

frozen recovery source blobs
  exact

inventory canonical JSON
  PASS

integration plan canonical JSON
  PASS

row sorting and anchor uniqueness
  PASS
```

## Input mutation

```text
input entries before/after
  173 / 173

input fingerprint before/after
  bbb95feb9aa861fd5f84bb845be1be4ce2f2745f8ba3434b0e5e5452b6d745c1

mutation check
  PASS
```

## Correction

Add exact classifications:

```python
("recovery_common.py", "add_intent"): "transaction-metadata"
("recovery_common.py", "mark_applied"): "transaction-metadata"
```

The `UNKNOWN=0` gate remains unchanged. No source blob, operation family, lifecycle behavior, recovery implementation, or durability obligation is weakened.

## Claim boundary

This failure proves that the inventory gate correctly rejected incomplete lifecycle classification. It does not indicate a failure in Gate 4 durability primitives or Gate 3 recovery behavior. It also does not prove integrated durability; Gate 5A remains pending a corrected target rerun.
