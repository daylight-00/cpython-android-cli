# Stage 3-B Phase 4.3 Scope: Termux Promoted Runtime Assembly

> **Status:** ACTIVE
> **Input:** verified Victor workstation handoff
> **Execution host:** Termux on Android arm64
> **Isolation:** frozen Stage 2-C / Stage 3-A runtime is not modified

## Question

> Can the synchronized promoted CPython package and promoted-input launcher be assembled into a separate Termux runtime candidate without any historical external archive?

## Input tree

```text
out/aarch64-linux-android24/release/
  bin/python3.14
  cpython/python-3.14.6-aarch64-linux-android.tar.gz
  cpython/SHA256SUMS
  metadata/build-info.txt
  metadata/cpython-product.json
```

## Candidate tree

```text
work/termux/stage3b-promoted-runtime/
  prefix/
    bin/python3.14
    bin/python3 -> python3.14
    bin/python -> python3
    include/
    lib/
  runtime.env
```

## Procedure

```sh
bash scripts/sync/pull-out.sh
bash experiments/stage3b-target-assembly/prepare-promoted-runtime.sh
```

Expected marker:

```text
STAGE3B_PROMOTED_RUNTIME_ASSEMBLY=PASS
```

## Acceptance conditions

```text
[ ] Git source updated on Termux
[ ] canonical out tree synchronized from Victor
[ ] package SHA256SUMS verification passes
[ ] assembly occurs under isolated Stage 3-B root
[ ] promoted launcher installed
[ ] python3 and python symlinks created
[ ] frozen Stage 2-C / Stage 3-A runtime root not modified
```

Assembly success does not imply runtime closure equivalence.
