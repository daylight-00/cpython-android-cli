# Stage 3-B Phase 4.2 Launcher Consumer Comparison

> **Status:** PASS — promoted development input accepted
> **Execution host:** Victor Linux workstation
> **Final marker:** `STAGE3B_PROMOTED_LAUNCHER_COMPARE=PASS`

## Test shape

The canonical launcher build script was invoked twice with isolated output paths:

```text
historical development prefix
    -> historical launcher candidate

promoted package-derived development prefix
    -> promoted launcher candidate
```

The compiler, source, flags, target, and build script were otherwise identical.

## Result

```text
historical size   10992 bytes
promoted size     10992 bytes

historical sha256 1854c482fec1ee111beae7255e713a61450351664dbf550ee2f075ed0ebd187d
promoted sha256   1854c482fec1ee111beae7255e713a61450351664dbf550ee2f075ed0ebd187d

exact_byte_match  true
```

Semantic checks:

```text
ELF header       PASS
dynamic tags     PASS
dynamic symbols  PASS
```

Observed dynamic contract remained:

```text
RUNPATH  $ORIGIN/../lib
NEEDED   libpython3.14.so
         libdl.so
         libm.so
         liblog.so
         libc.so
```

## Interpretation

The historical and replay `libpython3.14.so` files are byte-different but semantic-equivalent. The launcher link output is byte-identical because it consumes the same header and link-time symbol contract rather than embedding libpython bytes.

This closes the development-consumer gate:

> The promoted package-derived prefix can replace the historical experiment prefix as the canonical launcher development input without changing the launcher product.

## Workflow consequence

The active launcher build no longer needs a machine-local `CPYTHON_DEV_PREFIX` pointing into `experiments/bootstrap-android-build`.

The promoted derived prefix becomes project-defined generated state, while `CPYTHON_DEV_PREFIX_OVERRIDE` remains available only for explicit comparison experiments.
