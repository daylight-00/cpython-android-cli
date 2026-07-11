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

The wrapper fingerprints both the candidate and frozen runtime before and after the complete workflow.

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

The complete file inventory is retained for row-level comparison. Its aggregate entry count is reported as a non-gating observation because product and generated-state differences may change that count without changing the runtime closure.

### Probe mutation diagnosis and repair

The first Gate 2 run matched every semantic closure invariant but failed the candidate mutation control.

Post-failure comparison found:

```text
file entries before   3280
file entries after    3323
delta                    43

new __pycache__ dirs      4
new .pyc files           39
```

The fresh-process probes used `python -I -S -c ...`. Isolated mode ignores `PYTHON*` environment variables, so shell-level bytecode controls did not reach those child interpreters.

The repair makes the child contract explicit:

```text
python -I -B -S -c ...
```

The candidate was freshly assembled from the promoted package before the clean rerun.

Observed clean result:

```text
candidate file entries                  3155
ELF objects                               81
DT_NEEDED edges                          329
unresolved edges                           0
Android-system SONAME dlopen             5/5
extension imports                       67/67
candidate mutation control              PASS
frozen mutation control                 PASS
machine verifier checks                37/37
```

Final markers:

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

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROBE_MUTATION_DIAGNOSIS.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_CLOSURE.md
```

## Gate 3: CA and timezone boundary equivalence

Pre-run review found that the Stage 3-A boundary probes required contract repair before promoted-runtime reuse.

```text
CA child
  -I ignored shell bytecode controls
  -> add explicit -B

zoneinfo child
  -I ignored PYTHONTZPATH, the variable under test
  -> remove isolated mode
  -> sanitize ambient PYTHON* variables
  -> use -B -P -s
  -> record observed PYTHONTZPATH and flags
```

The Gate 3 workflow runs the corrected probes against both the promoted candidate and frozen runtime control under the same Termux host state:

```sh
rm -rf \
  results/termux/stage3b-promoted-boundaries

bash \
  experiments/stage3b-target-validation/validate-promoted-boundaries.sh
```

Results:

```text
results/termux/stage3b-promoted-boundaries
```

The workflow checks:

```text
frozen CA policy matrix
candidate/frozen CA semantic equivalence
actual PYTHONTZPATH delivery for every direct zoneinfo scenario
candidate/frozen direct-zoneinfo semantic equivalence
uv-injected first-party tzdata fallback for both runtimes
uv base-prefix identity for both runtimes
candidate and frozen runtime mutation controls
```

Expected final markers:

```text
CA_BOUNDARY_EQUIVALENCE=PASS
ZONEINFO_BOUNDARY_EQUIVALENCE=PASS
TZDATA_FALLBACK_EQUIVALENCE=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

Primary machine-readable verdict:

```text
results/termux/stage3b-promoted-boundaries/promoted-boundary-verification.json
```

Detailed rationale and claim correction:

```text
docs/evidence/STAGE3B_PHASE5_BOUNDARY_PROBE_REASSESSMENT.md
```

## Gate 4: whole-prefix relocation

Relocation remains pending until Gate 3 passes or is explicitly reviewed.

The relocation workflow must move the complete promoted prefix and reconfirm:

```text
runtime identity re-roots
active sysconfig paths re-root
subprocess identity re-roots
fresh venv base identity re-roots
uv run base identity re-roots
old prefix is absent from active runtime assertions
candidate and frozen controls are not mutated unexpectedly
```
