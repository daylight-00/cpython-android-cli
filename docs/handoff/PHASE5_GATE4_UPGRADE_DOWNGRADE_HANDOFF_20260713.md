# Phase 5 Gate 4 Upgrade and Downgrade Handoff — 2026-07-13

> **Status:** ACTIVE — second product authority and design pending
> **Prerequisite:** frozen Gate 3D final uninstall and ownership acceptance
> **Target:** Termux on Android arm64

## Frozen first-product authority

```text
product
  cpython-android-cli 3.14.6 / android24 / aarch64

Gate 3D archive sha256
  579b880495098e9a46b40e2d96c9555178d0ad8c725d40768e6b854227d66143

Gate 3D root result-index sha256
  5f9aa64cb4e0679a4784c9c3b8ebd6d8d91829704984672186dc9f9c0d96ed60

accepted repository tree
  5d54f8e0ab69ab5923949b9a5a34d71e2ab3da36

scenario / verifier / external audit
  44/44 / 138/138 / 37/37 PASS
```

## Gate 4 question

> Can one complete frozen three-artifact product be upgraded to, and downgraded from, a second complete frozen product while preserving dependency, ownership, residual, collision, transaction, recovery, and runtime-behavior boundaries?

## Required second-product authority

Gate 4 design must not begin from a synthetic version label or a manually edited copy of the first product. The second product must have its own complete, reproducible authority:

```text
runtime-base archive and manifest
complete development-addon archive and manifest
complete test-addon archive and manifest
product lock and manifest index
installation contract and ownership registry template
native closure and runtime behavior evidence
exact source/build provenance
byte-exact archive and manifest SHA-256 identities
```

The second product must be frozen independently before any upgrade or downgrade policy is accepted.

## Design inputs that remain open

The Gate 4 design must explicitly decide and verify, rather than assume:

```text
supported source and destination product identities
whole-product versus artifact-by-artifact transition order
addon compatibility across product identities
preflight rejection and collision behavior
modified-owned and unowned residual handling across versions
registry transition and product-lock replacement
PREPARED / APPLYING / COMMITTED recovery in both directions
second-recovery idempotence
runtime and addon behavior after upgrade and downgrade
rollback authority when a transition cannot commit
```

No scenario count, operation ordering, or acceptance policy is frozen yet.

## Immediate repository task

Acquire or build the second complete product authority and freeze its archives, manifests, product lock, ownership counts, native closure, runtime behavior, and provenance. Only then design the upgrade/downgrade matrix and repository verifier.

## Claim boundary

Gate 4 is authority/design pending. No upgrade, downgrade, compatibility, migration, recovery, or target acceptance claim is made by opening this handoff. Gate 3D remains frozen and must not be reopened implicitly.
