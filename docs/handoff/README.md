# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE5_GATE3B_PRODUCT_ACCEPTANCE_HANDOFF_20260712.md
3. ../../experiments/stage3c-installed-runtime-lifecycle/GATE3B_PRESERVATION_ACCEPTANCE.md
4. PHASE5_GATE3B0_PRESERVATION_DIAGNOSTIC_HANDOFF_20260712.md
5. ../evidence/STAGE3C_PHASE5_GATE3B0_PRESERVATION_DIAGNOSTIC_RESULT.md
6. ../stages/STAGE3C_PHASE5_SCOPE.md
7. STAGE3C_PHASE5_EVIDENCE_LEDGER.md
```

## Current state

```text
Phase 5 Gate 1
  FROZEN 80/80

Phase 5 historical Gate 2
  FROZEN 46/46

Phase 5 Gate 3A0 diagnostic
  FROZEN 17/17 + 31/31

Phase 4I missing-leaf intervention
  FROZEN 39/39 + 51/51

Phase 5 Gate 3A product acceptance
  FROZEN 29/29 + 80/80 + 69/69

Phase 5 Gate 2R corrected-engine relocation
  FROZEN 80/80 + 46/46 + 15/15

Phase 5 Gate 3B0 preservation diagnostic
  FROZEN 16/16 + 40/40

Phase 5 Gate 3B preserve-and-report product acceptance
  ACTIVE
  authoritative Termux run pending
```

## Frozen Gate 3B0 identity

```text
archive sha256
  ed5cb08cc576e74cacac4077cf9c9d7f3164a34913197aae9ef10cc8c113801a

result-index sha256
  7a8e982a44118dac3f232b2fefb578d22bedc0c7d32a6267ab3cd55c5e8deb27
```

Frozen census:

```text
registered mismatch + reinstall
  ENFORCED_REPAIR

unowned sentinel + reinstall
  PRESERVED_NOOP

modified registered leaf + uninstall
  PRESERVED_AND_DEREGISTERED

unowned sentinel + uninstall
  UNOWNED_PRESERVED
```

The frozen installation contract explicitly specifies preserve-and-report, remove-owned-directory-only-when-empty, preserve structural namespaces, and preserve unowned descendants. No intervention is required.

## Active Gate 3B topology

```text
happy reinstall roots          4
happy uninstall roots          4
crash-recovery roots          12
total inode-separated roots   20
scenario checks               29
independent checks            62
```

Crash boundaries:

```text
PREPARED                 rc 90
late APPLYING            rc 93
COMMITTED                rc 92
```

Late APPLYING uses the registry-intent ordinal:

```text
happy mutation_count
+ preserved registered-directory count
```

It does not use `mutation_count - 1`.

## Acceptance requirements

```text
exact preserved-path reporting
modified-leaf residual identity
unowned sentinel residual identity
registry 1/714 → 0/0
matching owned paths removed
only approved parent directories preserved
transaction residue 0
pre-commit rollback
committed recovery
idempotent second recovery
reinstall enforcement regressions
```

## Identity boundary

Registry-owned identity and residual identity are separate evidence surfaces. An unowned child must not be treated as a mutation of an owned directory whose registry identity is type and mode only.

## Termux execution policy

All target-only workflows must use one wrapper that verifies accepted inputs, performs fresh extraction, executes the workflow, captures logs synchronously, writes status and result indices, and packages a TGZ on PASS or FAIL.

## Authority rule

Only a complete independently inspected Termux TGZ can close Gate 3B. Console markers and scenario-level `pass` fields are insufficient.
