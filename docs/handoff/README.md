# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION_HANDOFF_20260712.md
3. ../evidence/STAGE3C_PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION_RESULT.md
4. ../stages/STAGE3C_PHASE5_SCOPE.md
5. STAGE3C_PHASE5_EVIDENCE_LEDGER.md
6. ../evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_RESULT.md
7. PHASE5_GATE3A_PRODUCT_ACCEPTANCE_HANDOFF_20260712.md
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

Phase 5 Gate 3B preservation boundaries
  ACTIVE
```

## Frozen Gate 2R identity

```text
archive sha256
  8e2c131567d78a4208e7c8eb02e783a479713f6d867a3e5cd98eae60aa5738a7

result-index sha256
  69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c

complete-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30

portable fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978
```

## Active Gate 3B target

```text
modified owned regular leaf
modified owned symlink
unowned sentinel file
unowned sentinel directory
install/repair enforcement versus uninstall preservation
registry and transaction state
full runtime revalidation where applicable
```

Policy must be derived from the frozen transaction contract rather than assumed.

## Termux execution policy

All target-only workflows must use one wrapper that verifies accepted inputs, performs fresh extraction, executes the workflow, captures status and result indices, and packages a TGZ on PASS or FAIL. Log capture must be synchronous before packaging.

## Authority rule

Only a complete independently inspected Termux TGZ can close an active target gate. Console markers and scenario-level `pass` fields are insufficient.
