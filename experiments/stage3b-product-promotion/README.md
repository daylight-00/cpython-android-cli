# Stage 3-B Phase 4.2: CPython Product Promotion

The frozen Phase 4.1 result selects the replay upstream package as the direct successor product.

Run on Victor:

```sh
bash experiments/stage3b-product-promotion/promote-replay-package.sh
```

The workflow:

```text
verifies replay archive against tracked product lock
copies only the canonical archive into out/
extracts prefix/ into disposable workstation work/
verifies the launcher's three-file development contract
writes a generated product manifest
```

Outputs:

```text
out/aarch64-linux-android24/release/
  cpython/python-3.14.6-aarch64-linux-android.tar.gz
  metadata/cpython-product.json

work/workstation/stage3b-promoted-cpython/
  prefix/
```

The extracted development prefix is not transported as a canonical artifact. It is a derived workstation consumer view. The archive is the canonical transport product.

Expected marker:

```text
STAGE3B_CPYTHON_PRODUCT_PROMOTION=PASS
```
