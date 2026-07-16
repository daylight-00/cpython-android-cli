# E2-P2 Gate 1: Standalone Build/Package/Verify Façade

> **Status:** FROZEN — repository façade implementation
> **Input:** E2-P1 contract at `68828691fcae382cf49b9dbc2b5231f9e21f9282`

## Question

Can the existing proven producer be exposed through stable `build`, `package`, and `verify` commands without changing the producer, runtime, installer, or frozen evidence?

## Accepted design

```text
stable command
  components/standalone/bin/cpython-android-standalone

build
  prepare-replay
  -> run-replay
  -> promote-product
  -> build-launcher
  -> deterministic build receipt

package
  promoted development prefix + canonical launcher
  -> runtime/development selection
  -> test and unsupported-GUI exclusion
  -> deterministic ELF strip step
  -> two byte-identical pax-tar+zstd serializations
  -> E2-P1 archive and sidecars
  -> unqualified, unselectable release index

verify
  repository façade authority
  or
  exact release-envelope static verification
```

The façade pins the direct Stage 3-B entry-point blobs. Drift is rejected before execution. The pinned scripts retain their own source, toolchain, package-lock, and producer-snapshot checks.

## Gate 1 verification

```text
synthetic package reproducibility     PASS
facade execution and drift rejection  PASS
archive mutation rejection            PASS
```

The package regression builds the same release assets twice and requires every byte to match. It confirms that runtime and development are present, test and unsupported GUI paths are absent, the archive has one `python/` root, and the result remains unselectable.

## Claim boundary

Gate 1 proves repository command structure and synthetic deterministic behavior. It does not prove a real CPython replay, a real standalone archive, Android execution, Termux behavior, native closure after stripping, license completeness, selectability, publication, or installer consumption.

## Next gate

E2-P2 Gate 2 runs the stable `build` and `package` operations on the configured Linux workstation. The returned release envelope remains unselectable and proceeds to independent static review before E2-P3 target qualification.
