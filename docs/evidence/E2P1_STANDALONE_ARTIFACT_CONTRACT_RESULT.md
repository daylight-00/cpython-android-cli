# E2-P1 Standalone Artifact Contract Result

> **Status:** FROZEN — repository contract verification complete
> **Base:** `a34e5fdc6224e66aa7ed335e921780fbadd728dc`, tree `7543e0a8ff86a3bee1fcda33fc86b11692c90b92`

## Result

```text
independent verifier   68/68 PASS
negative fixtures      15/15 PASS
git diff check         PASS
```

The accepted contract freezes:

```text
contract version       1
primary flavor         install_only_stripped
archive root           python/
archive format         pax-tar+zstd
payload classes        runtime + development
target triple          aarch64-linux-android
Android ABI            arm64-v8a
minimum API            24
wheel platform         android_24_arm64_v8a
primary profile        termux-cli
```

The deterministic fixture archive is safe, hash-exact, and manifest-exact. It is deliberately not CPython, its qualification status is `not-qualified`, and both the product row and release are unselectable.

## Inherited authority

E2-P1 preserves the Epoch 1 Stage 3-C ownership and transaction semantics and the Stage 3-F separation of immutable product bytes, publication snapshot, mutable locator, untrusted acquisition candidate, and verified cache.

## Claim boundary

This result proves repository contract structure, canonical JSON, deterministic fixture serialization, metadata linkage, checksum consistency, fail-closed selectability, and verifier regression behavior. It does not prove a real standalone build, Android execution, release publication, installer conversion, or uv integration.
