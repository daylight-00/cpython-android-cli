# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE5_GATE3B0_PRESERVATION_DIAGNOSTIC_HANDOFF_20260712.md
3. ../../experiments/stage3c-installed-runtime-lifecycle/GATE3B0_PRESERVATION_DIAGNOSTIC.md
4. ../evidence/STAGE3C_PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION_RESULT.md
5. PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION_HANDOFF_20260712.md
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
  ACTIVE
  authoritative Termux run pending
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

## Active Gate 3B0 topology

```text
corrected-engine seed roots        1
eight inode-separated scenarios    8
scenario checks                   16
independent checks                40
```

Current-behavior census:

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

This is diagnostic classification only. No preservation policy or uninstall product contract is accepted.

## Identity boundary

Registry-owned identity and unowned sentinel identity are separate evidence surfaces. An unowned child must not be treated as a mutation of an owned directory whose registry identity is only type and mode.

## Termux execution policy

All target-only workflows must use one wrapper that verifies accepted inputs, performs fresh extraction, executes the workflow, captures logs synchronously, writes status and result indices, and packages a TGZ on PASS or FAIL.

## Authority rule

Only a complete independently inspected Termux TGZ can close Gate 3B0. Console markers and scenario-level `pass` fields are insufficient.
