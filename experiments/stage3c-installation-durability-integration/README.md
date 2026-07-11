# Stage 3-C Phase 4: Recovery Durability Integration Inventory

> **Status:** ACTIVE — checkpoint classification corrected; target rerun pending
> **Input:** frozen Phase 4 Gate 4 durability result

## Run

```sh
bash experiments/stage3c-installation-durability-integration/run-recovery-durability-inventory.sh
```

## Purpose

Inventory every detected filesystem mutation and `fsync` call in the exact frozen Gate 3 recovery-engine sources before changing those sources.

The inventory is source-identity-bound and fails if:

```text
one frozen source blob changes
one detected call has no lifecycle category
one production call has no durability obligation
one call-site anchor is duplicated or omitted
Gate 4 input changes
```

## Preserved failed attempt

The first target run correctly failed because two durable journal checkpoint calls were detected but not classified:

```text
recovery_common.py:add_intent
  persist_journal(transaction, journal)

recovery_common.py:mark_applied
  persist_journal(transaction, journal)
```

Both are now explicitly classified as production `transaction-metadata`. The `UNKNOWN=0` requirement remains unchanged.

Failure evidence:

```text
docs/evidence/STAGE3C_PHASE4_DURABILITY_INVENTORY_CLASSIFICATION_FAILURE.md
```

## Source set

```text
recovery_common.py
recovery_operations.py
recovery_engine.py
```

## Outputs

```text
mutation-inventory.json
integration-plan.json
scenario.json
verification.json
workflow-status.json
result-index.json
```

## Checks

```text
inventory scenario       32/32
independent verifier     29/29
unknown categories        0
input mutation          PASS
```

The corrected inventory is expected to retain:

```text
all detected rows        81
production rows          67
transaction-metadata     10
```

## Expected markers

```text
STAGE3C_PHASE4_DURABILITY_INTEGRATION_INVENTORY=PASS
RECOVERY_DURABILITY_INVENTORY_ACCEPTED_INPUTS=PASS
RECOVERY_DURABILITY_INVENTORY_SCENARIO=32/32 PASS
RECOVERY_DURABILITY_INVENTORY_VERIFICATION=29/29 PASS
RECOVERY_DURABILITY_INVENTORY_SOURCE_BLOBS=PASS
RECOVERY_DURABILITY_INVENTORY_UNKNOWN_CALLS=0 PASS
RECOVERY_DURABILITY_INVENTORY_INPUT_MUTATION_CHECK=PASS
STAGE3C_PHASE4_RECOVERY_DURABILITY_INVENTORY=PASS
```

## Results

```text
results/termux/stage3c-phase4-recovery-durability-inventory/
```

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase4-recovery-durability-inventory"
ARCHIVE="$HOME/Downloads/stage3c-phase4-recovery-durability-inventory-corrected-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

The bundle contains the self-contained Gate 4 evidence and can be large.

## Claim boundary

A PASS proves inventory completeness only for the exact frozen source blobs and the scanner's declared mutation families. It does not prove integrated durability. The implementation gate must still replay `55/82` recovery behavior and `64/53` durability behavior after applying the generated plan.
