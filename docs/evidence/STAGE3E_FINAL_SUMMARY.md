# Stage 3-E Final Summary

> **Status:** FROZEN through Gate 5 independent distribution freeze

## Final gate state

```text
Gate 1  authority and productization-boundary design    FROZEN
Gate 2  isolated dual-version boundary census           FROZEN — external re-audit 117/117
Gate 3  managed-Python distribution contract            FROZEN
Gate 4  project-owned persistent-root validation        FROZEN — target 37/37, independent 74/74
Gate 5  independent distribution freeze                 FROZEN
```

## Final accepted model

Stage 3-E proves that exact HW-T CPython 3.14.5 and 3.14.6 runtime-only products can be bound to immutable local custom-catalog rows and managed side by side by uv 0.11.28 inside an explicit project-owned persistent root on Termux.

Exact patch requests are authoritative. Minor and unspecified requests remain conditional latest-patch aliases. The persistent root survives fresh process state, supports uv virtual environments, can be relocated as a whole, preserves installed products after a failed corrupt third-artifact operation, supports strict permission-preserving backup rollback, preserves the peer across uninstall, and tears down completely.

The Stage 3-D exact-path system-Python contract remains independent and frozen. No default uv managed directory, global executable, shell startup, registry, journal, or canonical product mutation is accepted.

## Evidence identities

```text
Gate 2 target archive     3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2
Gate 2 external audit     5813305c22528354e6af686330e8f635db2b90a8a7a48ed5ed3c9ad4d1a4fb4d — 117/117
Gate 4 target archive     4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112
Gate 4 target verifier    37/37
Gate 4 independent audit  794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a — 74/74
```

## Deferred to a new stage

```text
catalog and artifact publication
network mirrors and automatic acquisition
uv default user managed-root integration
global executable exposure and shell integration
upgrade/downgrade and migration policy
crash, concurrency, and power-loss recovery
third-product compatibility
upstream uv Android-support claims
```

These questions must not be added as an implicit continuation of Stage 3-E.
