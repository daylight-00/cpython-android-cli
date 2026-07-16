# E2-P2 Standalone Build/Package/Verify Façade

> **Status:** Gate 1 repository implementation

This experiment introduces the first stable standalone command without moving or rewriting the frozen Epoch 1 producer:

```text
components/standalone/bin/cpython-android-standalone
```

Supported operations:

```text
plan     resolve the bounded operation graph without mutation
build    run the frozen Stage 3-B workstation producer entry points
package  transform the promoted prefix and canonical launcher into E2-P1 assets
verify   verify the repository façade or one release envelope
```

Gate 1 verifies command routing, pinned predecessor entry points, deterministic package serialization, sidecar linkage, excluded payload policy, fail-closed drift detection, and archive mutation rejection with synthetic inputs.

Gate 1 does not execute the real CPython producer. Gate 2 must run `build` and `package` on the configured Linux workstation and return the exact unqualified envelope for independent review.
