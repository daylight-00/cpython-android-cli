# Project Context: Stage 3-D Consumer Integration

> **Status:** Stage 3-D frozen through Gate 6 bounded managed-Python feasibility
> **Active boundary:** Stage 3-D complete; production managed-Python distribution requires a new stage authority
> **Canonical branch:** `agent/stage3d-consumer-integration`
> **Gate 6 repository input:** `9d70ea1d3468ed02fa9684f61609c2cb5caf4ebc`, tree `fade17abba57b38f99c87368efc96b4e0aaa930a`

## Frozen foundation

Stage 2, Stage 3-A, Stage 3-B, and Stage 3-C through Gate 4E remain frozen. Stage 3-C accepts exact CPython 3.14.5 ↔ 3.14.6 transitions for runtime-only, runtime+development, runtime+test, and full topologies with 66/66 scenarios.

## Stage 3-D state

```text
Gate 1  scope and authority design              FROZEN
Gate 2  read-only Termux discovery census       FROZEN — 64/64, strict 12/12
Gate 3  system-Python integration contract      FROZEN
Gate 4  target implementation/validation        FROZEN — 48/48, independent 27/27
Gate 5  independent consumer-integration freeze FROZEN
Gate 6  bounded managed-Python feasibility      FROZEN — A/B/C accepted
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

## Gate 6 bounded managed-Python feasibility

Gate 6 answers a narrower research question without weakening the system-Python contract. On uv `0.11.28 (aarch64-linux-android)`, the built-in current-platform catalog exposes no CPython 3.14 download for the Android host, while the all-platform catalog contains Linux aarch64 GNU and musl entries but no `linux-aarch64-none` entry. A custom downloads JSON entry keyed as `cpython-3.14.5-linux-aarch64-none` is accepted as a current-platform candidate.

Using a local `file://` archive, an isolated `--install-dir`, isolated cache/data directories, `--no-bin`, offline mode, and `UV_PYTHON_DOWNLOADS=manual` only for the explicit install command, uv successfully installs and discovers the exact CPython 3.14.5 runtime-only product. The installed interpreter retains Android identity (`SOABI=cpython-314-aarch64-linux-android`, `MULTIARCH=aarch64-linux-android`), creates and runs a uv virtual environment, treats a second exact install as a no-op with byte/mode/link identity preserved, uninstalls cleanly, and then returns the expected managed-discovery failure.

Repository state, the real uv managed-install directory, `$PREFIX/bin`, shell startup files, and frozen product inputs remain unchanged. Gate 6 accepts feasibility only for this exact isolated local-catalog experiment.

## Non-reopening boundary

No global `$PREFIX/bin/python*` links, shell startup edits, production uv managed-install registration, automatic or network Python downloads, built-in catalog modification, uv patching, product mutation, registry schema change, journal schema change, root, proot, Shizuku, or Docker is authorized. Gate 6 does not accept a production catalog/distribution design, persistent user installation, CPython 3.14.6 or multi-version managed operation, upgrade policy, third-product compatibility, or a general upstream uv Android-support claim.

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
  -> experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json
  -> docs/evidence/STAGE3D_GATE6_MANAGED_PYTHON_FEASIBILITY_RESULT.md
  -> docs/handoff/STAGE3D_EVIDENCE_LEDGER.md
```

## Immediate next boundary

Stage 3-D is complete. Any persistent or user-facing managed-Python integration must open a new stage with explicit authority for catalog publication, artifact transport, global or user-level installation paths, multi-version behavior, upgrades, recovery, and coexistence with the frozen system-Python contract.
