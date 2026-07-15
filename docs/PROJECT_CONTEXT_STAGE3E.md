# Project Context: Stage 3-E Managed-Python Distribution

> **Status:** Stage 3-E active — Gate 1 authority design frozen
> **Active boundary:** Gate 2 isolated dual-version managed-Python boundary census
> **Canonical branch:** `agent/stage3e-managed-python-distribution`
> **Stage input:** `c4f0333db196b7bf0e074b9556d566e0d33c91aa`, tree `593695ee66270cb9f496df10bef624717ba7fc98`

## Frozen foundation

Stage 2, Stage 3-A, Stage 3-B, Stage 3-C through Gate 4E, and Stage 3-D through Gate 6 remain frozen. Stage 3-D preserves two distinct authorities:

```text
system-Python consumer integration
  CPython 3.14.5 and 3.14.6
  runtime-only, runtime+development, runtime+test, full
  uv python find, uv venv, uv run, uv sync

bounded managed-Python feasibility
  CPython 3.14.5 runtime-only only
  custom cpython-3.14.5-linux-aarch64-none catalog entry
  local file:// archive
  isolated install, discovery, launch, venv, exact no-op reinstall, uninstall
```

The feasibility result does not authorize production distribution.

## Stage question

How can exact HW-T Android CPython products be distributed and maintained through uv's managed-Python machinery without weakening the frozen system-Python contract or silently inventing upstream Android platform support?

## Gate state

```text
Gate 1  authority and productization-boundary design    FROZEN
Gate 2  isolated dual-version boundary census           ACTIVE NEXT
Gate 3  managed-Python distribution contract            pending
Gate 4  target implementation and lifecycle validation  pending
Gate 5  independent distribution freeze                 pending
```

## Gate 1 decision

The first target boundary remains isolated and offline. Gate 2 will construct one exact custom catalog containing the frozen CPython 3.14.5 and 3.14.6 runtime-only products and exercise side-by-side behavior only inside disposable install, cache, configuration, and data directories.

Gate 2 must observe:

```text
catalog recognition for both exact linux-aarch64-none keys
install order 3.14.5 -> 3.14.6 and 3.14.6 -> 3.14.5
installed list and exact-version discovery
minor-version and unspecified selection behavior
one-version uninstall while the peer remains usable
exact reinstall/no-op behavior for each product
interpreter identity and uv venv execution for both products
absence of writes to real managed, global-bin, shell, registry, and product state
```

Gate 2 does not publish a catalog, use network acquisition, or create a persistent user installation.

## Non-reopening boundary

Do not modify the Stage 3-D system-Python selector contract, canonical product bytes, Stage 3-C registry or journal schemas, the real uv managed directory, `$PREFIX/bin/python*`, or shell startup files. Do not patch uv, use root/proot/Shizuku/Docker, enable automatic Python downloads, or claim production recovery and upgrade behavior from an isolated census.

## Current reading path

```text
README.md
  -> docs/PROJECT_CONTEXT_STAGE3E.md
  -> docs/stages/STAGE3E_SCOPE.md
  -> experiments/stage3e-managed-python-distribution/GATE1_AUTHORITY_DESIGN.md
  -> experiments/stage3e-managed-python-distribution/gate1-authority.json
  -> docs/PROJECT_CONTEXT_STAGE3D.md
  -> experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json
  -> docs/evidence/STAGE3D_GATE6_MANAGED_PYTHON_FEASIBILITY_RESULT.md
  -> docs/session-operations/README.md
```

## Immediate next boundary

Design and execute Gate 2 as one bounded Termux target package. Preserve complete PASS-or-FAIL evidence, use both exact frozen runtime-only products, keep all managed-Python state disposable, and treat every production or persistent behavior as unaccepted.
