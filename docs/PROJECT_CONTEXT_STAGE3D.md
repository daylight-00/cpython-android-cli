# Project Context: Stage 3-D Consumer Integration

> **Status:** Current handoff context
> **Active boundary:** Gate 4 target implementation and validation
> **Canonical branch:** `agent/stage3d-consumer-integration`
> **Current frozen repository input:** `b0b938b6f8d4eea67e2fac1eca83f69c835a9cac`, tree `3b86355f3236a850512e8e1bdb6b3e1df73362f5`

## Frozen foundation

Stage 2, Stage 3-A, Stage 3-B, and Stage 3-C through Gate 4E remain frozen. Gate 4 accepts exact CPython 3.14.5 ↔ 3.14.6 transitions for runtime-only, runtime+development, runtime+test, and full topologies with 66/66 scenarios.

## Stage 3-D state

```text
Gate 1  scope and authority design             FROZEN
Gate 2  read-only Termux discovery census      FROZEN — 64/64, strict 12/12
Gate 3  system-Python integration contract     FROZEN
Gate 4  target implementation/validation       ACTIVE NEXT
Gate 5  independent freeze                     pending
Gate 6  managed-Python feasibility             deferred
```

Gate 2 authority:

```text
archive sha256   4958b3e669950035f21baf5783fa54029366182cdc36ecf1fb909dfb8276e98c
archive size     61374
self-index       780/780 exact
uv               0.11.28 (aarch64-linux-android)
process records  172
```

## Frozen system-Python contract

The exact selector is `<installed-prefix>/bin/python`. `uv python find` uses system-only, offline, download-disabled, managed-disabled selection. `uv venv` receives the same absolute interpreter and must verify exact realpath, CPython implementation, patch version, Android platform, and base prefix.

Install-directory and unique executable names are bounded secondary forms. PATH `python3.14`, request `3.14`, `.python-version`, and `requires-python` are conditional compatibility surfaces, not patch-exact selectors. Active virtual environments can outrank natural discovery; use `--system` when that is not intended.

Gate 2 executed no `uv run` and no `uv sync`. Gate 4 must validate them before support can be claimed.

## Non-reopening boundary

No global `$PREFIX/bin/python*` links, shell startup edits, uv managed-install registration, Python download fallback, uv patching, product mutation, registry schema change, journal schema change, root, proot, Shizuku, or Docker is authorized.

## Current reading path

```text
README.md
  -> docs/PROJECT_CONTEXT_STAGE3D.md
  -> docs/stages/STAGE3D_SCOPE.md
  -> experiments/stage3d-consumer-integration/GATE2_READ_ONLY_CONSUMER_CENSUS.md
  -> experiments/stage3d-consumer-integration/gate2-consumer-census-authority.json
  -> experiments/stage3d-consumer-integration/GATE3_SYSTEM_PYTHON_INTEGRATION_CONTRACT.md
  -> experiments/stage3d-consumer-integration/gate3-system-python-contract.json
  -> experiments/stage3d-consumer-integration/gate4-consumer-integration-validation-matrix.json
  -> docs/evidence/STAGE3D_GATE2_READ_ONLY_CONSUMER_CENSUS_RESULT.md
  -> docs/evidence/STAGE3D_GATE3_SYSTEM_PYTHON_INTEGRATION_CONTRACT_RESULT.md
```

## Immediate next boundary

Implement and execute Gate 4 without modifying global links or managed-Python state. Preserve complete PASS-or-FAIL evidence and treat `uv run` and `uv sync` as unaccepted until target results are independently audited.
