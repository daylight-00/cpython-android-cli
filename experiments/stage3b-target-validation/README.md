# Stage 3-B Phase 5 Target Validation

Run on Termux after isolated promoted runtime assembly:

```sh
bash experiments/stage3b-target-validation/smoke-promoted-runtime.sh
```

The wrapper reuses the canonical Stage 2-C smoke workload with:

```text
candidate runtime
  work/termux/stage3b-promoted-runtime

isolated results
  results/termux/stage3b-promoted-smoke
```

It fingerprints the frozen Stage 2-C runtime before and after the workload.

Expected final markers:

```text
STAGE2C_SMOKE=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_SMOKE=PASS
```
