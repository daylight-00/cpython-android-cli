# Project Context: Stage 3-E Managed-Python Distribution

> **Status:** Stage 3-E active — Gate 3 managed-Python distribution contract frozen
> **Active boundary:** Gate 4 project-owned persistent managed-root implementation and lifecycle validation
> **Canonical branch:** `agent/stage3e-managed-python-distribution`
> **Stage input:** `af930acdcbd5054733bfaa480d1eb18ecdc557bb`, tree `c0bb501656b82b4a43f94548e6080e993dabf974`

## Frozen foundation

Stage 2, Stage 3-A, Stage 3-B, Stage 3-C through Gate 4E, and Stage 3-D through Gate 6 remain frozen. The Stage 3-D system-Python contract remains the production-safe consumer surface and is not replaced by Stage 3-E.

## Gate state

```text
Gate 1  authority and productization-boundary design    FROZEN
Gate 2  isolated dual-version boundary census           FROZEN — external re-audit 117/117
Gate 3  managed-Python distribution contract            FROZEN
Gate 4  target implementation and lifecycle validation  ACTIVE NEXT
Gate 5  independent distribution freeze                 pending
```

## Gate 2 accepted observation

The accepted target result is the preserved v2 archive `3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2`. Its original verifier returned false because it tested three invalid assumptions:

```text
catalog preflight
  uv python list observed ambient system Python rather than the custom downloadable catalog
  both exact install successes independently prove both custom keys were accepted

minor/default selection
  verifier required an exact-key directory path
  uv returned cpython-3.14-linux-aarch64-none, the canonical minor alias
  installed-list output maps that alias to CPython 3.14.6 in both install orders

real-state snapshots
  verifier ran before after.txt was created
  the archived before.txt and after.txt are byte-identical
```

An independent external re-audit passes 117/117 checks. Both exact products install side by side in either order, retain Android identity, create and run uv virtual environments, preserve exact reinstall manifests, survive peer removal, uninstall cleanly, and leave real repository, managed, global-bin, shell, registry, journal, and product state unchanged.

Observed selection is order-independent:

```text
exact 3.14.5    -> cpython-3.14.5-linux-aarch64-none
exact 3.14.6    -> cpython-3.14.6-linux-aarch64-none
minor 3.14      -> cpython-3.14-linux-aarch64-none alias -> 3.14.6
unspecified     -> cpython-3.14-linux-aarch64-none alias -> 3.14.6
installed list -> 3.14.6, then 3.14.5
```

## Gate 3 frozen contract

Exact patch-version catalog keys and exact version requests are the authoritative managed-Python selectors. Minor and unspecified requests resolve to uv's latest-patch minor alias and are conditional convenience surfaces, not patch-exact selectors.

Each catalog key must bind one immutable artifact identity. Catalog metadata, artifact bytes, installation root, executable exposure, and lifecycle policy remain separate authorities. The system-Python exact-path contract continues to coexist independently.

Gate 4 begins with a project-owned persistent managed root supplied through an explicit install directory. It does not begin in uv's default real managed directory and does not create `$PREFIX/bin/python*` links or shell edits.

## Non-reopening boundary

Do not modify canonical product bytes, Stage 3-C registry or journal schemas, the Stage 3-D system-Python selector contract, uv source or built-in catalog, the default real uv managed directory, `$PREFIX/bin/python*`, or shell startup files. Network distribution, catalog publication, crash recovery, upgrade/downgrade, global executable exposure, and upstream uv Android-support claims remain unaccepted.

## Current reading path

```text
README.md
  -> docs/PROJECT_CONTEXT_STAGE3E.md
  -> docs/stages/STAGE3E_SCOPE.md
  -> docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md
  -> experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json
  -> experiments/stage3e-managed-python-distribution/GATE3_MANAGED_PYTHON_DISTRIBUTION_CONTRACT.md
  -> experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json
  -> docs/PROJECT_CONTEXT_STAGE3D.md
  -> docs/session-operations/README.md
```

## Immediate next boundary

Design Gate 4 as a bounded Termux target validation against one project-owned persistent managed root. Validate installation, coexistence, exact selection, virtual environments, peer-preserving uninstall, complete teardown, failure preservation, and rollback without using the default uv managed directory or global links.
