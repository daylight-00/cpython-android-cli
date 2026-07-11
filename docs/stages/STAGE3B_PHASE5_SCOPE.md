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

The baseline is read-only evidence during this phase. Candidate-specific observations are written under new `results/termux/stage3b-*` directories.

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

## Gate 1 result: promoted canonical smoke

Command:

```sh
bash experiments/stage3b-target-validation/smoke-promoted-runtime.sh
```

Observed:

```text
candidate executable/prefix/base_prefix identity   PASS
native stdlib smoke                                PASS
HTTPS                                               200
subprocess identity                                PASS
uv venv creation                                   PASS
venv prefix/base_prefix identity                   PASS
uv run                                             PASS
frozen runtime mutation check                      PASS
```

Final markers:

```text
STAGE2C_SMOKE=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_SMOKE=PASS
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_SMOKE.md
```

## Current action: closure equivalence

Run:

```sh
bash experiments/stage3b-target-validation/validate-promoted-closure.sh
```

The wrapper reuses the Stage 3-A inventory, closure analysis, Android-system SONAME probe, and extension-import probe with explicit candidate paths. It records results under:

```text
results/termux/stage3b-promoted-closure
```

It must not overwrite:

```text
results/termux/stage3a-runtime-closure
work/termux/stage2c/runtime/prefix
```

## Frozen semantic closure gates

The candidate must preserve:

```text
symlink_count                              5
elf_object_count                          81
needed_edge_count                        329
classification edges
  RUNTIME_INTERNAL                        80
  ANDROID_SYSTEM                         249
unresolved_edge_count                      0
inspection_error_count                     0
unique_needed_soname_count                 9
classification unique SONAMEs
  RUNTIME_INTERNAL                         4
  ANDROID_SYSTEM                           5
Android-system SONAME dlopen              5/5
isolated extension imports              67/67
```

Active runtime identity must also point to the promoted candidate:

```text
sys.executable
sys.prefix
sys.base_prefix
sys.exec_prefix
active sysconfig paths
active lib-dynload discovery
LD_LIBRARY_PATH candidate component
Termux CA file
```

Both the candidate and frozen runtime fingerprints must remain unchanged across the workflow.

## File-entry count policy

The frozen Stage 3-A aggregate was:

```text
file_entry_count=3280
```

The new workflow captures the complete candidate `files.tsv` and reports the aggregate delta, but does not make the raw count a semantic pass/fail gate. Generated runtime state can change the aggregate without changing the ELF closure or runtime product contract.

Any count difference is retained for row-level review before Phase 5 is frozen.

## Acceptance conditions

```text
[x] base runtime starts
[x] native stdlib imports pass
[x] HTTPS passes
[x] subprocess re-entry passes
[x] uv venv creation passes
[x] venv prefix/base_prefix identity passes
[x] uv run passes
[ ] full inventory captured
[ ] unresolved DT_NEEDED edges = 0
[ ] provider classification matches reviewed model
[ ] 67/67 extension imports pass
[ ] active runtime and sysconfig paths point to candidate
[ ] candidate and frozen runtime mutation controls pass
[ ] CA boundary preserved
[ ] timezone boundary preserved or intentionally reviewed
[ ] whole-prefix relocation passes
```

Phase 5 remains active until all open conditions are either passed or explicitly reviewed and reopened.
