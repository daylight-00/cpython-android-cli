# Stage 3-D Scope: Consumer Integration

> **Status:** FROZEN — Gate 5 independent consumer-integration freeze complete
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
Gate 4  target implementation and validation            FROZEN — 48/48
Gate 5  independent consumer-integration freeze         FROZEN — 27/27
Gate 6  optional managed-Python feasibility research    deferred
```

## Accepted consumer-integration contract

The canonical selector is the absolute installed interpreter path. Exact identity is always reprobed. `uv python find`, `uv venv`, `uv run`, and `uv sync` are accepted across both products and all four frozen topologies with downloads, network access, and managed fallback disabled. Relocation and both frozen transition directions retain the exact-path contract.

Install-directory and unique-name requests are secondary controlled forms. Minor-version PATH, `.python-version`, and `requires-python` selection remain conditional and do not choose an exact patch when multiple eligible products are visible. Virtual environments discovered from the current directory or its ancestors can take precedence; `--system` is required when those environments must be excluded.

## Gate 4 evidence

The accepted v3 archive is safe and self-indexed, matches all 48 frozen scenarios, records 150 process results, proves 8/8 `uv run`, 8/8 `uv sync`, and 4/4 exact transition-continuity cases, and preserves repository, authority, global paths, managed-install state, and product bytes. The independent result verifier passes 27/27 checks.

The v1 and v2 archives are preserved as invalid-for-acceptance correction evidence. They are not substituted for or merged into the accepted v3 result.

## Prohibited mutations and claims

Do not create global interpreter links, edit shell startup files, register Android products in uv's managed directory, permit Python downloads, patch uv, modify canonical product bytes, change registry schema 1 or journal schema 2, or use root/proot/Shizuku/Docker. This freeze does not accept managed-Python feasibility, third-product compatibility, or a broader Android platform-support claim for upstream uv.

## Authoritative files

```text
experiments/stage3d-consumer-integration/gate2-consumer-census-authority.json
experiments/stage3d-consumer-integration/gate3-system-python-contract.json
experiments/stage3d-consumer-integration/gate4-consumer-integration-validation-matrix.json
experiments/stage3d-consumer-integration/gate4-consumer-integration-authority.json
experiments/stage3d-consumer-integration/verify-gate2-consumer-census.py
experiments/stage3d-consumer-integration/verify-gate3-system-python-contract.py
experiments/stage3d-consumer-integration/verify-gate4-consumer-integration.py
docs/evidence/STAGE3D_GATE4_CONSUMER_INTEGRATION_TARGET_VALIDATION_RESULT.md
```
