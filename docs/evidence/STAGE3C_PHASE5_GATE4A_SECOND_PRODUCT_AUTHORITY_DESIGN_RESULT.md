# Stage 3-C Phase 5 Gate 4A Second-Product Authority Design Result

> **Status:** DESIGN FROZEN — A2 complete; A3 clean replay ready
> **Claim class:** repository design only

## Selected input

```text
CPython version  3.14.5
upstream tag     v3.14.5
source commit    5607950ef232dad16d75c0cf53101d9649d89115
target           aarch64-linux-android / API 24
NDK              27.3.13750724
```

The selection is the immediate stable predecessor of the frozen CPython 3.14.6 first product. It creates a real version boundary while keeping the minor line, target host, Android API, and NDK fixed.

## Producer boundary

```text
Android/android.py git blob
  ec4d28bbaad84d4db730678a5d627c4703bbb401

Android/android-env.sh git blob
  5859c0eac4a88fb552c495d46b77422ac5cdc2f0

v3.14.5 OpenSSL dependency
  openssl-3.0.20-0

frozen v3.14.6 OpenSSL dependency
  openssl-3.5.7-0
```

The dependency delta proves that a copied or relabeled first-product payload cannot serve as the second authority.

## Frozen acquisition design

```text
A1 selection and repository design          DESIGN FROZEN
A2 exact input and toolchain capture         FROZEN PASS
  A2a immutable remote inputs               FROZEN PASS — 81/81 external audit
  A2b Termux-native binary toolchain        FROZEN PASS — 46/46 combined audit
A3 clean upstream Android replay             READY — not started
A4 three-artifact materialization            pending
A5 standalone Termux validation              pending
A6 independent archive audit and freeze      pending
```

Machine authorities:

```text
experiments/stage3c-gate4-second-product-authority/gate4a-second-product-authority-input.json
experiments/stage3c-gate4-second-product-authority/gate4a-second-product-authority-matrix.json
```


## A2a accepted progress

```text
result archive sha256
  e9c9ed69098017017b3cbf70e8237c040ede26d378f6530043cc5ff4e7469caf

root result-index sha256
  5d87e7727aef99b793ac8ddacf5e9d77f96701caf2377094013753edcda17fbe

external audit
  81/81 PASS
```

The original A2a collector FAIL at 44/49 is preserved. Independent audit classified its five reused-dependency failures as a schema-comparison false negative and verified all intended stable fields plus the newly added safety diagnostics. A separate repository authority decision accepts A2b through the exact preserved custom-r27d Android/aarch64 binary asset and reproducible ephemeral linker overlay. A2 is complete, but the second-product artifact authority is not yet created.

## Claim boundary

The design fixes the second-product selection and acquisition evidence contract. The second-product artifact authority is not yet created.

No runtime-base, addon archive, manifest, product lock, target behavior, compatibility, upgrade, downgrade, migration, or transition recovery claim follows from this design. Gate 4 transition design remains closed until A6 independently freezes the complete second product.

## A2b scoped authority decision

The original workstation-only topology remains the historical design and the frozen first-product provenance remains unchanged. For the second product only, Gate 4A accepts a Termux-native producer exception defined by the exact preserved asset, installed-tree identity, producer run/job/commit binding, captured host tools, and one-byte ephemeral linker overlay.

```text
decision
  docs/evidence/STAGE3C_PHASE5_GATE4A_A2B_TERMUX_NATIVE_TOOLCHAIN_AUTHORITY_DECISION.md

machine authority
  experiments/stage3c-gate4-second-product-authority/gate4a-a2b-termux-native-toolchain-authority.json

external audit
  docs/evidence/STAGE3C_PHASE5_GATE4A_A2B_TERMUX_NATIVE_TOOLCHAIN_EXTERNAL_AUDIT.json
  46/46 PASS
```

No A3 or product claim follows from A2b acceptance.
