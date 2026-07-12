# Stage 3-C Phase 5 Gate 3A Diagnostic Scope

> **Status:** FROZEN DIAGNOSTIC PASS
> **Product acceptance:** BLOCKED
> **Next authority:** narrow Phase 4 missing-leaf repair intervention

## Frozen diagnostic identity

```text
archive
  stage3c-phase5-gate3a-reinstall-repair-diagnostic-results-20260712-172353.tgz

archive sha256
  9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2

result-index sha256
  a7507ab60de402a636c8e2899706aec77844896254f28dd068c8683dcb3dce7b

scenario checks
  17/17

independent verifier
  31/31

Phase 4 copied input
  324/324 exact
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
```

## Frozen classification matrix

```text
exact same-version reinstall            supported NOOP
regular byte mismatch                   supported repair
regular mode mismatch                   supported repair
symlink target mismatch                 supported repair
registered regular wrong type           supported repair
registered regular absent               unsupported
registered symlink absent               unsupported
```

## Confirmed missing-leaf sequence

```text
install                              rc 44 FileNotFoundError
journal before recovery              APPLYING
first recovery                       ROLLED_BACK, restored_count 0
retained journal                     ROLLED_BACK
second recovery                      NOOP_ROLLED_BACK
post-recovery verify                 same missing bad path
registry row                         retained
leaf                                 absent
```

## Architecture decision

Gate 3A product acceptance remains blocked. The defect is in the frozen registered non-directory repair execution path, which records a missing leaf as `replaced` and attempts to move a nonexistent source.

A narrow intervention is authorized in:

```text
docs/handoff/PHASE5_GATE3A_INTERVENTION_DECISION_20260712.md
```

The corrected missing-leaf path must reuse the existing `created` mutation and rollback semantics. No journal schema, registry schema, manifest, archive, ownership, uninstall, or addon-policy change is authorized.

## Claim boundary

The frozen diagnostic proves classification only. It does not prove missing-leaf repair or Gate 3A product acceptance.
