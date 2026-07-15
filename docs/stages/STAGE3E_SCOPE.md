# Stage 3-E Scope: Managed-Python Distribution

> **Status:** ACTIVE — Gate 1 authority design frozen; Gate 2 next
> **Input:** frozen Stage 3-D Gate 6 bounded managed-Python feasibility
> **Primary target:** Termux on Android arm64
> **Primary consumer:** uv managed-Python workflows for exact HW-T products

## Stage question

How should the bounded local-file feasibility result become a reproducible, persistent, multi-version distribution contract without reopening the frozen runtime, archive, ownership, transition, or system-Python consumer authorities?

## Gate sequence

```text
Gate 1  authority and productization-boundary design    FROZEN
Gate 2  isolated dual-version boundary census           ACTIVE NEXT
Gate 3  managed-Python distribution contract            pending
Gate 4  target implementation and lifecycle validation  pending
Gate 5  independent distribution freeze                 pending
```

## Frozen input

Stage 3-D Gate 6 proves only that uv 0.11.28 can consume one exact CPython 3.14.5 runtime-only product through a custom `linux-aarch64-none` entry and local `file://` archive in disposable directories. It does not prove production catalog publication, persistent registration, CPython 3.14.6, multi-version selection, upgrade/recovery, or network transport.

## Stage dimensions

```text
catalog identity and publication
artifact identity and transport
persistent user-level installation roots
side-by-side exact-version keys
minor/default selection semantics
install, reinstall, uninstall, upgrade, and recovery
coexistence with the frozen system-Python contract
failure preservation and rollback authority
```

Each dimension requires its own evidence. A PASS in one dimension does not authorize another.

## Gate 2 selected boundary

Gate 2 is an isolated dual-version census using the exact frozen CPython 3.14.5 and 3.14.6 runtime-only products.

Allowed:

```text
one local custom downloads JSON containing both exact keys
local file:// archives with exact SHA-256
isolated disposable install, cache, config, data, and home directories
offline explicit installs with manual download policy only for install commands
isolated list, find, launch, venv, reinstall, and uninstall probes
both installation orders
complete before/after invariant snapshots
```

Forbidden:

```text
real user managed-Python registration
$PREFIX/bin or shell startup modification
network or automatic Python acquisition
built-in uv catalog modification or uv patching
canonical product mutation
registry or journal schema change
persistent upgrade/downgrade or crash-recovery claims
root, proot, Shizuku, or Docker
```

## Required Gate 2 outputs

Gate 2 must produce a safe self-indexed PASS-or-FAIL archive that records exact product and catalog identities, every uv process record, selected interpreter paths and identities, installation tree manifests, operation order, expected negatives, and byte-exact global invariants.

## Not proved by Gate 1

This design does not prove dual-version behavior, catalog publication, persistent installation, network distribution, upgrades, recovery, default-selection policy, third-product compatibility, or upstream uv Android support.
