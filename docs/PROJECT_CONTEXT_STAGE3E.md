# Project Context: Stage 3-E Managed-Python Distribution

> **Status:** Stage 3-E frozen through Gate 5 independent distribution freeze
> **Active boundary:** Stage 3-E complete; broader publication and operations require a new stage authority
> **Canonical branch:** `agent/stage3e-managed-python-distribution`
> **Stage input:** `af930acdcbd5054733bfaa480d1eb18ecdc557bb`, tree `c0bb501656b82b4a43f94548e6080e993dabf974`
> **Gate 4 repository input:** `0b9ba82428f3ee15486fe689a5a8dd267ae399fe`, tree `6136a1a08b860b0572d768ce64ab3d357b783783`

## Frozen foundation

Stage 2, Stage 3-A, Stage 3-B, Stage 3-C through Gate 4E, and Stage 3-D through Gate 6 remain frozen. The Stage 3-D exact-path system-Python contract remains independent and production-safe; Stage 3-E does not replace or mutate it.

## Gate state

```text
Gate 1  authority and productization-boundary design    FROZEN
Gate 2  isolated dual-version boundary census           FROZEN — external re-audit 117/117
Gate 3  managed-Python distribution contract            FROZEN
Gate 4  project-owned persistent-root validation        FROZEN — target 37/37, independent 74/74
Gate 5  independent distribution freeze                 FROZEN
```

## Gate 4 correction lineage

The v1 target result passed 36/37 checks. Its backup bytes, paths, and symlink targets were correct, but non-root extraction applied the process umask and narrowed modes such as `0711 -> 0700` and `0666 -> 0600`. Strict candidate verification rejected that restore before any live-root swap, so the existing root remained intact and later peer lifecycle and teardown still completed.

The bounded v2 rerun retained every strict identity check and changed only backup extraction to preserve archived permissions. The accepted result is:

```text
archive sha256       4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112
archive size         54299
safe archive members 191
self-index            186/186 exact
target verifier       37/37 PASS
independent audit     74/74 PASS
independent audit sha 794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a
uv                     0.11.28 (aarch64-linux-android)
```

## Frozen Stage 3-E distribution surface

The accepted managed-Python surface is deliberately bounded:

```text
products
  CPython 3.14.5 runtime-only
  CPython 3.14.6 runtime-only

catalog
  exact immutable local rows
  cpython-3.14.5-linux-aarch64-none
  cpython-3.14.6-linux-aarch64-none

selection
  exact patch requests are authoritative
  minor and unspecified requests are conditional latest-patch aliases

installation
  explicit project-owned persistent managed root
  no uv default managed directory
  no global executable links or shell edits

lifecycle proved
  side-by-side install and exact discovery
  fresh-session re-entry
  uv virtual environments for both products
  managed-root relocation
  failed corrupt third-product install preserves existing products
  byte/mode/path/symlink-exact backup restoration
  candidate verification before atomic live-root replacement
  peer-preserving uninstall and exact reinstall
  final complete teardown and parent restoration
```

## Non-reopening and deferred boundary

Do not infer catalog publication, network or automatic downloads, uv default-root registration, `$PREFIX/bin/python*` exposure, shell integration, mutable endpoint policy, upgrade/downgrade, crash recovery, concurrent writer semantics, power-loss durability, third-product compatibility, or general upstream uv Android support. Those require a new stage authority and new target evidence.

## Current reading path

```text
README.md
  -> docs/PROJECT_CONTEXT_STAGE3E.md
  -> docs/stages/STAGE3E_SCOPE.md
  -> docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md
  -> experiments/stage3e-managed-python-distribution/GATE3_MANAGED_PYTHON_DISTRIBUTION_CONTRACT.md
  -> docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md
  -> experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json
  -> experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json
  -> experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md
  -> experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json
  -> docs/evidence/STAGE3E_FINAL_SUMMARY.md
  -> docs/PROJECT_CONTEXT_STAGE3D.md
  -> docs/session-operations/README.md
```

## Immediate next boundary

Stage 3-E is complete. Any move toward user-facing publication, the uv default managed root, global executable exposure, network mirrors, upgrades, recovery, concurrency, or durability must begin under a new stage authority rather than extending this freeze implicitly.
