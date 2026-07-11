# Stage 3-B Phase 4.2 Canonical Workstation Handoff

> **Status:** PASS — promoted workstation products complete
> **Execution host:** Victor Linux workstation

## Canonical tree

```text
out/aarch64-linux-android24/release/
  bin/python3.14
  cpython/
    python-3.14.6-aarch64-linux-android.tar.gz
    SHA256SUMS
  metadata/
    build-info.txt
    cpython-product.json
```

## CPython product

```text
archive size    22,346,066 bytes
archive sha256  a16e0433b6f7e69c4634b52ce582d4d387447fbcfed797425f669ac224631f4f
SHA256SUMS      PASS
product pass    true
source commit   c63aec69bd59c55314c06c23f4c22c03de76fe45
target host     aarch64-linux-android
```

Launcher development contract:

```text
Python.h          PASS
pyconfig.h        PASS
libpython3.14.so  PASS
```

## Canonical launcher

```text
size    10,992 bytes
sha256  1854c482fec1ee111beae7255e713a61450351664dbf550ee2f075ed0ebd187d
target  aarch64-linux-android24
```

The canonical build metadata records:

```text
cpython_dev_prefix=
  work/workstation/stage3b-promoted-cpython/prefix
```

It does not record the historical bootstrap experiment prefix.

Dynamic contract:

```text
interpreter  /system/bin/linker64
RUNPATH      $ORIGIN/../lib
NEEDED       libpython3.14.so
             libdl.so
             libm.so
             liblog.so
             libc.so
```

## Workstation conclusion

The active workstation pipeline is now:

```text
locked source/toolchain/dependencies
    -> controlled replay
    -> locked upstream package
    -> canonical archive in out/
    -> derived promoted dev prefix in work/
    -> canonical launcher in out/
```

The historical experiment prefix and external runtime archive are no longer active canonical inputs.

Result:

```text
STAGE3B_PHASE4_2=FROZEN
STAGE3B_PHASE4_3=READY
```
