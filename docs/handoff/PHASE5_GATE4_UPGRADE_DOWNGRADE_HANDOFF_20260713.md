# Phase 5 Gate 4 Upgrade and Downgrade Handoff — 2026-07-13

> **Status:** ACTIVE — second product authority and design pending
> **Gate 4A detail:** design frozen; A2 complete; A3 clean replay ready
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

## Selected second product

```text
version       CPython 3.14.5
upstream tag  v3.14.5
source commit 5607950ef232dad16d75c0cf53101d9649d89115
target        aarch64-linux-android / API 24
NDK           27.3.13750724
```

This is the immediate stable predecessor of the frozen 3.14.6 first product. The exact v3.14.5 `Android/android.py` declares OpenSSL 3.0.20-0 instead of first-product OpenSSL 3.5.7-0, so the second authority requires a genuine source-native replay and dependency capture.

Official Python.org source and Android package hashes are references only. The official Android package is not the project product authority.

Gate 4A sequence:

```text
A1 selection/design                  DESIGN FROZEN
A2 exact input/toolchain capture     PARTIAL
  A2a immutable remote inputs       FROZEN PASS — 81/81 external audit
  A2b Termux-native binary toolchain FROZEN PASS
A3 clean upstream replay             pending
A4 three-artifact materialization    pending
A5 standalone Termux validation      pending
A6 independent audit/freeze          pending
```

No second-product target authority exists until A6 passes.


## Accepted A2a result

```text
result archive
  20260713-gate4a-a2a-remote-input-capture-results-20260713T132628Z.tar.zst

archive sha256
  e9c9ed69098017017b3cbf70e8237c040ede26d378f6530043cc5ff4e7469caf

root result-index sha256
  5d87e7727aef99b793ac8ddacf5e9d77f96701caf2377094013753edcda17fbe

external audit
  81/81 PASS
```

The A2a collector's original 44/49 FAIL remains immutable diagnostic evidence. The five failed checks were a schema-comparison false negative: reused dependency identities and legacy archive inventory fields matched the first-product lock exactly, while the fresh capture added three valid archive-safety fields. A2a is accepted. A scoped repository authority decision also accepts A2b using the exact preserved custom-r27d Android/aarch64 binary asset and ephemeral linker overlay. A3-A6 remain open.

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

## Repository control-plane prerequisite

Before creating the second-product authority branch, reconcile the root README, current context, collaboration protocol, and default branch with the frozen Gate 3D state. This documentation/main alignment is repository governance work only and does not change any frozen product or target claim.

## Immediate repository task

Begin Gate 4A A3 clean replay on the accepted Termux-native producer host. Recreate the ephemeral r27d linker overlay from the preserved original linker, verify its exact identity, then replay the v3.14.5 producer from isolated source/build/output roots using the already accepted A2a inputs. Preserve raw commands and return codes. Do not claim a product archive until A4, and do not design upgrade/downgrade policy until A6 freezes the complete second authority.

Gate 4A machine design:

```text
experiments/stage3c-gate4-second-product-authority/gate4a-second-product-authority-input.json
experiments/stage3c-gate4-second-product-authority/gate4a-second-product-authority-matrix.json
```

## Claim boundary

Gate 4A input selection/design is frozen, but the second-product artifact authority is still pending. No second-product target authority, upgrade, downgrade, compatibility, migration, recovery, or transition acceptance claim is made by this handoff. Gate 3D remains frozen and must not be reopened implicitly.

No Gate 4 target claim is made by the Gate 4A design.
