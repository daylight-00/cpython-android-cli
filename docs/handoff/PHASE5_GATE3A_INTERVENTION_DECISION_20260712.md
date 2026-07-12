# Phase 5 Gate 3A Intervention Decision — 2026-07-12

> **Decision:** authorize a narrow Phase 4 engine intervention for missing registered non-directory repair.
> **Gate 3A product acceptance:** remains blocked until corrected target evidence passes.

## Confirmed defect

Authoritative Gate 3A0 Termux evidence proves that a registered missing regular or symlink leaf cannot be repaired by the frozen engine.

Current sequence:

```text
registry row exists
actual path absent
planner chooses repair
journal records replaced intent
durable_move(absent source, backup)
FileNotFoundError
journal remains APPLYING
recovery marks ROLLED_BACK with restored_count 0
leaf remains absent
registry row remains present
```

Accepted diagnostic archive:

```text
stage3c-phase5-gate3a-reinstall-repair-diagnostic-results-20260712-172353.tgz
sha256
  9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
```

## Authorized intervention

Only the registered non-directory repair execution path may change.

Required distinction:

```text
registered path exists and differs
  mutation kind replaced
  move existing path to backup
  publish frozen archive member

registered path is absent
  mutation kind created
  do not move a nonexistent source
  publish frozen archive member
```

The existing `created` rollback semantics must be reused. No new journal schema or recovery operation is authorized.

## Required crash boundaries

Corrected missing-leaf repair must be tested at least at:

```text
prepared before intents
created intent recorded but not applied
published leaf applied before registry mutation
registry mutation applied before commit
committed before transaction cleanup
```

Required recovery outcomes:

```text
before commit
  restore the original missing state and prior registry

after commit
  preserve the repaired leaf and committed registry

successful repair
  exact manifest identity
  no active or retained transaction residue
```

## Non-authorized changes

```text
manifest changes
archive changes
registry schema changes
artifact identity changes
ownership policy changes
uninstall behavior changes
addon dependency changes
new generic repair engine
```

## Authority reopening

The intervention reopens only the affected Phase 4 transaction/recovery/durability claim for registered missing non-directory repair.

The following remain frozen unless evidence shows a direct impact:

```text
Phase 1 product identity
Phase 2 contract derivation
Phase 3 manifests and archives
existing in-place repair semantics
uninstall preservation policy
Gate 1 portable payload identity
Gate 2 relocation semantics
```

## Mandatory revalidation order

```text
1. local static and synthetic recovery validation
2. Termux missing-leaf intervention scenarios
3. corrected Gate 3A reinstall/repair product acceptance
4. Gate 1 installed-runtime regression
5. Gate 2 relocation regression where the engine input identity changed
6. only then open Gate 3B
```

A downstream gate may reuse prior evidence only if its accepted input identity and exercised code path are proven unaffected. Otherwise it must be rerun.

## Successor action

Create a dedicated intervention branch from the diagnostic merge commit. Modify the minimum engine lines, add explicit missing regular and missing symlink success and crash-recovery scenarios, preserve the diagnostic failure evidence, and keep the corrective PR draft until authoritative Termux TGZ evidence is inspected.
