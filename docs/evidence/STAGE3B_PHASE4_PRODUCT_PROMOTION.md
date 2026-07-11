# Stage 3-B Phase 4.2 CPython Product Promotion

> **Status:** PASS — locked package promoted
> **Execution host:** Victor Linux workstation
> **Final marker:** `STAGE3B_CPYTHON_PRODUCT_PROMOTION=PASS`

## Canonical archive

```text
out/aarch64-linux-android24/release/cpython/
  python-3.14.6-aarch64-linux-android.tar.gz
```

Identity:

```text
size    22,346,066 bytes
sha256  a16e0433b6f7e69c4634b52ce582d4d387447fbcfed797425f669ac224631f4f
```

The copied canonical archive was re-hashed after copying.

## Derived workstation development view

```text
work/workstation/stage3b-promoted-cpython/prefix
```

Launcher contract verification:

```text
Python.h          PASS
pyconfig.h        PASS
libpython3.14.so  PASS
```

The derived prefix is disposable and reproducible from the canonical archive. It is not synchronized as a canonical transport artifact.

## Product roles

```text
tracked lock
  immutable expected identity

out/.../cpython/*.tar.gz
  canonical generated transport product

work/.../stage3b-promoted-cpython/prefix
  derived Victor-side development consumer view

out/.../metadata/cpython-product.json
  generated promotion evidence
```

## Hidden-path result

The launcher development contract can now be satisfied without:

```text
experiments/bootstrap-android-build/android-python-work/prefix
```

The next gate rebuilds the launcher from both historical and promoted inputs using the same canonical build script and compares the resulting launcher products.
