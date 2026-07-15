# Project Context: Stage 3-D Consumer Integration

> **Status:** Stage 3-D consumer integration frozen through Gate 5
> **Active boundary:** Gate 6 managed-Python feasibility remains deferred
> **Canonical branch:** `agent/stage3d-consumer-integration`
> **Gate 4 repository input:** `64a2066d464e437407bc84c85d21e3f04495d02a`, tree `2063517d5786ba179f71faa121e54c3e9b035239`

## Frozen foundation

Stage 2, Stage 3-A, Stage 3-B, and Stage 3-C through Gate 4E remain frozen. Stage 3-C accepts exact CPython 3.14.5 ↔ 3.14.6 transitions for runtime-only, runtime+development, runtime+test, and full topologies with 66/66 scenarios.

## Stage 3-D state

```text
Gate 1  scope and authority design             FROZEN
Gate 2  read-only Termux discovery census      FROZEN — 64/64, strict 12/12
Gate 3  system-Python integration contract     FROZEN
Gate 4  target implementation/validation       FROZEN — 48/48, independent 27/27
Gate 5  independent consumer-integration freeze FROZEN
Gate 6  managed-Python feasibility             deferred
```

## Gate 4 accepted authority

```text
archive sha256          13ed73fdeaf5ea13339b2df70b69a4c79aa2920fb1d9207229fb64db828b283c
archive size            58525
safe archive members    757
self-index              697/697 exact
scenario results        48/48 expectation match
harness completion      48/48
uv run                   8/8 exact product
uv sync                  8/8 exact product
transition continuity    4/4 exact
independent verification 27/27 PASS
uv                       0.11.28 (aarch64-linux-android)
```

The preserved v1 and v2 result archives remain part of the correction lineage. v1 exposed missing bounded working directories and an incomplete failure-path verifier. v2 completed 47/48 but X05 admitted the authoritative user-home virtual environment through physical working-directory ancestry. v3 retained the frozen matrix and inputs, added the documented `--system` isolation to X05, and passed all scenarios.

## Frozen system-Python consumer surface

The canonical exact selector is `<installed-prefix>/bin/python`. `uv python find`, `uv venv`, `uv run`, and `uv sync` are accepted for both frozen products and all four topologies with Python downloads, network access, and managed-Python fallback disabled. Exact interpreter identity is reprobed after selection.

Install-directory and unique executable names remain bounded secondary forms. PATH `python3.14`, request `3.14`, `.python-version`, and `requires-python` remain conditional compatibility surfaces rather than patch-exact selectors. Active virtual environments can outrank natural discovery; use `--system` when virtual-environment discovery is outside the intended test or workflow.

## Non-reopening boundary

No global `$PREFIX/bin/python*` links, shell startup edits, uv managed-install registration, Python download fallback, uv patching, product mutation, registry schema change, journal schema change, root, proot, Shizuku, or Docker is authorized. Gate 5 does not accept third-product compatibility or uv managed-Python feasibility.

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
  -> experiments/stage3d-consumer-integration/gate4-consumer-integration-authority.json
  -> experiments/stage3d-consumer-integration/verify-gate4-consumer-integration.py
  -> docs/evidence/STAGE3D_GATE4_CONSUMER_INTEGRATION_TARGET_VALIDATION_RESULT.md
  -> docs/handoff/STAGE3D_EVIDENCE_LEDGER.md
```

## Immediate next boundary

Stage 3-D is frozen through Gate 5. Gate 6 remains optional and deferred. Any managed-Python feasibility work requires a new authority decision and must not weaken the accepted system-Python contract or reopen frozen runtime, archive, ownership, transition, or consumer-integration behavior.
