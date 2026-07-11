# Stage 3-B Phase 5 Target Validation

Run these gates on Termux after isolated promoted runtime assembly.

Candidate runtime:

```text
work/termux/stage3b-promoted-runtime/prefix
```

Frozen baseline:

```text
work/termux/stage2c/runtime/prefix
```

The baseline is an observation and mutation-control input only. These workflows do not write results into the frozen Stage 3-A result directory.

## Gate 1: canonical behavior smoke

```sh
bash experiments/stage3b-target-validation/smoke-promoted-runtime.sh
```

Candidate-specific results:

```text
results/termux/stage3b-promoted-smoke
```

Observed final result:

```text
STAGE2C_SMOKE=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_SMOKE=PASS
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_SMOKE.md
```

## Gate 2: inventory and native closure equivalence

```sh
bash experiments/stage3b-target-validation/validate-promoted-closure.sh
```

This thin wrapper reuses the frozen Stage 3-A engines with candidate-specific path overrides:

```text
inventory-runtime.sh
    -> complete prefix inventory
    -> ELF and DT_NEEDED census

analyze-and-probe.sh
    -> unique SONAME aggregation
    -> fresh-process Android-system SONAME dlopen probes

probe-extension-imports.sh
    -> 67 isolated fresh-process extension imports
```

Candidate-specific results:

```text
results/termux/stage3b-promoted-closure
```

The wrapper also fingerprints both the candidate and frozen runtime before and after the complete workflow.

Hard gates are the frozen semantic closure invariants:

```text
symlinks                         5
ELF objects                    81
DT_NEEDED edges              329
RUNTIME_INTERNAL edges        80
ANDROID_SYSTEM edges         249
unresolved edges               0
unique needed SONAMEs          9
runtime-internal SONAMEs       4
Android-system SONAMEs         5
system SONAME dlopen          5/5
extension imports           67/67
inspection errors              0
```

The complete file inventory is retained for row-level comparison. Its aggregate entry count is reported as a non-gating observation because generated runtime state may change that count without changing the runtime closure.

Expected final markers:

```text
UNRESOLVED_EDGE_COUNT=0
SYSTEM_SONAME_PROBE=PASS
EXTENSION_IMPORT_PROBE=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_CLOSURE=PASS
```

Primary machine-readable verdict:

```text
results/termux/stage3b-promoted-closure/promoted-closure-verification.json
```
