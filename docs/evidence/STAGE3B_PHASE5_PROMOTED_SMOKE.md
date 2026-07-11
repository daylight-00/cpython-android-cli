# Stage 3-B Phase 5 Promoted Runtime Smoke

> **Status:** Selected evidence
> **Stage:** 3-B Phase 5
> **Execution host:** Termux on Android arm64
> **Result:** PASS

## Question

This gate asked:

> Does the isolated runtime assembled from the promoted CPython package and promoted launcher preserve the canonical Stage 2-C CLI, HTTPS, subprocess, venv, and uv behavior without mutating the frozen runtime?

## Inputs

Candidate runtime:

```text
work/termux/stage3b-promoted-runtime/prefix
```

Candidate-specific results:

```text
results/termux/stage3b-promoted-smoke
```

Read-only frozen baseline:

```text
work/termux/stage2c/runtime/prefix
```

The command was:

```sh
bash experiments/stage3b-target-validation/smoke-promoted-runtime.sh
```

The wrapper reused `scripts/test/smoke-termux.sh` with explicit candidate runtime and result-root overrides. It did not route the workload through the frozen prefix.

## Base runtime identity

Observed:

```text
sys.executable
  work/termux/stage3b-promoted-runtime/prefix/bin/python

sys.prefix
  work/termux/stage3b-promoted-runtime/prefix

sys.base_prefix
  work/termux/stage3b-promoted-runtime/prefix

LD_LIBRARY_PATH
  work/termux/stage3b-promoted-runtime/prefix/lib

SSL_CERT_FILE
  /data/data/com.termux/files/usr/etc/tls/cert.pem
```

The exact printed paths were rooted at:

```text
/data/data/com.termux/files/home/projects/cpython-android-cli/
```

This identity is the decisive evidence that the canonical workload exercised the promoted candidate rather than the historical frozen runtime.

## Behavior result

Observed:

```text
base interpreter startup             PASS
canonical native-stdlib smoke        PASS
HTTPS                                200
subprocess interpreter identity      candidate prefix
uv venv creation                     PASS
venv sys.prefix                      candidate-specific venv
venv sys.base_prefix                 candidate prefix
uv run                               PASS
```

The uv workload installed two packages and imported `anyio` successfully from a fresh ephemeral build environment.

## uv hardlink warning

uv reported that hardlinking from its cache was unavailable and fell back to copying files.

This was a performance-path warning, not an installation or runtime failure:

```text
hardlink attempt unavailable
    -> full-copy fallback
    -> packages installed
    -> uv workload PASS
```

No runtime configuration was changed merely to suppress the warning. If the cache and environment intentionally remain on different filesystems, `UV_LINK_MODE=copy` may be used later as an explicit noise-reduction policy, but it is not required for correctness.

## Frozen baseline mutation control

The wrapper fingerprinted the frozen Stage 2-C prefix before and after the promoted workload.

Observed final markers:

```text
STAGE2C_SMOKE=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_SMOKE=PASS
```

`STAGE2C_SMOKE=PASS` is the marker emitted by the reused canonical workload. It names the workload contract; it does not mean the frozen Stage 2-C prefix was selected. The printed runtime identity above proves that the candidate prefix was selected.

## Conclusion

The promoted candidate passed the first Phase 5 gate:

> Canonical Stage 2-C behavior is preserved on the tested Termux target, and the frozen runtime remained unchanged according to the wrapper fingerprint.

This result does not yet freeze Phase 5. The next gate is complete candidate inventory, native closure aggregation, Android-system SONAME loadability, and the isolated 67-extension import surface.
