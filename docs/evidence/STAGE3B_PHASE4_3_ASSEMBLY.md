# Stage 3-B Phase 4.3 Promoted Runtime Assembly

> **Status:** PASS
> **Execution host:** Termux on Android arm64
> **Final marker:** `STAGE3B_PROMOTED_RUNTIME_ASSEMBLY=PASS`

## Transport

The canonical Victor handoff was pulled into the Termux checkout:

```text
out/aarch64-linux-android24/release/
  bin/python3.14
  cpython/SHA256SUMS
  cpython/python-3.14.6-aarch64-linux-android.tar.gz
  metadata/build-info.txt
  metadata/cpython-product.json
```

Observed transfer size was approximately 22.35 MB.

## Input verification

Before assembly:

```text
python-3.14.6-aarch64-linux-android.tar.gz: OK
```

The canonical assembler repeated the same SHA-256 verification before extraction.

## Isolated assembly

Candidate root:

```text
work/termux/stage3b-promoted-runtime/prefix
```

Frozen baseline root remains separate:

```text
work/termux/stage2c/runtime/prefix
```

Assembly performed:

```text
extract upstream package
verify stdlib and libpython
create prefix/bin
install promoted-input launcher
create python3 -> python3.14
create python -> python3
write runtime.env
```

Launcher identity:

```text
sha256  1854c482fec1ee111beae7255e713a61450351664dbf550ee2f075ed0ebd187d
```

This matches the verified Victor handoff.

## Exact claim

Phase 4.3 proves:

> The promoted package and launcher can be transported and assembled on Termux as an isolated runtime candidate without the historical external runtime archive.

It does not yet prove runtime behavior or closure equivalence.
