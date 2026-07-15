# Stage 3-D Scope: Consumer Integration

> **Status:** ACTIVE — Gate 3 system-Python contract frozen; Gate 4 next
> **Input:** frozen Stage 3-C Gate 4E exact two-product transition authority
> **Primary target:** Termux on Android arm64
> **Primary consumer:** uv using the installed interpreter as a system Python

## Stage question

How should the frozen CPython 3.14.5 and 3.14.6 products be exposed to uv without pretending that Android is an upstream uv-managed Python platform or reopening runtime, archive, ownership, and transition contracts?

## Gate state

```text
Gate 1  scope and consumer authority design             FROZEN
Gate 2  read-only Termux consumer discovery census      FROZEN — 64/64
Gate 3  system-Python integration contract              FROZEN
Gate 4  target implementation and validation            ACTIVE NEXT — 48 scenarios
Gate 5  independent consumer-integration freeze         pending
Gate 6  optional managed-Python feasibility research    deferred
```

## Accepted Gate 3 contract

The canonical selector is the absolute installed interpreter path. Exact identity is always reprobed. `uv python find` and `uv venv` are accepted with downloads and managed fallback disabled. Relocation and both frozen transition directions retain this exact-path contract.

Install-directory and unique-name requests are secondary controlled forms. Minor-version PATH, `.python-version`, and `requires-python` selection are conditional and do not choose an exact patch when multiple eligible products are visible.

## Gate 4 requirements

The tracked 48-scenario matrix must cover explicit reconfirmation, `uv run`, `uv sync`, bounded discovery, transition continuity, precedence, negative requests, and invariants. A command unsupported by the observed uv build must produce an explicit preflight rejection rather than a fabricated PASS.

## Prohibited mutations and claims

Do not create global interpreter links, edit shell startup files, register Android products in uv's managed directory, permit Python downloads, patch uv, modify canonical product bytes, change registry schema 1 or journal schema 2, or use root/proot/Shizuku/Docker. `uv run` and `uv sync` remain unaccepted until Gate 4 evidence exists.

## Authoritative files

```text
experiments/stage3d-consumer-integration/gate2-consumer-census-authority.json
experiments/stage3d-consumer-integration/gate3-system-python-contract.json
experiments/stage3d-consumer-integration/gate4-consumer-integration-validation-matrix.json
experiments/stage3d-consumer-integration/verify-gate2-consumer-census.py
experiments/stage3d-consumer-integration/verify-gate3-system-python-contract.py
```
