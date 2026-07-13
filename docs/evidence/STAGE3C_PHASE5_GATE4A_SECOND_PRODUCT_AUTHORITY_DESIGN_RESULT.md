# Stage 3-C Phase 5 Gate 4A Second-Product Authority Design Result

> **Status:** DESIGN FROZEN — exact input capture pending
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
A2 exact input and toolchain capture         pending
A3 clean upstream Android replay             pending
A4 three-artifact materialization            pending
A5 standalone Termux validation              pending
A6 independent archive audit and freeze      pending
```

Machine authorities:

```text
experiments/stage3c-gate4-second-product-authority/gate4a-second-product-authority-input.json
experiments/stage3c-gate4-second-product-authority/gate4a-second-product-authority-matrix.json
```

## Claim boundary

The design fixes the second-product selection and acquisition evidence contract. The second-product artifact authority is not yet created.

No runtime-base, addon archive, manifest, product lock, target behavior, compatibility, upgrade, downgrade, migration, or transition recovery claim follows from this design. Gate 4 transition design remains closed until A6 independently freezes the complete second product.
