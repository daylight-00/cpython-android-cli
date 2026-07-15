# Stage 3-D Scope: Consumer Integration

> **Status:** FROZEN — Gate 6 bounded managed-Python feasibility complete
> **Input:** frozen Stage 3-C Gate 4E exact two-product transition authority
> **Primary target:** Termux on Android arm64
> **Primary consumer:** uv using the installed interpreter as a system Python; bounded managed-Python research is secondary

## Stage question

How should the frozen CPython 3.14.5 and 3.14.6 products be exposed to uv without pretending that Android is an upstream uv-managed Python platform or reopening runtime, archive, ownership, and transition contracts?

The accepted answer is two-layered: the production-facing contract remains exact-path system Python, while Gate 6 proves only that one frozen CPython 3.14.5 runtime-only product can participate in an isolated custom-catalog uv managed lifecycle without uv patching or global mutation.

## Gate state

```text
Gate 1  scope and consumer authority design             FROZEN
Gate 2  read-only Termux consumer discovery census      FROZEN — 64/64
Gate 3  system-Python integration contract              FROZEN
Gate 4  target implementation and validation            FROZEN — 48/48
Gate 5  independent consumer-integration freeze         FROZEN — 27/27
Gate 6  bounded managed-Python feasibility research     FROZEN — A/B/C accepted
```

## Accepted system-Python consumer contract

The canonical selector is the absolute installed interpreter path. Exact identity is always reprobed. `uv python find`, `uv venv`, `uv run`, and `uv sync` are accepted across both products and all four frozen topologies with downloads, network access, and managed fallback disabled. Relocation and both frozen transition directions retain the exact-path contract.

Install-directory and unique-name requests are secondary controlled forms. Minor-version PATH, `.python-version`, and `requires-python` selection remain conditional and do not choose an exact patch when multiple eligible products are visible. Virtual environments discovered from the current directory or its ancestors can take precedence; `--system` is required when those environments must be excluded.

## Gate 4 evidence

The accepted v3 archive is safe and self-indexed, matches all 48 frozen scenarios, records 150 process results, proves 8/8 `uv run`, 8/8 `uv sync`, and 4/4 exact transition-continuity cases, and preserves repository, authority, global paths, managed-install state, and product bytes. The independent result verifier passes 27/27 checks.

The v1 and v2 archives are preserved as invalid-for-acceptance correction evidence. They are not substituted for or merged into the accepted v3 result.

## Gate 6 feasibility result

Gate 6-A proves that uv's built-in current-platform CPython 3.14 catalog is empty on the tested Android host and that a custom `cpython-3.14.5-linux-aarch64-none` entry is accepted. Gate 6-B proves isolated local-file install, managed discovery, exact Android interpreter identity, and uv venv creation. Gate 6-C proves exact-install no-op behavior, byte/mode/link preservation, clean uninstall, empty post-uninstall listing, and expected-negative managed discovery.

The explicit install command alone uses `UV_PYTHON_DOWNLOADS=manual`; all non-install commands use `never`. Every command remains offline, the archive URL is local `file://`, the install/cache/data paths are disposable and isolated, and global bin links are disabled.

## Prohibited mutations and claims

Do not create global interpreter links, edit shell startup files, register Android products in the real uv managed directory, enable automatic or network Python downloads, modify uv's built-in catalog, patch uv, modify canonical product bytes, change registry schema 1 or journal schema 2, or use root/proot/Shizuku/Docker.

This freeze does not accept a production managed catalog, persistent user installation, CPython 3.14.6 or multi-version managed operation, upgrade/downgrade policy, third-product compatibility, or a broader Android platform-support claim for upstream uv.

## Authoritative files

```text
experiments/stage3d-consumer-integration/gate2-consumer-census-authority.json
experiments/stage3d-consumer-integration/gate3-system-python-contract.json
experiments/stage3d-consumer-integration/gate4-consumer-integration-validation-matrix.json
experiments/stage3d-consumer-integration/gate4-consumer-integration-authority.json
experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json
experiments/stage3d-consumer-integration/verify-gate2-consumer-census.py
experiments/stage3d-consumer-integration/verify-gate3-system-python-contract.py
experiments/stage3d-consumer-integration/verify-gate4-consumer-integration.py
docs/evidence/STAGE3D_GATE4_CONSUMER_INTEGRATION_TARGET_VALIDATION_RESULT.md
docs/evidence/STAGE3D_GATE6_MANAGED_PYTHON_FEASIBILITY_RESULT.md
```
