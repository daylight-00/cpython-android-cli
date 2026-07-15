# Project Context: Stage 3-D Consumer Integration

> **Status:** Current handoff context
> **Active boundary:** Gate 2 read-only Termux consumer discovery census
> **Canonical branch:** `agent/stage3d-consumer-integration`
> **Frozen input branch/commit:** `agent/phase5-gate4-second-product-authority` at `68b67dcc3b65872e1034c487747d3fcd1ad5a319`

## Project identity

```text
A CLI adaptation of upstream CPython Android builds for Termux,
with uv integration and an evidence-driven distribution lifecycle.
```

## Frozen foundation

```text
Stage 2    launcher and runtime architecture             FROZEN
Stage 3-A  runtime closure                               FROZEN
Stage 3-B  reproducible producer/product authority       FROZEN
Stage 3-C  archives, ownership, lifecycle, transition    FROZEN through Gate 4E
```

Gate 4 exact authority:

```text
products         CPython 3.14.5 and 3.14.6
artifact roles   runtime-base, development-addon, test-addon
topologies       runtime-only, runtime+development, runtime+test, full
matrix           66/66 PASS
Gate 4E commit   68b67dcc3b65872e1034c487747d3fcd1ad5a319
Gate 4E tree     2115f6fa3b923c9fcf21a1b8343cb6149afb6cc7
```

The preserved Gate 4D v1 FAIL archive and corrective v2 PASS archive are both part of the authority. The v1 false negatives were not overwritten.

## Current Stage 3-D decision

Stage 3-D begins with uv's **system Python** model. The project runtime was not installed by uv, so it is a system Python under uv terminology. The canonical control remains explicit absolute interpreter selection.

```text
Gate 1  scope and authority design             FROZEN
Gate 2  read-only Termux discovery census      ACTIVE NEXT
Gate 3  system integration contract            pending
Gate 4  target implementation/validation       pending
Gate 5  independent freeze                     pending
Gate 6  managed-Python feasibility             deferred
```

Managed-Python emulation is not accepted. Android is not listed in upstream uv's documented platform tiers, and uv's managed CPython distributions are based on bundled `python-build-standalone` downloads for its supported desktop/server platforms.

## Gate 2 scope

Gate 2 executes 64 isolated scenarios over both products and all four topologies. It observes:

```text
explicit executable paths and names
install-directory requests
PATH discovery names
version and implementation requests
.python-version and requires-python
uv python find
uv venv, uv run, uv sync
virtual-environment precedence
system/managed preference controls
negative and incompatible requests
both frozen transition directions
```

All Python downloads are disabled. No scenario may alter `$PREFIX/bin`, shell startup files, uv's managed installation directory, canonical product archives, registry schema 1, journal schema 2, or frozen transition behavior.

## Required Gate 2 evidence

```text
exact uv identity and Termux environment
exact product/topology and interpreter identity
request flags and configuration environment
stdout, stderr, exit code
selected interpreter and realpath
queried implementation/version/platform metadata
repository and installation pre/post invariants
one safe self-indexed .tar.zst result archive
```

A successful observation does not become product policy automatically. Gate 3 chooses the supported integration surface only after Gate 2 is independently audited.

## Collaboration and transport

Repository writes, commit, push, and target execution occur through the user's Termux local Git and one runner. GitHub connector/API operations are not part of this workflow. Agent/user exchange normally uses one `.tar.zst` per direction through Google Drive. New commits use local Git identity:

```text
daylight-00 <hwjang00@snu.ac.kr>
```

The runner uses `git commit -s`; the signoff trailer is not manually duplicated.

## Current reading path

```text
README.md
  -> docs/PROJECT_CONTEXT_STAGE3D.md
  -> docs/stages/STAGE3D_SCOPE.md
  -> experiments/stage3d-consumer-integration/GATE1_CONSUMER_AUTHORITY_DESIGN.md
  -> experiments/stage3d-consumer-integration/gate1-consumer-authority.json
  -> experiments/stage3d-consumer-integration/gate2-consumer-discovery-matrix.json
  -> docs/evidence/STAGE3D_GATE1_CONSUMER_AUTHORITY_DESIGN_RESULT.md
  -> docs/GITHUB_COLLABORATION_WORKFLOW.md
  -> docs/handoff/COLLABORATION_PROTOCOL.md
```

`docs/PROJECT_CONTEXT_STAGE3C.md` is the historical frozen Stage 3-C snapshot.

## Immediate next boundary

Prepare and execute Gate 2 as a read-only Termux census. Do not create global interpreter links or managed-Python metadata before the census is accepted.
