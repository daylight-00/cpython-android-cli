# Stage 3-E Gate 3 Managed-Python Distribution Contract

> **Status:** CONTRACT FROZEN
> **Input:** accepted Gate 2 isolated dual-version target evidence and external 117/117 re-audit
> **Next boundary:** Gate 4 project-owned persistent-root implementation and lifecycle validation

## Canonical identity

One managed product is identified by the complete tuple:

```text
implementation + exact major.minor.patch + os + architecture + libc + immutable artifact hash
```

The accepted keys are:

```text
cpython-3.14.5-linux-aarch64-none
cpython-3.14.6-linux-aarch64-none
```

Exact patch-version requests are canonical. A successful minor or unspecified request is not an exact product selector.

## Selection contract

```text
3.14.5      exact CPython 3.14.5
3.14.6      exact CPython 3.14.6
3.14        conditional latest-patch alias; observed 3.14.6
unspecified conditional latest eligible managed interpreter; observed 3.14.6
```

Minor and unspecified requests may be used only where latest-patch behavior is intended. Workflows requiring frozen product identity must request the exact patch and re-probe interpreter identity.

## Catalog and artifact contract

Catalog rows and artifact bytes are separate authorities. Every row must contain an immutable SHA-256 and an exact key. A mutable endpoint cannot redefine an already accepted key without a new authority decision.

Publication mechanism, mirror policy, availability, signing, and network transport remain pending. Gate 3 accepts local immutable catalog/artifact binding only.

## Installation contract

Gate 4 begins with an explicit project-owned persistent managed root. The uv default managed directory, `$PREFIX/bin`, and shell startup files remain outside the first implementation boundary.

Installation must remain relocatable at the managed-root level, preserve Android interpreter identity, and expose no global executable unless a later authority explicitly accepts it.

## Lifecycle contract

Accepted isolated semantics:

```text
install exact key
coexist exact 3.14.5 and 3.14.6
exact reinstall is no-op identity
remove one exact version while preserving peer
remove final version to empty state
```

Persistent transaction recovery, interruption behavior, upgrade/downgrade, and residue handling require Gate 4 evidence and are not inferred from Gate 2.

## Coexistence contract

The Stage 3-D system-Python exact-path contract remains independent and frozen. Managed-Python state must not alter its products, selectors, registry, journal, or global paths. Existing Termux Python remains ambient system Python and is not relabeled as an HW-T managed product.

## Gate 4 selected implementation boundary

Gate 4 will validate both exact runtime-only products in one project-owned persistent root using explicit install directory and local immutable catalog/artifact inputs. It must include success, expected-negative, interrupted/failed operation preservation, peer-preserving uninstall, complete teardown, and rollback evidence.
