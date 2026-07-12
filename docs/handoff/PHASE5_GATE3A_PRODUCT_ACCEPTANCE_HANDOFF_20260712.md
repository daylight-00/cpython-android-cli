# Phase 5 Gate 3A Product Acceptance Handoff — 2026-07-12

> **Status:** FROZEN PASS
> **Accepted target:** Termux on Android arm64
> **Next boundary:** Gate 2R corrected-engine relocation regression

## Frozen ancestry

```text
Gate 1 installed-runtime baseline
  FROZEN 80/80

historical Gate 2 relocation
  FROZEN 46/46

Gate 3A0 diagnostic
  FROZEN 17/17 + 31/31

Phase 4I intervention
  FROZEN 39/39 + 51/51
```

## Frozen Gate 3A identity

```text
archive
  stage3c-phase5-gate3a-reinstall-repair-acceptance-results-20260712-191758.tgz

archive sha256
  16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142

result-index sha256
  a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128

repair scenario checks
  29/29

Gate 1 regression
  80/80

acceptance verifier
  69/69
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_RESULT.md
```

## Accepted product contract

```text
exact reinstall NOOP
six isolated repair classes
six sequential repair cycles
registry bytes unchanged after every repair
unaffected owned paths unchanged
portable fingerprint f860caf... exact
strict shape and safety PASS
zero transaction residue
```

Runtime contract:

```text
Python 3.14.6
Android aarch64
HTTPS 200
smoke-termux PASS
uv venv PASS
uv run anyio PASS
native closure 81/329/0
system SONAME 5/5
extension imports 67/67
engine verify 1 artifact / 714 owned rows / 0 bad paths
```

## Identity semantics

```text
portable fingerprint
  cross-root installed identity

strict installed fingerprint
  contains mtime_ns
  same-tree mutation control only

manifest source-tree fingerprint
  frozen contract identity
  not an installed strict fingerprint
```

## Preserved first-run failure

The first target run remains preserved as an infrastructure failure. All product-facing work and the Gate 1 regression passed, but the modular verifier failed before running checks under Python isolated mode.

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_FAILURE_20260712.md
```

## Next action

Continue from:

```text
docs/handoff/PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION_HANDOFF_20260712.md
```

Gate 2R must use a one-command Termux wrapper that verifies inputs, executes the full workflow, and packages evidence on PASS or FAIL.
