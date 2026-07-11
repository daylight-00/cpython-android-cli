# Stage 3-B Phase 5 Scope: Target Runtime and Closure Equivalence

> **Status:** ACTIVE
> **Input:** isolated promoted runtime candidate
> **Execution host:** Termux on Android arm64
> **Baseline:** frozen Stage 3-A runtime and closure model

## Question

> Does the runtime assembled from promoted products preserve the frozen Stage 2 behavior and Stage 3-A closure invariants on the actual target?

## Candidate and baseline

```text
candidate
  work/termux/stage3b-promoted-runtime/prefix

baseline
  work/termux/stage2c/runtime/prefix
```

The baseline is read-only evidence during this phase.

## Validation order

```text
1. canonical behavior smoke
2. complete prefix inventory
3. ELF and DT_NEEDED closure
4. 67-extension isolated import surface
5. active runtime/sysconfig paths
6. CA and timezone boundary behavior
7. subprocess, uv and venv identity
8. whole-prefix relocation
```

A failure in an earlier gate is analyzed before later gates proceed.

## First action

Run the promoted candidate through the canonical smoke workload using isolated runtime and result roots:

```sh
bash experiments/stage3b-target-validation/smoke-promoted-runtime.sh
```

Expected final marker:

```text
STAGE3B_PROMOTED_SMOKE=PASS
```

## Acceptance conditions

```text
[ ] base runtime starts
[ ] native stdlib imports pass
[ ] HTTPS passes
[ ] subprocess re-entry passes
[ ] uv venv creation passes
[ ] venv prefix/base_prefix identity passes
[ ] uv run passes
[ ] full inventory captured
[ ] unresolved DT_NEEDED edges = 0
[ ] provider classification matches reviewed model
[ ] 67/67 extension imports pass
[ ] CA boundary preserved
[ ] timezone boundary preserved or intentionally reviewed
[ ] whole-prefix relocation passes
```
