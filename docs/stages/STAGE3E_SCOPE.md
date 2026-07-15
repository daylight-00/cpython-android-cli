# Stage 3-E Scope: Managed-Python Distribution

> **Status:** FROZEN — Gate 5 independent distribution freeze complete
> **Input:** frozen Stage 3-D Gate 6 feasibility and exact CPython 3.14.5/3.14.6 runtime-only products
> **Primary target:** Termux on Android arm64
> **Primary consumer:** uv managed-Python workflows for exact HW-T products

## Stage question

How should exact HW-T Android CPython products become a reproducible, persistent, multi-version managed-Python distribution without reopening frozen runtime, archive, ownership, transition, or system-Python authorities?

## Gate sequence

```text
Gate 1  authority and productization-boundary design    FROZEN
Gate 2  isolated dual-version boundary census           FROZEN — external re-audit 117/117
Gate 3  managed-Python distribution contract            FROZEN
Gate 4  project-owned persistent-root validation        FROZEN — target 37/37, independent 74/74
Gate 5  independent distribution freeze                 FROZEN
```

## Frozen result

Exact patch-version requests are canonical. Both exact runtime-only products coexist under one immutable local catalog and one explicit project-owned persistent root. Fresh-session discovery, direct launch, uv virtual environments, root relocation, failed-operation preservation, exact backup rollback, peer removal/reinstall, final teardown, and all protected-state invariants are accepted for the tested uv 0.11.28 Android host.

The accepted Gate 4 archive is `4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112`. It is safe and self-indexed with 191 members and 186/186 exact entries. The target verifier passes 37/37 and the independent freeze audit passes 74/74.

## Correction lineage

The v1 36/37 result is retained. Default tar extraction narrowed archived modes under the caller umask, and strict pre-swap comparison correctly rejected the candidate. The v2 rerun used permission-preserving extraction and passed the unchanged strict comparison and complete lifecycle.

## Proved

```text
local immutable exact-key catalog binding
exact 3.14.5 and 3.14.6 managed selection
conditional latest-patch minor/default alias behavior
project-owned explicit persistent root
process and fresh-session continuity
root-level relocation
failure preservation for a corrupt third artifact
mode/content/path/symlink-exact backup candidate verification
atomic live-root rollback after candidate acceptance
peer-preserving uninstall and exact reinstall
complete final teardown
repository, real managed root, global bin, shell, registry, journal, and product invariants
```

## Not proved

```text
uv default managed-root adoption
catalog or artifact network publication
automatic downloads or mutable endpoints
global executable links or shell integration
upgrade/downgrade and version-transition policy
crash, concurrent-writer, or power-loss recovery
third products or broader platform compatibility
upstream uv Android support
```

## Authoritative files

```text
docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md
experiments/stage3e-managed-python-distribution/GATE3_MANAGED_PYTHON_DISTRIBUTION_CONTRACT.md
experiments/stage3e-managed-python-distribution/gate3-managed-python-distribution-contract.json
docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md
experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json
experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json
experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md
experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json
docs/evidence/STAGE3E_FINAL_SUMMARY.md
```
