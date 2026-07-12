# Successor Session Handoff

Use these documents to continue the project without relying on prior chat context.

## Read in order

```text
1. COLLABORATION_PROTOCOL.md
2. PHASE5_GATE3A_PRODUCT_ACCEPTANCE_HANDOFF_20260712.md
3. ../../experiments/stage3c-installed-runtime-lifecycle/GATE3A_PRODUCT_ACCEPTANCE.md
4. ../evidence/STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_RESULT.md
5. ../stages/STAGE3C_PHASE5_SCOPE.md
6. STAGE3C_PHASE5_EVIDENCE_LEDGER.md
7. ../../experiments/stage3c-missing-leaf-repair-intervention/README.md

Historical intervention authority:
8. PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_HANDOFF_20260712.md
9. PHASE5_GATE3A_INTERVENTION_DECISION_20260712.md

Historical diagnostic authority:
10. ../evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
11. PHASE5_GATE3A_DIAGNOSTIC_HANDOFF_20260712.md
12. ../stages/STAGE3C_PHASE5_GATE3A_DIAGNOSTIC_SCOPE.md

Frozen Gate 2 evidence:
13. ../evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
14. PHASE5_GATE3_HANDOFF_20260712.md
```

## Current state

```text
Phase 5 Gate 1
  FROZEN 80/80

Phase 5 Gate 2
  FROZEN 46/46

Phase 5 Gate 3A0 diagnostic
  FROZEN 17/17 + 31/31

Phase 4I missing-leaf intervention
  FROZEN 39/39 + 51/51

Phase 5 Gate 3A product acceptance
  ACTIVE
  authoritative Termux run pending
```

## Frozen Phase 4I identity

```text
archive sha256
  d497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a

result-index sha256
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6
```

## Active Gate 3A topology

```text
isolated exact NOOP root       1
isolated repair roots          6
sequential repaired root       1
repair scenario checks        29
Gate 1 regression checks      80
acceptance verifier checks    69
```

The sequential root must pass:

```text
six repairs
registry byte identity
portable fingerprint f860caf... exact
strict shape/safety PASS
strict fingerprint unchanged across runtime probes
HTTPS 200
smoke-termux
uv venv and uv run
native closure 81/329/0
system SONAME 5/5
extension imports 67/67
zero transaction residue
```

The manifest source-tree fingerprint is not an installed strict fingerprint. Strict output includes mtime and is used only as a same-tree mutation control.

Gate 2 corrected-engine relocation regression remains a separate boundary.

## Authority rule

Only a complete independently inspected Termux TGZ can close Gate 3A product acceptance. Scenario-level PASS fields and console markers are insufficient.
